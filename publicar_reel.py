# -*- coding: utf-8 -*-
"""Reel do dia (09h BRT) no feed da @vendanaobra.

Fila fixa: os 12 cortes da participacao do Diego no Aluparts Podcast #EP25
(`reels_ep25.json`). Um por dia, na ordem escrita no arquivo, ate acabar.

Por que 09h e nao 12h: a mini-aula ocupa terca e quinta as 12h (`miniaula.yml`).
09h e o segundo melhor horario medido da conta (mediana 427 views contra 545 das
12h, no periodo organico de jul/ago) e deixa 3 horas de folga do carrossel.

Cada post entra como **colaboracao** com o perfil da Aluparts: aparece nos dois
feeds e soma o alcance dos dois publicos. O convite precisa ser aceito por
alguem de la — ate aceitar, o Reel fica so no perfil do Diego.

Uso:
    python publicar_reel.py --ensaio     # mostra o que sairia e para
    python publicar_reel.py              # proximo da fila
    python publicar_reel.py --id 05      # corte especifico
    python publicar_reel.py --garantir   # so publica se ainda nao saiu hoje

Trava: sem VNO_REEL_ATIVO=1 o script recusa publicar. E o mesmo padrao do
publicar.py — nada vai ao ar por acidente enquanto a fila esta em aprovacao.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone

BASE = os.path.dirname(os.path.abspath(__file__))
FUSO_BR = timezone(timedelta(hours=-3))

IG_USER_ID = "17841470188725651"          # @vendanaobra
API = "https://graph.facebook.com/v21.0"
REPO_RAW = "https://raw.githubusercontent.com/diegohenriquemoraes-eng/posts-vendanaobra/main"

FILA = os.path.join(BASE, "reels_ep25.json")
PLANO = os.path.join(BASE, "plano_ep25.json")
PUBLICADOS = os.path.join(BASE, "publicados_reels.json")
MIDIA = "midia/reels"                      # caminho dentro do repo


def _log(msg: str) -> None:
    print(f"[{datetime.now(FUSO_BR):%H:%M:%S}] {msg}", flush=True)


def _token() -> str:
    tok = os.environ.get("META_TOKEN", "").strip()
    if tok:
        return tok
    caminho = r"C:\Users\NOTE\Desktop\Perffec\Claude\meta_system_user_token.txt"
    if os.path.exists(caminho):
        with open(caminho, encoding="utf-8") as f:
            return f.read().strip()
    raise SystemExit("Sem token: defina META_TOKEN ou salve meta_system_user_token.txt")


def _post(endpoint: str, campos: dict) -> dict:
    dados = urllib.parse.urlencode(campos).encode()
    req = urllib.request.Request(f"{API}/{endpoint}", data=dados, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        raise SystemExit(f"Graph API falhou em {endpoint}: {e.read().decode(errors='replace')}")


def _get(endpoint: str, campos: dict) -> dict:
    url = f"{API}/{endpoint}?" + urllib.parse.urlencode(campos)
    try:
        with urllib.request.urlopen(url, timeout=60) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        raise SystemExit(f"Graph API falhou em {endpoint}: {e.read().decode(errors='replace')}")


def _carregar(caminho, padrao):
    if not os.path.exists(caminho):
        return padrao
    with open(caminho, encoding="utf-8") as f:
        return json.load(f)


def _salvar(caminho, dados) -> None:
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=1)
        f.write("\n")


def _git(*args: str) -> None:
    subprocess.run(["git", *args], cwd=BASE, check=True)


def _commitar(mensagem: str, *caminhos: str) -> None:
    _git("add", *caminhos)
    mudou = subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=BASE).returncode != 0
    if mudou:
        _git("-c", "user.name=vendanaobra-bot",
             "-c", "user.email=bot@vendanaobra.com.br", "commit", "-m", mensagem)
    _git("push", "origin", "main")


def conferir_token(token: str) -> None:
    r = _get(IG_USER_ID, {"fields": "username,followers_count", "access_token": token})
    _log(f"token ok — @{r['username']}, {r['followers_count']} seguidores")


def esperar_container(cid: str, token: str, tentativas: int = 90) -> None:
    """Video demora bem mais que imagem: a API baixa, transcodifica e so entao
    libera. 90 tentativas x 5s = ate 7min30 de folga."""
    for i in range(tentativas):
        r = _get(cid, {"fields": "status_code,status", "access_token": token})
        estado = r.get("status_code")
        if estado == "FINISHED":
            _log(f"container pronto em {i * 5}s")
            return
        if estado == "ERROR":
            raise SystemExit(f"Container {cid} falhou: {r.get('status')}")
        time.sleep(5)
    raise SystemExit(f"Container {cid} nao ficou pronto a tempo")


def _ultimo_reel(token: str) -> dict | None:
    r = _get(f"{IG_USER_ID}/media", {
        "fields": "id,media_product_type,permalink,timestamp", "limit": "3",
        "access_token": token})
    for m in r.get("data", []):
        if m.get("media_product_type") == "REELS":
            return m
    return None


def _publicar_conferindo(cid: str, token: str) -> tuple[str, str]:
    """Publica e confirma olhando o feed.

    Em 24/08/2026 o media_publish do corte 01 devolveu OAuthException code 2
    ("is_transient": true) e MESMO ASSIM publicou o Reel. Se a gente confiasse no
    erro, o retry do dia seguinte postaria o mesmo corte duas vezes. Entao: no
    erro, conferir o feed antes de desistir.
    """
    antes = _ultimo_reel(token)
    id_antes = antes["id"] if antes else None
    try:
        post = _post(f"{IG_USER_ID}/media_publish",
                     {"creation_id": cid, "access_token": token})
        agora = _ultimo_reel(token)
        return post["id"], (agora or {}).get("permalink", "")
    except SystemExit as erro:
        _log(f"media_publish devolveu erro; conferindo se publicou assim mesmo... ({erro})")
        time.sleep(20)
        depois = _ultimo_reel(token)
        if depois and depois["id"] != id_antes:
            _log("publicou — o erro era da resposta, nao da publicacao")
            return depois["id"], depois.get("permalink", "")
        raise


def _hoje() -> str:
    return datetime.now(FUSO_BR).strftime("%Y-%m-%d")


def ja_publicou_hoje() -> bool:
    return any(p["data"] == _hoje() for p in _carregar(PUBLICADOS, []))


def escolher(fila: dict, id_forcado: str | None) -> tuple[dict, bool]:
    """Proximo corte do calendario + se ele vai para o feed.

    A ordem deixou de ser a do `reels_ep25.json` em 27/08/2026: quem manda e' o
    `plano_ep25.json` (ver `plano.py`). Quase todo corte sai **so na aba de
    Reels**; so os escolhidos pelo Diego aparecem na grade do perfil, e sao
    esses — e apenas esses — que levam colab com a Aluparts.
    """
    feitos = {p["id"] for p in _carregar(PUBLICADOS, [])}
    itens = {c["id"]: c for c in fila["cortes"]}
    plano = _carregar(PLANO, [])
    if not plano:
        raise SystemExit("plano_ep25.json nao encontrado — rode `python plano.py`")
    no_feed = {d["id"]: bool(d.get("feed")) for d in plano}

    if id_forcado:
        if id_forcado not in itens:
            raise SystemExit(f"Corte {id_forcado} nao existe na fila")
        return itens[id_forcado], no_feed.get(id_forcado, False)

    # Desde 31/08/2026 a fila e' so' dos cortes de FEED, e cada um tem DATA.
    # Antes isto era posicional ("o proximo da fila") — o que, com poucos cortes
    # restando, publicaria todos em dias seguidos e ignoraria o calendario.
    hoje = _hoje()
    restantes = [d for d in plano
                 if d["id"] not in feitos and d.get("ativo", True)]
    if not restantes:
        raise SystemExit("Fila do EP25 terminou — nada a publicar.")
    vencidos = [d for d in restantes if d["dia"] <= hoje]
    if not vencidos:
        prox = min(d["dia"] for d in restantes)
        _log(f"nada marcado para hoje; o proximo e' {prox}")
        raise SystemExit(0)
    if len(restantes) <= 2:
        _log(f"AVISO: so restam {len(restantes)} cortes na fila.")
    d = vencidos[0]
    return itens[d["id"]], bool(d.get("feed"))


def _travar() -> None:
    if os.environ.get("VNO_REEL_ATIVO", "").strip() == "1":
        return
    raise SystemExit(
        "Publicacao de Reel desligada. A fila do EP25 esta em aprovacao com o Diego.\n"
        "Para publicar mesmo assim: VNO_REEL_ATIVO=1"
    )


def main() -> None:
    # o console do Windows e cp1252 e as legendas tem emoji: sem isto o
    # `--ensaio` quebra ao imprimir a legenda
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    a = argparse.ArgumentParser()
    a.add_argument("--ensaio", action="store_true")
    a.add_argument("--garantir", action="store_true")
    a.add_argument("--id")
    a = a.parse_args()

    fila = _carregar(FILA, None)
    if not fila:
        raise SystemExit("reels_ep25.json nao encontrado")

    if a.garantir and ja_publicou_hoje():
        _log("ja publicou hoje, nada a fazer")
        return

    corte, no_feed = escolher(fila, a.id)
    video = f"{REPO_RAW}/{MIDIA}/{corte['arquivo']}"
    capa = f"{REPO_RAW}/{MIDIA}/{corte['capa']}"
    # colab so nos que aparecem na grade: nos de aba de Reels o post nao entra
    # no feed de ninguem, entao marcar a Aluparts nao entrega nada a eles
    colabs = (fila.get("colaboradores") or []) if no_feed else []

    _log(f"corte {corte['id']} — {corte['titulo']} ({corte['duracao']}s)")
    _log("destino: FEED + aba de Reels" if no_feed else "destino: SO a aba de Reels (fora da grade)")
    _log(f"video: {video}")
    _log(f"capa:  {capa}")
    _log(f"colab: {', '.join(colabs) if colabs else 'NENHUM (post sai so no perfil do Diego)'}")

    if a.ensaio:
        print("\n--- legenda ---\n" + corte["legenda"] + "\n---------------\n")
        _log("ensaio: parando antes de publicar")
        return

    _travar()
    token = _token()
    conferir_token(token)

    campos = {
        "media_type": "REELS",
        "video_url": video,
        "cover_url": capa,
        "caption": corte["legenda"],
        "share_to_feed": "true" if no_feed else "false",
        "access_token": token,
    }
    if colabs:
        campos["collaborators"] = json.dumps(colabs)

    r = _post(f"{IG_USER_ID}/media", campos)
    cid = r["id"]
    _log(f"container {cid} criado, esperando o Instagram processar o video...")
    esperar_container(cid, token)

    media_id, link = _publicar_conferindo(cid, token)
    _log(f"publicado: {media_id} — {link}")

    feitos = _carregar(PUBLICADOS, [])
    feitos.append({"id": corte["id"], "slug": corte["slug"], "media_id": media_id,
                   "permalink": link, "data": _hoje(), "colaboradores": colabs,
                   "feed": no_feed})
    _salvar(PUBLICADOS, feitos)
    _commitar(f"reel {corte['id']} publicado", "publicados_reels.json")


if __name__ == "__main__":
    main()

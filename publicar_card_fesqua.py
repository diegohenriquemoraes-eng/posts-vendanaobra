# -*- coding: utf-8 -*-
"""Publica no feed da @vendanaobra o card de contagem regressiva da Fesqua.

Post de IMAGEM (nao Reel), em COLABORACAO com a @fesqua: o convite faz a peca
aparecer tambem no feed do perfil da feira — 100 mil seguidores do publico exato
do Diego, contra os ~9,3 mil dele. E por isso que o post existe; sem o convite
ele alcanca a mediana de 73 contas e nao muda nada.

O convite precisa ser ACEITO do outro lado. Ate a Fesqua aceitar, o post fica so
no perfil do Diego — nada quebra, ninguem e avisado. Se ela nunca aceitar, o
post continua valendo pelo conteudo.

Peca e legenda vivem em `fesqua_card.json`; a imagem e servida do proprio repo
(raw.githubusercontent), que e' como todo o resto deste projeto sobe para a
Graph API.

Uso:
    python publicar_card_fesqua.py --ensaio    # mostra o que sairia e para
    python publicar_card_fesqua.py             # publica (exige VNO_FESQUA_ATIVO=1)
    python publicar_card_fesqua.py --garantir  # nao publica se ja saiu hoje

Trava: sem VNO_FESQUA_ATIVO=1 o script recusa publicar — mesmo padrao do
publicar.py e do publicar_reel.py, para nada ir ao ar por acidente.
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

# o console do Windows abre em cp1252 e a legenda tem emoji: sem isto o
# --ensaio quebra no PC do Diego (no runner, que e' UTF-8, passaria batido)
for _fluxo in (sys.stdout, sys.stderr):
    try:
        _fluxo.reconfigure(encoding="utf-8")
    except AttributeError:
        pass

BASE = os.path.dirname(os.path.abspath(__file__))
FUSO_BR = timezone(timedelta(hours=-3))

IG_USER_ID = "17841470188725651"          # @vendanaobra
API = "https://graph.facebook.com/v21.0"
REPO_RAW = "https://raw.githubusercontent.com/diegohenriquemoraes-eng/posts-vendanaobra/main"

CARD = os.path.join(BASE, "fesqua_card.json")
PUBLICADOS = os.path.join(BASE, "fesqua_publicados.json")


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


def esperar_container(cid: str, token: str, tentativas: int = 30) -> None:
    """Imagem fica pronta em segundos — bem mais rapido que video."""
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


def _hoje() -> str:
    return datetime.now(FUSO_BR).strftime("%Y-%m-%d")


def _criar_container(url: str, legenda: str, colabs: list[str], token: str) -> str:
    """Cria o container da imagem; se o convite de colab for recusado, cria sem ele.

    A Graph API recusa `collaborators` quando o outro perfil bloqueia convite,
    quando ja tem convite pendente ou quando o @ esta errado. Perder o post do dia
    por causa do convite seria pior: o card e' uma contagem regressiva — amanha
    o numero ja esta errado e ele nao serve mais.
    """
    campos = {"image_url": url, "caption": legenda, "access_token": token}
    if colabs:
        try:
            return _post(f"{IG_USER_ID}/media",
                         dict(campos, collaborators=json.dumps(colabs)))["id"]
        except SystemExit as erro:
            _log(f"convite de colaboracao recusado pela API ({erro}); "
                 "publicando sem colab — marque a @fesqua na mao pelo app")
    return _post(f"{IG_USER_ID}/media", campos)["id"]


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--ensaio", action="store_true", help="mostra o que sairia e para")
    p.add_argument("--garantir", action="store_true", help="nao publica se ja saiu hoje")
    a = p.parse_args()

    card = _carregar(CARD, None)
    if not card:
        raise SystemExit("fesqua_card.json nao encontrado")

    feitos = _carregar(PUBLICADOS, [])
    if any(f["data"] == _hoje() for f in feitos) and a.garantir:
        _log("ja publicou hoje, nada a fazer")
        return
    if any(f["arquivo"] == card["arquivo"] for f in feitos):
        _log("este card ja foi publicado; nada a fazer")
        return

    # o card e' uma contagem regressiva: fora da data ele mente
    if a.garantir and card["data"] != _hoje():
        _log(f"card e' de {card['data']} e hoje e' {_hoje()} — nada a fazer")
        return

    url = f"{REPO_RAW}/{card['arquivo']}"
    colabs = card.get("colaboradores") or []
    _log(f"card:  {url}")
    _log(f"colab: {', '.join('@' + c for c in colabs) if colabs else 'NENHUM'}")

    if a.ensaio:
        print("\n--- legenda ---\n" + card["legenda"] + "\n---------------\n")
        _log("ensaio: parando antes de publicar")
        return

    if os.environ.get("VNO_FESQUA_ATIVO") != "1":
        raise SystemExit("trava: defina VNO_FESQUA_ATIVO=1 para publicar de verdade")

    token = _token()
    conferir_token(token)

    cid = _criar_container(url, card["legenda"], colabs, token)
    _log(f"container {cid} criado")
    esperar_container(cid, token)

    post = _post(f"{IG_USER_ID}/media_publish",
                 {"creation_id": cid, "access_token": token})
    media = _get(post["id"], {"fields": "permalink", "access_token": token})
    _log(f"publicado: {post['id']} — {media.get('permalink', '')}")

    feitos.append({"data": _hoje(), "arquivo": card["arquivo"],
                   "media_id": post["id"], "permalink": media.get("permalink", ""),
                   "colaboradores": colabs})
    _salvar(PUBLICADOS, feitos)
    _commitar("card da Fesqua publicado", "fesqua_publicados.json")


if __name__ == "__main__":
    main()

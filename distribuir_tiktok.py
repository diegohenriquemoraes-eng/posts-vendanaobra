"""Distribuidor — o Reel do @vendanaobra vira video no TikTok.

POR QUE ISSO EXISTE (18/09/2026)
--------------------------------
O Diego pediu "puxar automatico pro TikTok todos os videos que coloco no
Instagram", igual ao que `distribuir.py` ja faz para o YouTube. A API oficial do
TikTok (Content Posting API) so publica PUBLICO depois de uma auditoria do app
(2-4 semanas, sem garantia, e exige uma interface com seletor de privacidade,
toggles de duet/stitch, declaracao de conteudo comercial...). Sem auditoria,
tudo sai como rascunho privado (SELF_ONLY). Foi nisso que as tentativas de
julho e setembro morreram.

O CAMINHO QUE FUNCIONA SEM AUDITORIA: um intermediario que JA passou por ela.
O Zernio (ex-Late, zernio.com) tem app do TikTok auditado, API REST, e as duas
primeiras contas conectadas sao gratis com posts ilimitados (pricing de
06/05/2026: "your first 2 accounts are free"; teto de 15 videos/dia no TikTok
para o tier gratis). Ou seja: o Diego conecta o TikTok @vendanaobra no Zernio
UMA vez, gera uma chave, e este script faz o resto na nuvem, sem PC ligado.

O DESENHO, E O MOTIVO DE CADA ESCOLHA
-------------------------------------
- A fonte e a CONTA do Instagram, nao o motor (mesma regra do distribuir.py):
  entra o Reel que o Diego posta na mao pelo celular.
- O video vem de `media_url` da Graph API — renditizacao limpa, SEM a marca
  d'agua "@usuario" que o botao "salvar" do app carimba. Video com marca de
  outra plataforma e penalizado no TikTok tanto quanto no YouTube.
- O arquivo e baixado no runner e subido ao armazenamento do Zernio (presign +
  PUT), nao passado por URL: a `media_url` do Instagram expira em horas e o
  Zernio so busca a URL na hora de publicar. Se a publicacao atrasar, a URL
  morta viraria post falhado.
- SEM link na legenda. No TikTok a URL em texto nao e clicavel e e penalizada.
  O link do Raio-X vai no campo "site" do perfil (Conta Comercial), nao aqui.
- Mencoes "@fulano" do Instagram perdem o "@": no TikTok marcariam OUTRA pessoa
  (ou ninguem). O credito fica como texto.
- Teto de 3 por dia. Nao e cota (o Zernio da 15): e a leitura de spam do
  TikTok numa conta nova/dormente recebendo rajada. O acervo escoa aos poucos,
  do Reel mais novo para o mais antigo — quem publica quer ver o video de HOJE
  no ar hoje.
- `distribuidos_tiktok.json` e versionado como o `distribuidos.json`: o runner
  e descartavel; sem o estado commitado a proxima execucao republicaria.

Uso:
    python distribuir_tiktok.py --contas          # lista as contas ligadas no Zernio
    python distribuir_tiktok.py --ensaio          # mostra o que subiria (so precisa do META_TOKEN)
    python distribuir_tiktok.py                   # sobe 1
    python distribuir_tiktok.py --limite 2 --dias 60

Variaveis: META_TOKEN (Graph API), ZERNIO_API_KEY (sk_...),
ZERNIO_TIKTOK_ACCOUNT_ID (opcional; sem ela, usa a unica conta TikTok ativa).
"""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import re
import sys
import tempfile
import time
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone

# Reaproveita coleta e limpeza de legenda do distribuidor do YouTube: a fonte
# (Graph API) e a mesma e a regra "linha util" tambem.
from distribuir import _linhas_uteis, coletar  # noqa: E402

AQUI = pathlib.Path(__file__).parent
ESTADO = AQUI / "distribuidos_tiktok.json"

ZERNIO = "https://zernio.com/api/v1"

# TETO DIARIO: leitura de spam do TikTok, nao cota. Conta nova/dormente que
# recebe 10 videos num dia e assinatura de robo. 3/dia escoa o acervo em
# semanas sem parecer despejo.
TETO_DIA = 3

# Depois de 2 falhas no mesmo Reel (conteudo duplicado, moderacao, video curto
# demais), para de insistir: cada tentativa gasta uma das vagas do dia.
MAX_TENTATIVAS = 2

# REEL DO DIA NUNCA ESPERA O TETO (19/09/2026). Na noite da carga inicial os 15
# do acervo subiram entre 02h e 03h UTC de 19/09 e contaram como "enviados
# hoje": as cinco janelas do dia leram 15/3 e pararam, e os Reels que o Diego
# postou em 19/09 ficaram no Instagram sem ir para o TikTok. O teto existe para
# o ACERVO escoar devagar; o que foi postado agora e o que o Diego quer ver no
# ar hoje, e 2-4 por dia e o ritmo normal da conta, nao rajada. Vale para
# Threads e Pinterest tambem (importam daqui).
RECENTE_H = 36
TETO_API_TIKTOK = 15  # teto da propria API do TikTok no Zernio

HASHTAGS_FIXAS = ["vendas", "esquadrias", "construcaocivil"]
MAX_HASHTAGS = 5
MAX_LEGENDA = 1000  # o TikTok aceita 2.200; acima de ~1.000 ninguem le no feed


# --------------------------------------------------------------------------- #
# Legenda
# --------------------------------------------------------------------------- #
def montar_legenda(legenda_ig: str) -> str | None:
    """Legenda do TikTok a partir da do Instagram.

    Devolve None quando nao ha texto aproveitavel (Reel so com "@vendanaobra").
    Video sem legenda no TikTok ate sai, mas nao tem gancho escrito nem termo
    de busca — melhor pular, como o YouTube ja faz.
    """
    linhas = _linhas_uteis(legenda_ig)
    if not linhas:
        return None

    corpo = "\n\n".join(linhas[:5])
    corpo = re.sub(r"https?://\S+", "", corpo)          # URL em texto e penalizada
    corpo = re.sub(r"(?<!\w)@([\w.]+)", r"\1", corpo)    # @ do Instagram nao vale aqui
    corpo = re.sub(r"[ \t]+\n", "\n", corpo).strip()
    if len(corpo) > MAX_LEGENDA:
        corpo = corpo[: MAX_LEGENDA - 1].rsplit(" ", 1)[0] + "…"

    achadas = [t.lower() for t in re.findall(r"#(\w+)", legenda_ig or "")]
    tags, vistas = [], set()
    for t in HASHTAGS_FIXAS + achadas:
        if t not in vistas and len(tags) < MAX_HASHTAGS:
            vistas.add(t)
            tags.append(t)

    return f"{corpo}\n\n" + " ".join(f"#{t}" for t in tags)


def e_do_dia(midia: dict, horas: int = RECENTE_H) -> bool:
    """Reel publicado no Instagram ha menos de `horas` — passa na frente do teto."""
    quando = datetime.fromisoformat(midia["timestamp"].replace("+0000", "+00:00"))
    return quando >= datetime.now(timezone.utc) - timedelta(hours=horas)


def selecionar(pendentes: list[dict], limite: int, teto: int, teto_api: int,
               saiu_hoje: int) -> list[dict]:
    """Quem sai nesta execucao: TODO Reel do dia (ate o teto da API) e, do
    acervo, ate `limite` respeitando o teto diario. Usado pelos 3 distribuidores."""
    do_dia = [m for m in pendentes if e_do_dia(m)]
    acervo = [m for m in pendentes if not e_do_dia(m)]
    vaga_api = max(teto_api - saiu_hoje, 0)
    escolhidos = do_dia[:vaga_api]
    resta = max(teto - saiu_hoje - len(escolhidos), 0)
    escolhidos += acervo[:min(limite, resta)]
    return escolhidos


# --------------------------------------------------------------------------- #
# Zernio
# --------------------------------------------------------------------------- #
def chave_zernio() -> str:
    return os.environ.get("ZERNIO_API_KEY", "").strip()


def _zernio(metodo: str, caminho: str, corpo: dict | None = None) -> tuple[int, dict]:
    dados = json.dumps(corpo).encode("utf-8") if corpo is not None else None
    req = urllib.request.Request(
        f"{ZERNIO}{caminho}",
        data=dados,
        method=metodo,
        headers={
            "Authorization": f"Bearer {chave_zernio()}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "VendaNaObra-Distribuidor/1.0",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return r.status, json.load(r)
    except urllib.error.HTTPError as e:
        try:
            detalhe = json.load(e)
        except Exception:
            detalhe = {"erro": e.read().decode("utf-8", "replace")[:500]}
        return e.code, detalhe


def contas_tiktok() -> list[dict]:
    status, resp = _zernio("GET", "/accounts?platform=tiktok")
    if status != 200:
        sys.exit(f"Zernio /accounts devolveu {status}: {resp}")
    return [c for c in resp.get("accounts", []) if c.get("platform") == "tiktok"]


def conta_tiktok() -> dict:
    """A conta TikTok que recebe os videos.

    Trava de seguranca (mesma logica do YT_CANAL do distribuir.py): se houver
    mais de uma conta TikTok ligada e nenhuma escolhida por variavel, para —
    publicar no perfil errado ja aconteceu uma vez neste projeto.
    """
    contas = contas_tiktok()
    ativas = [c for c in contas if c.get("isActive", True) and c.get("enabled", True)]
    alvo = os.environ.get("ZERNIO_TIKTOK_ACCOUNT_ID", "").strip()
    if alvo:
        for c in contas:
            if c.get("_id") == alvo:
                return c
        sys.exit(f"ZERNIO_TIKTOK_ACCOUNT_ID={alvo} nao esta entre as contas ligadas.")
    if not ativas:
        sys.exit("Nenhuma conta TikTok ativa no Zernio. Conecte o @vendanaobra em zernio.com.")
    if len(ativas) > 1:
        nomes = ", ".join(f"{c.get('username')} ({c.get('_id')})" for c in ativas)
        sys.exit(f"Mais de uma conta TikTok ligada ({nomes}); defina ZERNIO_TIKTOK_ACCOUNT_ID.")
    return ativas[0]


def subir_midia(caminho: pathlib.Path) -> str:
    """Presign → PUT direto no storage → publicUrl estavel para o post."""
    tamanho = caminho.stat().st_size
    status, resp = _zernio(
        "POST",
        "/media/presign",
        {"filename": caminho.name, "contentType": "video/mp4", "size": tamanho},
    )
    if status != 200 or not resp.get("uploadUrl"):
        sys.exit(f"Zernio /media/presign devolveu {status}: {resp}")

    req = urllib.request.Request(
        resp["uploadUrl"],
        data=caminho.read_bytes(),
        method="PUT",
        headers={"Content-Type": "video/mp4"},
    )
    with urllib.request.urlopen(req, timeout=600) as r:
        if r.status not in (200, 201, 204):
            sys.exit(f"PUT no storage do Zernio devolveu {r.status}")
    return resp["publicUrl"]


def publicar_tiktok(conta: dict, url_video: str, legenda: str) -> tuple[bool, dict]:
    """publishNow: 201 = publicou, 207 = pelo menos uma plataforma falhou."""
    corpo = {
        "content": legenda,
        "mediaItems": [{"type": "video", "url": url_video}],
        "platforms": [{"platform": "tiktok", "accountId": conta["_id"]}],
        # Os dois ultimos sao a declaracao legal que a auditoria do TikTok exige
        # de quem publica; no Zernio ela e passada aqui, por post.
        "tiktokSettings": {
            "privacy_level": "PUBLIC_TO_EVERYONE",
            "allow_comment": True,
            "allow_duet": True,
            "allow_stitch": True,
            "content_preview_confirmed": True,
            "express_consent_given": True,
        },
        "publishNow": True,
    }
    status, resp = _zernio("POST", "/posts", corpo)
    post = resp.get("post", resp)
    plataformas = post.get("platforms") or []
    tk = next((p for p in plataformas if p.get("platform") == "tiktok"), {})
    if status in (200, 201) and post.get("status") not in ("failed", "partial"):
        return True, {"post_id": post.get("_id"), "url": tk.get("platformPostUrl")}
    # O TETO DE 15 DO TIKTOK E JANELA MOVEL DE 24 H, NAO DIA UTC (pago em
    # 20/09/2026, 00:05 UTC): a carga inicial das 02h-03h de 19/09 ainda contava
    # e o Zernio respondeu 207 com o post "pending", `tiktokBusinessCapDeferredUntil`
    # e "queued and will publish automatically after ...". O Zernio publica sozinho
    # na hora; criar outro post seria video DUPLICADO no TikTok. Fica PENDENTE e a
    # proxima rodada confere (`resolver_pendentes`), como o Pinterest ja fazia.
    if post.get("_id") and (
        tk.get("status") in ("pending", "processing", "uploading", "scheduled")
        or post.get("status") in ("publishing", "scheduled")
    ):
        return None, {"post_id": post["_id"], "erro": tk.get("errorMessage"),
                      "quando": (tk.get("platformSpecificData") or {}).get("tiktokBusinessCapDeferredUntil")
                      or tk.get("scheduledFor")}
    return False, {
        "http": status,
        "status": post.get("status"),
        "erro": tk.get("errorMessage") or resp.get("message") or resp.get("error") or str(resp)[:300],
        "post_id": post.get("_id"),
    }


def consultar(post_id: str) -> tuple[bool | None, dict]:
    """True publicado / False falhou / None ainda na fila ou processando."""
    status, resp = _zernio("GET", f"/posts/{post_id}")
    if status != 200:
        return None, {"post_id": post_id}
    post = resp.get("post", {})
    tk = next((p for p in (post.get("platforms") or []) if p.get("platform") == "tiktok"), {})
    if tk.get("status") == "published" or post.get("status") == "published":
        return True, {"post_id": post_id, "url": tk.get("platformPostUrl")}
    if tk.get("status") in ("failed", "cancelled") or post.get("status") in ("failed", "cancelled"):
        return False, {"post_id": post_id, "erro": tk.get("errorMessage") or post.get("status")}
    return None, {"post_id": post_id, "erro": tk.get("errorMessage")}


def resolver_pendentes(estado: dict) -> None:
    """Posts que ficaram na fila do Zernio (teto movel do TikTok): publicou? falhou?"""
    for mid, reg in estado.items():
        if not reg.get("pendente"):
            continue
        r, info = consultar(reg["zernio_post"])
        if r is True:
            reg.pop("pendente", None)
            reg["tiktok"] = info.get("url") or True
            print(f"  pendente resolvido: {reg.get('permalink')} -> {reg['tiktok']}")
        elif r is False:
            reg.pop("pendente", None)
            reg["tentativas"] = reg.get("tentativas", 0) + 1
            reg["erro"] = info.get("erro")
            print(f"  pendente FALHOU: {reg.get('permalink')} — {reg['erro']}")


def esperar_url(post_id: str, segundos: int = 150) -> str | None:
    """O TikTok processa depois do 201; a URL final chega em minutos."""
    fim = time.time() + segundos
    while time.time() < fim:
        status, resp = _zernio("GET", f"/posts/{post_id}")
        if status == 200:
            for p in resp.get("post", {}).get("platforms", []):
                if p.get("platform") == "tiktok":
                    if p.get("platformPostUrl"):
                        return p["platformPostUrl"]
                    if p.get("status") == "failed":
                        return None
        time.sleep(15)
    return None


# --------------------------------------------------------------------------- #
def carregar_estado() -> dict:
    if ESTADO.exists():
        return json.loads(ESTADO.read_text(encoding="utf-8"))
    return {}


def gravar_estado(estado: dict) -> None:
    ESTADO.write_text(json.dumps(estado, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--ensaio", action="store_true", help="mostra sem publicar")
    p.add_argument("--contas", action="store_true", help="lista as contas ligadas no Zernio")
    p.add_argument("--limite", type=int, default=1, help="quantos por execucao")
    p.add_argument("--dias", type=int, default=45, help="janela de coleta")
    p.add_argument("--id", help="forcar um id de midia do Instagram")
    p.add_argument("--ordem", choices=["novo", "antigo"], default="novo")
    # --teto e --pausa existem para a carga inicial do acervo (19/09/2026, o Diego
    # pediu os ultimos 15 de uma vez). O cron NAO os usa: no dia a dia vale TETO_DIA.
    p.add_argument("--teto", type=int, default=TETO_DIA,
                   help="teto diario so nesta execucao (o TikTok aceita 15/dia)")
    p.add_argument("--pausa", type=int, default=0,
                   help="segundos entre um video e outro")
    args = p.parse_args()

    if args.contas:
        if not chave_zernio():
            sys.exit("ZERNIO_API_KEY nao definida.")
        for c in contas_tiktok():
            print(f"{c.get('_id')}  @{c.get('username')}  ativa={c.get('isActive')}  "
                  f"seguidores={c.get('followersCount')}")
        return

    if not args.ensaio and not chave_zernio():
        # Antes de o Diego conectar o TikTok no Zernio o cron roda em vao; sair
        # limpo aqui evita uma issue de "falhou" por dia sem motivo.
        print("ZERNIO_API_KEY nao definida — aguardando a conta do Zernio. Nada feito.")
        return

    estado = carregar_estado()
    if not args.ensaio and chave_zernio():
        resolver_pendentes(estado)
        gravar_estado(estado)
    reels = coletar(args.dias)
    if args.id:
        reels = [m for m in reels if m["id"] == args.id]

    def elegivel(m: dict) -> bool:
        reg = estado.get(m["id"])
        if not reg:
            return True
        if reg.get("tiktok") or reg.get("pulado") or reg.get("pendente"):
            return False
        return reg.get("tentativas", 0) < MAX_TENTATIVAS

    pendentes = [m for m in reels if elegivel(m)]
    if args.ordem == "antigo":
        pendentes = pendentes[::-1]

    hoje = datetime.now(timezone.utc).date().isoformat()
    saiu_hoje = sum(
        1 for v in estado.values()
        if (v.get("distribuido_em") or v.get("tentado_em") or "").startswith(hoje)
        and not v.get("pulado")
    )
    teto = min(args.teto, TETO_API_TIKTOK)
    escolhidos = selecionar(pendentes, args.limite, teto, TETO_API_TIKTOK, saiu_hoje)
    do_dia = sum(1 for m in escolhidos if e_do_dia(m))

    print(
        f"{len(reels)} Reels na janela de {args.dias} dias · {len(pendentes)} ainda nao "
        f"distribuidos · {saiu_hoje}/{teto} enviados hoje · {do_dia} do dia nesta rodada"
    )
    if not pendentes:
        print("Nada a fazer.")
        return
    if not escolhidos:
        print(f"Teto diario de {teto} atingido (acervo). Volta na proxima rodada.")
        return

    conta = None if args.ensaio else conta_tiktok()
    if conta:
        print(f"Conta TikTok: @{conta.get('username')} ({conta['_id']})")

    for i, midia in enumerate(escolhidos):
        if i and args.pausa:
            time.sleep(args.pausa)
        legenda_ig = midia.get("caption") or ""
        legenda = montar_legenda(legenda_ig)
        print(f"\n[{midia['timestamp'][:10]}] {midia['permalink']}")

        if legenda is None:
            print("  pulado: legenda sem texto")
            if not args.ensaio:
                estado[midia["id"]] = {"pulado": "sem legenda", "permalink": midia["permalink"]}
                gravar_estado(estado)
            continue

        print("  legenda: " + legenda.replace("\n", " ⏎ ")[:160])
        if args.ensaio:
            print("  (ensaio: nada foi publicado)")
            continue

        with tempfile.TemporaryDirectory() as tmp:
            destino = pathlib.Path(tmp) / f"reel-{midia['id']}.mp4"
            urllib.request.urlretrieve(midia["media_url"], destino)
            print(f"  baixado: {destino.stat().st_size / 1e6:.1f} MB")
            url_video = subir_midia(destino)
            print("  no storage do Zernio")

        ok, info = publicar_tiktok(conta, url_video, legenda)
        agora = datetime.now(timezone.utc).isoformat(timespec="seconds")
        reg = estado.get(midia["id"], {})
        if ok is None:
            print(f"  na fila do Zernio (teto movel do TikTok); publica sozinho em "
                  f"{info.get('quando') or 'breve'} — a proxima rodada confere")
            estado[midia["id"]] = {
                "pendente": True,
                "zernio_post": info.get("post_id"),
                "permalink": midia["permalink"],
                "publicado_ig": midia["timestamp"],
                "distribuido_em": agora,
            }
            gravar_estado(estado)
            continue
        if ok:
            url = info.get("url") or (esperar_url(info["post_id"]) if info.get("post_id") else None)
            print(f"  TikTok: {url or '(publicado; URL ainda processando)'}")
            estado[midia["id"]] = {
                "tiktok": url or True,
                "zernio_post": info.get("post_id"),
                "permalink": midia["permalink"],
                "publicado_ig": midia["timestamp"],
                "distribuido_em": agora,
            }
        else:
            tent = reg.get("tentativas", 0) + 1
            print(f"  FALHOU ({tent}/{MAX_TENTATIVAS}): {info.get('erro')}")
            estado[midia["id"]] = {
                "tentativas": tent,
                "erro": info.get("erro"),
                "zernio_post": info.get("post_id"),
                "permalink": midia["permalink"],
                "tentado_em": agora,
            }
        gravar_estado(estado)
        if not ok:
            sys.exit(1)  # o workflow abre issue; o estado ja esta gravado


if __name__ == "__main__":
    main()

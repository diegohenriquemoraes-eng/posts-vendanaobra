"""Distribuidor — o Reel do @vendanaobra vira Pin de video no Pinterest (via Zernio).

POR QUE ISSO EXISTE (19/09/2026)
--------------------------------
Decisao do Diego: abrir o Pinterest com os mesmos Reels. O Pinterest e BUSCADOR
(o Pin ranqueia no Google e continua sendo achado meses depois) e o nicho de
vendas para construcao nao esta la. A API propria e sandbox (o Pin so aparece
para o dono) — pelo Zernio isso some, e a conta ocupa a 2a vaga gratis.

O DESENHO
---------
- Fonte: a conta do Instagram (Graph API), como nos irmaos.
- TITULO de busca (ate 100 chars) reescrito pelo Groq via `titulo_para_busca`
  do distribuidor do YouTube — no Pinterest quem traz gente e a frase digitada.
- DESCRICAO ate 800 chars: legenda limpa (sem URL, sem @).
- LINK do Pin (clicavel, e o que importa aqui): `/r/pi-raiox`. O medidor do site
  so aceita canais de uma lista fixa; o Pinterest entra como `outro/pinterest`
  para nao mexer no coletor.
- CAPA: `thumbnail_url` do Reel (o frame que o Diego escolheu no app).
- Video baixado no runner e hospedado no Zernio (presign), como no TikTok.
- Teto de 3/dia; estado em `distribuidos_pinterest.json`.

Uso:
    python distribuir_pinterest.py --contas       # contas e boards no Zernio
    python distribuir_pinterest.py --ensaio
    python distribuir_pinterest.py --limite 15 --teto 15 --pausa 30

Variaveis: META_TOKEN, ZERNIO_API_KEY, GROQ_API_KEY (titulo), opcionais
ZERNIO_PINTEREST_ACCOUNT_ID e ZERNIO_PINTEREST_BOARD_ID (sem elas: a unica
conta Pinterest ativa e o primeiro board dela).
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
import urllib.parse
import urllib.request
from datetime import datetime, timezone

from distribuir import GRAPH, _linhas_uteis, coletar, titulo_para_busca, token_meta  # noqa: E402
from distribuir_tiktok import _zernio, chave_zernio, subir_midia  # noqa: E402

AQUI = pathlib.Path(__file__).parent
ESTADO = AQUI / "distribuidos_pinterest.json"

LINK = "https://vendanaobra.com.br/r/pi-raiox"
TETO_DIA = 3
MAX_TENTATIVAS = 2
MAX_DESCRICAO = 800


def montar_descricao(legenda_ig: str) -> str | None:
    linhas = _linhas_uteis(legenda_ig)
    if not linhas:
        return None
    corpo = "\n\n".join(linhas[:5])
    corpo = re.sub(r"https?://\S+", "", corpo)
    corpo = re.sub(r"(?<!\w)@([\w.]+)", r"\1", corpo)
    corpo = re.sub(r"[ \t]+\n", "\n", corpo).strip()
    rodape = "\n\nDiego Moraes, Venda na Obra. Raio-X comercial grátis no link."
    teto = MAX_DESCRICAO - len(rodape)
    if len(corpo) > teto:
        corpo = corpo[: teto - 1].rsplit(" ", 1)[0] + "…"
    return corpo + rodape


def thumbnail(media_id: str) -> str | None:
    url = f"{GRAPH}/{media_id}?" + urllib.parse.urlencode(
        {"fields": "thumbnail_url", "access_token": token_meta()}
    )
    try:
        with urllib.request.urlopen(url, timeout=30) as r:
            return json.load(r).get("thumbnail_url")
    except Exception:
        return None


def contas_pinterest() -> list[dict]:
    status, resp = _zernio("GET", "/accounts?platform=pinterest")
    if status != 200:
        sys.exit(f"Zernio /accounts devolveu {status}: {resp}")
    return [c for c in resp.get("accounts", []) if c.get("platform") == "pinterest"]


def _boards(conta_id: str) -> list[dict]:
    status, resp = _zernio("GET", f"/accounts/{conta_id}/pinterest-boards")
    if status != 200:
        return []
    if isinstance(resp, list):
        return resp
    return resp.get("boards") or resp.get("data") or []


def conta_e_board() -> tuple[dict, str] | None:
    """None enquanto o Diego nao conectar o Pinterest no Zernio (sai limpo)."""
    contas = [c for c in contas_pinterest() if c.get("isActive", True)]
    alvo = os.environ.get("ZERNIO_PINTEREST_ACCOUNT_ID", "").strip()
    if alvo:
        contas = [c for c in contas if c.get("_id") == alvo]
    if not contas:
        print("Nenhuma conta Pinterest no Zernio ainda. Nada feito.")
        return None
    if len(contas) > 1:
        sys.exit("Mais de uma conta Pinterest; defina ZERNIO_PINTEREST_ACCOUNT_ID.")
    conta = contas[0]
    board = os.environ.get("ZERNIO_PINTEREST_BOARD_ID", "").strip()
    if not board:
        boards = _boards(conta["_id"])
        if not boards:
            sys.exit("A conta Pinterest nao tem board; crie um (ex.: 'Venda na Obra') e rode de novo.")
        board = boards[0].get("id") or boards[0].get("_id")
    return conta, board


def publicar(conta: dict, board: str, url_video: str, titulo: str, descricao: str,
             capa: str | None) -> tuple[bool, dict]:
    dados = {"title": titulo[:100], "boardId": board, "link": LINK}
    if capa:
        dados["coverImageUrl"] = capa
    corpo = {
        "content": descricao,
        "mediaItems": [{"type": "video", "url": url_video}],
        "platforms": [{"platform": "pinterest", "accountId": conta["_id"],
                       "platformSpecificData": dados}],
        "publishNow": True,
    }
    status, resp = _zernio("POST", "/posts", corpo)
    post = resp.get("post", resp)
    pl = next((p for p in (post.get("platforms") or []) if p.get("platform") == "pinterest"), {})
    if status in (200, 201) and post.get("status") not in ("failed", "partial"):
        return True, {"post_id": post.get("_id"), "url": pl.get("platformPostUrl")}
    # O Pinterest processa video devagar. O Zernio devolve 207 com o post em
    # "publishing"/"pending" e a mensagem "processing timeout... Will retry with
    # backoff": NAO e falha, e fila. Espera um pouco; se nao resolver, fica
    # PENDENTE e a proxima rodada consulta (`resolver_pendentes`).
    if post.get("_id") and (post.get("status") in ("publishing", "scheduled")
                            or pl.get("status") in ("pending", "processing", "uploading")):
        estado_final = esperar(post["_id"], 240)
        if estado_final is not None:
            return estado_final
        return None, {"post_id": post["_id"], "erro": pl.get("errorMessage")}
    return False, {"http": status, "erro": pl.get("errorMessage") or resp.get("message") or str(resp)[:300],
                   "post_id": post.get("_id")}


def consultar(post_id: str) -> tuple[bool | None, dict]:
    """True publicado / False falhou / None ainda processando."""
    status, resp = _zernio("GET", f"/posts/{post_id}")
    if status != 200:
        return None, {"post_id": post_id}
    post = resp.get("post", {})
    pl = next((p for p in (post.get("platforms") or []) if p.get("platform") == "pinterest"), {})
    if pl.get("status") == "published" or post.get("status") == "published":
        return True, {"post_id": post_id, "url": pl.get("platformPostUrl")}
    if pl.get("status") in ("failed", "cancelled") or post.get("status") in ("failed", "cancelled"):
        return False, {"post_id": post_id, "erro": pl.get("errorMessage") or post.get("status")}
    return None, {"post_id": post_id, "erro": pl.get("errorMessage")}


def esperar(post_id: str, segundos: int) -> tuple[bool, dict] | None:
    fim = time.time() + segundos
    while time.time() < fim:
        time.sleep(20)
        r, info = consultar(post_id)
        if r is not None:
            return r, info
    return None


def resolver_pendentes(estado: dict) -> None:
    for mid, reg in estado.items():
        if not reg.get("pendente"):
            continue
        r, info = consultar(reg["zernio_post"])
        if r is True:
            reg.pop("pendente", None)
            reg["pinterest"] = info.get("url") or True
            print(f"  pendente resolvido: {reg.get('permalink')} -> {reg['pinterest']}")
        elif r is False:
            reg.pop("pendente", None)
            reg["tentativas"] = reg.get("tentativas", 0) + 1
            reg["erro"] = info.get("erro")
            print(f"  pendente FALHOU: {reg.get('permalink')} — {reg['erro']}")


def carregar_estado() -> dict:
    return json.loads(ESTADO.read_text(encoding="utf-8")) if ESTADO.exists() else {}


def gravar_estado(estado: dict) -> None:
    ESTADO.write_text(json.dumps(estado, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--ensaio", action="store_true")
    p.add_argument("--contas", action="store_true")
    p.add_argument("--limite", type=int, default=1)
    p.add_argument("--dias", type=int, default=45)
    p.add_argument("--id")
    p.add_argument("--ordem", choices=["novo", "antigo"], default="novo")
    p.add_argument("--teto", type=int, default=TETO_DIA)
    p.add_argument("--pausa", type=int, default=0)
    args = p.parse_args()

    if args.contas:
        for c in contas_pinterest():
            print(f"{c.get('_id')}  @{c.get('username')}  ativa={c.get('isActive')}")
            for b in _boards(c["_id"]):
                print(f"  board {b.get('id') or b.get('_id')}  {b.get('name')}")
        return

    if not args.ensaio and not chave_zernio():
        print("ZERNIO_API_KEY nao definida. Nada feito.")
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
        if reg.get("pinterest") or reg.get("pulado") or reg.get("pendente"):
            return False
        return reg.get("tentativas", 0) < MAX_TENTATIVAS

    pendentes = [m for m in reels if elegivel(m)]
    if args.ordem == "antigo":
        pendentes = pendentes[::-1]

    hoje = datetime.now(timezone.utc).date().isoformat()
    saiu_hoje = sum(
        1 for v in estado.values()
        if (v.get("distribuido_em") or v.get("tentado_em") or "").startswith(hoje) and not v.get("pulado")
    )
    teto = min(args.teto, 25)  # 25 e o teto diario do Pinterest no Zernio
    resta = max(teto - saiu_hoje, 0)
    print(f"{len(reels)} Reels na janela de {args.dias} dias · {len(pendentes)} ainda nao "
          f"distribuidos · {saiu_hoje}/{teto} enviados hoje")
    if not pendentes:
        print("Nada a fazer.")
        return
    if resta == 0:
        print(f"Teto diario de {teto} atingido. Volta na proxima rodada.")
        return

    conta = board = None
    if not args.ensaio:
        par = conta_e_board()
        if par is None:
            return
        conta, board = par
        print(f"Conta Pinterest: @{conta.get('username')} · board {board}")

    for i, midia in enumerate(pendentes[: min(args.limite, resta)]):
        if i and args.pausa:
            time.sleep(args.pausa)
        legenda_ig = midia.get("caption") or ""
        titulo = titulo_para_busca(legenda_ig)
        descricao = montar_descricao(legenda_ig)
        print(f"\n[{midia['timestamp'][:10]}] {midia['permalink']}")
        if titulo is None or descricao is None:
            print("  pulado: legenda sem texto")
            if not args.ensaio:
                estado[midia["id"]] = {"pulado": "sem legenda", "permalink": midia["permalink"]}
                gravar_estado(estado)
            continue
        print(f"  titulo: {titulo}")
        if args.ensaio:
            print("  (ensaio: nada foi publicado)")
            continue

        capa = thumbnail(midia["id"])
        with tempfile.TemporaryDirectory() as tmp:
            destino = pathlib.Path(tmp) / f"reel-{midia['id']}.mp4"
            urllib.request.urlretrieve(midia["media_url"], destino)
            print(f"  baixado: {destino.stat().st_size / 1e6:.1f} MB")
            url_video = subir_midia(destino)

        ok, info = publicar(conta, board, url_video, titulo, descricao, capa)
        agora = datetime.now(timezone.utc).isoformat(timespec="seconds")
        reg = estado.get(midia["id"], {})
        if ok is None:
            print("  em processamento no Pinterest (pendente; a proxima rodada confere)")
            estado[midia["id"]] = {"pendente": True, "zernio_post": info.get("post_id"),
                                   "titulo": titulo, "permalink": midia["permalink"],
                                   "publicado_ig": midia["timestamp"], "distribuido_em": agora}
            gravar_estado(estado)
            continue
        if ok:
            print(f"  Pinterest: {info.get('url') or '(publicado; URL processando)'}")
            estado[midia["id"]] = {
                "pinterest": info.get("url") or True, "zernio_post": info.get("post_id"),
                "titulo": titulo, "permalink": midia["permalink"],
                "publicado_ig": midia["timestamp"], "distribuido_em": agora,
            }
        else:
            tent = reg.get("tentativas", 0) + 1
            print(f"  FALHOU ({tent}/{MAX_TENTATIVAS}): {info.get('erro')}")
            estado[midia["id"]] = {"tentativas": tent, "erro": info.get("erro"),
                                   "zernio_post": info.get("post_id"),
                                   "permalink": midia["permalink"], "tentado_em": agora}
        gravar_estado(estado)
        if not ok:
            sys.exit(1)


if __name__ == "__main__":
    main()

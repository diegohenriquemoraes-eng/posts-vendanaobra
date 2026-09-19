"""Distribuidor — o Reel do @vendanaobra vira video no Threads.

POR QUE ISSO EXISTE (19/09/2026)
--------------------------------
`threads_publicar.py` leva o BLOG ao Threads e, de proposito, nao levava o Reel:
a premissa de 05/09 era que "o Instagram ja espelha o Reel no Threads sozinho".
Conferido em 19/09 na aba Midia do @vendanaobra: de 35 Reels em 30 dias, **4**
chegaram ao Threads. O espelho e um botao que o Diego marca (ou nao) na hora de
postar pelo app — nao e automatico. Este script fecha esse buraco.

O DESENHO, E O MOTIVO DE CADA ESCOLHA
-------------------------------------
- A fonte e a CONTA do Instagram (Graph API), como nos distribuidores do
  YouTube e do TikTok: entra o que o Diego posta na mao.
- O video vai por URL (`media_url` do Instagram): a API do Threads so aceita
  `video_url`, nao upload. A URL e assinada e publica; e da mesma CDN da Meta.
  Ela expira em horas, por isso o post sai na mesma execucao — nunca fica
  agendado.
- **Dedupe contra o que JA esta no Threads**, nao so contra o estado local:
  antes de publicar, le os ultimos 100 posts do perfil e pula o Reel cujo texto
  ja aparece la. Assim o Diego pode continuar marcando "compartilhar no Threads"
  no app sem gerar post duplicado — e a carga inicial nao repete os 4 que ele
  ja tinha espelhado.
- **Link CLICAVEL** no fim do texto — e a unica vantagem real do Threads sobre
  o Instagram e o TikTok. Rota `/r/th-raiox` (ja existe no site), com UTM.
- Mencoes "@fulano" viram texto: no Threads o @ marcaria outra conta (ou
  ninguem). Hashtags saem: o Threads so aceita UM topico por post.
- Teto de 3 por dia, o mesmo ritmo do Instagram. O Threads nao pune volume como
  o LinkedIn, e o blog ja poe 1/dia — fica em ~4 posts/dia no total.
- `distribuidos_threads.json` versionado, como os irmaos.

Uso:
    python distribuir_threads.py --ensaio
    python distribuir_threads.py
    python distribuir_threads.py --limite 11 --teto 15 --pausa 60   # carga de acervo

Variaveis: META_TOKEN (Graph API do Instagram), THREADS_TOKEN (o mesmo do
threads_publicar.py, renovado todo dia pelo workflow Threads diario).
"""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone

from distribuir import _linhas_uteis, coletar  # noqa: E402

AQUI = pathlib.Path(__file__).parent
ESTADO = AQUI / "distribuidos_threads.json"

API = "https://graph.threads.net/v1.0"
LINK = "https://vendanaobra.com.br/r/th-raiox"
CHAMADA = f"Raio-X comercial grátis, 3 minutos: {LINK}"
LIMITE_TEXTO = 500
TETO_DIA = 3
MAX_TENTATIVAS = 2
TETO_API = 15  # o mesmo teto por execucao dos irmaos; a API aceita 250/dia


def token() -> str:
    t = os.environ.get("THREADS_TOKEN", "").strip()
    if t:
        return t
    local = pathlib.Path(r"C:\Users\NOTE\Desktop\Perffec\Claude\threads_token_vendanaobra.txt")
    if local.exists():
        return local.read_text(encoding="utf-8").strip()
    return ""


def _api(caminho: str, params: dict | None = None, post: bool = False) -> dict:
    params = dict(params or {})
    params["access_token"] = token()
    dados = urllib.parse.urlencode(params).encode("utf-8")
    url = f"{API}/{caminho}"
    if not post:
        url += "?" + dados.decode("utf-8")
        dados = None
    req = urllib.request.Request(url, data=dados, headers={"User-Agent": "VendaNaObra-Threads/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        try:
            return {"error": json.load(e).get("error", {}), "http": e.code}
        except Exception:
            return {"error": {"message": e.read().decode("utf-8", "replace")[:300]}, "http": e.code}


# --------------------------------------------------------------------------- #
# Texto
# --------------------------------------------------------------------------- #
def _chave(texto: str) -> str:
    """Primeiros ~40 caracteres, sem acento/pontuacao — para comparar com o
    que ja esta no Threads (o espelho do app copia a legenda inteira)."""
    t = unicodedata.normalize("NFKD", texto or "").encode("ascii", "ignore").decode()
    t = re.sub(r"[^a-z0-9 ]+", " ", t.lower())
    return " ".join(t.split())[:40]


def montar_texto(legenda_ig: str) -> str | None:
    linhas = _linhas_uteis(legenda_ig)
    if not linhas:
        return None
    corpo = "\n\n".join(linhas[:5])
    corpo = re.sub(r"https?://\S+", "", corpo)
    corpo = re.sub(r"(?<!\w)@([\w.]+)", r"\1", corpo)
    corpo = re.sub(r"[ \t]+\n", "\n", corpo).strip()
    teto = LIMITE_TEXTO - len(CHAMADA) - 2
    if len(corpo) > teto:
        corpo = corpo[: teto - 1].rsplit(" ", 1)[0].rstrip(",;:") + "…"
    return f"{corpo}\n\n{CHAMADA}"


# --------------------------------------------------------------------------- #
# Threads
# --------------------------------------------------------------------------- #
def ja_no_threads() -> set[str]:
    """Chaves de texto dos posts de VIDEO ja publicados no perfil."""
    r = _api("me/threads", {"fields": "id,text,media_type", "limit": 100})
    if "error" in r:
        sys.exit(f"Threads /me/threads: {r['error']}")
    return {_chave(p.get("text", "")) for p in r.get("data", []) if p.get("media_type") == "VIDEO"}


def publicar(video_url: str, texto: str) -> tuple[bool, dict]:
    r = _api("me/threads", {"media_type": "VIDEO", "video_url": video_url, "text": texto}, post=True)
    if "error" in r:
        return False, {"erro": r["error"].get("message", str(r["error"]))}
    caixa = r["id"]
    # O video e baixado e processado do lado da Meta; publicar antes de FINISHED
    # devolve erro. Costuma levar 20-60 s.
    fim = time.time() + 300
    while time.time() < fim:
        s = _api(caixa, {"fields": "status,error_message"})
        st = s.get("status")
        if st == "FINISHED":
            break
        if st == "ERROR":
            return False, {"erro": s.get("error_message") or "container ERROR"}
        time.sleep(10)
    else:
        return False, {"erro": "container nao processou em 5 min"}
    p = _api("me/threads_publish", {"creation_id": caixa}, post=True)
    if "error" in p:
        return False, {"erro": p["error"].get("message", str(p["error"]))}
    pid = p["id"]
    info = _api(pid, {"fields": "permalink"})
    return True, {"post_id": pid, "url": info.get("permalink")}


# --------------------------------------------------------------------------- #
def carregar_estado() -> dict:
    return json.loads(ESTADO.read_text(encoding="utf-8")) if ESTADO.exists() else {}


def gravar_estado(estado: dict) -> None:
    ESTADO.write_text(json.dumps(estado, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--ensaio", action="store_true")
    p.add_argument("--limite", type=int, default=1)
    p.add_argument("--dias", type=int, default=45)
    p.add_argument("--id")
    p.add_argument("--ordem", choices=["novo", "antigo"], default="novo")
    p.add_argument("--teto", type=int, default=TETO_DIA, help="teto diario so nesta execucao")
    p.add_argument("--pausa", type=int, default=0, help="segundos entre um post e outro")
    p.add_argument("--listar", action="store_true", help="diagnostico: os ultimos 100 posts do perfil")
    args = p.parse_args()

    if not token():
        print("THREADS_TOKEN nao definido. Nada feito.")
        return

    if args.listar:
        r = _api("me/threads", {"fields": "id,text,media_type,timestamp,permalink", "limit": 100})
        for q in r.get("data", []):
            print(q.get("timestamp", "")[:16], q.get("media_type"), (q.get("text") or "")[:60].replace(chr(10), " "))
        return

    estado = carregar_estado()
    reels = coletar(args.dias)
    if args.id:
        reels = [m for m in reels if m["id"] == args.id]

    existentes = ja_no_threads()

    def elegivel(m: dict) -> bool:
        reg = estado.get(m["id"])
        if reg and (reg.get("threads") or reg.get("pulado")):
            return False
        if reg and reg.get("tentativas", 0) >= MAX_TENTATIVAS:
            return False
        return True

    pendentes = [m for m in reels if elegivel(m)]
    if args.ordem == "antigo":
        pendentes = pendentes[::-1]

    hoje = datetime.now(timezone.utc).date().isoformat()
    saiu_hoje = sum(
        1 for v in estado.values()
        if (v.get("distribuido_em") or v.get("tentado_em") or "").startswith(hoje) and not v.get("pulado")
    )
    teto = min(args.teto, TETO_API)
    resta = max(teto - saiu_hoje, 0)
    print(
        f"{len(reels)} Reels na janela de {args.dias} dias · {len(pendentes)} ainda nao "
        f"distribuidos · {len(existentes)} videos ja no Threads · {saiu_hoje}/{teto} enviados hoje"
    )
    if not pendentes:
        print("Nada a fazer.")
        return
    if resta == 0:
        print(f"Teto diario de {teto} atingido. Volta na proxima rodada.")
        return

    feitos = 0
    for midia in pendentes:
        if feitos >= min(args.limite, resta):
            break
        legenda_ig = midia.get("caption") or ""
        texto = montar_texto(legenda_ig)
        print(f"\n[{midia['timestamp'][:10]}] {midia['permalink']}")

        if texto is None:
            print("  pulado: legenda sem texto")
            if not args.ensaio:
                estado[midia["id"]] = {"pulado": "sem legenda", "permalink": midia["permalink"]}
                gravar_estado(estado)
            continue

        if _chave(legenda_ig) in existentes:
            print("  ja esta no Threads (espelhado pelo app) — marcado, nao repete")
            if not args.ensaio:
                estado[midia["id"]] = {"threads": "espelho-app", "permalink": midia["permalink"]}
                gravar_estado(estado)
            continue

        print("  texto: " + texto.replace("\n", " ⏎ ")[:150])
        if args.ensaio:
            print("  (ensaio: nada foi publicado)")
            feitos += 1
            continue

        if feitos and args.pausa:
            time.sleep(args.pausa)
        ok, info = publicar(midia["media_url"], texto)
        agora = datetime.now(timezone.utc).isoformat(timespec="seconds")
        reg = estado.get(midia["id"], {})
        if ok:
            print(f"  Threads: {info.get('url') or info.get('post_id')}")
            estado[midia["id"]] = {
                "threads": info.get("url") or info.get("post_id"),
                "permalink": midia["permalink"],
                "publicado_ig": midia["timestamp"],
                "distribuido_em": agora,
            }
        else:
            tent = reg.get("tentativas", 0) + 1
            print(f"  FALHOU ({tent}/{MAX_TENTATIVAS}): {info.get('erro')}")
            estado[midia["id"]] = {
                "tentativas": tent, "erro": info.get("erro"),
                "permalink": midia["permalink"], "tentado_em": agora,
            }
        gravar_estado(estado)
        feitos += 1
        if not ok:
            sys.exit(1)


if __name__ == "__main__":
    main()

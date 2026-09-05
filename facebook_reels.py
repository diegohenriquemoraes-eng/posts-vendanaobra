"""O Reel do @vendanaobra vira Reel na Página do Facebook.

POR QUE (05/09/2026)
--------------------
A Página "Venda na Obra" existe desde sempre — mas só para ligar o Instagram à
API. Tem **0 post e 0 seguidor**. E a permissão de publicar nela (`pages_manage_posts`)
JÁ ESTAVA concedida no mesmo aplicativo que publica os Reels: não precisou de
login novo, aprovação nem token novo.

Reels do Facebook são distribuídos por ALGORITMO, não por seguidores — página
zerada recebe view de quem não segue. E o dono de vidraçaria de 45 anos vive no
Facebook, não no Threads. Custo marginal: zero, é o mesmo vídeo.

COMO PUBLICA
------------
A API de Reels da Página é em três fases (`start` → `upload` → `finish`), e o
`upload` aceita a URL do vídeo em vez do arquivo (`file_url`) — então o vídeo
vai direto do CDN do Instagram para o Facebook, sem passar pelo disco.

Uso:
    python facebook_reels.py --ensaio
    python facebook_reels.py --limite 2
"""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import re
import sys
import time

import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone

AQUI = pathlib.Path(__file__).parent
ESTADO = AQUI / "facebook_publicados.json"

IG_USER_ID = "17841470188725651"
PAGE_ID = "1272959582565285"
GRAPH = "https://graph.facebook.com/v21.0"
TETO_DIA = 5


def token_sistema() -> str:
    t = os.environ.get("META_TOKEN", "").strip()
    if t:
        return t
    p = pathlib.Path(r"C:\Users\NOTE\Desktop\Perffec\Claude\meta_system_user_token.txt")
    if p.exists():
        return p.read_text().strip()
    sys.exit("META_TOKEN ausente.")


def token_pagina() -> str:
    """Reel de Página exige token DA PÁGINA, não o do usuário de sistema."""
    t = os.environ.get("META_PAGE_TOKEN", "").strip()
    if t:
        return t
    u = f"{GRAPH}/{PAGE_ID}?" + urllib.parse.urlencode(
        {"fields": "access_token", "access_token": token_sistema()}
    )
    with urllib.request.urlopen(u, timeout=45) as r:
        return json.load(r)["access_token"]


def _post(url: str, campos: dict) -> dict:
    req = urllib.request.Request(url, data=urllib.parse.urlencode(campos).encode())
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.load(r)


def coletar(dias: int) -> list[dict]:
    campos = "id,media_product_type,media_url,permalink,caption,timestamp"
    u = f"{GRAPH}/{IG_USER_ID}/media?" + urllib.parse.urlencode(
        {"fields": campos, "limit": 50, "access_token": token_sistema()}
    )
    with urllib.request.urlopen(u, timeout=60) as r:
        dados = json.load(r)
    corte = datetime.now(timezone.utc) - timedelta(days=dias)
    return [
        m
        for m in dados.get("data", [])
        if m.get("media_product_type") == "REELS"
        and m.get("media_url")
        and datetime.fromisoformat(m["timestamp"].replace("+0000", "+00:00")) >= corte
    ]


def legenda_para_facebook(bruta: str) -> str:
    """Tira o que é gíria de Instagram e deixa o texto respirar."""
    texto = re.sub(r"^\s*🎯?\s*venda n[ãa]o [ée] dom,?\s*(venda\s+)?[ée] m[ée]todo!?\s*", "", bruta or "", flags=re.I)
    linhas = []
    for l in texto.split("\n"):
        l = l.strip()
        if not l:
            continue
        # Hashtag no Facebook não distribui nada e ainda deixa cara de repost.
        if l.startswith("#"):
            continue
        if re.match(r"^epis[óo]dio completo", l, flags=re.I):
            continue
        linhas.append(l)
    corpo = "\n\n".join(linhas[:5])
    return (corpo + "\n\nRaio-X gratuito do seu comercial: https://vendanaobra.com.br/r/ig").strip()


def publicar_reel(video_url: str, descricao: str) -> str:
    pt = token_pagina()
    inicio = _post(f"{GRAPH}/{PAGE_ID}/video_reels", {"upload_phase": "start", "access_token": pt})
    vid = inicio["video_id"]

    # ⚠ O caminho por `file_url` NÃO funciona aqui: o Facebook recusa buscar
    # vídeo da própria infraestrutura da Meta — "First-party Meta-hosted URLs
    # are not permitted" —, e a URL do Reel vem do CDN do Instagram. Então o
    # arquivo passa por aqui mesmo: baixa e sobe os bytes.
    with urllib.request.urlopen(video_url, timeout=180) as r:
        bytes_video = r.read()

    req = urllib.request.Request(
        f"https://rupload.facebook.com/video-upload/v21.0/{vid}",
        data=bytes_video,
        headers={
            "Authorization": f"OAuth {pt}",
            "offset": "0",
            "file_size": str(len(bytes_video)),
            "Content-Type": "application/octet-stream",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=300) as r:
        json.load(r)

    _post(
        f"{GRAPH}/{PAGE_ID}/video_reels",
        {
            "upload_phase": "finish",
            "video_id": vid,
            "video_state": "PUBLISHED",
            "description": descricao[:2000],
            "access_token": pt,
        },
    )
    return vid


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--ensaio", action="store_true")
    p.add_argument("--limite", type=int, default=2)
    p.add_argument("--dias", type=int, default=45)
    args = p.parse_args()

    estado = json.loads(ESTADO.read_text(encoding="utf-8")) if ESTADO.exists() else {}
    reels = coletar(args.dias)
    pendentes = [m for m in reels if m["id"] not in estado]  # mais novo primeiro

    hoje = datetime.now(timezone.utc).date().isoformat()
    saiu_hoje = sum(1 for v in estado.values() if v.get("em", "").startswith(hoje))
    resta = max(TETO_DIA - saiu_hoje, 0)

    print(f"{len(reels)} Reels na janela · {len(pendentes)} pendentes · {saiu_hoje}/{TETO_DIA} hoje")
    if not pendentes or resta == 0:
        print("Nada a fazer.")
        return

    for m in pendentes[: min(args.limite, resta)]:
        desc = legenda_para_facebook(m.get("caption") or "")
        print(f"\n[{m['timestamp'][:10]}] {m['permalink']}")
        print("  " + desc.split("\n")[0][:80])
        if args.ensaio:
            print("  (ensaio: nada foi publicado)")
            continue
        try:
            vid = publicar_reel(m["media_url"], desc)
        except Exception as e:
            corpo = e.read().decode()[:300] if hasattr(e, "read") else str(e)[:300]
            print(f"  falhou: {corpo}")
            continue
        print(f"  Facebook: https://www.facebook.com/reel/{vid}")
        estado[m["id"]] = {
            "video": vid,
            "em": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "permalink": m["permalink"],
        }
        ESTADO.write_text(json.dumps(estado, ensure_ascii=False, indent=2), encoding="utf-8")
        time.sleep(3)


if __name__ == "__main__":
    main()

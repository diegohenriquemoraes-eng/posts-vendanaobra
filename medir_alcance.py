# -*- coding: utf-8 -*-
"""Linha de base real do @vendanaobra: alcance por post, e o que acontece nos
dias em que sai mais de uma peca.

Existe porque em 04/09/2026 o Diego perguntou se subir o volume dilui o alcance
por post — e a resposta honesta era "nao sei, nunca foi medido". Isto mede.

Nao publica nada: so le. O token sai do mesmo lugar que o publicador usa e nunca
e' impresso.

Uso: python medir_alcance.py            # ultimos 90 dias
     python medir_alcance.py --dias 180
"""
import json, os, sys, urllib.parse, urllib.request, argparse
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from statistics import median

IG_USER_ID = "17841470188725651"          # @vendanaobra
API = "https://graph.facebook.com/v21.0"
FUSO_BR = timezone(timedelta(hours=-3))
METRICAS = ["reach", "saved", "likes", "comments", "shares", "views"]


def _token() -> str:
    tok = os.environ.get("META_TOKEN", "").strip()
    if tok:
        return tok
    caminho = r"C:\Users\NOTE\Desktop\Perffec\Claude\meta_system_user_token.txt"
    if os.path.exists(caminho):
        return open(caminho, encoding="utf-8").read().strip()
    raise SystemExit("Sem token: defina META_TOKEN ou salve meta_system_user_token.txt")


def _get(endpoint: str, campos: dict):
    url = f"{API}/{endpoint}?" + urllib.parse.urlencode(campos)
    try:
        with urllib.request.urlopen(url, timeout=60) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        return {"__erro": e.read().decode(errors="replace")[:200]}


def posts(token, desde):
    """Todos os posts publicados a partir de `desde` (datetime com fuso)."""
    out, url = [], None
    campos = {"fields": "id,media_type,media_product_type,timestamp,permalink",
              "limit": 100, "access_token": token}
    while True:
        r = _get(f"{IG_USER_ID}/media", campos) if url is None else json.loads(
            urllib.request.urlopen(url, timeout=60).read())
        if "__erro" in r:
            raise SystemExit("Graph API: " + r["__erro"])
        for m in r.get("data", []):
            t = datetime.fromisoformat(m["timestamp"].replace("+0000", "+00:00")).astimezone(FUSO_BR)
            if t < desde:
                return out
            m["quando"] = t
            out.append(m)
        url = r.get("paging", {}).get("next")
        if not url:
            return out


def insights(mid, token):
    r = _get(f"{mid}/insights", {"metric": ",".join(METRICAS), "access_token": token})
    if "__erro" in r:            # metrica indisponivel para o tipo: tenta uma a uma
        d = {}
        for m in METRICAS:
            x = _get(f"{mid}/insights", {"metric": m, "access_token": token})
            if "data" in x and x["data"]:
                d[m] = x["data"][0]["values"][0]["value"]
        return d
    return {i["name"]: i["values"][0]["value"] for i in r.get("data", [])}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dias", type=int, default=90)
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")

    token = _token()
    quem = _get(IG_USER_ID, {"fields": "username,followers_count", "access_token": token})
    if "__erro" in quem:
        raise SystemExit("token nao respondeu: " + quem["__erro"])
    print(f"@{quem['username']} — {quem['followers_count']} seguidores\n")

    desde = datetime.now(FUSO_BR) - timedelta(days=a.dias)
    ms = posts(token, desde)
    print(f"{len(ms)} posts nos ultimos {a.dias} dias\n")

    por_dia = defaultdict(list)
    for m in ms:
        m["ins"] = insights(m["id"], token)
        por_dia[m["quando"].strftime("%Y-%m-%d")].append(m)

    # 1) alcance por tipo
    print("ALCANCE POR TIPO DE POST (mediana)")
    tipos = defaultdict(list)
    for m in ms:
        tipo = m.get("media_product_type") or m["media_type"]
        if m["ins"].get("reach"):
            tipos[tipo].append(m["ins"]["reach"])
    for t, v in sorted(tipos.items(), key=lambda x: -len(x[1])):
        print(f"  {t:12s} n={len(v):3d}  alcance med={median(v):7.0f}  "
              f"min={min(v):6d}  max={max(v):6d}")

    # 2) a pergunta do Diego: dia com mais posts dilui o alcance de cada um?
    print("\nALCANCE POR POST, AGRUPADO POR QUANTOS POSTS SAIRAM NAQUELE DIA")
    grupos = defaultdict(list)
    salv = defaultdict(list)
    for dia, lista in por_dia.items():
        n = len(lista)
        for m in lista:
            if m["ins"].get("reach"):
                grupos[n].append(m["ins"]["reach"])
            if m["ins"].get("saved") is not None:
                salv[n].append(m["ins"]["saved"])
    for n in sorted(grupos):
        dias = sum(1 for d, l in por_dia.items() if len(l) == n)
        s = f"  salvamentos med={median(salv[n]):5.1f}" if salv.get(n) else ""
        print(f"  {n} post(s)/dia:  {dias:3d} dias, {len(grupos[n]):3d} posts  "
              f"alcance med por post={median(grupos[n]):7.0f}{s}")

    # 3) os ultimos, para olho no detalhe
    print("\nULTIMOS 12 POSTS")
    for m in ms[:12]:
        i = m["ins"]
        print(f"  {m['quando']:%d/%m %H:%M}  {(m.get('media_product_type') or m['media_type']):9s} "
              f"alcance={i.get('reach','?'):>6}  views={i.get('views','?'):>7}  "
              f"salvos={i.get('saved','?'):>4}  {m['permalink']}")


if __name__ == "__main__":
    main()

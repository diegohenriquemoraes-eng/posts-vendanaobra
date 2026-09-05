# -*- coding: utf-8 -*-
"""Os posts campeoes do @vendanaobra — a referencia que o Afonso manda consumir.

O "consumo intencional" da Rota 100K e' cacar referencia de FORMATO antes de
gravar. Em 04/09/2026 o Diego decidiu nao fazer isso a mao ("pesquise as
referencias e abasteca o conteudo") — entao a referencia passa a sair daqui: do
que a propria conta ja provou, medido, nao do que parece bom.

Nao publica nada: so le. Token pelo mesmo caminho do publicador, nunca impresso.

Uso: python top_posts.py                  # 120 dias, top 15 por alcance
     python top_posts.py --dias 180 --n 25
     python top_posts.py --json ref.json  # salva para alimentar o Canteiro
"""
import argparse
import json
import os
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone

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
        return {"__erro": e.read().decode(errors="replace")[:300]}


def posts(token, desde):
    out, url = [], None
    campos = {"fields": "id,media_type,media_product_type,timestamp,permalink,caption",
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


def metricas(token, post):
    r = _get(f"{post['id']}/insights",
             {"metric": ",".join(METRICAS), "access_token": token})
    if "__erro" in r:
        return {}
    return {d["name"]: d["values"][0]["value"] for d in r.get("data", [])}


def gancho(legenda: str) -> str:
    """A primeira linha da legenda — que e' o gancho escrito do post."""
    for linha in (legenda or "").split("\n"):
        if linha.strip():
            return linha.strip()
    return "(sem legenda)"


def main() -> None:
    a = argparse.ArgumentParser()
    a.add_argument("--dias", type=int, default=120)
    a.add_argument("--n", type=int, default=15)
    a.add_argument("--json", default="")
    o = a.parse_args()

    token = _token()
    desde = datetime.now(FUSO_BR) - timedelta(days=o.dias)
    tudo = posts(token, desde)
    linhas = []
    for p in tudo:
        m = metricas(token, p)
        if not m:
            continue
        linhas.append({
            "quando": p["quando"].strftime("%d/%m"),
            "tipo": p.get("media_product_type") or p.get("media_type"),
            "alcance": m.get("reach", 0),
            "salvos": m.get("saved", 0),
            "compart": m.get("shares", 0),
            "coment": m.get("comments", 0),
            "curtidas": m.get("likes", 0),
            "gancho": gancho(p.get("caption", "")),
            "link": p.get("permalink", ""),
        })

    linhas.sort(key=lambda d: d["alcance"], reverse=True)
    top = linhas[:o.n]
    print(f"{len(linhas)} posts medidos nos ultimos {o.dias} dias\n")
    print(f"{'data':>6} {'tipo':<12} {'alcance':>8} {'salvos':>7} {'comp':>5}  gancho")
    for d in top:
        print(f"{d['quando']:>6} {d['tipo']:<12} {d['alcance']:>8} {d['salvos']:>7} "
              f"{d['compart']:>5}  {d['gancho'][:70]}")

    if o.json:
        with open(o.json, "w", encoding="utf-8") as f:
            json.dump(top, f, ensure_ascii=False, indent=1)
        print(f"\nsalvo em {o.json}")


if __name__ == "__main__":
    main()

# -*- coding: utf-8 -*-
"""Le o teste de CTA do carrossel: link na bio (dono/gestor) x compartilhar (vendedor).

Decisao do Diego, 07/09/2026. Ate entao 33 dos 44 carrosseis pediam as duas
coisas no mesmo slide ("Salva e usa... Raio-X: link na bio") — pedido duplo nao
mede nada. Agora cada carrossel tem UM pedido so, escolhido pelo publico do
tema: carrossel de dono/gestor manda para o Raio-X; carrossel de vendedor pede
salvar/mandar para alguem.

O braco de cada carrossel esta em `publico` no banco do Canteiro
(canteiro-stories/docs/carrosseis.json) — este script nao adivinha nada, so
casa o que foi publicado com o que estava planejado, por dia e hora.

O que olhar: `bio` ganha em SALVOS+COMPARTILHAMENTOS? Entao o pedido de
compartilhar nao estava faltando. `compartilhar` ganha em alcance e nao muda o
volume de Raio-X preenchido? Entao o link na bio custa alcance e nao paga.
O numero de Raio-X preenchidos NAO vem daqui — vem do painel do Raio-X.

Uso: python medir_cta.py                # desde 08/09/2026
     python medir_cta.py --desde 2026-09-15
     python medir_cta.py --json cta.json
"""
import argparse
import json
import os
import statistics
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

IG_USER_ID = "17841470188725651"          # @vendanaobra
API = "https://graph.facebook.com/v21.0"
FUSO_BR = timezone(timedelta(hours=-3))
METRICAS = ["reach", "saved", "shares", "likes", "comments"]
BANCO = Path(r"C:\Users\NOTE\Desktop\Projetos\canteiro-stories\docs\carrosseis.json")
INICIO = "2026-09-08"                      # primeiro dia com CTA de braco unico


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


def carrosseis_publicados(token, desde):
    """So CAROUSEL_ALBUM do feed — Reels e foto unica nao entram no teste."""
    out, url = [], None
    campos = {"fields": "id,media_type,timestamp,permalink,caption",
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
            if m.get("media_type") == "CAROUSEL_ALBUM":
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


def planejados():
    banco = json.loads(BANCO.read_text(encoding="utf-8"))
    return [c for c in banco if c.get("publico")]


def casar(post, plano):
    """O carrossel planejado do mesmo dia com a hora mais proxima da publicada.

    Casa por proximidade porque o Diego publica a mao: o de 07:30 pode sair
    07:41 ou 08:15, e exigir hora exata perderia o post inteiro.
    """
    dia = post["quando"].strftime("%Y-%m-%d")
    candidatos = [c for c in plano if c["dia"] == dia]
    if not candidatos:
        return None
    minutos = post["quando"].hour * 60 + post["quando"].minute
    def dist(c):
        h, m = c["hora"].split(":")
        return abs(int(h) * 60 + int(m) - minutos)
    return min(candidatos, key=dist)


def resumo(nome, linhas):
    if not linhas:
        return f"{nome:<14} — nenhum post medido ainda"
    med = lambda k: statistics.median(d[k] for d in linhas)
    return (f"{nome:<14} {len(linhas):>3} posts | alcance {med('alcance'):>7.0f} | "
            f"salvos {med('salvos'):>5.0f} | compart {med('compart'):>4.0f} | "
            f"curtidas {med('curtidas'):>4.0f}")


def main() -> None:
    a = argparse.ArgumentParser()
    a.add_argument("--desde", default=INICIO)
    a.add_argument("--json", default="")
    o = a.parse_args()

    token = _token()
    desde = datetime.strptime(o.desde, "%Y-%m-%d").replace(tzinfo=FUSO_BR)
    plano = planejados()
    linhas = []
    for p in carrosseis_publicados(token, desde):
        c = casar(p, plano)
        if not c:
            continue
        m = metricas(token, p)
        if not m:
            continue
        linhas.append({
            "quando": p["quando"].strftime("%d/%m %H:%M"),
            "publico": c["publico"],
            "titulo": c["titulo"],
            "alcance": m.get("reach", 0),
            "salvos": m.get("saved", 0),
            "compart": m.get("shares", 0),
            "curtidas": m.get("likes", 0),
            "link": p.get("permalink", ""),
        })

    linhas.sort(key=lambda d: d["quando"])
    print(f"Teste de CTA do carrossel — desde {o.desde} · {len(linhas)} posts casados\n")
    print(f"{'quando':>12} {'braco':<13} {'alc':>6} {'salv':>5} {'comp':>5}  titulo")
    for d in linhas:
        print(f"{d['quando']:>12} {d['publico']:<13} {d['alcance']:>6} {d['salvos']:>5} "
              f"{d['compart']:>5}  {d['titulo'][:46]}")

    print()
    print(resumo("bio", [d for d in linhas if d["publico"] == "bio"]))
    print(resumo("compartilhar", [d for d in linhas if d["publico"] == "compartilhar"]))
    print("\nRaio-X preenchido nao aparece aqui: conferir no painel do Raio-X, "
          "cruzando com os dias de carrossel 'bio'.")

    if o.json:
        with open(o.json, "w", encoding="utf-8") as f:
            json.dump(linhas, f, ensure_ascii=False, indent=1)
        print(f"salvo em {o.json}")


if __name__ == "__main__":
    main()

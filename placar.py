# -*- coding: utf-8 -*-
"""O placar de sexta que a Rota 100K exige — medido, nao estimado.

Tres leituras numa pagina so':

1. **Posts da semana**: alcance, salvos e compartilhamentos, com a mediana e os
   tres melhores por SALVOS (o metodo manda separar os melhores para o trafego —
   e por salvamento, nao por views).
2. **Stories**: as duas reguas do Destrave Story, dia a dia, a partir do que o
   `coletar_stories.py` fotografou (views do 1o >= 10% dos seguidores; ultimo
   >= 40% do primeiro).
3. **Comentarios**: a terceira fonte de gancho do metodo, que ate agora nunca foi
   usada. Lista os comentarios em forma de pergunta — cada um e' pauta pronta.

Uso: python placar.py               # semana corrente (ultimos 7 dias)
     python placar.py --dias 14
     python placar.py --md caminho.md
"""
import argparse
import json
import re
from datetime import datetime, timedelta
from pathlib import Path
from statistics import median

from top_posts import FUSO_BR, _get, _token, gancho, metricas, posts

HIST = Path(__file__).parent / "dados" / "stories.json"
PERGUNTA = re.compile(r"\?|^(como|qual|quanto|quando|onde|por que|porque|pq|tem como|da pra|dá pra)\b",
                      re.I)


def comentarios(token, media_id):
    r = _get(f"{media_id}/comments",
             {"fields": "text,username,timestamp,like_count", "limit": 50,
              "access_token": token})
    return r.get("data", [])


def main():
    a = argparse.ArgumentParser()
    a.add_argument("--dias", type=int, default=7)
    a.add_argument("--md", default="")
    o = a.parse_args()

    token = _token()
    desde = datetime.now(FUSO_BR) - timedelta(days=o.dias)
    linhas, perguntas = [], []
    for p in posts(token, desde):
        m = metricas(token, p)
        if not m:
            continue
        linhas.append({
            "quando": p["quando"].strftime("%d/%m"),
            "tipo": p.get("media_product_type") or p.get("media_type"),
            "alcance": m.get("reach", 0), "salvos": m.get("saved", 0),
            "compart": m.get("shares", 0), "coment": m.get("comments", 0),
            "gancho": gancho(p.get("caption", "")), "link": p.get("permalink", ""),
        })
        for c in comentarios(token, p["id"]):
            t = (c.get("text") or "").strip()
            if PERGUNTA.search(t) and len(t) > 12:
                perguntas.append({"quem": c.get("username", ""), "texto": t,
                                  "post": p["quando"].strftime("%d/%m")})

    out = []
    w = out.append
    hoje = datetime.now(FUSO_BR).strftime("%d/%m/%Y")
    w(f"# Placar @vendanaobra — {hoje} (últimos {o.dias} dias)\n")

    if linhas:
        alc = [d["alcance"] for d in linhas]
        w(f"## Posts: {len(linhas)} no período\n")
        w(f"- Mediana de alcance: **{median(alc):.0f}** · melhor: {max(alc)} · pior: {min(alc)}")
        w(f"- Salvos no período: **{sum(d['salvos'] for d in linhas)}** · "
          f"compartilhamentos: **{sum(d['compart'] for d in linhas)}**\n")
        w("### Os 3 para levar ao tráfego (por SALVOS)\n")
        for d in sorted(linhas, key=lambda x: (x["salvos"], x["compart"]), reverse=True)[:3]:
            w(f"1. **{d['salvos']} salvos · {d['alcance']} alcance** — {d['gancho'][:80]}  \n   {d['link']}")
        w("\n### Tudo, por alcance\n")
        w("| data | tipo | alcance | salvos | comp | gancho |")
        w("|---|---|---:|---:|---:|---|")
        for d in sorted(linhas, key=lambda x: x["alcance"], reverse=True):
            w(f"| {d['quando']} | {d['tipo']} | {d['alcance']} | {d['salvos']} | "
              f"{d['compart']} | {d['gancho'][:60]} |")
        w("")

    if HIST.exists():
        hist = json.loads(HIST.read_text(encoding="utf-8"))[-o.dias:]
        w("## Stories — as duas réguas do Destrave Story\n")
        w("| dia | stories | 1º | meta 10% | último | último/1º | meta 40% |")
        w("|---|---:|---:|---:|---:|---:|---|")
        for h in hist:
            v = [i.get("views", i.get("reach", 0)) for i in h["stories"]]
            if not v:
                continue
            piso = h["seguidores"] * 0.10
            q = v[-1] / v[0] if v[0] else 0
            w(f"| {h['dia'][-5:]} | {len(v)} | {v[0]} | {piso:.0f} "
              f"{'✅' if v[0] >= piso else '❌'} | {v[-1]} | {q:.0%} "
              f"| {'✅' if q >= 0.40 else '❌'} |")
        w("")
    else:
        w("## Stories\n\nSem histórico ainda — rode `python coletar_stories.py` "
          "todo dia à noite (é o que alimenta esta tabela).\n")

    w(f"## Comentários que são pergunta ({len(perguntas)}) — pauta pronta\n")
    if perguntas:
        for c in perguntas[:25]:
            w(f"- **@{c['quem']}** ({c['post']}): {c['texto'][:180]}")
    else:
        w("Nenhum no período. Sem pergunta nos comentários, a fonte de gancho mais "
          "barata do método está fechada — vale terminar todo Reels perguntando.")
    w("")

    texto = "\n".join(out)
    print(texto)
    destino = Path(o.md) if o.md else Path(
        rf"C:\Users\NOTE\Desktop\Perffec\Claude\Placar-vendanaobra-{datetime.now(FUSO_BR):%Y-%m-%d}.md")
    destino.write_text(texto, encoding="utf-8")
    print(f"\nsalvo em {destino}")


if __name__ == "__main__":
    main()

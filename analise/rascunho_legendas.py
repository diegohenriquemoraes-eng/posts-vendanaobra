# -*- coding: utf-8 -*-
"""Rascunho dos blocos de legenda a partir das palavras com tempo.

Sai para revisao humana: o texto automatico do YouTube erra nome proprio,
pontuacao e aspas. O arquivo revisado e' `legendas_ep25.json`.
"""
import json, io, sys

MAX_LINHA = 34
MAX_BLOCO = 68

def limpar(w):
    return w.replace(">>", "").strip()

def quebrar(txt):
    palavras = txt.split()
    linhas, atual = [], ""
    for p in palavras:
        if atual and len(atual) + 1 + len(p) > MAX_LINHA:
            linhas.append(atual); atual = p
        else:
            atual = (atual + " " + p).strip()
    if atual: linhas.append(atual)
    return "\n".join(linhas)

def blocos(pal):
    out, buf = [], []
    for p in pal:
        w = limpar(p["w"])
        if not w: continue
        cand = " ".join(x["w"] for x in buf) + " " + w
        fecha = buf and (len(cand) > MAX_BLOCO or buf[-1]["w"][-1:] in ".?!")
        if fecha:
            out.append(buf); buf = []
        buf.append({"t": p["t"], "w": w})
    if buf: out.append(buf)
    res = []
    for i, b in enumerate(out):
        ini = b[0]["t"] - 0.12
        fim = out[i+1][0]["t"] - 0.12 if i + 1 < len(out) else b[-1]["t"] + 1.2
        res.append({"ini": round(max(0, ini), 2), "fim": round(fim, 2),
                    "txt": quebrar(" ".join(x["w"] for x in b))})
    return res

if __name__ == "__main__":
    pal = json.load(io.open("analise/palavras.json", encoding="utf-8"))
    out = {a: blocos(p) for a, p in sorted(pal.items())}
    json.dump(out, io.open("analise/legendas_rascunho.json", "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    alvo = sys.argv[1] if len(sys.argv) > 1 else None
    for a, bs in out.items():
        if alvo and not a.startswith(alvo): continue
        print("###", a, len(bs), "blocos")
        for i, b in enumerate(bs):
            print(f"{i:3d} {b['ini']:6.2f}-{b['fim']:6.2f} | {b['txt']}".replace("\n", " / "))

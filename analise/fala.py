# -*- coding: utf-8 -*-
"""Linha do tempo de quem fala, por corte, em passos de 0,2 s.

Timbre (log-mel) classifica cada janela; os turnos marcados com ">>" na
transcricao automatica do YouTube servem de moldura: dentro de um turno o
falante e' unico, entao vale a moda.
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
import numpy as np
from voz import audio, feats, classificar, suavizar

PASSO = 0.2

def turnos(palavras, dur):
    """Fatia o corte nos ">>" da transcricao."""
    marcas = [0.0]
    for p in palavras:
        if p["w"].startswith(">>") and p["t"] > marcas[-1] + 0.6:
            marcas.append(max(0.0, p["t"] - 0.15))
    marcas.append(dur)
    return list(zip(marcas[:-1], marcas[1:]))

if __name__ == "__main__":
    PA, PD = np.load("analise/proto.npy")
    pal = json.load(open("analise/palavras.json", encoding="utf-8"))
    out = {}
    for arq in sorted(pal):
        x = audio(os.path.join("midia/reels", arq))
        F, E = feats(x)
        lab, marg = classificar(F, E, PA, PD)
        lab = suavizar(lab)
        dur = len(x) / 16000.0
        for a, b in turnos(pal[arq], dur):
            i, j = int(a / PASSO), int(b / PASSO)
            if j - i < 3: continue
            trecho = lab[i:j]
            m = marg[i:j]
            # moda ponderada pela confianca
            voto = float(np.sign(m[np.abs(m) > 0.02].sum())) if np.any(np.abs(m) > 0.02) else 0.0
            if voto != 0: lab[i:j] = 1 if voto > 0 else 0
            else: lab[i:j] = 1 if trecho.mean() > 0.5 else 0
        out[arq] = "".join("A" if v == 1 else "D" for v in lab)
        a = out[arq].count("A")
        print(f"{arq[:42]:42s} Diego {(len(out[arq])-a)*PASSO:6.1f}s  Audrey {a*PASSO:6.1f}s", flush=True)
    json.dump(out, open("analise/fala.json", "w"), indent=0)

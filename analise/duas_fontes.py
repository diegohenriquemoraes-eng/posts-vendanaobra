# -*- coding: utf-8 -*-
"""Mostra as duas transcricoes de um corte lado a lado, para a revisao da legenda.

A automatica do YouTube acerta contexto e nome proprio; a propria (Whisper)
pontua melhor e as vezes inventa. Onde as duas batem, a confianca e' alta.
"""
import json, io, sys, os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def arquivo_de(cid):
    for f in sorted(os.listdir(os.path.join(BASE, "midia/reels"))):
        if f.startswith(cid + "-") and f.endswith(".mp4"):
            return f
    raise SystemExit("corte " + cid + " nao encontrado")

def mostrar(cid):
    arq = arquivo_de(cid)
    w = json.load(io.open(os.path.join(BASE, "analise/whisper.json"), encoding="utf-8"))
    pal = json.load(io.open(os.path.join(BASE, "analise/palavras.json"), encoding="utf-8"))
    print("=" * 70)
    print("### " + arq)
    print("--- propria (Whisper) ---")
    for s in w.get(arq, []):
        print("%6.2f-%6.2f %s" % (s["ini"], s["fim"], s["txt"]))
    print("--- YouTube (com >> marcando troca de voz) ---")
    print(" ".join(p["w"] for p in pal.get(arq, [])))

if __name__ == "__main__":
    for cid in sys.argv[1:]:
        mostrar(cid)

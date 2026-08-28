# -*- coding: utf-8 -*-
"""Grava os blocos revisados de um corte em legendas_ep25.json."""
import json, io, sys

def gravar(arq, blocos):
    p = "legendas_ep25.json"
    d = json.load(io.open(p, encoding="utf-8"))
    d[arq] = blocos
    json.dump(d, io.open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    fala_a = sum(b["fim"] - b["ini"] for b in blocos if b.get("quem") == "A")
    print(f"{arq}: {len(blocos)} blocos, Audrey em {fala_a:.1f}s")

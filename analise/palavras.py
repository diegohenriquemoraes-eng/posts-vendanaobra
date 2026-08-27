# -*- coding: utf-8 -*-
"""Palavras com tempo (do json3 do YouTube) recortadas na janela de cada corte."""
import json, io, sys

def palavras(path):
    d = json.load(io.open(path, encoding="utf-8"))
    out = []
    for e in d["events"]:
        if "segs" not in e: continue
        t0 = e["tStartMs"]
        for s in e["segs"]:
            w = s.get("utf8", "")
            if not w.strip(): continue
            out.append({"t": (t0 + (s.get("tOffsetMs") or 0)) / 1000.0, "w": w.strip()})
    out.sort(key=lambda x: x["t"])
    return out

if __name__ == "__main__":
    ws = palavras("master/ep25.pt.json3")
    jan = json.load(open("analise/janelas.json"))
    res = {}
    for arq, j in sorted(jan.items()):
        a, b = j["inicio"], j["fim"]
        sel = [{"t": round(w["t"] - a, 2), "w": w["w"]} for w in ws if a - 0.3 <= w["t"] <= b + 0.3]
        res[arq] = sel
    json.dump(res, io.open("analise/palavras.json", "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    print("cortes:", len(res), "palavras totais:", sum(len(v) for v in res.values()))

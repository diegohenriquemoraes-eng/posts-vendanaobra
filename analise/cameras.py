# -*- coding: utf-8 -*-
"""Qual das 3 cameras esta no ar, a cada 1/FPS s, nos trechos dos 27 cortes.

A = fechada na Audrey · D = fechada no Diego · W = plano aberto (TV ao fundo).
"""
import subprocess, json, sys
import numpy as np

FPS = 5
W, H = 64, 36
GX, GY = 8, 6

def grade(buf):
    im = np.frombuffer(buf, dtype=np.uint8).astype(np.float32).reshape(H, W, 3) / 255.0
    cy, cx = H // GY, W // GX
    return im[:GY*cy, :GX*cx].reshape(GY, cy, GX, cx, 3).mean(axis=(1, 3)).ravel()

def ler(path, ss, dur):
    cmd = ["ffmpeg", "-v", "error", "-ss", str(ss), "-i", path, "-t", str(dur),
           "-vf", f"fps={FPS},scale={W}:{H}", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"]
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, bufsize=10**7)
    n = W * H * 3
    out = []
    while True:
        b = p.stdout.read(n)
        if len(b) < n: break
        out.append(grade(b))
    p.wait()
    return np.stack(out) if out else np.zeros((0, GX*GY*3))

def prototipos(master, amostras):
    P = {}
    for nome, ts in amostras.items():
        fs = [ler(master, t, 0.6)[0] for t in ts]
        P[nome] = np.stack(fs).mean(axis=0)
    return P

def suavizar(lab, k=5):
    out = lab.copy()
    for i in range(len(lab)):
        a, b = max(0, i-k), min(len(lab), i+k+1)
        vals, cts = np.unique(lab[a:b], return_counts=True)
        out[i] = vals[cts.argmax()]
    return out

if __name__ == "__main__":
    master = sys.argv[1]
    AMOSTRAS = {"A": [60, 180, 100], "D": [300, 540, 1140, 1620], "W": [420, 660, 1020, 1980]}
    P = prototipos(master, AMOSTRAS)
    nomes = list(P.keys())
    M = np.stack([P[n] for n in nomes])
    jan = json.load(open("analise/janelas.json"))
    res = {}
    for arq, j in sorted(jan.items()):
        X = ler(master, j["inicio"], j["dur"])
        d = np.stack([((X - M[i]) ** 2).sum(axis=1) for i in range(len(nomes))], axis=1)
        lab = suavizar(d.argmin(axis=1))
        seq = [nomes[i] for i in lab]
        # compacta em segmentos
        segs, ini = [], 0
        for i in range(1, len(seq) + 1):
            if i == len(seq) or seq[i] != seq[ini]:
                segs.append({"ini": round(ini / FPS, 2), "fim": round(i / FPS, 2), "cam": seq[ini]})
                ini = i
        res[arq] = segs
        conta = {n: round(sum(s["fim"]-s["ini"] for s in segs if s["cam"] == n), 1) for n in nomes}
        print(f"{arq[:42]:42s} {len(segs):3d} planos  {conta}", flush=True)
    json.dump(res, open("analise/cameras.json", "w"), indent=0)

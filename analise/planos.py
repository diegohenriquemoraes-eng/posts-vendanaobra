# -*- coding: utf-8 -*-
"""Amostra o master, acha as trocas de camera e agrupa os planos por assinatura visual."""
import subprocess, sys, os, json
import numpy as np

FPS = 2
W, H = 48, 27   # miniatura para assinatura

def frames(path):
    cmd = ["ffmpeg", "-v", "error", "-i", path, "-vf", f"fps={FPS},scale={W}:{H}",
           "-f", "rawvideo", "-pix_fmt", "rgb24", "-"]
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, bufsize=10**7)
    n = W * H * 3
    while True:
        buf = p.stdout.read(n)
        if len(buf) < n: break
        yield np.frombuffer(buf, dtype=np.uint8).astype(np.float32) / 255.0

if __name__ == "__main__":
    master = sys.argv[1]
    fs = []
    for i, f in enumerate(frames(master)):
        fs.append(f)
        if i % 2000 == 0: print("frame", i, flush=True)
    X = np.stack(fs); del fs
    print("amostrado:", X.shape, X.shape[0]/FPS, "s", flush=True)

    d = np.abs(np.diff(X, axis=0)).mean(axis=1)
    lim = max(0.055, float(np.percentile(d, 99.0)))
    cortes = [0] + [int(i)+1 for i in np.where(d > lim)[0]] + [X.shape[0]]
    print("limiar", round(lim,4), "cortes detectados:", len(cortes)-2, flush=True)

    cenas = []
    for a, b in zip(cortes[:-1], cortes[1:]):
        if b - a < 2: continue
        cenas.append((a, b, X[a+1:b-1 if b-1 > a+1 else b].mean(axis=0)))
    print("cenas:", len(cenas), flush=True)

    # k-means simples
    F = np.stack([c[2] for c in cenas])
    k = 6
    rng = np.random.default_rng(0)
    C = F[rng.choice(len(F), k, replace=False)]
    for _ in range(40):
        dist = np.stack([((F - C[j]) ** 2).sum(axis=1) for j in range(k)], axis=1)
        lab = dist.argmin(axis=1)
        for j in range(k):
            if (lab == j).any(): C[j] = F[lab == j].mean(axis=0)
    out = [{"ini": round(a/FPS, 2), "fim": round(b/FPS, 2), "grupo": int(l)}
           for (a, b, _), l in zip(cenas, lab)]
    json.dump(out, open("analise/cenas.json", "w"), indent=1)
    for j in range(k):
        seg = [o for o in out if o["grupo"] == j]
        tot = sum(o["fim"]-o["ini"] for o in seg)
        print(f"grupo {j}: {len(seg):4d} cenas, {tot/60:6.1f} min, exemplo em {seg[0]['ini'] if seg else 0}s", flush=True)

# -*- coding: utf-8 -*-
"""Quem fala a cada 0,2s em cada corte, pela altura da voz (F0).

Diego tem voz grave; Audrey, aguda. O limiar sai do proprio episodio (2 modas).
"""
import subprocess, os, json
import numpy as np

SR = 8000
JAN = 1600            # 0,2 s
F_MIN, F_MAX = 70, 330

def audio(path):
    cmd = ["ffmpeg", "-v", "error", "-i", path, "-ac", "1", "-ar", str(SR), "-f", "s16le", "-"]
    raw = subprocess.run(cmd, capture_output=True).stdout
    return np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0

def f0_serie(x):
    n = len(x) // JAN
    fs = np.zeros(n); cs = np.zeros(n); es = np.zeros(n)
    lo, hi = SR // F_MAX, SR // F_MIN
    N = 4096
    for k in range(n):
        seg = x[k*JAN:(k+1)*JAN]
        seg = seg - seg.mean()
        e = float(np.sqrt((seg**2).mean()))
        es[k] = e
        if e < 0.005: continue
        S = np.fft.rfft(seg * np.hanning(len(seg)), N)
        ac = np.fft.irfft(S*np.conj(S), N)[:len(seg)]
        if ac[0] <= 0: continue
        ac = ac / ac[0]
        i = int(np.argmax(ac[lo:hi])) + lo
        fs[k] = SR / i; cs[k] = ac[i]
    return fs, cs, es

if __name__ == "__main__":
    pasta = "midia/reels"
    bruto = {}
    todas = []
    for f in sorted(os.listdir(pasta)):
        if not f.endswith(".mp4"): continue
        fs, cs, es = f0_serie(audio(os.path.join(pasta, f)))
        bruto[f] = (fs, cs, es)
        todas.append(fs[(cs > 0.4) & (fs > 0)])
        print("f0", f[:40], flush=True)
    v = np.concatenate(todas)
    print("voz:", len(v), "p25", round(np.percentile(v,25)), "p50", round(np.percentile(v,50)),
          "p75", round(np.percentile(v,75)))
    LIM = 165.0
    res = {}
    for f, (fs, cs, es) in bruto.items():
        lab = []
        for k in range(len(fs)):
            if cs[k] < 0.4 or fs[k] <= 0 or es[k] < 0.008: lab.append("-")
            else: lab.append("D" if fs[k] < LIM else "A")
        # suaviza: janela de 5 (1 s), moda, ignorando silencio
        out = []
        for i in range(len(lab)):
            jan = [l for l in lab[max(0,i-3):i+4] if l != "-"]
            if not jan: out.append("-")
            else: out.append(max(set(jan), key=jan.count))
        res[f] = "".join(out)
        d = out.count("D"); a = out.count("A"); s = out.count("-")
        print(f"{f[:42]:42s} Diego {d/5:6.1f}s  Audrey {a/5:6.1f}s  silencio {s/5:5.1f}s", flush=True)
    json.dump(res, open("analise/falante.json", "w"), indent=0)

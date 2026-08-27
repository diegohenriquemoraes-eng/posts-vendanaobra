# -*- coding: utf-8 -*-
"""Descobre onde cada corte MP4 comeca no master, por correlacao de envelope de audio."""
import subprocess, sys, os, json
import numpy as np

SR = 8000          # taxa para o envelope
HOP = 80           # 100 Hz de envelope

def audio(path, ss=None, t=None):
    cmd = ["ffmpeg", "-v", "error"]
    if ss is not None: cmd += ["-ss", str(ss)]
    cmd += ["-i", path]
    if t is not None: cmd += ["-t", str(t)]
    cmd += ["-ac", "1", "-ar", str(SR), "-f", "s16le", "-"]
    raw = subprocess.run(cmd, capture_output=True).stdout
    return np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0

def envelope(x):
    n = len(x) // HOP
    x = x[:n * HOP].reshape(n, HOP)
    e = np.sqrt((x ** 2).mean(axis=1) + 1e-12)
    e = np.log(e + 1e-6)
    return (e - e.mean()) / (e.std() + 1e-9)

def achar(env_master, env_corte):
    n = len(env_master); m = len(env_corte)
    N = 1
    while N < n + m: N *= 2
    F = np.fft.rfft(env_master, N) * np.conj(np.fft.rfft(env_corte, N))
    c = np.fft.irfft(F, N)[:n]
    i = int(np.argmax(c))
    pico = float(c[i]) / m
    return i / 100.0, pico

if __name__ == "__main__":
    master = sys.argv[1]
    print("lendo audio do master...", flush=True)
    em = envelope(audio(master))
    print("master:", len(em)/100.0, "s", flush=True)
    out = {}
    pasta = "midia/reels"
    for f in sorted(os.listdir(pasta)):
        if not f.endswith(".mp4"): continue
        ec = envelope(audio(os.path.join(pasta, f)))
        t, p = achar(em, ec)
        dur = len(ec) / 100.0
        out[f] = {"inicio": round(t, 2), "fim": round(t + dur, 2), "dur": round(dur, 2), "score": round(p, 3)}
        print(f"{f[:44]:44s} {t:8.2f} -> {t+dur:8.2f}  score {p:.3f}", flush=True)
    json.dump(out, open("analise/janelas.json", "w"), indent=1)

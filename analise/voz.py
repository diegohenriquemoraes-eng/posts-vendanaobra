# -*- coding: utf-8 -*-
"""Quem fala, por timbre (log-mel) em vez de so altura.

Ancoras: a abertura do episodio e' a Audrey (host); monologos longos do Diego
saem dos trechos de camera fechada nele sem troca de turno na transcricao.
"""
import subprocess, json, os
import numpy as np

SR = 16000
JAN = 3200          # 0,2 s
NFFT = 4096
NMEL = 26

def _mel_bank():
    def hz2mel(f): return 2595 * np.log10(1 + f / 700)
    def mel2hz(m): return 700 * (10 ** (m / 2595) - 1)
    lo, hi = hz2mel(80), hz2mel(7000)
    pts = mel2hz(np.linspace(lo, hi, NMEL + 2))
    bins = np.floor((NFFT + 1) * pts / SR).astype(int)
    B = np.zeros((NMEL, NFFT // 2 + 1))
    for i in range(NMEL):
        a, b, c = bins[i], bins[i+1], bins[i+2]
        if b == a: b = a + 1
        if c == b: c = b + 1
        B[i, a:b] = np.linspace(0, 1, b - a)
        B[i, b:c] = np.linspace(1, 0, c - b)
    return B

BANK = _mel_bank()

def audio(path, ss=None, dur=None):
    cmd = ["ffmpeg", "-v", "error"]
    if ss is not None: cmd += ["-ss", str(ss)]
    cmd += ["-i", path]
    if dur is not None: cmd += ["-t", str(dur)]
    cmd += ["-ac", "1", "-ar", str(SR), "-f", "s16le", "-"]
    raw = subprocess.run(cmd, capture_output=True).stdout
    return np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0

def feats(x):
    """log-mel normalizado + energia, por janela de 0,2 s."""
    n = len(x) // JAN
    F = np.zeros((n, NMEL)); E = np.zeros(n)
    w = np.hanning(JAN)
    for k in range(n):
        seg = x[k*JAN:(k+1)*JAN]
        E[k] = float(np.sqrt((seg**2).mean()))
        S = np.abs(np.fft.rfft(seg * w, NFFT)) ** 2
        m = np.log(BANK @ S + 1e-10)
        F[k] = m - m.mean()          # tira ganho; sobra o timbre
    return F, E

def classificar(F, E, PA, PD, corte=0.008):
    def cos(A, p):
        return (A @ p) / (np.linalg.norm(A, axis=1) * np.linalg.norm(p) + 1e-9)
    sa, sd = cos(F, PA), cos(F, PD)
    lab = np.where(sa > sd, 1, 0)          # 1 = Audrey, 0 = Diego
    lab = np.where(E < corte, -1, lab)
    return lab, sa - sd

def suavizar(lab, k=4):
    out = lab.copy()
    for i in range(len(lab)):
        jan = [v for v in lab[max(0, i-k):i+k+1] if v >= 0]
        if jan: out[i] = 1 if sum(jan) * 2 > len(jan) else 0
    # tapa buracos de silencio com o vizinho
    ult = 0
    for i in range(len(out)):
        if out[i] < 0: out[i] = ult
        else: ult = out[i]
    return out

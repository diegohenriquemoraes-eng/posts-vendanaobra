# -*- coding: utf-8 -*-
"""Onde esta o rosto de cada pessoa, em cada camera do master — com detector de verdade.

Por que existe (04/09/2026): os recortes 9:16 de `montar_reel.py` eram retangulos
escritos a mao e nunca conferidos contra onde as pessoas realmente sentam. No
plano aberto a Audrey saia encostada na borda esquerda do vertical (~195 px fora
do centro) e o Diego ~100 px. O Diego pediu enquadramento centralizado.

Detector: MediaPipe Face Detection (BlazeFace), o mesmo motor que os editores de
video usam por baixo do "auto reframe". Roda offline, o master nao sai daqui.
Uma tentativa anterior por tom de pele foi descartada: devolvia a parede de
marmore como rosto (topo do "rosto" em y=0 nas quatro cameras).

Como o rosto no plano aberto e' pequeno demais para o modelo short-range, a
faixa esperada e' recortada e AMPLIADA antes de detectar — e a coordenada volta
para a escala do master no fim.

Uso: python analise/medir_enquadramento.py
"""
import json, subprocess, sys
import numpy as np
import cv2
import mediapipe as mp
from mediapipe.tasks import python as mpp
from mediapipe.tasks.python import vision

sys.stdout.reconfigure(encoding="utf-8")
MASTER = "master/ep25.mp4"
MODELO = "analise/modelos/blaze_face_short_range.tflite"
LARG, ALT = 1920, 1080

_det = vision.FaceDetector.create_from_options(vision.FaceDetectorOptions(
    base_options=mpp.BaseOptions(model_asset_path=MODELO),
    min_detection_confidence=0.5))


def frame(t):
    b = subprocess.run(
        ["ffmpeg", "-v", "error", "-ss", f"{t:.3f}", "-i", MASTER, "-frames:v", "1",
         "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
    n = LARG * ALT * 3
    return np.frombuffer(b[:n], dtype=np.uint8).reshape(ALT, LARG, 3).copy() if len(b) >= n else None


def rosto(img, x0, x1, escala=2.0):
    """Maior rosto na faixa [x0,x1). -> (cx, cy, olhos_y, largura) na escala do master."""
    faixa = img[:, x0:x1]
    amp = cv2.resize(faixa, None, fx=escala, fy=escala, interpolation=cv2.INTER_LINEAR)
    r = _det.detect(mp.Image(image_format=mp.ImageFormat.SRGB, data=np.ascontiguousarray(amp)))
    if not r.detections:
        return None
    d = max(r.detections, key=lambda d: d.bounding_box.width * d.bounding_box.height)
    b = d.bounding_box
    cx = x0 + (b.origin_x + b.width / 2) / escala
    cy = (b.origin_y + b.height / 2) / escala
    # os olhos sao os dois primeiros keypoints do BlazeFace
    ks = d.keypoints
    olhos = ((ks[0].y + ks[1].y) / 2 * amp.shape[0] / escala) if len(ks) >= 2 else cy
    return cx, cy, olhos, b.width / escala


def medir(nome, x0, x1, amostras, escala=2.0):
    linhas = [rosto(img, x0, x1, escala) for img in (frame(t) for t in amostras) if img is not None]
    linhas = [l for l in linhas if l]
    if not linhas:
        print(f"{nome}: nenhum rosto encontrado"); return None
    a = np.array(linhas)
    cx, olhos, larg = np.median(a[:, 0]), np.median(a[:, 2]), np.median(a[:, 3])
    print(f"{nome}: n={len(a)}/{len(amostras)}  centro_x={cx:7.1f} "
          f"(p10 {np.percentile(a[:,0],10):.0f} · p90 {np.percentile(a[:,0],90):.0f})  "
          f"olhos_y={olhos:6.1f}  larg_rosto={larg:5.1f}")
    return cx, olhos, larg


def main():
    cams = json.load(open("analise/cameras.json"))
    jan = json.load(open("analise/janelas.json"))
    por_cam = {"D": [], "A": [], "W": []}
    for arq, cs in cams.items():
        if arq not in jan:
            continue
        t0 = jan[arq]["inicio"]
        for c in cs:
            if c["fim"] - c["ini"] > 1.5:
                por_cam[c["cam"]].append((t0 + c["ini"] + 0.5, t0 + c["fim"] - 0.5))

    rng = np.random.default_rng(7)
    def amostrar(trechos, n=50):
        return [float(rng.uniform(*trechos[rng.integers(len(trechos))])) for _ in range(n)]

    am_D, am_A, am_W = amostrar(por_cam["D"]), amostrar(por_cam["A"]), amostrar(por_cam["W"])
    print("camera fechada no DIEGO"); medir("  D ", 500, 1920, am_D, 1.0)
    print("camera fechada na AUDREY"); medir("  A ", 0, 1400, am_A, 1.0)
    print("plano aberto — AUDREY");   medir("  WA", 0, 900, am_W, 2.5)
    print("plano aberto — DIEGO");    medir("  WD", 1050, 1920, am_W, 2.5)


if __name__ == "__main__":
    main()

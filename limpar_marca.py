# -*- coding: utf-8 -*-
"""Remove a estrela de marca d'água que o Gemini carimba nas imagens geradas.

A estrela é um overlay claro, semitransparente, sempre na região inferior
direita. O conserto: detectar o bounding box dela por luminância anômala numa
janela dessa região, e cobrir com um remendo do próprio entorno (espelhado e com
média/desvio casados com o anel ao redor), colado com máscara elíptica de borda
muito suave. Funciona bem em fundo de textura contínua (chão, parede, madeira).

Uso:
    python limpar_marca.py entrada.png saida.png
    python limpar_marca.py entrada.png saida.png --debug  (salva o recorte para conferir)

SEMPRE conferir o resultado ampliado — em fundo muito estruturado (grade de
esquadria, estante) o remendo pode falhar e é melhor regenerar a foto.
"""
from __future__ import annotations

import sys
from PIL import Image, ImageDraw, ImageFilter
import numpy as np


def achar_estrela(A: np.ndarray) -> tuple[int, int, int, int] | None:
    """Procura o overlay claro na região inferior direita. Devolve (x0,y0,x1,y1)."""
    H, W, _ = A.shape
    lum = A.sum(axis=2) / 3
    jx0, jy0 = int(W * 0.70), int(H * 0.72)
    win = lum[jy0:, jx0:]
    med = np.median(win)
    mask = win > med + 34
    if mask.sum() < 300:          # nada relevante
        return None
    ys, xs = np.nonzero(mask)
    # concentra no maior aglomerado: descarta pontos isolados (reflexos, céu)
    cx, cy = int(np.median(xs)), int(np.median(ys))
    perto = (np.abs(xs - cx) < 140) & (np.abs(ys - cy) < 140)
    xs, ys = xs[perto], ys[perto]
    if len(xs) < 300:
        return None
    return (jx0 + xs.min(), jy0 + ys.min(), jx0 + xs.max(), jy0 + ys.max())


def limpar(origem: str, destino: str, debug: bool = False) -> bool:
    im = Image.open(origem).convert("RGB")
    A = np.asarray(im).astype(np.float64)
    H, W, _ = A.shape

    box = achar_estrela(A)
    if box is None:
        im.save(destino)
        print("nenhuma marca encontrada — copiado como esta")
        return False
    bx0, by0, bx1, by1 = box
    print(f"estrela em x {bx0}-{bx1}, y {by0}-{by1}")

    # retangulo de trabalho com folga grande (a mascara precisa morrer antes da borda)
    F = 120
    X0, Y0 = max(0, bx0 - F), max(0, by0 - F)
    X1, Y1 = min(W, bx1 + F), min(H, by1 + F)
    w, h = X1 - X0, Y1 - Y0

    # fonte do remendo: mesma faixa, deslocada para a esquerda; espelhada
    dx = w + 40
    if X0 - dx < 0:               # sem espaco a esquerda: usa acima
        dy = h + 40
        src = A[Y0 - dy:Y1 - dy, X0:X1][::-1, :, :].copy()
    else:
        src = A[Y0:Y1, X0 - dx:X0 - dx + w][:, ::-1, :].copy()

    anel = np.concatenate([
        A[max(0, Y0 - 30):Y0, X0:X1].reshape(-1, 3),
        A[Y1:min(H, Y1 + 30), X0:X1].reshape(-1, 3),
        A[Y0:Y1, max(0, X0 - 30):X0].reshape(-1, 3),
        A[Y0:Y1, X1:min(W, X1 + 30)].reshape(-1, 3),
    ])
    for c in range(3):
        s = src[:, :, c]
        src[:, :, c] = (s - s.mean()) * (anel[:, c].std() / max(s.std(), 1e-6)) + anel[:, c].mean()

    m = Image.new("L", (w, h), 0)
    ImageDraw.Draw(m).ellipse([bx0 - 18 - X0, by0 - 18 - Y0,
                               bx1 + 18 - X0, by1 + 18 - Y0], fill=255)
    m = (np.asarray(m.filter(ImageFilter.GaussianBlur(26))).astype(np.float64) / 255.0)[:, :, None]

    A[Y0:Y1, X0:X1] = src * m + A[Y0:Y1, X0:X1] * (1 - m)
    out = Image.fromarray(np.clip(A, 0, 255).astype(np.uint8))
    out.save(destino)

    if debug:
        out.crop((max(0, bx0 - 160), max(0, by0 - 160),
                  min(W, bx1 + 160), min(H, by1 + 160))).save(destino + ".debug.png")
    return True


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if a != "--debug"]
    limpar(args[0], args[1], debug="--debug" in sys.argv)

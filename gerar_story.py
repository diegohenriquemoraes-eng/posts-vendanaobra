# -*- coding: utf-8 -*-
"""Gera o Story de reforco do post do dia (1080x1920).

O Story existe para colocar o post na tela de quem ja segue: boa parte dos
seguidores nao ve o feed, mas ve Story. Formato definido pelo Diego em
03/08/2026: **so a arte do proprio post**, emoldurada no fundo navy — sem
"saiu post novo", sem "toca no perfil", sem chamada nenhuma. A frase do post
E o story.
"""
from __future__ import annotations

import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter

BASE = os.path.dirname(os.path.abspath(__file__))
FONTE = os.path.join(BASE, "fontes", "Inter-Regular.ttf")

LARG, ALT = 1080, 1920
NAVY_ESCURO = (13, 38, 68)
DOURADO = (240, 168, 46)
BRANCO = (255, 255, 255)


def _f(tamanho: int, peso: int = 400) -> ImageFont.FreeTypeFont:
    f = ImageFont.truetype(FONTE, tamanho)
    try:
        f.set_variation_by_axes([14, peso])
    except Exception:
        pass
    return f


def gerar_story(arte_do_post: str, destino: str) -> str:
    """Monta o story com a arte do dia (1080x1080 da frase ou 1080x1350 da aula)."""
    img = Image.new("RGB", (LARG, ALT), NAVY_ESCURO)
    d = ImageDraw.Draw(img)

    arte = Image.open(arte_do_post).convert("RGB")

    # so a arte, grande e centralizada — sem texto nenhum em volta
    w = int(LARG * 0.92)
    h = int(arte.height * w / arte.width)
    h_max = ALT - 240                      # respiro nas pontas
    if h > h_max:
        h = h_max
        w = int(arte.width * h / arte.height)
    arte = arte.resize((w, h), Image.LANCZOS)

    x = (LARG - w) // 2
    y = (ALT - h) // 2

    # sombra suave atras da arte, para descolar do fundo
    sombra = Image.new("RGB", (LARG, ALT), NAVY_ESCURO)
    ImageDraw.Draw(sombra).rectangle([x + 10, y + 14, x + w + 10, y + h + 14],
                                     fill=(5, 16, 30))
    img = Image.composite(sombra.filter(ImageFilter.GaussianBlur(18)), img,
                          Image.new("L", (LARG, ALT), 255))
    img.paste(arte, (x, y))

    os.makedirs(os.path.dirname(destino), exist_ok=True)
    img.save(destino, "JPEG", quality=92, subsampling=0, optimize=True)
    return destino

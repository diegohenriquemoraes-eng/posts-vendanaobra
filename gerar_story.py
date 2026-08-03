# -*- coding: utf-8 -*-
"""Gera o Story de reforco do post do dia (1080x1920).

O Story existe para colocar o post na tela de quem ja segue: boa parte dos
seguidores nao ve o feed, mas ve Story. E a arte do proprio post do dia
(slide 1), emoldurada num fundo navy com uma chamada curta em cima e o
direcionamento para o feed embaixo. Sem link (a Graph API nao publica sticker
de link em story) — o caminho e "post novo no feed".
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

    # arte a ~86% da largura, centralizada; altura conforme a proporcao original
    w = int(LARG * 0.86)
    h = int(arte.height * w / arte.width)
    h_max = ALT - 560                      # sobra para o texto em cima e embaixo
    if h > h_max:
        h = h_max
        w = int(arte.width * h / arte.height)
    arte = arte.resize((w, h), Image.LANCZOS)

    x = (LARG - w) // 2
    y = (ALT - h) // 2 + 20

    # sombra suave atras da arte, para descolar do fundo
    sombra = Image.new("RGB", (LARG, ALT), NAVY_ESCURO)
    ImageDraw.Draw(sombra).rectangle([x + 10, y + 14, x + w + 10, y + h + 14],
                                     fill=(5, 16, 30))
    img = Image.composite(sombra.filter(ImageFilter.GaussianBlur(18)), img,
                          Image.new("L", (LARG, ALT), 255))
    img.paste(arte, (x, y))
    d = ImageDraw.Draw(img)

    # chamada no topo
    d.text((LARG / 2, y - 150), "SAIU POST NOVO", font=_f(34, peso=800),
           fill=DOURADO, anchor="ma")
    d.text((LARG / 2, y - 96), "no feed do @vendanaobra", font=_f(40, peso=600),
           fill=BRANCO, anchor="ma")

    # direcionamento embaixo
    d.text((LARG / 2, y + h + 60), "Toca no perfil e ve o post completo",
           font=_f(32, peso=500), fill=(200, 214, 232), anchor="ma")

    os.makedirs(os.path.dirname(destino), exist_ok=True)
    img.save(destino, "JPEG", quality=92, subsampling=0, optimize=True)
    return destino

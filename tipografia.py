# -*- coding: utf-8 -*-
"""Fonte única da identidade visual dos posts: Instagram Sans.

É a mesma fonte das legendas dos Reels do Diego (legenda automática nativa do
Instagram) — decisão de 12/08/2026 para unificar a identidade visual: todo
conteúdo do @vendanaobra sai com o mesmo tipo de letra, do vídeo ao carrossel.

Diferente da Inter antiga (variável, peso via set_variation_by_axes), a
Instagram Sans vem em arquivos estáticos por peso. Pesos pedidos entre os
arquivos disponíveis arredondam para o mais próximo: >=600 usa Bold, 500 usa
Medium, o resto usa Regular.
"""
from __future__ import annotations

import os
from PIL import ImageFont

BASE = os.path.dirname(os.path.abspath(__file__))

_ARQUIVOS = {
    400: os.path.join(BASE, "fontes", "InstagramSans-Regular.ttf"),
    500: os.path.join(BASE, "fontes", "InstagramSans-Medium.ttf"),
    700: os.path.join(BASE, "fontes", "InstagramSans-Bold.ttf"),
}


def fonte(tamanho: int, peso: int = 400) -> ImageFont.FreeTypeFont:
    """Devolve a Instagram Sans no tamanho pedido, no peso mais próximo."""
    if peso >= 600:
        arquivo = _ARQUIVOS[700]
    elif peso >= 500:
        arquivo = _ARQUIVOS[500]
    else:
        arquivo = _ARQUIVOS[400]
    return ImageFont.truetype(arquivo, tamanho)

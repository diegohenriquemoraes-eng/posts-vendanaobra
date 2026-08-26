# -*- coding: utf-8 -*-
"""Tipografia da identidade do @vendanaobra — a letra nova vive SO NA CAPA.

Historico curto, porque a regra mudou duas vezes no mesmo dia:

25/08/2026, manha — o Diego mandou o print de um Reel dele ("voce perdeu a venda
NA PRIMEIRA REUNIAO", legenda de destaque em serifada didone) e pediu identidade
mais profissional, sem letra arredondada. Troquei a Instagram Sans pela dupla
Playfair Display + Archivo na peca inteira.

25/08/2026, depois de ver — aprovou a capa ("ficou melhor") e **mandou limitar a
mudanca as capas**: o miolo volta a letra de antes, que le melhor em texto
corrido. Entao hoje:

    titulo()  -> Playfair Display   gancho da capa do carrossel e da capa do Reel
    rotulo()  -> Archivo            etiqueta dourada e assinatura, DENTRO da capa
    fonte()   -> Instagram Sans     todo o resto: slides de conteudo, corpo,
                                    numero, CTA, rodape, story e carrossel de frase

A legenda queimada dos 27 Reels do EP25 sempre foi Instagram Sans (arquivos .ass
renderizados em 24/08, medidos no Reel dele) — nunca entrou nessa troca.

Regra para peca nova: **serifada so em texto grande sobre foto**. Em 30px sobre
navy a haste fina da didone perde traco no feed comprimido do Instagram, e foi
exatamente essa a leitura do Diego.
"""
from __future__ import annotations

import os
from PIL import ImageFont

BASE = os.path.dirname(os.path.abspath(__file__))
PASTA = os.path.join(BASE, "fontes")

TITULO_TTF = os.path.join(PASTA, "PlayfairDisplay-Lining.ttf")
# copia da Playfair com algarismos alinhados — ver fontes/preparar_playfair.py
ROTULO_TTF = os.path.join(PASTA, "Archivo.ttf")        # wght 100..900, wdth 62..125

# Instagram Sans: arquivos ESTATICOS por peso (nada de set_variation_by_axes).
_INSTAGRAM = {
    400: os.path.join(PASTA, "InstagramSans-Regular.ttf"),
    500: os.path.join(PASTA, "InstagramSans-Medium.ttf"),
    700: os.path.join(PASTA, "InstagramSans-Bold.ttf"),
}


def _limitar(valor: int, minimo: int, maximo: int) -> int:
    return max(minimo, min(maximo, valor))


def titulo(tamanho: int, peso: int = 700) -> ImageFont.FreeTypeFont:
    """Playfair Display — SO no gancho da capa (carrossel e Reel).

    Peso util: 800/900. A capa aparece pequena na grade do perfil e precisa de
    haste grossa.
    """
    f = ImageFont.truetype(TITULO_TTF, tamanho)
    f.set_variation_by_axes([_limitar(peso, 400, 900)])
    return f


def rotulo(tamanho: int, peso: int = 700, largura: int = 100) -> ImageFont.FreeTypeFont:
    """Archivo — etiqueta dourada e assinatura DENTRO da capa."""
    f = ImageFont.truetype(ROTULO_TTF, tamanho)
    f.set_variation_by_axes([_limitar(peso, 100, 900), _limitar(largura, 62, 125)])
    return f


def fonte(tamanho: int, peso: int = 400) -> ImageFont.FreeTypeFont:
    """Instagram Sans — todo o resto. Pesos >=600 usam Bold, 500 usa Medium."""
    if peso >= 600:
        arquivo = _INSTAGRAM[700]
    elif peso >= 500:
        arquivo = _INSTAGRAM[500]
    else:
        arquivo = _INSTAGRAM[400]
    return ImageFont.truetype(arquivo, tamanho)


def escrever_espacado(d, xy, texto: str, fonte, fill, tracking: float = 0.0) -> float:
    """Escreve com espacamento entre letras (o Pillow nao tem tracking).

    Serve para a etiqueta em caixa alta pequena — dourada na capa. Caixa alta
    apertada parece sigla; com ~10% de tracking vira etiqueta de revista.
    Devolve a largura total escrita, ancorada em "la" (esquerda, topo).
    """
    x, y = xy
    for ch in texto:
        d.text((x, y), ch, font=fonte, fill=fill, anchor="la")
        x += fonte.getlength(ch) + tracking
    return x - xy[0] - (tracking if texto else 0)

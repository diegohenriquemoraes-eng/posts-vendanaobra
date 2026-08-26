# -*- coding: utf-8 -*-
"""Tipografia da identidade do @vendanaobra — duas familias, um par editorial.

Decisao de 25/08/2026 (Diego): a Instagram Sans saiu dos TITULOS. A referencia e
a legenda de destaque dos Reels dele (print do Reel "voce perdeu a venda NA
PRIMEIRA REUNIAO"): serifada didone, alto contraste, caixa alta — cara de
publicacao, nao de aplicativo. A Instagram Sans, geometrica e arredondada,
puxava a peca para o lado "post de celular".

    titulo()  -> Playfair Display   ganchos, titulos de slide, numeros, CTA
    fonte()   -> Archivo            corpo, etiquetas, rodape, assinatura

Por que NAO usar a serifada tambem no corpo: didone tem hastes finissimas; em
30px sobre navy, no feed comprimido do Instagram, o texto perde traco e cansa a
leitura. O par classico de revista e exatamente este — display serifada + sans
neutra de texto. A Archivo e grotesca (nao arredondada), entao a peca inteira
sai do registro anterior, titulo e corpo.

Ambas sao variaveis: o peso pedido vai direto no eixo wght, sem arredondar para
arquivo estatico como era com a Instagram Sans.
"""
from __future__ import annotations

import os
from PIL import ImageFont

BASE = os.path.dirname(os.path.abspath(__file__))
PASTA = os.path.join(BASE, "fontes")

TITULO_TTF = os.path.join(PASTA, "PlayfairDisplay-Lining.ttf")  # wght 400..900
# (copia da Playfair com algarismos alinhados — ver fontes/preparar_playfair.py)
CORPO_TTF = os.path.join(PASTA, "Archivo.ttf")            # wght 100..900, wdth 62..125

# Instagram Sans continua na pasta: as legendas queimadas dos Reels (arquivos .ass
# ja renderizados) foram medidas nela e nao se refazem.


def _limitar(valor: int, minimo: int, maximo: int) -> int:
    return max(minimo, min(maximo, valor))


def titulo(tamanho: int, peso: int = 700) -> ImageFont.FreeTypeFont:
    """Playfair Display no peso pedido. Usar em gancho, titulo e numero.

    Peso util: 700 para titulo de slide, 800/900 para gancho de capa (a capa
    aparece pequena na grade do perfil e precisa de haste grossa).
    """
    f = ImageFont.truetype(TITULO_TTF, tamanho)
    f.set_variation_by_axes([_limitar(peso, 400, 900)])
    return f


def fonte(tamanho: int, peso: int = 400, largura: int = 100) -> ImageFont.FreeTypeFont:
    """Archivo no peso pedido. Usar em corpo, etiqueta, rodape e assinatura."""
    f = ImageFont.truetype(CORPO_TTF, tamanho)
    f.set_variation_by_axes([_limitar(peso, 100, 900), _limitar(largura, 62, 125)])
    return f


def escrever_espacado(d, xy, texto: str, fonte, fill, tracking: float = 0.0) -> float:
    """Escreve com espacamento entre letras (o Pillow nao tem tracking).

    Serve para a etiqueta em caixa alta pequena — dourada na capa. Caixa alta
    apertada parece sigla; com ~8% de tracking vira etiqueta de revista.
    Devolve a largura total escrita, ancorada em "la" (esquerda, topo).
    """
    x, y = xy
    for ch in texto:
        d.text((x, y), ch, font=fonte, fill=fill, anchor="la")
        x += fonte.getlength(ch) + tracking
    return x - xy[0] - (tracking if texto else 0)

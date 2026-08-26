# -*- coding: utf-8 -*-
"""Gera PlayfairDisplay-Lining.ttf a partir do arquivo original do Google Fonts.

A Playfair Display vem com algarismos OLD-STYLE por padrao (o 3, o 4, o 7 e o 9
descem abaixo da linha de base). Em texto corrido isso e bonito; no numero
grande do slide da mini-aula quebra o alinhamento entre slides — foi exatamente
a reprovacao do Diego em 03/08/2026 ("o 4 parece mais baixo que o 3").

A fonte tem os algarismos alinhados (feature `lnum`, glifos `*.lf`), mas o
Pillow desta maquina foi compilado SEM libraqm e nao aplica features OpenType.
A saida e apontar o cmap dos digitos direto para os glifos `.lf` e salvar uma
copia. Rodar de novo so se a fonte for atualizada:

    python fontes/preparar_playfair.py
"""
import os
from fontTools.ttLib import TTFont

BASE = os.path.dirname(os.path.abspath(__file__))
ORIGEM = os.path.join(BASE, "PlayfairDisplay.ttf")
DESTINO = os.path.join(BASE, "PlayfairDisplay-Lining.ttf")

DIGITOS = {ord(str(n)): nome for n, nome in enumerate(
    ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine"])}

fonte = TTFont(ORIGEM)
faltando = [g for g in DIGITOS.values() if f"{g}.lf" not in fonte.getGlyphOrder()]
if faltando:
    raise SystemExit(f"Glifos lining ausentes: {faltando}")

for tabela in fonte["cmap"].tables:
    for cp, nome in DIGITOS.items():
        if cp in tabela.cmap:
            tabela.cmap[cp] = f"{nome}.lf"

fonte.save(DESTINO)
print("gravado:", DESTINO)

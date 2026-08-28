# -*- coding: utf-8 -*-
"""Exporta a foto de capa da mini-aula do MASTER para fotos/miniaula-XX.jpg.

Existe por causa de um erro pago em 27/08/2026: seis capas (04, 06, 10, 13, 16,
18) foram exportadas do PREVIEW do Gemini (928x1152) em vez do "tamanho
original" (1856x2304). Como o slide e 1080x1350, a foto era AMPLIADA na
montagem e a capa saiu borrada no feed — o post da aula 10 foi ao ar assim.

Regra que fica: **a foto de capa nunca pode ser menor que o slide**. Este
script e a porta de entrada de qualquer foto nova; `gerar_miniaula.gerar_capa`
recusa foto pequena, e `publicar_miniaula.escolher` pula a aula que tiver uma
(mesmo tratamento de "aula sem foto"), para o robo nunca publicar capa ampliada.

Uso:
    python preparar_foto.py 10                       # master padrao da pasta Fotos-IA
    python preparar_foto.py 18 --de caminho/x.png    # master especifico
    python preparar_foto.py --conferir               # audita as fotos ja no repo
"""
from __future__ import annotations

import argparse
import glob
import os

from PIL import Image

BASE = os.path.dirname(os.path.abspath(__file__))
FOTOS = os.path.join(BASE, "fotos")
MASTERS = r"C:\Users\NOTE\Desktop\Perffec\Claude\Fotos-IA\miniaulas"

# o slide da capa (gerar_miniaula.LARG/ALT). Abaixo disso a foto e ampliada.
MIN_LARG, MIN_ALT = 1080, 1350


def conferir(caminho: str) -> tuple[int, int]:
    """Devolve o tamanho, ou levanta se a foto for menor que o slide."""
    with Image.open(caminho) as im:
        larg, alt = im.size
    if larg < MIN_LARG or alt < MIN_ALT:
        raise SystemExit(
            f"{os.path.basename(caminho)}: {larg}x{alt} e MENOR que o slide "
            f"{MIN_LARG}x{MIN_ALT} — capa sairia ampliada/borrada. "
            "Baixe o 'tamanho original' do Gemini (1856x2304), nao o preview."
        )
    return larg, alt


def master_de(num: str) -> str:
    """O master da aula: prefere a versao v2 (cena de construcao) quando existe."""
    for padrao in (f"miniaula-{num}-v2-*.png", f"miniaula-{num}-master.png"):
        achados = sorted(glob.glob(os.path.join(MASTERS, padrao)))
        if achados:
            return achados[-1]
    raise SystemExit(f"nenhum master encontrado para a aula {num} em {MASTERS}")


def exportar(num: str, de: str | None = None) -> str:
    origem = de or master_de(num)
    larg, alt = conferir(origem)
    destino = os.path.join(FOTOS, f"miniaula-{num}.jpg")
    with Image.open(origem) as im:
        im.convert("RGB").save(destino, "JPEG", quality=95, subsampling=0, optimize=True)
    print(f"{os.path.basename(origem)} ({larg}x{alt}) -> {destino}")
    return destino


def auditar() -> int:
    """Lista as fotos do repo e aponta as que sairiam ampliadas."""
    ruins = 0
    for caminho in sorted(glob.glob(os.path.join(FOTOS, "*.jpg"))):
        with Image.open(caminho) as im:
            larg, alt = im.size
        ok = larg >= MIN_LARG and alt >= MIN_ALT
        ruins += 0 if ok else 1
        print(f"{'ok  ' if ok else 'BAIXA'} {os.path.basename(caminho)} {larg}x{alt}")
    if ruins:
        print(f"\n{ruins} foto(s) abaixo de {MIN_LARG}x{MIN_ALT}: refazer o "
              "download do master no tamanho original antes de publicar.")
    return ruins


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("numero", nargs="?", help="numero da aula, com zero (ex.: 04)")
    ap.add_argument("--de", metavar="PNG", help="master especifico")
    ap.add_argument("--conferir", action="store_true", help="audita fotos/ e sai")
    args = ap.parse_args()
    if args.conferir:
        raise SystemExit(1 if auditar() else 0)
    if not args.numero:
        ap.error("informe o numero da aula ou use --conferir")
    exportar(args.numero.zfill(2), args.de)

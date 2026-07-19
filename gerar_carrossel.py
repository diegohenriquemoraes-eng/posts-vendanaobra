# -*- coding: utf-8 -*-
"""Gera os 2 slides do carrossel a partir de uma frase.

Slide 1: fundo branco, letra preta.
Slide 2: fundo preto, letra branca.

Formato de referencia: @juliopereira.oficial — frase centralizada entre aspas
tipograficas, blocos separados por linha em branco, assinatura discreta no rodape.
"""
from __future__ import annotations

import os
from PIL import Image, ImageDraw, ImageFont

BASE = os.path.dirname(os.path.abspath(__file__))
FONTE = os.path.join(BASE, "fontes", "Inter-Regular.ttf")

LADO = 1080
MARGEM_X = 132
LARGURA_TEXTO = LADO - 2 * MARGEM_X

ASSINATURA = "Para vender mais siga o @vendanaobra"

TEMAS = {
    "claro": {"fundo": (255, 255, 255), "texto": (17, 17, 17), "assinatura": (184, 184, 184)},
    "escuro": {"fundo": (11, 11, 11), "texto": (255, 255, 255), "assinatura": (110, 110, 110)},
}

# alturas maximas que o bloco de texto pode ocupar
ALTURA_MAX = 700
TOPO_AREA = 158          # area util do texto comeca aqui
Y_ASSINATURA = 968

TAMANHO_MAX = 58
TAMANHO_MIN = 28
ENTRELINHA = 1.42        # multiplicador da altura da linha
GAP_PARAGRAFO = 0.80     # espaco extra entre blocos, em linhas


def _fonte(tamanho: int, peso: int = 400) -> ImageFont.FreeTypeFont:
    f = ImageFont.truetype(FONTE, tamanho)
    try:
        f.set_variation_by_axes([14, peso])
    except Exception:
        pass
    return f


def _quebrar(texto: str, fonte: ImageFont.FreeTypeFont, largura: int) -> list[str]:
    """Quebra um paragrafo em linhas que cabem na largura dada."""
    linhas: list[str] = []
    for palavra in texto.split():
        if not linhas:
            linhas.append(palavra)
            continue
        tentativa = linhas[-1] + " " + palavra
        if fonte.getlength(tentativa) <= largura:
            linhas[-1] = tentativa
        else:
            linhas.append(palavra)
    return linhas


def _montar(frase: str, tamanho: int) -> tuple[list[tuple[str, bool]], int, int]:
    """Devolve (linhas, altura_total, altura_linha) para um tamanho de fonte.

    Cada item de `linhas` e (texto, e_ultima_linha_do_paragrafo).
    """
    fonte = _fonte(tamanho)
    altura_linha = int(tamanho * ENTRELINHA)
    paragrafos = [p.strip() for p in frase.split("\n\n") if p.strip()]

    linhas: list[tuple[str, bool]] = []
    for p in paragrafos:
        quebradas = _quebrar(p, fonte, LARGURA_TEXTO)
        for i, ln in enumerate(quebradas):
            linhas.append((ln, i == len(quebradas) - 1))

    altura = 0
    for i, (_, fim_par) in enumerate(linhas):
        altura += altura_linha
        if fim_par and i != len(linhas) - 1:
            altura += int(altura_linha * GAP_PARAGRAFO)
    return linhas, altura, altura_linha


def _ajustar(frase: str) -> tuple[list[tuple[str, bool]], int, int, int]:
    """Acha o maior tamanho de fonte em que a frase ainda cabe na area util."""
    for tamanho in range(TAMANHO_MAX, TAMANHO_MIN - 1, -1):
        linhas, altura, altura_linha = _montar(frase, tamanho)
        cabe_largura = all(
            _fonte(tamanho).getlength(ln) <= LARGURA_TEXTO for ln, _ in linhas
        )
        if altura <= ALTURA_MAX and cabe_largura:
            return linhas, altura, altura_linha, tamanho
    linhas, altura, altura_linha = _montar(frase, TAMANHO_MIN)
    return linhas, altura, altura_linha, TAMANHO_MIN


def gerar_slide(frase: str, tema: str, destino: str) -> str:
    cores = TEMAS[tema]
    img = Image.new("RGB", (LADO, LADO), cores["fundo"])
    d = ImageDraw.Draw(img)

    texto = "“" + frase.strip() + "”"
    linhas, altura, altura_linha, tamanho = _ajustar(texto)
    fonte = _fonte(tamanho)

    y = TOPO_AREA + (ALTURA_MAX - altura) // 2
    for i, (ln, fim_par) in enumerate(linhas):
        d.text((LADO / 2, y), ln, font=fonte, fill=cores["texto"], anchor="ma")
        y += altura_linha
        if fim_par and i != len(linhas) - 1:
            y += int(altura_linha * GAP_PARAGRAFO)

    fonte_ass = _fonte(25, peso=400)
    d.text(
        (LADO / 2, Y_ASSINATURA),
        ASSINATURA,
        font=fonte_ass,
        fill=cores["assinatura"],
        anchor="ma",
    )

    os.makedirs(os.path.dirname(destino), exist_ok=True)
    img.save(destino, "JPEG", quality=95, subsampling=0, optimize=True)
    return destino


def gerar_carrossel(frase: str, pasta: str, slug: str) -> list[str]:
    return [
        gerar_slide(frase, "claro", os.path.join(pasta, f"{slug}-1.jpg")),
        gerar_slide(frase, "escuro", os.path.join(pasta, f"{slug}-2.jpg")),
    ]


if __name__ == "__main__":
    import sys

    frase = sys.argv[1] if len(sys.argv) > 1 else (
        "Orçamento enviado não é venda em andamento.\n\n"
        "É só um preço esperando alguém decidir por você."
    )
    for caminho in gerar_carrossel(frase, os.path.join(BASE, "saida"), "teste"):
        print(caminho)

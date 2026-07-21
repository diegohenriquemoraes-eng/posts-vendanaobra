# -*- coding: utf-8 -*-
"""Gera os slides do carrossel a partir de uma frase.

Slide 1: fundo branco, letra preta.
Slide 2: fundo preto, letra branca.
Slide 3 (CTA): fundo azul da marca (#18406F), letra branca — o azul do site
vendanaobra.com.br, que fecha o carrossel. O conteudo do CTA vem de fora
(legenda.py).

Formato de referencia: @juliopereira.oficial — frase centralizada entre aspas
tipograficas, blocos separados por linha em branco, assinatura discreta no rodape.
"""
from __future__ import annotations

import os
from PIL import Image, ImageDraw, ImageFont

BASE = os.path.dirname(os.path.abspath(__file__))
FONTE = os.path.join(BASE, "fontes", "Inter-Regular.ttf")

LADO = 1080
MARGEM_X = 150          # margem lateral folgada: o texto nunca encosta na borda
LARGURA_TEXTO = LADO - 2 * MARGEM_X

ASSINATURA = "Para vender mais siga o @vendanaobra"

TEMAS = {
    "claro": {"fundo": (255, 255, 255), "texto": (17, 17, 17), "assinatura": (184, 184, 184)},
    "escuro": {"fundo": (11, 11, 11), "texto": (255, 255, 255), "assinatura": (110, 110, 110)},
    # azul da marca (#18406F, amostrado do hero de vendanaobra.com.br), texto
    # branco; rodape num azul-claro suave para ler como assinatura discreta
    "cta": {"fundo": (24, 64, 111), "texto": (255, 255, 255), "assinatura": (200, 214, 232)},
}

# altura maxima que o bloco de texto pode ocupar (limite antes de encolher a fonte)
ALTURA_MAX = 700
CENTRO_TEXTO = 540       # o bloco e centralizado no meio da imagem (1080/2)
Y_ASSINATURA = 968

# Tamanho de fonte FIXO para dar um padrao unico em todos os posts: a frase sai
# sempre com a mesma letra e na mesma posicao. So encolhe (ate TAMANHO_MIN) se
# uma frase excepcionalmente longa nao couber — no banco atual nenhuma precisa.
TAMANHO_MAX = 52
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


def _desenhar_texto(d: ImageDraw.ImageDraw, texto: str, cor) -> None:
    """Desenha o bloco de texto centralizado na area util (auto-ajuste de fonte)."""
    linhas, altura, altura_linha, tamanho = _ajustar(texto)
    fonte = _fonte(tamanho)

    y = CENTRO_TEXTO - altura // 2
    for i, (ln, fim_par) in enumerate(linhas):
        d.text((LADO / 2, y), ln, font=fonte, fill=cor, anchor="ma")
        y += altura_linha
        if fim_par and i != len(linhas) - 1:
            y += int(altura_linha * GAP_PARAGRAFO)


def _rodape(d: ImageDraw.ImageDraw, texto: str, cor, tamanho: int = 25, peso: int = 400) -> None:
    d.text((LADO / 2, Y_ASSINATURA), texto, font=_fonte(tamanho, peso=peso), fill=cor, anchor="ma")


def _salvar_jpeg(img: Image.Image, destino: str) -> str:
    os.makedirs(os.path.dirname(destino), exist_ok=True)
    img.save(destino, "JPEG", quality=95, subsampling=0, optimize=True)
    return destino


def gerar_slide(frase: str, tema: str, destino: str) -> str:
    cores = TEMAS[tema]
    img = Image.new("RGB", (LADO, LADO), cores["fundo"])
    d = ImageDraw.Draw(img)

    _desenhar_texto(d, "“" + frase.strip() + "”", cores["texto"])
    _rodape(d, ASSINATURA, cores["assinatura"])
    return _salvar_jpeg(img, destino)


def gerar_slide_cta(texto: str, rodape: str, destino: str) -> str:
    """Terceiro slide: CTA em fundo azul da marca, texto branco.

    Sem aspas tipograficas (nao e uma frase-citacao, e uma chamada). `rodape`
    e o direcionamento: @vendanaobra no CTA de seguir, vendanaobra.com.br nos
    de produto. Fica um pouco mais forte que a assinatura dos outros slides,
    porque aqui o rodape e o proprio destino da acao.
    """
    cores = TEMAS["cta"]
    img = Image.new("RGB", (LADO, LADO), cores["fundo"])
    d = ImageDraw.Draw(img)

    _desenhar_texto(d, texto.strip(), cores["texto"])
    _rodape(d, rodape, cores["assinatura"], tamanho=30, peso=600)
    return _salvar_jpeg(img, destino)


def gerar_carrossel(
    frase: str,
    pasta: str,
    slug: str,
    cta_texto: str | None = None,
    cta_rodape: str | None = None,
) -> list[str]:
    """Gera os slides 1 e 2 sempre; o 3o (CTA) quando `cta_texto` e passado."""
    caminhos = [
        gerar_slide(frase, "claro", os.path.join(pasta, f"{slug}-1.jpg")),
        gerar_slide(frase, "escuro", os.path.join(pasta, f"{slug}-2.jpg")),
    ]
    if cta_texto is not None:
        caminhos.append(
            gerar_slide_cta(cta_texto, cta_rodape or "", os.path.join(pasta, f"{slug}-3.jpg"))
        )
    return caminhos


if __name__ == "__main__":
    import sys

    frase = sys.argv[1] if len(sys.argv) > 1 else (
        "Orçamento enviado não é venda em andamento.\n\n"
        "É só um preço esperando alguém decidir por você."
    )
    for caminho in gerar_carrossel(
        frase,
        os.path.join(BASE, "saida"),
        "teste",
        cta_texto="Gostou?\n\nSegue o @vendanaobra e vem vender mais na obra.",
        cta_rodape="@vendanaobra",
    ):
        print(caminho)

# -*- coding: utf-8 -*-
"""Gera o carrossel de MINI-AULA (formato F2) — 1080x1350, 4:5.

Diferente do carrossel de frase (`gerar_carrossel.py`, 1080x1080), que existe
para identidade e compartilhamento. A mini-aula existe para ser SALVA: ensina
uma coisa inteira dentro do post. O algoritmo distribui pelo que e salvo, e em
B2B o formato mais salvo e o utilitario (script pronto, checklist, passo a passo).

Decisoes de formato (benchmark de agosto/2026, ver CLAUDE.md):
  - 4:5 (1080x1350) e nao 1:1 — ocupa mais tela no feed do celular;
  - 6 a 8 slides (o sweet spot medido e 7) — 10 derruba a taxa de conclusao;
  - capa com FOTO e gancho de 4 a 7 palavras; uma ideia por slide dali em diante;
  - ultimo slide pede a acao.

A capa e o unico slide com foto. Os slides de conteudo sao tipograficos no navy
da marca, pelo mesmo motivo do carrossel de frase: legibilidade no feed e custo
zero de producao.
"""
from __future__ import annotations

import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter

from tipografia import fonte as _fonte_base

BASE = os.path.dirname(os.path.abspath(__file__))

LARG, ALT = 1080, 1350          # 4:5
MARGEM = 96
UTIL = LARG - 2 * MARGEM

# Paleta da marca (mesma do site e do carrossel de frase)
NAVY = (24, 64, 111)            # #18406F
NAVY_ESCURO = (13, 38, 68)
DOURADO = (240, 168, 46)        # #F0A82E, o acento dos CTAs do site
BRANCO = (255, 255, 255)
PRATA = (243, 243, 243)
GRAFITE = (20, 19, 15)
CINZA = (150, 163, 180)

ASSINATURA = "@vendanaobra"


def _f(tamanho: int, peso: int = 400) -> ImageFont.FreeTypeFont:
    return _fonte_base(tamanho, peso)


def _quebrar(texto: str, fonte, largura: int) -> list[str]:
    linhas: list[str] = []
    for palavra in texto.split():
        if not linhas:
            linhas.append(palavra)
            continue
        if fonte.getlength(linhas[-1] + " " + palavra) <= largura:
            linhas[-1] += " " + palavra
        else:
            linhas.append(palavra)
    return linhas


def _bloco(d, texto: str, x: int, y: int, largura: int, fonte,
           cor, entrelinha: float = 1.38, gap_par: float = 0.7,
           ancora: str = "la") -> int:
    """Escreve um texto com paragrafos (\\n\\n) e devolve o y final."""
    lh = int(fonte.size * entrelinha)
    pars = [p.strip() for p in texto.split("\n\n") if p.strip()]
    for i, p in enumerate(pars):
        for ln in _quebrar(p, fonte, largura):
            d.text((x, y), ln, font=fonte, fill=cor, anchor=ancora)
            y += lh
        if i != len(pars) - 1:
            y += int(lh * gap_par)
    return y


def _altura_bloco(texto: str, largura: int, fonte,
                  entrelinha: float = 1.38, gap_par: float = 0.7) -> int:
    lh = int(fonte.size * entrelinha)
    pars = [p.strip() for p in texto.split("\n\n") if p.strip()]
    h = 0
    for i, p in enumerate(pars):
        h += lh * len(_quebrar(p, fonte, largura))
        if i != len(pars) - 1:
            h += int(lh * gap_par)
    return h


def _ajustar(texto: str, largura: int, altura_max: int,
             maior: int, menor: int, peso: int = 400):
    """Maior corpo em que o texto ainda cabe na caixa."""
    for t in range(maior, menor - 1, -1):
        f = _f(t, peso)
        if _altura_bloco(texto, largura, f) <= altura_max:
            return f
    return _f(menor, peso)


def _salvar(img: Image.Image, destino: str) -> str:
    os.makedirs(os.path.dirname(destino), exist_ok=True)
    img.save(destino, "JPEG", quality=92, subsampling=0, optimize=True)
    return destino


# --------------------------------------------------------------------- capa

def _cobrir(foto: Image.Image, larg: int, alt: int) -> Image.Image:
    """Recorta a foto no formato do slide sem distorcer (efeito object-fit: cover)."""
    escala = max(larg / foto.width, alt / foto.height)
    nova = foto.resize((round(foto.width * escala), round(foto.height * escala)),
                       Image.LANCZOS)
    esq = (nova.width - larg) // 2
    topo = (nova.height - alt) // 2
    return nova.crop((esq, topo, esq + larg, topo + alt))


def gerar_capa(titulo: str, etiqueta: str, foto_path: str, destino: str) -> str:
    """Slide 1: foto + gancho curto.

    O degrade fecha em preto SOLIDO na base (mesma regra da secao de servicos do
    site): sem isso o texto briga com a foto e o slide fica ilegivel no feed.
    """
    img = _cobrir(Image.open(foto_path).convert("RGB"), LARG, ALT)

    # escurece a foto inteira de leve, para o texto ganhar contraste
    img = Image.blend(img, Image.new("RGB", (LARG, ALT), (0, 0, 0)), 0.18)

    # degrade de baixo para cima, fechando em preto solido atras do texto.
    # A curva usa smoothstep: comeco e fim suaves, sem o degrau visivel que uma
    # rampa linear (ou de expoente unico) deixa no meio da foto.
    grad = Image.new("L", (1, ALT))
    ini, fim = 0.40, 0.90
    for y in range(ALT):
        p = y / ALT
        if p <= ini:
            v = 0
        else:
            t = min(1.0, (p - ini) / (fim - ini))
            v = int(255 * (t * t * (3 - 2 * t)))
        grad.putpixel((0, y), v)
    mascara = grad.resize((LARG, ALT))
    img = Image.composite(Image.new("RGB", (LARG, ALT), (6, 10, 16)), img, mascara)

    d = ImageDraw.Draw(img)

    # etiqueta dourada no alto do bloco de texto
    fe = _f(30, peso=700)
    y_txt = ALT - 130
    ft = _ajustar(titulo, UTIL, 560, 92, 54, peso=800)
    altura_titulo = _altura_bloco(titulo, UTIL, ft, entrelinha=1.16)
    y_titulo = y_txt - altura_titulo
    d.text((MARGEM, y_titulo - 58), etiqueta.upper(), font=fe, fill=DOURADO, anchor="la")
    _bloco(d, titulo, MARGEM, y_titulo, UTIL, ft, BRANCO, entrelinha=1.16)

    # marca discreta no topo
    d.text((MARGEM, 64), ASSINATURA, font=_f(30, peso=600), fill=(255, 255, 255), anchor="la")

    # dica de swipe, no rodape direito
    d.text((LARG - MARGEM, ALT - 52), "arrasta →", font=_f(26, peso=500),
           fill=(190, 200, 214), anchor="ra")
    return _salvar(img, destino)


# ----------------------------------------------------------------- conteudo

# ------------------------------------------------------------------- ancoras
# Y FIXO para cada elemento, igual em TODOS os slides da peca. Nada de
# centralizar o bloco pelo conteudo do proprio slide: isso fazia o numero comecar
# numa altura diferente em cada um, e ao deslizar o carrossel o elemento "pulava".
# Ver feedback do Diego em 03/08/2026 (o "4" parecia maior e mais baixo que o "3").
Y_NUMERO = 190
Y_TITULO = 340
Y_CORPO = 640            # espaco reservado para titulo de ate 3 linhas
Y_TITULO_SEM_NUM = 240   # slides sem numero (o claro) comecam mais acima
Y_CORPO_SEM_NUM = 560
Y_RODAPE = ALT - 110


def gerar_slide(numero: str, titulo: str, corpo: str, destino: str,
                rodape: str | None = None,
                fonte_titulo=None, fonte_corpo=None) -> str:
    """Slide de conteudo: navy, numero dourado, um titulo e um corpo.

    `fonte_titulo` e `fonte_corpo` vem prontos de fora (calculados uma vez para a
    peca inteira em `_fontes_da_peca`), para todos os slides sairem com a mesma
    letra. Auto-ajuste por slide fazia um titulo parecer maior que o do vizinho.
    """
    img = Image.new("RGB", (LARG, ALT), NAVY)
    d = ImageDraw.Draw(img)

    # faixa dourada fininha no topo: costura visual entre os slides
    d.rectangle([0, 0, LARG, 8], fill=DOURADO)

    ft = fonte_titulo or _f(56, peso=700)
    fc = fonte_corpo or _f(34, peso=400)

    if numero:
        d.text((MARGEM, Y_NUMERO), numero, font=_f(104, peso=800),
               fill=DOURADO, anchor="ls")
        _bloco(d, titulo, MARGEM, Y_TITULO, UTIL, ft, BRANCO, entrelinha=1.22)
        _bloco(d, corpo, MARGEM, Y_CORPO, UTIL, fc, (214, 224, 238))
    else:
        _bloco(d, titulo, MARGEM, Y_TITULO_SEM_NUM, UTIL, ft, BRANCO, entrelinha=1.22)
        _bloco(d, corpo, MARGEM, Y_CORPO_SEM_NUM, UTIL, fc, (214, 224, 238))

    if rodape:
        d.text((MARGEM, Y_RODAPE), rodape, font=_f(27, peso=500), fill=CINZA, anchor="la")
    d.text((LARG - MARGEM, Y_RODAPE), ASSINATURA, font=_f(27, peso=600),
           fill=CINZA, anchor="ra")
    return _salvar(img, destino)


def gerar_slide_claro(titulo: str, corpo: str, destino: str,
                      fonte_titulo=None, fonte_corpo=None) -> str:
    """Slide prata: quebra o ritmo do navy. Usado na virada do argumento.

    Usa as MESMAS ancoras e as mesmas fontes dos slides navy sem numero, para o
    contraste ser so de cor — nada de posicao muda ao deslizar.
    """
    img = Image.new("RGB", (LARG, ALT), PRATA)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, LARG, 8], fill=NAVY)

    ft = fonte_titulo or _f(56, peso=700)
    fc = fonte_corpo or _f(34, peso=400)

    _bloco(d, titulo, MARGEM, Y_TITULO_SEM_NUM, UTIL, ft, GRAFITE, entrelinha=1.22)
    _bloco(d, corpo, MARGEM, Y_CORPO_SEM_NUM, UTIL, fc, (74, 78, 86))

    d.text((LARG - MARGEM, Y_RODAPE), ASSINATURA, font=_f(27, peso=600),
           fill=(150, 150, 150), anchor="ra")
    return _salvar(img, destino)


def gerar_slide_cta(titulo: str, corpo: str, palavra: str, destino: str) -> str:
    """Ultimo slide: a acao. Navy escuro + pilula dourada com a palavra do Direct."""
    img = Image.new("RGB", (LARG, ALT), NAVY_ESCURO)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, LARG, 8], fill=DOURADO)

    TOPO, BASE, GAP = 180, 210, 40
    ALTURA_PILULA = 208            # pilula + a linha de apoio abaixo dela
    disponivel = ALT - TOPO - BASE

    ft = _ajustar(titulo, UTIL, 340, 72, 44, peso=800)
    h_tit = _altura_bloco(titulo, UTIL, ft, entrelinha=1.2)
    fc = _ajustar(corpo, UTIL, disponivel - h_tit - GAP - ALTURA_PILULA, 38, 26, peso=400)
    h_cor = _altura_bloco(corpo, UTIL, fc)

    total = h_tit + GAP + h_cor + (ALTURA_PILULA if palavra else 0)
    y = TOPO + max(0, (disponivel - total) // 2)
    y = _bloco(d, titulo, MARGEM, y, UTIL, ft, BRANCO, entrelinha=1.2)
    y += GAP
    y = _bloco(d, corpo, MARGEM, y, UTIL, fc, (206, 218, 234))

    # pilula dourada com a palavra-chave do comment-to-DM
    if palavra:
        fp = _f(46, peso=800)
        texto = f"Comenta {palavra}"
        larg_txt = fp.getlength(texto)
        px, py = MARGEM, y + 70
        pw, ph = larg_txt + 96, 104
        d.rounded_rectangle([px, py, px + pw, py + ph], radius=ph // 2, fill=DOURADO)
        d.text((px + pw / 2, py + ph / 2), texto, font=fp, fill=(20, 20, 20), anchor="mm")
        d.text((MARGEM, py + ph + 34), "que eu te mando o link no seu Direct.",
               font=_f(30, peso=400), fill=(180, 195, 214), anchor="la")

    d.text((LARG - MARGEM, ALT - 110), ASSINATURA, font=_f(27, peso=600),
           fill=CINZA, anchor="ra")
    return _salvar(img, destino)


def _fontes_da_peca(aula: dict) -> tuple:
    """UM tamanho de titulo e UM de corpo para o carrossel inteiro.

    Acha o maior corpo em que o PIOR caso (o texto mais longo da peca) ainda cabe
    na caixa, e usa esse tamanho em todos os slides. Sem isso, o auto-ajuste dava
    letra diferente em cada slide e o vizinho parecia maior — foi a reprovacao do
    Diego em 03/08/2026.
    """
    titulos = [s["titulo"] for s in aula["slides"]]
    corpos = [s["corpo"] for s in aula["slides"]]

    caixa_titulo = Y_CORPO - Y_TITULO - 30           # espaco reservado ao titulo
    caixa_corpo = Y_RODAPE - Y_CORPO - 60

    ft = _f(56, peso=700)
    for t in range(58, 37, -1):
        f = _f(t, peso=700)
        if all(_altura_bloco(x, UTIL, f, entrelinha=1.22) <= caixa_titulo for x in titulos):
            ft = f
            break

    fc = _f(30, peso=400)
    for t in range(38, 25, -1):
        f = _f(t, peso=400)
        if all(_altura_bloco(x, UTIL, f) <= caixa_corpo for x in corpos):
            fc = f
            break
    return ft, fc


def gerar(aula: dict, pasta: str, slug: str) -> list[str]:
    """Monta o carrossel inteiro a partir do dicionario da mini-aula."""
    ft, fc = _fontes_da_peca(aula)

    caminhos = [gerar_capa(aula["titulo"], aula["etiqueta"], aula["foto"],
                           os.path.join(pasta, f"{slug}-1.jpg"))]

    n = 2
    for s in aula["slides"]:
        destino = os.path.join(pasta, f"{slug}-{n}.jpg")
        if s.get("tema") == "claro":
            caminhos.append(gerar_slide_claro(s["titulo"], s["corpo"], destino, ft, fc))
        else:
            caminhos.append(gerar_slide(s.get("numero", ""), s["titulo"], s["corpo"],
                                        destino, s.get("rodape"), ft, fc))
        n += 1

    cta = aula["cta"]
    caminhos.append(gerar_slide_cta(cta["titulo"], cta["corpo"], cta["palavra"],
                                    os.path.join(pasta, f"{slug}-{n}.jpg")))
    return caminhos

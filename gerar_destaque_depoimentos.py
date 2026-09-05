# -*- coding: utf-8 -*-
"""Artes do destaque "Depoimentos" do @vendanaobra (Venda 10x).

Decisao do Diego em 05/09/2026: no destaque vale mais o PRINT da conversa do
que o depoimento formalizado do site — texto editado "parece superficial".

Por que os baloes sao REDESENHADOS e nao o print original:

1. O print do Gilliard vem com o painel de contato aberto do WhatsApp Web:
   foto e **telefone** dele na tela. Publicar aquilo no Instagram vazaria o
   numero de um cliente.
2. O da Sueli tem erros de digitacao ("bo", "carreira" por "cara", "ru cobro");
   o Diego pediu a correcao.
3. Tres prints de origens diferentes (larguras, zoom e recorte distintos) ficam
   desalinhados no destaque, que e lido em sequencia.

O texto e o das mensagens, palavra por palavra — so a ortografia da Sueli foi
corrigida. Nada de balao inventado: cada bloco abaixo tem a data e a hora que
estao no print guardado com o Diego.

Uso:  python gerar_destaque_depoimentos.py
Saida: imagens/destaque-venda10x/*.jpg  (1080x1920, o que a Graph API pede)
"""
from __future__ import annotations

import os
from PIL import Image, ImageDraw, ImageFilter

from tipografia import fonte as _fonte, rotulo as _rotulo, escrever_espacado

BASE = os.path.dirname(os.path.abspath(__file__))
SAIDA = os.path.join(BASE, "imagens", "destaque-venda10x")
SELO = os.path.join("C:\\", "Users", "NOTE", "Desktop", "Perffec", "Claude",
                    "Logo-Venda10x", "selo-venda10x-1024.png")

LARG, ALT = 1080, 1920
NAVY = (13, 38, 68)
NAVY_FUNDO = (9, 26, 47)
DOURADO = (240, 168, 46)
BRANCO = (255, 255, 255)

# papel de parede e balao do WhatsApp claro
PAPEL = (236, 229, 221)
BALAO = (255, 255, 255)
TEXTO = (17, 27, 33)
HORA = (102, 119, 129)

MARGEM = 64          # borda do card de conversa
PAD = 30             # respiro dentro do balao


DEPOIMENTOS = [
    {
        "arquivo": "1-gilliard",
        "nome": "Gilliard",
        "papel": "Aluno do Venda 10x",
        "data": "05/09/2026",
        "baloes": [
            ("Diego, queria deixar registrado com você que uma das técnicas de "
             "quando o cliente diz vou pensar! Apliquei e foi certeira, cliente "
             "ligou em seguida agendando e fechamos logo no outro dia. Na mesma "
             "técnica quando pediu desconto até consigo mais desta forma… top "
             "Diego, não vejo a hora de descobrir o que vem de ensinamento pelas "
             "aulas futuras! Grande abraço", "16:42"),
        ],
    },
    {
        "arquivo": "4-gabriel",
        "nome": "Gabriel Pires",
        "papel": "Aluno do Venda 10x",
        "data": "05/09/2026",
        "baloes": [
            ("Fala, Diego! Cara, para falar a verdade, eu até acho estranho.",
             "18:13"),
            ("Eu pensei que iam ser umas aulas bem básicas.", "18:14"),
            ("Mas eu me surpreendi: as aulas estão muito boas, o pessoal que "
             "está lá também é muito bom.", "18:15"),
            ("E são assuntos na aula que eu passo todos os dias.", "18:15"),
        ],
    },
    {
        "arquivo": "2-nice",
        "nome": "Nice Laso",
        "papel": "Aluna do Venda 10x",
        "data": "30/07/2026",
        "baloes": [
            ("Participar do Venda 10X foi um divisor de águas para o meu negócio. "
             "Recomendo o Venda 10X para qualquer empresário que queira vender "
             "mais, com estratégia, consistência e acompanhamento de verdade.",
             "00:03"),
        ],
    },
    {
        "arquivo": "3-sueli",
        "nome": "Sueli Aguiar",
        "papel": "Aluna do Venda 10x",
        "data": "30/07/2026",
        "baloes": [
            ("Me ajudou a me posicionar sobre como tem que ser o trabalho e "
             "deixar bom. Clareza de como tem que ser, porque às vezes a pessoa "
             "quer um trabalho mal feito para pagar menos, então falo como tem "
             "que ser feito.", "22:25"),
            ("E com qualidade. Tanto é que sou conhecida como cara, aí eu falo "
             "que cobro o preço justo.", "22:27"),
        ],
    },
]


# --------------------------------------------------------------------------- base

def _fundo() -> Image.Image:
    """Navy da marca com um claro suave no alto — chapado puro fica morto."""
    img = Image.new("RGB", (LARG, ALT), NAVY_FUNDO)
    brilho = Image.new("L", (LARG, ALT), 0)
    ImageDraw.Draw(brilho).ellipse([-360, -720, LARG + 360, 760], fill=70)
    brilho = brilho.filter(ImageFilter.GaussianBlur(200))
    return Image.composite(Image.new("RGB", (LARG, ALT), NAVY), img, brilho)


def _selo(altura: int) -> Image.Image:
    s = Image.open(SELO).convert("RGBA")
    larg = int(s.width * altura / s.height)
    return s.resize((larg, altura), Image.LANCZOS)


def _quebrar(texto: str, fonte, largura: int) -> list:
    linhas, atual = [], ""
    for palavra in texto.split():
        teste = (atual + " " + palavra).strip()
        if fonte.getlength(teste) <= largura:
            atual = teste
        else:
            if atual:
                linhas.append(atual)
            atual = palavra
    if atual:
        linhas.append(atual)
    return linhas


def _sombra(img: Image.Image, caixa, raio: int, desfoque: int, alfa: int) -> Image.Image:
    camada = Image.new("L", img.size, 0)
    x0, y0, x1, y1 = caixa
    ImageDraw.Draw(camada).rounded_rectangle([x0, y0 + 6, x1, y1 + 10], raio, fill=alfa)
    camada = camada.filter(ImageFilter.GaussianBlur(desfoque))
    escuro = Image.new("RGB", img.size, (4, 12, 24))
    return Image.composite(escuro, img, camada)


# --------------------------------------------------------------------------- pecas

def capa(destino: str) -> str:
    """Abertura do destaque — e tambem a imagem que vira a capa redonda.

    O selo fica no CENTRO exato da tela porque o recorte da capa do destaque e
    quadrado e puxa o meio; texto perto da borda seria cortado no circulo.
    """
    img = _fundo()
    d = ImageDraw.Draw(img)

    f_top = _rotulo(38, peso=700, largura=100)
    rotulo_txt = "O QUE DIZEM OS ALUNOS"
    larg = sum(f_top.getlength(c) + 8 for c in rotulo_txt) - 8
    escrever_espacado(d, ((LARG - larg) / 2, 470), rotulo_txt, f_top, DOURADO,
                      tracking=8)

    s = _selo(660)
    img.paste(s, ((LARG - s.width) // 2, 960 - s.height // 2), s)

    d = ImageDraw.Draw(img)
    f_lin = _fonte(40, peso=500)
    d.text((LARG / 2, 1420), "Mensagens que chegaram no WhatsApp", font=f_lin,
           fill=(210, 222, 238), anchor="ma")
    f_pe = _fonte(34, peso=400)
    d.text((LARG / 2, 1500), "vendanaobra.com.br/venda-10x", font=f_pe,
           fill=(150, 170, 195), anchor="ma")

    os.makedirs(os.path.dirname(destino), exist_ok=True)
    img.save(destino, "JPEG", quality=93, subsampling=0, optimize=True)
    return destino


def depoimento(item: dict, destino: str) -> str:
    img = _fundo()

    f_texto = _fonte(38, peso=400)
    f_hora = _fonte(24, peso=400)
    f_nome = _rotulo(44, peso=700, largura=100)
    f_papel = _fonte(32, peso=400)

    card_x0, card_x1 = MARGEM, LARG - MARGEM
    larg_max = int((card_x1 - card_x0) * 0.86) - 2 * PAD

    # mede os baloes antes de desenhar: o card cresce com o conteudo e fica
    # centrado, entao a peca de 1 balao nao fica com um vazio embaixo.
    medidas = []
    for texto, hora in item["baloes"]:
        linhas = _quebrar(texto, f_texto, larg_max)
        larg_texto = max(f_texto.getlength(l) for l in linhas)
        larg_balao = int(max(larg_texto, f_hora.getlength(hora) + 40)) + 2 * PAD
        alt_balao = len(linhas) * 52 + 2 * PAD + 30   # +30 = linha da hora
        medidas.append((linhas, hora, larg_balao, alt_balao))

    alt_card = sum(m[3] for m in medidas) + 22 * (len(medidas) - 1) + 34 + 46 + 34
    # O bloco (card + assinatura) e centrado na faixa que a interface do Story
    # nao cobre: acima de 380 fica a barra de progresso, abaixo de 1700 a
    # caixa de "enviar mensagem".
    ASSINATURA = 200
    card_y0 = 380 + max(0, (1320 - alt_card - ASSINATURA) // 2)
    card_y1 = card_y0 + alt_card

    img = _sombra(img, (card_x0, card_y0, card_x1, card_y1), 34, 26, 150)
    d = ImageDraw.Draw(img)

    f_top = _rotulo(32, peso=700, largura=100)
    rot = "O QUE DIZEM OS ALUNOS"
    larg_rot = sum(f_top.getlength(c) + 7 for c in rot) - 7
    escrever_espacado(d, ((LARG - larg_rot) / 2, 268), rot, f_top, DOURADO,
                      tracking=7)

    d.rounded_rectangle([card_x0, card_y0, card_x1, card_y1], 34, fill=PAPEL)

    # etiqueta de data, como a do WhatsApp
    f_dia = _fonte(26, peso=500)
    larg_dia = f_dia.getlength(item["data"]) + 44
    d.rounded_rectangle([(LARG - larg_dia) / 2, card_y0 + 22,
                         (LARG + larg_dia) / 2, card_y0 + 70], 24,
                        fill=(225, 216, 205))
    d.text((LARG / 2, card_y0 + 46), item["data"], font=f_dia, fill=(90, 105, 115),
           anchor="mm")

    y = card_y0 + 34 + 46
    for linhas, hora, larg_balao, alt_balao in medidas:
        x0 = card_x0 + 34
        x1 = x0 + larg_balao
        d.rounded_rectangle([x0, y, x1, y + alt_balao], 22, fill=BALAO)
        # rabicho do balao recebido, no canto de cima a esquerda
        d.polygon([(x0, y), (x0 - 14, y), (x0, y + 22)], fill=BALAO)
        ty = y + PAD
        for linha in linhas:
            d.text((x0 + PAD, ty), linha, font=f_texto, fill=TEXTO, anchor="la")
            ty += 52
        d.text((x1 - PAD, y + alt_balao - PAD + 6), hora, font=f_hora, fill=HORA,
               anchor="rs")
        y += alt_balao + 22

    # assinatura fora do card: o destaque tem de dizer de quem e a voz
    d.line([(MARGEM + 8, card_y1 + 70), (MARGEM + 68, card_y1 + 70)], fill=DOURADO,
           width=4)
    d.text((MARGEM + 8, card_y1 + 100), item["nome"].upper(), font=f_nome, fill=BRANCO,
           anchor="la")
    d.text((MARGEM + 8, card_y1 + 158), item["papel"], font=f_papel,
           fill=(168, 186, 210), anchor="la")

    s = _selo(124)
    img.paste(s, (LARG - MARGEM - s.width, card_y1 + 84), s)

    d = ImageDraw.Draw(img)
    f_pe = _fonte(30, peso=400)
    d.text((LARG / 2, 1790), "vendanaobra.com.br/venda-10x", font=f_pe,
           fill=(140, 160, 188), anchor="ma")

    os.makedirs(os.path.dirname(destino), exist_ok=True)
    img.save(destino, "JPEG", quality=93, subsampling=0, optimize=True)
    return destino


def gerar_tudo() -> list:
    feitos = [capa(os.path.join(SAIDA, "0-capa.jpg"))]
    for item in DEPOIMENTOS:
        feitos.append(depoimento(item, os.path.join(SAIDA, item["arquivo"] + ".jpg")))
    return feitos


if __name__ == "__main__":
    for caminho in gerar_tudo():
        print(caminho)

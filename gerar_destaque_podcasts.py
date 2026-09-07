# -*- coding: utf-8 -*-
"""Artes do destaque "Podcasts" do @vendanaobra — as participacoes do Diego.

Levantamento de 07/09/2026: varredura dos 651 posts do perfil pela Graph API
(legenda com "podcast/episodio/convidado" e os nomes dos programas), cruzada
com a busca dentro de CADA canal no YouTube. Deu **8 episodios em 5 casas** —
tres a mais do que o site mostrava (Papo de Esquadria 2026, Na Veia EP77 e
EP80) e um que o site nao tinha (Alem do Drywall #109).

Duas correcoes que sairam dai, e valem para o site tambem:

- "Papo de Esquadria" e "Premium Cast" nao sao dois podcasts: o Premium Cast e
  um programa DENTRO do canal Papo de Esquadria. Sao dois episodios distintos
  (2025 e 2026), com dois anos de diferenca.
- "Na Veia - Nosso Setor" e uma mesa do **Maos a Obra Podcast**, nao um podcast
  proprio: a foto do post do Diego mostra o copo do Maos a Obra na mesa, e a
  marcacao do post e @maosaobrapodcast.

A arte de cada peca e a CAPA OFICIAL do episodio (thumbnail do YouTube). E o
que identifica o programa de relance — cada capa traz o logo do podcast — e o
que a pessoa vai reconhecer se procurar depois. As capas sao baixadas na hora
para `imagens/_cache_podcasts/` (fora do Git); so as pecas montadas sobem.

Uso:  python gerar_destaque_podcasts.py
Saida: imagens/destaque-podcasts/*.jpg  (1080x1920)
"""
from __future__ import annotations

import os
import urllib.request

from PIL import Image, ImageDraw, ImageFilter

from tipografia import fonte as _fonte, rotulo as _rotulo, escrever_espacado

BASE = os.path.dirname(os.path.abspath(__file__))
SAIDA = os.path.join(BASE, "imagens", "destaque-podcasts")
CACHE = os.path.join(BASE, "imagens", "_cache_podcasts")
LOGO = os.path.join("C:\\", "Users", "NOTE", "Desktop", "Perffec", "Claude",
                    "Logo-Venda10x", "logo-vendanaobra-vertical-escuro.png")

LARG, ALT = 1080, 1920
NAVY = (13, 38, 68)
NAVY_FUNDO = (9, 26, 47)
# Champagne #D8B888: a cor oficial da marca desde 26/08/2026 (o dourado vivo
# #F0A82E saiu). O destaque de depoimentos ainda usa o dourado antigo.
CHAMPAGNE = (216, 184, 136)
BRANCO = (255, 255, 255)
CINZA = (150, 170, 195)

MARGEM = 60


EPISODIOS = [
    {
        "arquivo": "1-premium-cast",
        "yt": "Zl6tsJN4lgE",
        "podcast": "Papo de Esquadria",
        "programa": "Premium Cast #9",
        "titulo": "Técnicas de vendas e upsell",
        "quando": "abril de 2025",
        "segundos": 5182,
    },
    {
        "arquivo": "2-maos-a-obra-54",
        "yt": "5284N4N7pvk",
        "podcast": "Mãos à Obra",
        "programa": "EP 54",
        "titulo": "Venda na Obra: vender na construção civil sem depender de preço",
        "quando": "maio de 2025",
        "segundos": 4577,
    },
    {
        "arquivo": "3-vidro-na-obra-72",
        "yt": "dFaMdB40BiQ",
        "podcast": "Vidro na Obra",
        "programa": "#72",
        "titulo": "Posicionamento, upsell e negociação por WhatsApp",
        "quando": "junho de 2025",
        "segundos": 4897,
    },
    {
        "arquivo": "4-alem-do-drywall-109",
        "yt": "LVWCVvkeiUw",
        "podcast": "Além do Drywall",
        "programa": "#109",
        "titulo": "Você não sabe vender seu serviço",
        "quando": "julho de 2025",
        "segundos": 6240,
    },
    {
        "arquivo": "5-na-veia-77",
        "yt": "0C3hPU31eJ0",
        "podcast": "Na Veia · Mãos à Obra",
        "programa": "EP 77",
        "titulo": "Debate sobre o setor de esquadrias, com Carlos Neylon e Ana Juraszck",
        "quando": "abril de 2026",
        "segundos": 6158,
    },
    {
        "arquivo": "6-papo-de-esquadria",
        "yt": "HLgl9ABlgJc",
        "podcast": "Papo de Esquadria",
        "programa": "2026",
        "titulo": "Marketing para esquadrias, com Ana Juraszck",
        "quando": "abril de 2026",
        "segundos": 6042,
    },
    {
        "arquivo": "7-na-veia-80",
        "yt": "GT0aa9LNy7k",
        "podcast": "Na Veia · Mãos à Obra",
        "programa": "EP 80",
        "titulo": "A mesa do setor: mão de obra, formação e o que trava o crescimento",
        "quando": "maio de 2026",
        "segundos": 7223,
    },
    {
        "arquivo": "8-aluparts-25",
        "yt": "e6clG_KFAPA",
        "podcast": "Aluparts",
        "programa": "#EP25",
        "titulo": "Construção civil e vendas: como crescer com estratégia",
        "quando": "agosto de 2026",
        "segundos": 4390,
    },
]


# --------------------------------------------------------------------------- base

def _fundo() -> Image.Image:
    img = Image.new("RGB", (LARG, ALT), NAVY_FUNDO)
    brilho = Image.new("L", (LARG, ALT), 0)
    ImageDraw.Draw(brilho).ellipse([-360, -720, LARG + 360, 760], fill=70)
    brilho = brilho.filter(ImageFilter.GaussianBlur(200))
    return Image.composite(Image.new("RGB", (LARG, ALT), NAVY), img, brilho)


def _logo(altura: int) -> Image.Image:
    s = Image.open(LOGO).convert("RGBA")
    # o arquivo vem com muita margem transparente em volta
    s = s.crop(s.getbbox())
    larg = int(s.width * altura / s.height)
    return s.resize((larg, altura), Image.LANCZOS)


def _capa(yt: str) -> Image.Image:
    """Capa oficial do episodio, com cache local (fora do Git)."""
    os.makedirs(CACHE, exist_ok=True)
    destino = os.path.join(CACHE, f"{yt}.jpg")
    if not os.path.exists(destino):
        urllib.request.urlretrieve(
            f"https://i.ytimg.com/vi/{yt}/maxresdefault.jpg", destino)
    return Image.open(destino).convert("RGB")


def _cobrir(img: Image.Image, larg: int, alt: int) -> Image.Image:
    """Preenche larg x alt sem deformar (corta a sobra)."""
    escala = max(larg / img.width, alt / img.height)
    novo = img.resize((max(1, int(img.width * escala)),
                       max(1, int(img.height * escala))), Image.LANCZOS)
    x = (novo.width - larg) // 2
    y = (novo.height - alt) // 2
    return novo.crop((x, y, x + larg, y + alt))


def _cantos(img: Image.Image, raio: int) -> Image.Image:
    mascara = Image.new("L", img.size, 0)
    ImageDraw.Draw(mascara).rounded_rectangle([0, 0, img.width - 1, img.height - 1],
                                              raio, fill=255)
    img = img.convert("RGBA")
    img.putalpha(mascara)
    return img


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


def _rotulo_topo(d, texto: str, y: int, tamanho: int = 34) -> None:
    f = _rotulo(tamanho, peso=700, largura=100)
    larg = sum(f.getlength(c) + 7 for c in texto) - 7
    escrever_espacado(d, ((LARG - larg) / 2, y), texto, f, CHAMPAGNE, tracking=7)


def _duracao(segundos: int) -> str:
    h, m = divmod(round(segundos / 60), 60)
    return f"{h}h{m:02d}" if h else f"{m} min"


# --------------------------------------------------------------------------- pecas

def capa(destino: str) -> str:
    """Abertura do destaque, e a imagem que vira a capa redonda.

    O logo fica no CENTRO exato: o recorte da capa do destaque e quadrado e
    puxa o meio da imagem.
    """
    img = _fundo()
    d = ImageDraw.Draw(img)
    _rotulo_topo(d, "PARTICIPAÇÕES EM", 430, 32)

    f_tit = _rotulo(120, peso=800, largura=100)
    d.text((LARG / 2, 490), "PODCASTS", font=f_tit, fill=BRANCO, anchor="ma")

    lg = _logo(320)
    img.paste(lg, ((LARG - lg.width) // 2, 960 - lg.height // 2), lg)

    d = ImageDraw.Draw(img)
    f = _fonte(40, peso=500)
    d.text((LARG / 2, 1330), "8 episódios · 5 podcasts do setor", font=f,
           fill=(210, 222, 238), anchor="ma")
    f2 = _fonte(34, peso=400)
    d.text((LARG / 2, 1400), "2025 · 2026", font=f2, fill=CINZA, anchor="ma")
    d.text((LARG / 2, 1500), "vendanaobra.com.br", font=f2, fill=CINZA, anchor="ma")

    os.makedirs(os.path.dirname(destino), exist_ok=True)
    img.save(destino, "JPEG", quality=93, subsampling=0, optimize=True)
    return destino


def episodio(item: dict, destino: str) -> str:
    img = _fundo()
    d = ImageDraw.Draw(img)
    _rotulo_topo(d, "PARTICIPAÇÕES EM PODCASTS", 268)

    # capa 16:9 com sombra
    larg_c = LARG - 2 * MARGEM
    alt_c = round(larg_c * 9 / 16)
    x0, y0 = MARGEM, 470
    sombra = Image.new("L", img.size, 0)
    ImageDraw.Draw(sombra).rounded_rectangle([x0, y0 + 10, x0 + larg_c, y0 + alt_c + 16],
                                             28, fill=150)
    img = Image.composite(Image.new("RGB", img.size, (4, 12, 24)), img,
                          sombra.filter(ImageFilter.GaussianBlur(24)))
    arte = _cantos(_cobrir(_capa(item["yt"]), larg_c, alt_c), 28)
    img.paste(arte, (x0, y0), arte)

    d = ImageDraw.Draw(img)
    y = y0 + alt_c + 90

    # nome do podcast + etiqueta do episodio, na mesma linha de leitura
    f_pod = _rotulo(52, peso=700, largura=100)
    d.text((MARGEM, y), item["podcast"].upper(), font=f_pod, fill=CHAMPAGNE,
           anchor="la")
    y += 78

    f_ep = _fonte(32, peso=600)
    etiqueta = item["programa"]
    larg_et = f_ep.getlength(etiqueta) + 36
    d.rounded_rectangle([MARGEM, y, MARGEM + larg_et, y + 52], 26,
                        outline=CHAMPAGNE, width=2)
    d.text((MARGEM + larg_et / 2, y + 26), etiqueta, font=f_ep, fill=CHAMPAGNE,
           anchor="mm")
    y += 92

    f_tit = _fonte(44, peso=500)
    for linha in _quebrar(item["titulo"], f_tit, LARG - 2 * MARGEM):
        d.text((MARGEM, y), linha, font=f_tit, fill=BRANCO, anchor="la")
        y += 58

    y += 18
    f_meta = _fonte(32, peso=400)
    d.text((MARGEM, y), f'{item["quando"]} · {_duracao(item["segundos"])} de conversa',
           font=f_meta, fill=CINZA, anchor="la")

    # Rodape acima de 1700: a caixa de "enviar mensagem" do Story cobre o pe
    # da tela, e no destaque ela existe do mesmo jeito.
    f_pe = _fonte(30, peso=400)
    d.text((LARG / 2, 1630), "episódio completo no YouTube", font=f_pe,
           fill=(140, 160, 188), anchor="ma")

    lg = _logo(70)
    img.paste(lg, (LARG - MARGEM - lg.width, 1500), lg)

    os.makedirs(os.path.dirname(destino), exist_ok=True)
    img.save(destino, "JPEG", quality=93, subsampling=0, optimize=True)
    return destino


def fecho(destino: str) -> str:
    """Convite final — FORA do destaque desde 07/09/2026.

    Foi publicado junto com o resto e o Diego apagou o Story ("pode deixar sem
    esse no destaque"). A funcao fica porque a peca esta pronta se ele mudar de
    ideia; ela nao entra em `gerar_tudo` nem na fila do publicador.
    """
    img = _fundo()
    d = ImageDraw.Draw(img)
    _rotulo_topo(d, "PARTICIPAÇÕES EM PODCASTS", 268)

    f_tit = _rotulo(64, peso=800, largura=100)
    for i, linha in enumerate(["QUER O DIEGO", "NO SEU PODCAST?"]):
        d.text((LARG / 2, 700 + i * 86), linha, font=f_tit, fill=BRANCO, anchor="ma")

    f = _fonte(40, peso=400)
    texto = ("Vendas na construção civil, sem depender de preço: método, "
             "posicionamento e negociação.")
    y = 940
    for linha in _quebrar(texto, f, LARG - 2 * MARGEM - 60):
        d.text((LARG / 2, y), linha, font=f, fill=(210, 222, 238), anchor="ma")
        y += 56

    d.line([(LARG / 2 - 40, y + 40), (LARG / 2 + 40, y + 40)], fill=CHAMPAGNE, width=4)

    f2 = _fonte(38, peso=600)
    d.text((LARG / 2, y + 90), "vendanaobra.com.br", font=f2, fill=CHAMPAGNE,
           anchor="ma")

    lg = _logo(260)
    img.paste(lg, ((LARG - lg.width) // 2, 1380), lg)

    os.makedirs(os.path.dirname(destino), exist_ok=True)
    img.save(destino, "JPEG", quality=93, subsampling=0, optimize=True)
    return destino


def gerar_tudo() -> list:
    feitos = [capa(os.path.join(SAIDA, "0-capa.jpg"))]
    for item in EPISODIOS:
        feitos.append(episodio(item, os.path.join(SAIDA, item["arquivo"] + ".jpg")))
    return feitos


if __name__ == "__main__":
    for caminho in gerar_tudo():
        print(caminho)

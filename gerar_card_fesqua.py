# -*- coding: utf-8 -*-
"""Card de contagem regressiva da Fesqua 2026 — 1080x1350 (4:5), feed do @vendanaobra.

Nasceu em 05/09/2026: o Diego mandou o card que a PROPRIA feira publica com os
embaixadores dela (Ricardo Camara) e pediu o mesmo com ele, marcando a @fesqua
como colaboradora. Na segunda volta ele foi explicito: **copiar o layout da peca
original**, trocando so a foto, o numero de dias e o assunto — que no caso dele
e' VENDA, nao tecnologia.

Por isso este arquivo persegue a peca da feira elemento por elemento: fundo de
pavilhao tingido de vermelho, moldura branca fina, "Faltam N dias" com o numero
numa caixa branca, logo a direita, chamada em tres linhas com uma delas em caixa
cheia, paragrafo curto, pessoa recortada a esquerda, cracha com nome e funcao, e
o rodape com data e endereco, cada um com o seu icone.

Tres coisas que NAO se copiam:

- **A credencial.** O card do Ricardo diz "Embaixador". O Diego nao e' embaixador
  — a pagina oficial tem 13 e ele nao esta la. E, no ajuste que ele mesmo pediu
  as 12h55 de 05/09/2026 (FESQUA-2026-registro-envios.md, na pasta da Perffec),
  a credencial se escreve "influenciador da Fesqua 2026", sem "oficial".
- **A promessa.** A peca da feira vende a feira ("descubra novas tecnologias").
  A dele vende o que so ele entrega: a leitura comercial do que estiver la.
- **O numero.** E' calculado da data de PUBLICACAO ate 09/09/2026, nunca escrito
  a mao — contagem regressiva com numero errado e' o erro que o feed inteiro ve.

Armadilhas ja pagas na montagem, cada uma custou um render:

- O numero NAO pode cair sobre o rosto: na peca original ele fica ACIMA da
  cabeca, e a pessoa comeca abaixo do bloco da contagem. Foi a primeira correcao
  que o Diego pediu.
- Vermelho chapado sai "vermelho demais": a peca original tem FOTO de pavilhao
  por tras do vermelho, e e' ela que da profundidade ao card.
- O halo atras da silhueta precisa de folga no canvas antes do desfoque, senao o
  desfoque bate na borda do bitmap e vira um RETANGULO claro no card.
- O recorte e' plano MEDIO: sem dissolver os ultimos pixels, o corpo aparece
  cortado por uma linha reta no meio da arte.

Uso:
    python gerar_card_fesqua.py                 # card para amanha (padrao)
    python gerar_card_fesqua.py --data 2026-09-06
    python gerar_card_fesqua.py --dias 3        # forca o numero (conferencia)
"""
from __future__ import annotations

import argparse
import os
from datetime import date, datetime, timedelta

from PIL import Image, ImageChops, ImageDraw, ImageEnhance, ImageFilter

from tipografia import rotulo as _archivo
from tipografia import escrever_espacado as _espacado

BASE = os.path.dirname(os.path.abspath(__file__))
ATIVOS = os.path.join(BASE, "midia", "fesqua")
SAIDA = os.path.join(BASE, "imagens")

LARG, ALT = 1080, 1350
ABERTURA = date(2026, 9, 9)          # primeiro dia da Fesqua 2026

# a paleta sai da propria peca da feira: vermelho, branco, nada mais
VERMELHO = (150, 12, 18)
VERMELHO_CLARO = (196, 22, 28)
BRANCO = (255, 255, 255)
ROSA = (255, 222, 222)

# a chamada: mesma forma da peca original (verbo + duas linhas), assunto trocado
TITULO = ["DESCUBRA", "O QUE", "VENDE MAIS"]
DESTAQUE = 2                          # a linha em caixa cheia, como "TECNOLOGIAS"
CORPO = ("Vou estar os 4 dias na feira olhando lançamento por lançamento "
         "com uma pergunta só: isso vira venda no seu balcão?")
NOME = "Diego Moraes"
CARGO = "Influenciador da Fesqua 2026"
ARROBA = "@vendanaobra"
DATAS = ["09 A 12", "DE SETEMBRO", "DE 2026"]
LOCAL = ["SÃO PAULO EXPO", "Rodovia dos Imigrantes, 1,5 km",
         "Vila Água Funda, São Paulo - SP", "CEP 04329-900"]


def dias_para_a_feira(quando: date) -> int:
    return (ABERTURA - quando).days


def _fundo() -> Image.Image:
    """Pavilhao de feira tingido de vermelho — o fundo da peca original.

    A foto e' de dominio publico (CC0, Wikimedia Commons) e entra so como
    TEXTURA: desfocada, dessaturada e coberta por uma rampa vermelha que fecha
    quase opaca embaixo, onde vao o cracha e o rodape. O que sobra visivel e' o
    teto e o vulto das pessoas no alto — que e' o que a peca da feira mostra.
    """
    foto = Image.open(os.path.join(ATIVOS, "fundo-feira.jpg")).convert("RGB")
    if foto.size != (LARG, ALT):
        foto = foto.resize((LARG, ALT), Image.LANCZOS)
    foto = foto.filter(ImageFilter.GaussianBlur(7))
    foto = ImageEnhance.Color(foto).enhance(0.22)
    foto = ImageEnhance.Brightness(foto).enhance(0.68)
    foto = ImageChops.multiply(foto, Image.new("RGB", foto.size, (236, 44, 46)))

    rampa = Image.linear_gradient("L").resize(foto.size)
    rampa = rampa.point(lambda v: int(52 + v * 0.78))      # 20% no topo, 92% na base
    return Image.composite(Image.new("RGB", foto.size, VERMELHO), foto, rampa)


def _desvanecer_base(recorte: Image.Image, altura: int) -> Image.Image:
    """Dissolve os ultimos pixels do recorte no fundo.

    A foto e' um plano MEDIO: termina na cintura, e sem isto o corpo aparece
    cortado por uma linha reta no meio do card — o olho le como erro de
    montagem, nao como enquadramento.
    """
    rampa = Image.linear_gradient("L").resize((recorte.width, altura))
    rampa = rampa.transpose(Image.FLIP_TOP_BOTTOM)          # 255 em cima, 0 embaixo
    campo = Image.new("L", recorte.size, 255)
    campo.paste(rampa, (0, recorte.height - altura))
    saida = recorte.copy()
    saida.putalpha(ImageChops.multiply(recorte.split()[3], campo))
    return saida


def _halo(recorte: Image.Image) -> Image.Image:
    """Brilho claro atras da pessoa.

    O Diego esta de paleto PRETO sobre fundo vermelho escuro: sem separar os
    dois, o ombro dele some e sobra uma cabeca flutuando. A folga de 90 px existe
    porque o recorte vem cortado no bbox — sem ela o desfoque bate na borda do
    bitmap e o halo vira um RETANGULO claro no card.
    """
    folga = 90
    campo = Image.new("L", (recorte.width + 2 * folga, recorte.height + 2 * folga), 0)
    campo.paste(recorte.split()[3], (folga, folga))
    alfa = campo.filter(ImageFilter.GaussianBlur(38))
    halo = Image.new("RGBA", campo.size, (255, 96, 84, 0))
    halo.putalpha(alfa.point(lambda v: int(min(255, v * 1.9) * 0.42)))
    return halo


def _escrever(d, xy, texto, fonte, fill, anchor="la", sombra=False) -> None:
    """Escreve com sombra opcional.

    O fundo agora e' FOTO: texto branco sem sombra perde a borda assim que o
    Instagram comprime a imagem.
    """
    if sombra:
        d.text((xy[0] + 3, xy[1] + 3), texto, font=fonte, fill=(58, 0, 4), anchor=anchor)
    d.text(xy, texto, font=fonte, fill=fill, anchor=anchor)


def _caber(texto: str, largura: int, tamanho: int, peso: int, largura_fonte: int):
    """Reduz a letra ate a linha caber na coluna.

    A chamada e' escrita a mao neste arquivo e a coluna da direita tem 460 px:
    trocar uma palavra por uma maior cortava a ultima letra no meio, e o card ia
    para o feed assim sem ninguem ver.
    """
    f = _archivo(tamanho, peso=peso, largura=largura_fonte)
    while f.getlength(texto) > largura and tamanho > 26:
        tamanho -= 2
        f = _archivo(tamanho, peso=peso, largura=largura_fonte)
    return f


def _quebrar(texto: str, fonte, largura: int) -> list[str]:
    linhas, atual = [], ""
    for palavra in texto.split():
        teste = f"{atual} {palavra}".strip()
        if fonte.getlength(teste) <= largura or not atual:
            atual = teste
        else:
            linhas.append(atual)
            atual = palavra
    if atual:
        linhas.append(atual)
    return linhas


def _icone_calendario(d, xy) -> None:
    x, y = xy
    d.rounded_rectangle([x, y + 8, x + 46, y + 52], radius=6, outline=BRANCO, width=4)
    d.line([x + 12, y, x + 12, y + 14], fill=BRANCO, width=5)
    d.line([x + 34, y, x + 34, y + 14], fill=BRANCO, width=5)
    d.line([x + 2, y + 24, x + 44, y + 24], fill=BRANCO, width=4)


def _icone_pin(d, xy) -> None:
    x, y = xy
    d.ellipse([x + 6, y, x + 42, y + 36], outline=BRANCO, width=4)
    d.polygon([(x + 14, y + 28), (x + 34, y + 28), (x + 24, y + 54)], fill=BRANCO)
    d.ellipse([x + 18, y + 12, x + 30, y + 24], fill=BRANCO)


def montar(quando: date, dias: int, destino: str) -> str:
    tela = _fundo().convert("RGBA")

    # ---- pessoa: a esquerda, comecando ABAIXO do bloco da contagem
    pessoa = Image.open(os.path.join(ATIVOS, "diego-recorte.png")).convert("RGBA")
    alvo_alt = 830
    pessoa = pessoa.resize((int(pessoa.width * alvo_alt / pessoa.height), alvo_alt),
                           Image.LANCZOS)
    pessoa = _desvanecer_base(pessoa, 130)
    px, py = -34, 1170 - alvo_alt
    halo = _halo(pessoa)
    tela.alpha_composite(halo, (px - (halo.width - pessoa.width) // 2,
                                py - (halo.height - pessoa.height) // 2))
    tela.alpha_composite(pessoa, (px, py))

    d = ImageDraw.Draw(tela)
    d.rectangle([26, 26, LARG - 27, ALT - 27], outline=(255, 255, 255, 150), width=3)

    # ---- contagem regressiva, no alto a esquerda e ACIMA da cabeca
    x, y = 88, 74
    _escrever(d, (x, y), "FALTAM", _archivo(64, peso=800, largura=88), BRANCO,
              sombra=True)

    f_num = _archivo(170, peso=900, largura=80)
    cx0, cy0 = x, y + 80
    cw = max(int(f_num.getlength(str(dias))) + 62, 142)
    ch = 176
    d.rounded_rectangle([cx0, cy0, cx0 + cw, cy0 + ch], radius=14, fill=BRANCO)
    _escrever(d, (cx0 + cw / 2, cy0 + ch / 2 + 4), str(dias), f_num,
              VERMELHO_CLARO, anchor="mm")
    _escrever(d, (cx0 + cw + 22, cy0 + ch / 2 + 2), "dias" if dias != 1 else "dia",
              _archivo(74, peso=800, largura=88), BRANCO, anchor="lm", sombra=True)

    # ---- logo da feira, no alto a direita
    logo = Image.open(os.path.join(ATIVOS, "fesqua-logo-branco.png")).convert("RGBA")
    lw = 342
    logo = logo.resize((lw, int(logo.height * lw / logo.width)), Image.LANCZOS)
    tela.alpha_composite(logo, (LARG - 88 - lw, 100))

    # ---- chamada e paragrafo, na coluna da direita
    xt = 528
    util = LARG - xt - 84
    y = 336
    for i, linha in enumerate(TITULO):
        peso, largura, tam = (900, 78, 76) if i == DESTAQUE else (600, 84, 68)
        f = _caber(linha, util, tam, peso, largura)
        _escrever(d, (xt, y), linha, f, BRANCO, sombra=True)
        y += int(f.size * 1.14)

    y += 26
    f_corpo = _archivo(30, peso=400, largura=100)
    for linha in _quebrar(CORPO, f_corpo, util):
        _escrever(d, (xt, y), linha, f_corpo, ROSA, sombra=True)
        y += 43

    # ---- cracha: nome e funcao (nem "embaixador" nem "oficial" — ver o docstring)
    yn = 1000
    _escrever(d, (88, yn), NOME, _archivo(50, peso=800, largura=92), BRANCO, sombra=True)
    _espacado(d, (90, yn + 64), CARGO.upper(),
              _archivo(24, peso=600, largura=95), ROSA, tracking=2.2)
    _espacado(d, (90, yn + 100), ARROBA,
              _archivo(24, peso=500, largura=95), (255, 170, 170), tracking=1.4)

    # ---- rodape: data e local, cada um com o seu icone
    yr = ALT - 176
    _icone_calendario(d, (88, yr + 4))
    f_datap = _archivo(24, peso=500, largura=95)
    _escrever(d, (158, yr), DATAS[0], _archivo(40, peso=900, largura=86), BRANCO)
    _escrever(d, (158, yr + 50), DATAS[1], f_datap, ROSA)
    _escrever(d, (158, yr + 80), DATAS[2], f_datap, ROSA)

    xl = 528
    _icone_pin(d, (xl, yr + 4))
    _escrever(d, (xl + 62, yr), LOCAL[0], _archivo(37, peso=900, largura=86), BRANCO)
    yy = yr + 50
    for linha in LOCAL[1:]:
        _escrever(d, (xl + 62, yy), linha, _archivo(22, peso=500, largura=95), ROSA)
        yy += 31

    os.makedirs(os.path.dirname(destino), exist_ok=True)
    tela.convert("RGB").save(destino, "JPEG", quality=94, subsampling=0, optimize=True)
    return destino


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--data", help="dia da publicação (AAAA-MM-DD); padrão: amanhã")
    p.add_argument("--dias", type=int, help="força o número da contagem")
    p.add_argument("--saida", help="caminho do arquivo final")
    a = p.parse_args()

    quando = (datetime.strptime(a.data, "%Y-%m-%d").date() if a.data
              else date.today() + timedelta(days=1))
    dias = a.dias if a.dias is not None else dias_para_a_feira(quando)
    if dias < 0:
        raise SystemExit(f"{quando} é depois da abertura ({ABERTURA}) — nada a contar")

    destino = a.saida or os.path.join(SAIDA, f"{quando:%Y-%m-%d}",
                                      f"{quando:%Y-%m-%d}-fesqua-faltam-{dias}.jpg")
    print(f"{quando:%d/%m/%Y} — faltam {dias} dias -> {montar(quando, dias, destino)}")


if __name__ == "__main__":
    main()

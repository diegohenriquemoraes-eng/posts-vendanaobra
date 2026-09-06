# -*- coding: utf-8 -*-
"""Card de contagem regressiva da Fesqua 2026 — 1080x1350 (4:5), feed do @vendanaobra.

Nasceu em 05/09/2026: o Diego mandou o card de contagem regressiva que a propria
Fesqua publica com os EMBAIXADORES dela (foto recortada sobre vermelho, "Faltam
N dias", logo, data e endereco) e pediu o mesmo com ele, marcando a @fesqua como
colaboradora.

Duas coisas que NAO se copiam da peca de referencia:

- **A credencial.** O card do Ricardo Camara diz "Embaixador". O Diego nao e
  embaixador: a pagina oficial tem 13 embaixadores e ele nao esta la. E, no
  ajuste que ele mesmo pediu as 12h55 de 05/09/2026 (registrado em
  FESQUA-2026-registro-envios.md), a credencial se escreve **"influenciador da
  Fesqua 2026"** — sem a palavra "oficial". O card segue esse texto: dar-se um
  cargo maior do que o que se tem, na semana em que ele fala com as marcas
  expositoras usando exatamente essa credencial, e o tipo de erro que volta.
- **A promessa.** A peca da feira vende a feira ("descubra novas tecnologias").
  A dele vende o que so ele entrega: a leitura comercial do que estiver la.

O numero da contagem e calculado da data de PUBLICACAO ate 09/09/2026, nao
escrito a mao — card de contagem regressiva com numero errado e o unico erro que
o feed inteiro percebe.

Uso:
    python gerar_card_fesqua.py                 # card para amanha (padrao)
    python gerar_card_fesqua.py --data 2026-09-06
    python gerar_card_fesqua.py --dias 3        # forca o numero (conferencia)
"""
from __future__ import annotations

import argparse
import os
from datetime import date, datetime, timedelta

from PIL import Image, ImageChops, ImageDraw, ImageFilter

from tipografia import rotulo as _archivo
from tipografia import escrever_espacado as _espacado

BASE = os.path.dirname(os.path.abspath(__file__))
ATIVOS = os.path.join(BASE, "midia", "fesqua")
SAIDA = os.path.join(BASE, "imagens")

LARG, ALT = 1080, 1350
ABERTURA = date(2026, 9, 9)          # primeiro dia da Fesqua 2026

# a paleta sai da propria peca da feira: vermelho profundo, branco, nada mais
VERMELHO_CLARO = (196, 22, 28)
VERMELHO_ESCURO = (86, 6, 12)
BRANCO = (255, 255, 255)

TITULO = ["VAMOS", "NOS VER", "NA FESQUA"]
DESTAQUE = 1                          # a linha que vai em caixa cheia
LINHA_FINA = 0                        # a linha que vai em peso leve
CORPO = ("Estarei os 4 dias na feira, olhando lançamento por lançamento com "
         "uma pergunta só: isso vira venda no seu balcão?")
NOME = "Diego Moraes"
CARGO = "Influenciador da Fesqua 2026"
ARROBA = "@vendanaobra"
DATAS = ["09 A 12", "DE SETEMBRO", "DE 2026"]
LOCAL = ["SÃO PAULO EXPO", "Rodovia dos Imigrantes, 1,5 km",
         "Vila Água Funda, São Paulo - SP", "CEP 04329-900"]


def dias_para_a_feira(quando: date) -> int:
    return (ABERTURA - quando).days


def _fundo() -> Image.Image:
    """Vermelho da feira: claro no alto a direita, fechando escuro nas bordas."""
    peq = 68
    base = Image.new("RGB", (peq, int(peq * ALT / LARG)), VERMELHO_ESCURO)
    px = base.load()
    lp, ap = base.size
    focox, focoy = lp * 0.62, ap * 0.30
    raio = (lp ** 2 + ap ** 2) ** 0.5 * 0.72
    for y in range(ap):
        for x in range(lp):
            d = min(1.0, (((x - focox) ** 2 + (y - focoy) ** 2) ** 0.5) / raio)
            t = 1.0 - d * d                      # cai devagar no centro
            px[x, y] = tuple(int(e + (c - e) * t)
                             for c, e in zip(VERMELHO_CLARO, VERMELHO_ESCURO))
    return base.resize((LARG, ALT), Image.LANCZOS).filter(ImageFilter.GaussianBlur(6))


def _desvanecer_base(recorte: Image.Image, altura: int) -> Image.Image:
    """Dissolve os ultimos pixels do recorte no fundo.

    A foto e' um plano MEDIO: termina na cintura, e sem isto o corpo aparece
    cortado por uma linha reta no meio do card — o olho le como erro de montagem,
    nao como enquadramento.
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

    O Diego esta de paleto PRETO e o fundo e' vermelho escuro: sem separar os
    dois, o ombro dele desaparece no card e sobra uma cabeca flutuando. Sombra
    escura (o reflexo automatico) piorava; o que resolve e' o contrario — um
    halo vermelho claro logo atras da silhueta.
    """
    # A folga de 90 px existe porque o recorte vem cortado no bbox: sem ela o
    # desfoque bate na borda do bitmap e o halo vira um RETANGULO claro no card.
    folga = 90
    campo = Image.new("L", (recorte.width + 2 * folga, recorte.height + 2 * folga), 0)
    campo.paste(recorte.split()[3], (folga, folga))
    alfa = campo.filter(ImageFilter.GaussianBlur(38))
    halo = Image.new("RGBA", campo.size, (255, 96, 84, 0))
    halo.putalpha(alfa.point(lambda v: int(min(255, v * 1.9) * 0.42)))
    return halo


def _texto_medido(d, xy, texto, fonte, fill, anchor="la"):
    d.text(xy, texto, font=fonte, fill=fill, anchor=anchor)


def montar(quando: date, dias: int, destino: str) -> str:
    tela = _fundo().convert("RGBA")

    # ---- pessoa: ancorada na base, a esquerda, como na peca da feira
    pessoa = Image.open(os.path.join(ATIVOS, "diego-recorte.png")).convert("RGBA")
    alvo_alt = 890
    escala = alvo_alt / pessoa.height
    pessoa = pessoa.resize((int(pessoa.width * escala), alvo_alt), Image.LANCZOS)
    pessoa = _desvanecer_base(pessoa, 150)
    base_pessoa = 1160                      # onde o paleto se dissolve no vermelho
    px, py = -26, base_pessoa - alvo_alt
    halo = _halo(pessoa)
    tela.alpha_composite(halo, (px - (halo.width - pessoa.width) // 2,
                                py - (halo.height - pessoa.height) // 2))
    tela.alpha_composite(pessoa, (px, py))

    d = ImageDraw.Draw(tela)

    # ---- moldura fina, a assinatura visual do card da feira
    d.rectangle([26, 26, LARG - 27, ALT - 27], outline=(255, 255, 255, 150), width=3)

    # ---- contagem regressiva, na frente da pessoa (como o "5" da peca original)
    x, y = 92, 92
    _texto_medido(d, (x, y), "FALTAM", _archivo(72, peso=800, largura=88), BRANCO)

    f_num = _archivo(196, peso=900, largura=80)
    cx0, cy0 = x, y + 88
    cw = max(int(f_num.getlength(str(dias))) + 70, 158)
    ch = 200
    d.rounded_rectangle([cx0, cy0, cx0 + cw, cy0 + ch], radius=16, fill=BRANCO)
    _texto_medido(d, (cx0 + cw / 2, cy0 + ch / 2 + 4), str(dias), f_num,
                  VERMELHO_CLARO, anchor="mm")
    _texto_medido(d, (cx0 + cw + 24, cy0 + ch / 2 + 2),
                  "dias" if dias != 1 else "dia",
                  _archivo(84, peso=800, largura=88), BRANCO, anchor="lm")

    # ---- logo da feira, no alto a direita
    logo = Image.open(os.path.join(ATIVOS, "fesqua-logo-branco.png")).convert("RGBA")
    lw = 356
    logo = logo.resize((lw, int(logo.height * lw / logo.width)), Image.LANCZOS)
    tela.alpha_composite(logo, (LARG - 92 - lw, 112))

    # ---- coluna da direita: titulo, corpo e assinatura
    xt = 540
    util = LARG - xt - 88
    y = 392
    for i, linha in enumerate(TITULO):
        peso, largura, tam = (900, 78, 78) if i == DESTAQUE else (
            (400, 84, 70) if i == LINHA_FINA else (800, 80, 70))
        f = _caber(linha, util, tam, peso, largura)
        _texto_medido(d, (xt, y), linha, f, BRANCO)
        y += int(f.size * 1.12)

    y += 26
    f_corpo = _archivo(30, peso=400, largura=100)
    for linha in _quebrar(CORPO, f_corpo, util):
        _texto_medido(d, (xt, y), linha, f_corpo, (255, 224, 224))
        y += 43

    # ---- crachá: nome e credencial (nem "embaixador" nem "oficial" — ver o docstring)
    y += 34
    d.line([xt, y, xt + 96, y], fill=BRANCO, width=4)
    y += 26
    _texto_medido(d, (xt, y), NOME, _archivo(46, peso=800, largura=92), BRANCO)
    _espacado(d, (xt + 2, y + 58), CARGO.upper(),
              _archivo(23, peso=600, largura=95), (255, 202, 202), tracking=2.0)
    _espacado(d, (xt + 2, y + 92), ARROBA,
              _archivo(23, peso=500, largura=95), (255, 172, 172), tracking=1.4)

    # ---- rodape: data e local, cada um com o seu icone
    yr = ALT - 176
    _icone_calendario(d, (92, yr + 4))
    f_datap = _archivo(24, peso=500, largura=95)
    _texto_medido(d, (162, yr), DATAS[0], _archivo(40, peso=900, largura=86), BRANCO)
    _texto_medido(d, (162, yr + 50), DATAS[1], f_datap, (255, 224, 224))
    _texto_medido(d, (162, yr + 80), DATAS[2], f_datap, (255, 224, 224))

    xl = 540
    _icone_pin(d, (xl, yr + 4))
    _texto_medido(d, (xl + 62, yr), LOCAL[0], _archivo(37, peso=900, largura=86), BRANCO)
    yy = yr + 50
    for linha in LOCAL[1:]:
        _texto_medido(d, (xl + 62, yy), linha, _archivo(22, peso=500, largura=95),
                      (255, 224, 224))
        yy += 31

    os.makedirs(os.path.dirname(destino), exist_ok=True)
    tela.convert("RGB").save(destino, "JPEG", quality=94, subsampling=0, optimize=True)
    return destino


def _caber(texto: str, largura: int, tamanho: int, peso: int, largura_fonte: int):
    """Reduz a letra ate a linha caber na coluna.

    O titulo e' escrito a mao neste arquivo e a coluna da direita tem 452 px:
    trocar uma palavra por uma maior cortava a ultima letra no meio, e o card
    saia assim para o feed sem ninguem ver.
    """
    f = _archivo(tamanho, peso=peso, largura=largura_fonte)
    while f.getlength(texto) > largura and tamanho > 28:
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

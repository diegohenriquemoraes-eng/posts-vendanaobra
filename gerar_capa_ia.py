# -*- coding: utf-8 -*-
"""Capa de IA para 1 em cada 3 Reels do EP25 — 1080x1920.

Mesma diagramacao da capa do podcast (degrade smoothstep, etiqueta dourada,
gancho em Playfair, @vendanaobra no topo), mas com foto gerada no Gemini em vez
do frame do episodio, e **sem a etiqueta "ALUPARTS PODCAST"**: a ideia e' que a
pessoa so descubra que e' corte de podcast depois de clicar. O credito da
Aluparts continua no colab do post e na legenda — o que muda e' so a capa.

Uso:
    python gerar_capa_ia.py 09 --foto capas-ia/09-bruta.jpg --etiqueta "RELACIONAMENTO COM ARQUITETO"
    python gerar_capa_ia.py 09 ... --previa    # nao grava em midia/reels
"""
from __future__ import annotations

import argparse, json, os
from PIL import Image, ImageDraw

from tipografia import rotulo as _fonte
from tipografia import titulo as _titulo
from tipografia import escrever_espacado as _espacado

BASE = os.path.dirname(os.path.abspath(__file__))
LARG, ALT = 1080, 1920
MARGEM = 96
UTIL = LARG - 2 * MARGEM
DOURADO = (240, 168, 46)
BRANCO = (255, 255, 255)
FUNDO = (6, 10, 16)
Y_BASE = 1500

def _quebrar(texto, fonte, largura):
    palavras, linhas, atual = texto.split(), [], ""
    for p in palavras:
        teste = (atual + " " + p).strip()
        if fonte.getlength(teste) <= largura or not atual:
            atual = teste
        else:
            linhas.append(atual); atual = p
    if atual: linhas.append(atual)
    return linhas

def _ajustar(texto, largura, alt_max, maior, menor):
    for tam in range(maior, menor - 1, -2):
        f = _titulo(tam)
        ls = _quebrar(texto, f, largura)
        if len(ls) * tam * 1.16 <= alt_max:
            return f
    return _titulo(menor)

def _encaixar(caminho):
    """Foto qualquer -> 1080x1920 sem deformar, cortando o excedente pelo centro."""
    im = Image.open(caminho).convert("RGB")
    escala = max(LARG / im.width, ALT / im.height)
    im = im.resize((round(im.width * escala), round(im.height * escala)), Image.LANCZOS)
    esq = (im.width - LARG) // 2
    topo = (im.height - ALT) // 2
    return im.crop((esq, topo, esq + LARG, topo + ALT))

def gerar(titulo, foto, etiqueta, destino):
    img = _encaixar(foto)
    img = Image.blend(img, Image.new("RGB", (LARG, ALT), (0, 0, 0)), 0.18)

    grad = Image.new("L", (1, ALT))
    ini, fim = 0.42, 0.80
    for y in range(ALT):
        p = y / ALT
        if p <= ini:
            v = 0
        else:
            t = min(1.0, (p - ini) / (fim - ini))
            v = int(255 * (t * t * (3 - 2 * t)))
        grad.putpixel((0, y), v)
    img = Image.composite(Image.new("RGB", (LARG, ALT), FUNDO), img, grad.resize((LARG, ALT)))

    d = ImageDraw.Draw(img)
    ft = _ajustar(titulo, UTIL, 520, 112, 66)
    linhas = _quebrar(titulo, ft, UTIL)
    y_titulo = Y_BASE - len(linhas) * ft.size * 1.16

    fe = _fonte(30, peso=700)
    _espacado(d, (MARGEM, y_titulo - 62), etiqueta, fe, DOURADO, tracking=fe.size * 0.10)
    y = y_titulo
    for ln in linhas:
        d.text((MARGEM, y), ln, font=ft, fill=BRANCO, anchor="la")
        y += ft.size * 1.16

    d.text((MARGEM, 300), "@vendanaobra", font=_fonte(32, peso=600), fill=BRANCO, anchor="la")
    os.makedirs(os.path.dirname(destino) or ".", exist_ok=True)
    img.save(destino, "JPEG", quality=92, optimize=True)
    return destino

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("id")
    ap.add_argument("--foto", required=True)
    ap.add_argument("--etiqueta", required=True)
    ap.add_argument("--previa", action="store_true")
    a = ap.parse_args()
    capas = json.load(open(os.path.join(BASE, "capas_ep25.json"), encoding="utf-8"))
    dados = capas[a.id]
    destino = (os.path.join(BASE, "capas-ia", f"{a.id}-capa.jpg") if a.previa
               else os.path.join(BASE, "midia", "reels", f"{a.id}-{dados['slug']}.jpg"))
    print(gerar(dados["titulo"], a.foto, a.etiqueta, destino))

if __name__ == "__main__":
    main()

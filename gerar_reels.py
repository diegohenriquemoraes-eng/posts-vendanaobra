# -*- coding: utf-8 -*-
"""Reels tipografico (formato F3): video 9:16 sem rosto, so texto animado.

Existe porque Reels e o unico formato do Instagram que entrega para quem NAO
segue o perfil — carrossel e story falam com quem ja esta la. Renderiza no
GitHub Actions como os outros formatos: custo zero, sem gravacao.

Tecnica: em vez de 24 quadros por segundo (330+ imagens numa maquina de 4GB),
gera so os estados VISUAIS do texto e monta com ffmpeg concat, cada estado com
sua duracao. Um Reels de 15s vira ~30 imagens.

Uso:  python gerar_reels.py --id 2
      python gerar_reels.py --texto "gancho|virada" --palavra LIVRO
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess

from PIL import Image, ImageDraw, ImageFont, ImageFilter

BASE = os.path.dirname(os.path.abspath(__file__))
FONTE = os.path.join(BASE, "fontes", "Inter-Regular.ttf")
SAIDA = os.path.join(BASE, "saida_reels")

LARG, ALT = 1080, 1920
NAVY = (13, 38, 68)
NAVY_FUNDO = (8, 26, 48)
DOURADO = (240, 168, 46)
BRANCO = (255, 255, 255)
PRATA = (199, 207, 222)

FPS = 24
MARGEM_X = 110


def _f(tamanho: int, peso: int = 400) -> ImageFont.FreeTypeFont:
    f = ImageFont.truetype(FONTE, tamanho)
    try:
        f.set_variation_by_axes([14, peso])
    except Exception:
        pass
    return f


def _fundo() -> Image.Image:
    """Navy com vinheta — o degrade evita o 'fundo chapado' que lê como amador."""
    img = Image.new("RGB", (LARG, ALT), NAVY_FUNDO)
    brilho = Image.new("L", (LARG, ALT), 0)
    d = ImageDraw.Draw(brilho)
    d.ellipse([-260, 240, LARG + 260, ALT - 240], fill=90)
    brilho = brilho.filter(ImageFilter.GaussianBlur(220))
    return Image.composite(Image.new("RGB", (LARG, ALT), NAVY), img, brilho)


def _quebrar(texto: str, fonte: ImageFont.FreeTypeFont, largura: int) -> list[str]:
    linhas, atual = [], ""
    for palavra in texto.split():
        teste = (atual + " " + palavra).strip()
        if fonte.getbbox(teste)[2] <= largura:
            atual = teste
        else:
            if atual:
                linhas.append(atual)
            atual = palavra
    if atual:
        linhas.append(atual)
    return linhas


def _desenhar_bloco(img: Image.Image, texto: str, fonte, cor, reveladas: int,
                    y_centro: int) -> None:
    """Revela as `reveladas` primeiras palavras SEM mover as demais.

    A quebra de linha é calculada com o texto COMPLETO e cada palavra fica
    ancorada na sua posição final. Se recalculássemos a cada palavra, o bloco
    se recentralizaria a cada quadro e o texto pularia na tela — mesma regra
    de âncora fixa dos carrosséis.
    """
    d = ImageDraw.Draw(img)
    linhas = _quebrar(texto, fonte, LARG - 2 * MARGEM_X)
    alt_linha = int(fonte.size * 1.32)
    y = y_centro - (len(linhas) * alt_linha) // 2

    indice = 0
    espaco = fonte.getbbox(" ")[2]
    for linha in linhas:
        palavras = linha.split()
        w_linha = fonte.getbbox(linha)[2]
        x = (LARG - w_linha) // 2
        for palavra in palavras:
            if indice < reveladas:
                d.text((x, y), palavra, font=fonte, fill=cor)
            x += fonte.getbbox(palavra)[2] + espaco
            indice += 1
        y += alt_linha


def _rodape(img: Image.Image) -> None:
    d = ImageDraw.Draw(img)
    f = _f(30, 500)
    txt = "@vendanaobra"
    w = f.getbbox(txt)[2]
    d.text(((LARG - w) // 2, ALT - 130), txt, font=f, fill=(150, 165, 190))


def _barra(img: Image.Image, progresso: float) -> None:
    """Barra dourada de progresso no topo — prende o olho no tempo do video."""
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, LARG, 8], fill=(24, 48, 80))
    d.rectangle([0, 0, int(LARG * progresso), 8], fill=DOURADO)


def montar(blocos: list[str], palavra: str, destino: str) -> str:
    """blocos[0] = gancho, blocos[1:] = desenvolvimento. O CTA e montado aqui."""
    os.makedirs(SAIDA, exist_ok=True)
    quadros: list[tuple[str, float]] = []   # (arquivo, duracao em segundos)
    n = 0

    f_gancho = _f(68, 800)
    f_corpo = _f(58, 600)
    f_cta = _f(58, 700)

    # ---- cada bloco entra palavra a palavra, depois respira ----
    total_estados = sum(len(b.split()) for b in blocos) + 6
    estado = 0

    for i, bloco in enumerate(blocos):
        fonte = f_gancho if i == 0 else f_corpo
        cor = BRANCO if i == 0 else PRATA
        palavras = bloco.split()
        for k in range(1, len(palavras) + 1):
            estado += 1
            img = _fundo()
            _barra(img, estado / total_estados)
            _desenhar_bloco(img, bloco, fonte, cor, k, ALT // 2)
            _rodape(img)
            caminho = os.path.join(SAIDA, f"q{n:03d}.jpg")
            img.save(caminho, "JPEG", quality=90, subsampling=0)
            # a ultima palavra do bloco segura o tempo de ler a frase inteira
            quadros.append((caminho, 1.9 if k == len(palavras) else 0.22))
            n += 1

    # ---- CTA final: pilula dourada com a palavra-chave ----
    for etapa in range(3):
        estado += 2
        img = _fundo()
        _barra(img, min(1.0, estado / total_estados))
        d = ImageDraw.Draw(img)

        titulo = "Comenta"
        f_t = _f(52, 600)
        w = f_t.getbbox(titulo)[2]
        d.text(((LARG - w) // 2, ALT // 2 - 190), titulo, font=f_t, fill=PRATA)

        pw = f_cta.getbbox(palavra)[2]
        pad_x, pad_y = 62, 34
        cx0 = (LARG - pw) // 2 - pad_x
        cy0 = ALT // 2 - 90
        cx1 = cx0 + pw + 2 * pad_x
        cy1 = cy0 + f_cta.size + 2 * pad_y
        raio = (cy1 - cy0) // 2
        cor_pilula = DOURADO if etapa % 2 == 0 else (255, 196, 92)
        d.rounded_rectangle([cx0, cy0, cx1, cy1], radius=raio, fill=cor_pilula)
        d.text(((LARG - pw) // 2, cy0 + pad_y - 6), palavra, font=f_cta, fill=(16, 24, 40))

        fim = "que eu te mando no Direct"
        f_fim = _f(42, 400)
        w2 = f_fim.getbbox(fim)[2]
        d.text(((LARG - w2) // 2, cy1 + 60), fim, font=f_fim, fill=PRATA)

        _rodape(img)
        caminho = os.path.join(SAIDA, f"q{n:03d}.jpg")
        img.save(caminho, "JPEG", quality=90, subsampling=0)
        quadros.append((caminho, 0.55 if etapa < 2 else 1.6))
        n += 1

    # ---- ffmpeg concat: cada imagem com sua duracao ----
    lista = os.path.join(SAIDA, "lista.txt")
    with open(lista, "w", encoding="utf-8") as fh:
        for caminho, dur in quadros:
            fh.write(f"file '{os.path.basename(caminho)}'\nduration {dur}\n")
        fh.write(f"file '{os.path.basename(quadros[-1][0])}'\n")  # ffmpeg exige repetir a ultima

    subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", lista,
        "-vf", f"fps={FPS},format=yuv420p", "-c:v", "libx264", "-preset", "medium",
        "-crf", "20", "-movflags", "+faststart", destino,
    ], check=True, capture_output=True)

    for caminho, _ in quadros:
        os.remove(caminho)
    os.remove(lista)
    return destino


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--id", type=int, help="id da frase em frases.json")
    p.add_argument("--texto", help="blocos separados por |")
    p.add_argument("--palavra", default="LIVRO")
    p.add_argument("--saida", default=os.path.join(SAIDA, "reels.mp4"))
    args = p.parse_args()

    if args.texto:
        blocos = [b.strip() for b in args.texto.split("|") if b.strip()]
    else:
        banco = json.load(open(os.path.join(BASE, "frases.json"), encoding="utf-8"))
        frase = next(f for f in banco["frases"] if f["id"] == (args.id or 2))
        blocos = [b.strip() for b in frase["texto"].split("\n") if b.strip()]

    os.makedirs(os.path.dirname(args.saida), exist_ok=True)
    montar(blocos, args.palavra, args.saida)
    print("reels:", args.saida, os.path.getsize(args.saida) // 1024, "KB")


if __name__ == "__main__":
    main()

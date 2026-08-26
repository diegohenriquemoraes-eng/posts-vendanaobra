# -*- coding: utf-8 -*-
"""Capa (cover) dos Reels do Aluparts Podcast #EP25 — 1080x1920.

Mesma receita da capa da mini-aula: frame do episodio, escurecido de leve,
degrade smoothstep fechando em preto solido embaixo, etiqueta dourada, gancho
grande e @vendanaobra no topo. A tipografia e a de `tipografia.py` — gancho na
Playfair Display, etiqueta e assinatura na Archivo. A letra nova fica SO na capa:
a legenda queimada do video e o miolo dos carrosseis seguem na Instagram Sans
(decisao do Diego em 25/08/2026, depois de ver a capa pronta).

Por que o bloco de texto termina em y=1500 e nao no rodape: a grade do perfil
corta o 1080x1920 num 1080x1350 central, e texto colado na base some no grid.

O frame vem do YouTube, nao do MP4 do corte: o corte ja tem a legenda queimada
no terco inferior, exatamente onde entra o gancho. `yt-dlp --download-sections`
baixa so ~10s em volta do instante — o master de 723 MB nao precisa ficar no
disco (ver o aperto de espaco de 24/08/2026).

Uso:
    python gerar_capa_reel.py 04            # uma capa
    python gerar_capa_reel.py 04 05 06      # varias
    python gerar_capa_reel.py --restantes   # todos que ainda nao publicaram
    python gerar_capa_reel.py 04 --previa   # nao grava em midia/reels
    python gerar_capa_reel.py --restantes --master ep25_full.mp4   # lote, sem baixar 25x
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile

from PIL import Image, ImageDraw

from tipografia import rotulo as _fonte
from tipografia import titulo as _titulo
from tipografia import escrever_espacado as _espacado

BASE = os.path.dirname(os.path.abspath(__file__))
VIDEO = "https://www.youtube.com/watch?v=e6clG_KFAPA"
CAPAS = os.path.join(BASE, "capas_ep25.json")
FILA = os.path.join(BASE, "reels_ep25.json")
PUBLICADOS = os.path.join(BASE, "publicados_reels.json")
DESTINO = os.path.join(BASE, "midia", "reels")

LARG, ALT = 1080, 1920
MARGEM = 96
UTIL = LARG - 2 * MARGEM
DOURADO = (240, 168, 46)
BRANCO = (255, 255, 255)
FUNDO = (6, 10, 16)
ETIQUETA = "ALUPARTS PODCAST · EP25"
Y_BASE = 1500                      # a base do bloco de texto


def _quebrar(texto: str, fonte, largura: int) -> list[str]:
    linhas: list[str] = []
    for palavra in texto.split():
        if linhas and fonte.getlength(linhas[-1] + " " + palavra) <= largura:
            linhas[-1] += " " + palavra
        else:
            linhas.append(palavra)
    return linhas


def _ajustar(texto: str, largura: int, alt_max: int, maior: int, menor: int):
    for tam in range(maior, menor - 1, -2):
        f = _titulo(tam, peso=800)
        if len(_quebrar(texto, f, largura)) * tam * 1.16 <= alt_max:
            return f
    return _titulo(menor, peso=800)


def _recortar(fonte_video: str, instante: float, x: int, destino_png: str) -> None:
    subprocess.run(
        ["ffmpeg", "-y", "-v", "error", "-ss", f"{instante:.2f}", "-i", fonte_video,
         "-frames:v", "1",
         "-vf", f"crop=608:1080:{x}:0,scale=1080:1920:flags=lanczos", destino_png],
        check=True)


def _frame(t_abs: float, x: int, destino_png: str, master: str | None = None) -> None:
    """Frame ja recortado em 9:16, do master local ou de ~8s baixados do YouTube."""
    if master:
        _recortar(master, t_abs, x, destino_png)
        return
    tmp = tempfile.mkdtemp(prefix="capa-ep25-")
    ini = max(0.0, t_abs - 6)
    saida = os.path.join(tmp, "trecho.%(ext)s")
    subprocess.run(
        ["yt-dlp", "-q", "--no-warnings",
         "-f", "bv[height<=1080][ext=mp4]/bv*[height<=1080]",
         "--download-sections", f"*{ini:.2f}-{t_abs + 2:.2f}",
         "-o", saida, VIDEO],
        check=True)
    trecho = next(os.path.join(tmp, f) for f in os.listdir(tmp) if f.startswith("trecho"))

    # o corte cai no keyframe anterior ao pedido: o instante certo dentro do
    # arquivo e a diferenca entre t_abs e o inicio real do trecho.
    dur = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                          "-of", "csv=p=0", trecho], capture_output=True, text=True).stdout.strip()
    dentro = max(0.0, float(dur) - 2.0) if dur else t_abs - ini

    _recortar(trecho, dentro, x, destino_png)
    for f in os.listdir(tmp):
        os.remove(os.path.join(tmp, f))
    os.rmdir(tmp)


def gerar(cid: str, dados: dict, destino: str, master: str | None = None) -> str:
    png = os.path.join(tempfile.gettempdir(), f"capa-ep25-{cid}.png")
    _frame(dados["t_abs"], dados["x"], png, master)

    img = Image.open(png).convert("RGB")
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
    ft = _ajustar(dados["titulo"], UTIL, 520, 112, 66)
    linhas = _quebrar(dados["titulo"], ft, UTIL)
    y_titulo = Y_BASE - len(linhas) * ft.size * 1.16

    fe = _fonte(30, peso=700)
    _espacado(d, (MARGEM, y_titulo - 62), ETIQUETA, fe, DOURADO, tracking=fe.size * 0.10)
    y = y_titulo
    for ln in linhas:
        d.text((MARGEM, y), ln, font=ft, fill=BRANCO, anchor="la")
        y += ft.size * 1.16

    d.text((MARGEM, 300), "@vendanaobra", font=_fonte(32, peso=600), fill=BRANCO, anchor="la")

    os.makedirs(os.path.dirname(destino), exist_ok=True)
    img.save(destino, "JPEG", quality=92, optimize=True)
    os.remove(png)
    return destino


def _restantes() -> list[str]:
    fila = json.load(open(FILA, encoding="utf-8"))["cortes"]
    saiu = set()
    if os.path.exists(PUBLICADOS):
        publicados = json.load(open(PUBLICADOS, encoding="utf-8"))
        # o arquivo e uma lista de posts (nao um dicionario com chave)
        saiu = {p.get("id") for p in publicados}
    return [c["id"] for c in fila if c["id"] not in saiu]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("ids", nargs="*", help="ids dos cortes (01, 02, ...)")
    ap.add_argument("--restantes", action="store_true", help="todos os que ainda nao foram ao ar")
    ap.add_argument("--previa", metavar="PASTA", nargs="?", const=os.path.join(BASE, "saida", "capas"),
                    help="grava numa pasta de previa em vez de midia/reels")
    ap.add_argument("--master", metavar="MP4",
                    help="usa um MP4 do episodio ja baixado (evita um download por capa)")
    args = ap.parse_args()

    capas = json.load(open(CAPAS, encoding="utf-8"))
    ids = _restantes() if args.restantes else args.ids
    if not ids:
        sys.exit("Nada a fazer: passe ids ou --restantes")

    pasta = args.previa or DESTINO
    for cid in ids:
        dados = capas[cid]
        destino = os.path.join(pasta, f"{cid}-{dados['slug']}.jpg")
        print(cid, gerar(cid, dados, destino, args.master), flush=True)


if __name__ == "__main__":
    main()

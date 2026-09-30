# -*- coding: utf-8 -*-
"""Reel de 7 s do @vendanaobra: filmagem do Diego em ação + uma frase na tela.

É o 2º formato da Rota 100K (vídeo curto que segura até o fim, entrega na legenda
longa). Pedido do Diego em 30/09/2026: eu escolho o trecho, recorto, ponho a frase
e escrevo a legenda; ele aprova. Sai sem música (a API não põe música).

Uso:
  python reel7s.py --src bruto.mp4 --ini 29 --dur 7 --crop 150,20,540,960 \
      --texto "Linha 1|Linha 2" --saida reel.mp4

--crop x,y,l,a recorta um retângulo 9:16 do bruto antes de escalar para 1080x1920
(é como se tira legenda queimada do original: o recorte fica acima dela).
"""
import argparse
import subprocess
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

FONTE = Path(__file__).parent / "fontes" / "InstagramSans-Bold.ttf"
L, A = 1080, 1920


def arte_texto(linhas: list[str], y_centro: int, caminho: str) -> None:
    img = Image.new("RGBA", (L, A), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    f = ImageFont.truetype(str(FONTE), 74)
    alt_linha = 92
    larguras = [d.textlength(t, font=f) for t in linhas]
    caixa_l = int(max(larguras)) + 96
    caixa_a = alt_linha * len(linhas) + 64
    x0 = (L - caixa_l) // 2
    y0 = y_centro - caixa_a // 2
    d.rounded_rectangle((x0, y0, x0 + caixa_l, y0 + caixa_a), radius=28,
                        fill=(10, 16, 28, 215))
    for i, t in enumerate(linhas):
        d.text((L // 2, y0 + 32 + alt_linha * i + alt_linha // 2), t, font=f,
               fill="white", anchor="mm")
    img.save(caminho)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True)
    ap.add_argument("--ini", type=float, required=True)
    ap.add_argument("--dur", type=float, default=7)
    ap.add_argument("--crop", required=True, help="x,y,largura,altura")
    ap.add_argument("--texto", required=True, help="linhas separadas por |")
    ap.add_argument("--y", type=int, default=560, help="centro vertical do texto")
    ap.add_argument("--saida", required=True)
    o = ap.parse_args()
    x, y, w, h = o.crop.split(",")
    with tempfile.TemporaryDirectory() as tmp:
        png = str(Path(tmp) / "texto.png")
        arte_texto(o.texto.split("|"), o.y, png)
        filtro = (f"[0:v]crop={w}:{h}:{x}:{y},scale={L}:{A}:flags=lanczos,"
                  f"eq=contrast=1.04:saturation=1.08,fps=30[v];[v][1:v]overlay=0:0[out]")
        subprocess.run([
            "ffmpeg", "-v", "error", "-y", "-ss", str(o.ini), "-t", str(o.dur), "-i", o.src,
            "-i", png, "-f", "lavfi", "-t", str(o.dur), "-i", "anullsrc=r=44100:cl=stereo",
            "-filter_complex", filtro, "-map", "[out]", "-map", "2:a",
            "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "128k", "-shortest", "-movflags", "+faststart", o.saida,
        ], check=True)
    print("gravado", o.saida)


if __name__ == "__main__":
    main()

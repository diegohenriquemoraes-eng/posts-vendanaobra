# -*- coding: utf-8 -*-
"""Gera a foto de capa das mini-aulas pela API do Gemini, sem passar pelo navegador.

Por que existe: gerar capa pelo gemini.google.com no Chrome se mostrou fragil —
a conversa some sozinha, o Enter as vezes nao envia, o renderizador congela e a
extensao perde permissao. Pela API isso vira uma chamada previsivel, que da'
para rodar em lote e conferir.

Regras do projeto que estao embutidas no prompt (ver CLAUDE.md):
  * NITIDEZ em toda a cena, sem bokeh forte — a capa da aula 10 saiu borrada e
    o Diego reprovou; foto de fundo com texto grande por cima nao pode ter
    desfoque;
  * NENHUM logotipo, marca ou texto legivel — o Gemini desobedece isso com
    frequencia, entao TODA foto ainda precisa ser conferida ampliada antes de
    publicar (ja apareceram um logo da Dell e a palavra CONTRACT);
  * a cena fala com a construcao INTEIRA, nao so' com esquadria — esquadria so'
    quando a aula for especificamente da Venda Blindada.

Uso:
    python gerar_foto_ia.py 20                 # gera o master da aula 20
    python gerar_foto_ia.py 20 21 22           # varias
    python gerar_foto_ia.py --todas            # todas as que faltam foto
"""
from __future__ import annotations

import argparse, base64, io, json, os, sys, time, urllib.request, urllib.error

BASE = os.path.dirname(os.path.abspath(__file__))
CHAVE = r"C:\Users\NOTE\Desktop\Perffec\Claude\gemini_api_token.txt"
MASTERS = os.path.join(BASE, "fotos", "masters")
CENAS = os.path.join(BASE, "cenas_miniaulas.json")
MODELO = "gemini-3-pro-image"

REGRAS = (
    " Fotografia realista, como foto de banco de imagens profissional. "
    "Nitidez em toda a cena, diafragma fechado tipo f/11, grande profundidade de "
    "campo, SEM desfoque de fundo e sem bokeh. "
    "Proibido: qualquer logotipo, marca, etiqueta, texto legivel ou numero em "
    "qualquer objeto, roupa, placa ou tela. "
    "O terco inferior da imagem deve ser simples e pouco carregado, porque leva "
    "texto grande por cima. Enquadramento vertical 4:5."
)


def _chave() -> str:
    with io.open(CHAVE, encoding="utf-8") as f:
        for linha in f:
            if linha.strip():
                return linha.strip()
    raise SystemExit("arquivo de chave vazio")


def gerar(cena: str, destino: str, tentativas: int = 3) -> str:
    corpo = json.dumps({
        "contents": [{"parts": [{"text": cena + REGRAS}]}],
        "generationConfig": {"imageConfig": {"aspectRatio": "4:5"}},
    }).encode("utf-8")
    url = (f"https://generativelanguage.googleapis.com/v1beta/models/"
           f"{MODELO}:generateContent?key={_chave()}")
    for n in range(1, tentativas + 1):
        try:
            req = urllib.request.Request(url, data=corpo,
                                         headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=300) as r:
                d = json.load(r)
            for parte in d["candidates"][0]["content"]["parts"]:
                dados = parte.get("inlineData") or parte.get("inline_data")
                if dados:
                    os.makedirs(os.path.dirname(destino), exist_ok=True)
                    with open(destino, "wb") as f:
                        f.write(base64.b64decode(dados["data"]))
                    return destino
            raise RuntimeError("resposta sem imagem: " + json.dumps(d)[:200])
        except urllib.error.HTTPError as e:
            msg = e.read()[:200].decode(errors="replace")
            if e.code in (429, 500, 503) and n < tentativas:
                print(f"    HTTP {e.code}, tentando de novo em 20s", flush=True)
                time.sleep(20)
                continue
            raise SystemExit(f"Gemini HTTP {e.code}: {msg}")
    raise SystemExit("nao consegui gerar")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("ids", nargs="*")
    ap.add_argument("--todas", action="store_true")
    a = ap.parse_args()

    cenas = json.load(io.open(CENAS, encoding="utf-8"))
    alvos = sorted(cenas) if a.todas else a.ids
    for cid in alvos:
        destino = os.path.join(MASTERS, f"miniaula-{int(cid):02d}.png")
        if a.todas and os.path.exists(destino):
            continue
        print(f"aula {cid}...", flush=True)
        gerar(cenas[str(int(cid))], destino)
        try:
            from PIL import Image
            with Image.open(destino) as im:
                print(f"  ok {im.size[0]}x{im.size[1]} -> {destino}", flush=True)
        except Exception:
            print("  ok ->", destino, flush=True)


if __name__ == "__main__":
    main()

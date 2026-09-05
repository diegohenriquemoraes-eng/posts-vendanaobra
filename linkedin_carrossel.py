"""Post de DOCUMENTO no LinkedIn — o artigo do blog vira carrossel em PDF.

POR QUE (05/09/2026)
--------------------
Não é canal novo: é a mesma esteira do `linkedin_publicar.py` com outra forma.
No LinkedIn, post de documento (o PDF que o leitor passa folha a folha) segura
o leitor dentro da página em vez de mandá-lo embora num link — e a rede
distribui muito mais quem prende do que quem manda sair. O texto puro continua
existindo; este alterna com ele.

COMO FUNCIONA
-------------
O PDF é desenhado aqui mesmo com PyMuPDF (já instalado, sem dependência nova),
em 1080x1080 com a paleta do site. O envio é em três passos da API do LinkedIn:
`initializeUpload` → PUT do arquivo → `POST /rest/posts` com o documento anexado.

Uso:
    python linkedin_carrossel.py --ensaio     # gera o PDF e para
    python linkedin_carrossel.py
"""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import re
import sys
import textwrap
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone

import fitz  # PyMuPDF

AQUI = pathlib.Path(__file__).parent
ESTADO = AQUI / "linkedin_carrossel_publicados.json"
FONTES = AQUI / "fontes"
LLMS = "https://vendanaobra.com.br/llms.txt"
VERSAO = "202608"
DIAS_PARA_RECICLAR = 180

NAVY = (7 / 255, 16 / 255, 37 / 255)
CREME = (250 / 255, 250 / 255, 247 / 255)
OURO = (216 / 255, 184 / 255, 136 / 255)
LADO = 1080


def credenciais() -> tuple[str, str]:
    tok = os.environ.get("LINKEDIN_TOKEN", "").strip()
    urn = os.environ.get("LINKEDIN_URN", "").strip()
    if tok and urn:
        return tok, urn
    base = pathlib.Path(r"C:\Users\NOTE\Desktop\Perffec\Claude")
    return (
        json.loads((base / "linkedin_token.json").read_text(encoding="utf-8"))["access_token"],
        (base / "linkedin_urn.txt").read_text().strip(),
    )


def artigos() -> list[dict]:
    req = urllib.request.Request(LLMS, headers={"User-Agent": "VendaNaObra/1.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        texto = r.read().decode("utf-8")
    saida = []
    for linha in texto.split("\n"):
        m = re.match(r"^- \[(.+?)\]\((https://[^)]+/blog/[^)]+)\): (.+)$", linha.strip())
        if m:
            t, u, resto = m.groups()
            saida.append(
                {
                    "slug": u.rstrip("/").split("/")[-1],
                    "titulo": t,
                    "url": u,
                    "resposta": re.sub(r"\s*\(categoria:.*$", "", resto).strip(),
                }
            )
    return saida


def frases_de(texto: str) -> list[str]:
    """Quebra em frases sem cair nas abreviações.

    ⚠ O corte ingênuo por ponto partiu "no São Paulo Expo (Rod. dos Imigrantes)"
    no meio e a folha do carrossel saiu terminando em "(Rod." — corte exige
    ponto seguido de espaço E letra maiúscula, e nunca depois de abreviação
    conhecida.
    """
    abrev = r"(?<!\bRod)(?<!\bAv)(?<!\bR)(?<!\bSr)(?<!\bSra)(?<!\bDr)(?<!\bnº)(?<!\bkm)"
    partes = re.split(abrev + r"(?<=[.!?])\s+(?=[A-ZÁÉÍÓÚÂÊÔÃÕÇ])", texto)
    return [p.strip() for p in partes if p.strip()]


def folhas(art: dict) -> list[tuple[str, str]]:
    """(título da folha, corpo). A capa vende a passagem; o fim pede a leitura."""
    frases = frases_de(art["resposta"])
    miolo = frases[:4] or [art["titulo"]]
    paginas = [("", art["titulo"])]
    for i, f in enumerate(miolo, 1):
        paginas.append((f"{i}", f))
    paginas.append(("", "O artigo completo está no vendanaobra.com.br/blog"))
    return paginas


def desenhar(art: dict, destino: pathlib.Path) -> pathlib.Path:
    doc = fitz.open()
    negrito = str(FONTES / "InstagramSans-Bold.ttf")
    normal = str(FONTES / "InstagramSans-Regular.ttf")
    tem_fonte = pathlib.Path(negrito).exists()

    for i, (numero, texto) in enumerate(folhas(art)):
        pg = doc.new_page(width=LADO, height=LADO)
        capa = i == 0
        fim = texto.startswith("O artigo completo")
        pg.draw_rect(fitz.Rect(0, 0, LADO, LADO), color=None, fill=NAVY if (capa or fim) else CREME)

        cor = CREME if (capa or fim) else NAVY
        tamanho = 58 if capa else 44
        largura = 22 if capa else 30

        if numero:
            pg.insert_text(
                (90, 150), numero, fontsize=40, color=OURO,
                fontfile=negrito if tem_fonte else None,
                fontname="F0" if tem_fonte else "hebo",
            )

        # Bloco centrado na folha: com o y fixo, frase curta ficava colada no
        # topo e sobrava meia folha vazia embaixo.
        linhas = textwrap.wrap(texto, width=largura)[:9]
        altura = len(linhas) * (tamanho + 18)
        y = max(260, (LADO - altura) / 2 + tamanho)
        for l in linhas:
            pg.insert_text(
                (90, y), l, fontsize=tamanho, color=cor,
                fontfile=(negrito if (capa or fim) else normal) if tem_fonte else None,
                fontname=("F1" if (capa or fim) else "F2") if tem_fonte else "helv",
            )
            y += tamanho + 18

        # Assinatura discreta em toda folha: quem compartilha o PDF leva a marca.
        pg.insert_text(
            (90, LADO - 70), "vendanaobra.com.br", fontsize=26,
            color=OURO if (capa or fim) else (0.42, 0.42, 0.4),
            fontfile=normal if tem_fonte else None,
            fontname="F3" if tem_fonte else "helv",
        )

    doc.save(str(destino))
    doc.close()
    return destino


def enviar(pdf: pathlib.Path, titulo: str, comentario: str) -> str:
    tok, urn = credenciais()
    cab = {
        "Authorization": f"Bearer {tok}",
        "Content-Type": "application/json",
        "LinkedIn-Version": VERSAO,
        "X-Restli-Protocol-Version": "2.0.0",
    }

    req = urllib.request.Request(
        "https://api.linkedin.com/rest/documents?action=initializeUpload",
        data=json.dumps({"initializeUploadRequest": {"owner": urn}}).encode(),
        headers=cab,
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        val = json.load(r)["value"]
    url_upload, doc_urn = val["uploadUrl"], val["document"]

    envio = urllib.request.Request(
        url_upload, data=pdf.read_bytes(),
        headers={"Authorization": f"Bearer {tok}", "Content-Type": "application/octet-stream"},
        method="PUT",
    )
    with urllib.request.urlopen(envio, timeout=180):
        pass

    corpo = {
        "author": urn,
        "commentary": comentario,
        "visibility": "PUBLIC",
        "distribution": {"feedDistribution": "MAIN_FEED", "targetEntities": [], "thirdPartyDistributionChannels": []},
        "content": {"media": {"id": doc_urn, "title": titulo[:100]}},
        "lifecycleState": "PUBLISHED",
        "isReshareDisabledByAuthor": False,
    }
    req2 = urllib.request.Request(
        "https://api.linkedin.com/rest/posts", data=json.dumps(corpo).encode(), headers=cab
    )
    with urllib.request.urlopen(req2, timeout=90) as r:
        return r.headers.get("x-restli-id") or "publicado"


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--ensaio", action="store_true")
    p.add_argument("--forcar", action="store_true")
    args = p.parse_args()

    hoje = datetime.now(timezone.utc)
    if hoje.weekday() >= 5 and not args.forcar:
        print("Fim de semana: o LinkedIn e rede de trabalho.")
        return

    estado = json.loads(ESTADO.read_text(encoding="utf-8")) if ESTADO.exists() else {}
    lista = artigos()
    if not lista:
        sys.exit("Nenhum artigo lido do /llms.txt.")

    def visto(a):
        r = estado.get(a["slug"])
        return datetime.fromisoformat(r["em"]) if r else datetime.min.replace(tzinfo=timezone.utc)

    # Não repetir no carrossel o artigo que o post de TEXTO usou há pouco: os
    # dois publicam no mesmo perfil e o mesmo assunto duas vezes na semana
    # parece robô — que é exatamente o que o leitor de LinkedIn fareja.
    texto_estado = AQUI / "linkedin_publicados.json"
    recentes = set()
    if texto_estado.exists():
        for slug, reg in json.loads(texto_estado.read_text(encoding="utf-8")).items():
            if hoje - datetime.fromisoformat(reg["em"]) < timedelta(days=7):
                recentes.add(slug)

    lista.sort(key=visto)
    candidatos = [a for a in lista if a["slug"] not in recentes] or lista
    art = candidatos[0]
    if art["slug"] in estado and hoje - visto(art) < timedelta(days=DIAS_PARA_RECICLAR):
        print("Nada devido.")
        return

    saida = pathlib.Path(os.environ.get("RUNNER_TEMP", ".")) / f"carrossel-{art['slug']}.pdf"
    desenhar(art, saida)
    print(f"[{art['titulo']}] PDF com {len(folhas(art))} folhas: {saida.stat().st_size/1024:.0f} KB")

    comentario = (
        f"{art['resposta'].split('. ')[0]}.\n\n"
        "Passe as folhas — e o artigo completo está em "
        f"{art['url']}?utm_source=linkedin&utm_medium=carrossel"
    )
    if args.ensaio:
        print(comentario)
        print("(ensaio: nada foi publicado)")
        return

    try:
        pid = enviar(saida, art["titulo"], comentario)
    except urllib.error.HTTPError as e:
        sys.exit(f"LinkedIn recusou ({e.code}): {e.read().decode()[:400]}")
    print(f"Publicado: {pid}")
    estado[art["slug"]] = {"em": hoje.isoformat(timespec="seconds"), "post": pid, "titulo": art["titulo"]}
    ESTADO.write_text(json.dumps(estado, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()

"""Distribuidor — o Reel do @vendanaobra vira video nativo no LinkedIn do Diego.

POR QUE, E POR QUE COM FREIO (decisao do Diego, 19/09/2026)
-----------------------------------------------------------
No LinkedIn quem le e o DONO da vidracaria / gerente da construtora — e o unico
canal que gera contrato, nao e-book. Duas regras que os outros distribuidores
nao tem:

1. **Um post por dia, no maximo.** O LinkedIn canibaliza o post anterior quando
   se publica duas vezes no dia. Este script roda DENTRO do workflow do LinkedIn
   diario (seg/qua/sex): se publica um video, o post de texto do blog e pulado
   naquele dia. Terca e quinta continuam com o carrossel.
2. **Nem todo Reel serve.** So entra Reel cuja legenda tem NUMERO, NOME de
   empresa/feira ou RESULTADO (`elegivel_para_dono`): historia com nome e numero
   fala com o dono; "vendedor ansioso justificando preco" fala com o vendedor e
   soa pequeno para quem contrata.

O texto e REESCRITO para o decisor pelo Groq (mesmo prompt-base do
`linkedin_publicar.py`), com o link /r/li-raiox. Video sobe pela API nativa
(`/rest/videos` initializeUpload → PUT por partes → finalizeUpload → /rest/posts),
sem gastar vaga no Zernio. Token e URN os mesmos do LinkedIn diario.

Uso:
    python distribuir_linkedin.py --ensaio
    python distribuir_linkedin.py            # publica 1 (se houver Reel elegivel)
Imprime `LINKEDIN_VIDEO_PUBLICADO` quando publica — o workflow le isso para
pular o post de texto.
"""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import re
import sys
import tempfile
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone

from distribuir import _linhas_uteis, coletar  # noqa: E402
from linkedin_publicar import VERSAO, credenciais  # noqa: E402

AQUI = pathlib.Path(__file__).parent
ESTADO = AQUI / "distribuidos_linkedin.json"
LINK = "https://vendanaobra.com.br/r/li-raiox"
MAX_TENTATIVAS = 2

# O que faz um Reel falar com o DONO: numero (R$, %, anos, mil), nome de feira/
# empresa, ou palavra de resultado. Sem isso o Reel fica so no Instagram/TikTok.
_NUMERO = re.compile(r"(R\$\s?\d|\d+\s?%|\d+\s?(anos?|meses|dias|mil|milh)|\b\d{2,}\b)", re.I)
_NOMES = re.compile(r"\b(fesqua|perffec|aluparts|glassec|expo|feira|construtora|incorporadora)\b", re.I)
_RESULTADO = re.compile(r"\b(fechou|fechamos|contrato|faturou|faturamento|lucro|margem|carteira|processo)\b", re.I)


def elegivel_para_dono(legenda: str) -> bool:
    t = " ".join(_linhas_uteis(legenda))
    return bool(_NUMERO.search(t) or _NOMES.search(t) or _RESULTADO.search(t))


def escrever(legenda: str) -> str | None:
    linhas = _linhas_uteis(legenda)
    if not linhas:
        return None
    base = "\n".join(linhas[:6])
    base = re.sub(r"https?://\S+", "", base)
    base = re.sub(r"(?<!\w)@([\w.]+)", r"\1", base)
    chave = os.environ.get("GROQ_API_KEY", "").strip()
    if chave:
        pedido = (
            "Você escreve posts de LinkedIn para Diego Moraes, que trabalha com estruturação "
            "comercial na construção civil. Quem lê é DONO de vidraçaria, serralheria ou "
            "fábrica de esquadrias, gerente de construtora ou industrial do alumínio — "
            "decisor, não executor. O post acompanha um VÍDEO curto em que o Diego conta "
            "o caso abaixo; o texto apresenta o vídeo para o dono, não repete o vídeo.\n"
            "Escreva UM post e nada além dele.\n"
            "Regras: entre 350 e 700 caracteres; português do Brasil; primeira linha curta e "
            "forte, porque é a única que aparece antes do 'ver mais'; frases curtas em linhas "
            "separadas; tom seco, de quem opera; sem emoji; sem hashtag; sem aspas; não "
            "invente número nem caso que não esteja no texto; NÃO inclua link.\n\n"
            f"LEGENDA DO VÍDEO:\n{base}"
        )
        try:
            corpo = json.dumps({"model": "groq/compound-mini", "temperature": 0.4,
                                "max_tokens": 400,
                                "messages": [{"role": "user", "content": pedido}]}).encode("utf-8")
            req = urllib.request.Request(
                "https://api.groq.com/openai/v1/chat/completions", data=corpo,
                headers={"Authorization": f"Bearer {chave}", "Content-Type": "application/json",
                         "User-Agent": "VendaNaObra-LinkedIn/1.0"})
            with urllib.request.urlopen(req, timeout=45) as r:
                t = json.load(r)["choices"][0]["message"]["content"].strip().strip('"')
            t = "\n".join(l.rstrip() for l in t.split("\n"))
            if 150 <= len(t) <= 1000:
                return f"{t}\n\nRaio-X comercial gratuito, 3 minutos: {LINK}"
        except Exception as e:
            print(f"  (Groq indisponivel, usando a legenda: {e})")
    return f"{base}\n\nRaio-X comercial gratuito, 3 minutos: {LINK}"


# --------------------------------------------------------------------------- #
# LinkedIn — video nativo
# --------------------------------------------------------------------------- #
def _cab(tok: str) -> dict:
    return {"Authorization": f"Bearer {tok}", "Content-Type": "application/json",
            "LinkedIn-Version": VERSAO, "X-Restli-Protocol-Version": "2.0.0"}


def _post(url: str, corpo: dict, tok: str):
    req = urllib.request.Request(url, data=json.dumps(corpo).encode(), headers=_cab(tok))
    return urllib.request.urlopen(req, timeout=90)


def subir_video(arquivo: pathlib.Path) -> str:
    tok, urn = credenciais()
    tamanho = arquivo.stat().st_size
    with _post("https://api.linkedin.com/rest/videos?action=initializeUpload",
               {"initializeUploadRequest": {"owner": urn, "fileSizeBytes": tamanho,
                                            "uploadCaptions": False, "uploadThumbnail": False}},
               tok) as r:
        val = json.load(r)["value"]
    video_urn, token_upload = val["video"], val["uploadToken"]
    dados = arquivo.read_bytes()
    etags = []
    for parte in val["uploadInstructions"]:
        a, b = parte["firstByte"], parte["lastByte"]
        req = urllib.request.Request(parte["uploadUrl"], data=dados[a:b + 1], method="PUT",
                                     headers={"Content-Type": "application/octet-stream"})
        with urllib.request.urlopen(req, timeout=300) as r:
            etags.append(r.headers.get("ETag") or r.headers.get("etag") or "")
    with _post("https://api.linkedin.com/rest/videos?action=finalizeUpload",
               {"finalizeUploadRequest": {"video": video_urn, "uploadToken": token_upload,
                                          "uploadedPartIds": etags}}, tok):
        pass
    # Processamento: o post so aceita o video quando status == AVAILABLE.
    fim = time.time() + 300
    while time.time() < fim:
        req = urllib.request.Request(
            "https://api.linkedin.com/rest/videos/" + urllib.parse.quote(video_urn, safe=""),
            headers=_cab(tok))
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                st = json.load(r).get("status")
        except urllib.error.HTTPError:
            st = None
        if st == "AVAILABLE":
            return video_urn
        if st in ("PROCESSING_FAILED",):
            raise RuntimeError(f"LinkedIn: processamento do video falhou ({st})")
        time.sleep(10)
    raise RuntimeError("LinkedIn: video nao ficou AVAILABLE em 5 min")


def publicar(video_urn: str, texto: str, titulo: str) -> str:
    tok, urn = credenciais()
    corpo = {
        "author": urn, "commentary": texto, "visibility": "PUBLIC",
        "distribution": {"feedDistribution": "MAIN_FEED", "targetEntities": [],
                         "thirdPartyDistributionChannels": []},
        "content": {"media": {"id": video_urn, "title": titulo[:100]}},
        "lifecycleState": "PUBLISHED", "isReshareDisabledByAuthor": False,
    }
    with _post("https://api.linkedin.com/rest/posts", corpo, tok) as r:
        return r.headers.get("x-restli-id") or "publicado"


# --------------------------------------------------------------------------- #
def main() -> None:
    import urllib.parse  # noqa: F401  (usado em subir_video)
    p = argparse.ArgumentParser()
    p.add_argument("--ensaio", action="store_true")
    p.add_argument("--dias", type=int, default=30)
    p.add_argument("--id")
    p.add_argument("--forcar", action="store_true", help="ignora a regra de dia util")
    args = p.parse_args()

    hoje = datetime.now(timezone.utc)
    if hoje.weekday() >= 5 and not args.forcar and not args.ensaio:
        print("Fim de semana: nada no LinkedIn.")
        return

    estado = json.loads(ESTADO.read_text(encoding="utf-8")) if ESTADO.exists() else {}
    dia = hoje.date().isoformat()
    if any((v.get("distribuido_em") or "").startswith(dia) for v in estado.values()) and not args.ensaio:
        print("Ja saiu video no LinkedIn hoje. Um por dia.")
        return

    reels = coletar(args.dias)
    if args.id:
        reels = [m for m in reels if m["id"] == args.id]

    def elegivel(m: dict) -> bool:
        reg = estado.get(m["id"])
        if reg and (reg.get("linkedin") or reg.get("pulado")):
            return False
        if reg and reg.get("tentativas", 0) >= MAX_TENTATIVAS:
            return False
        return True

    candidatos = [m for m in reels if elegivel(m)]
    print(f"{len(reels)} Reels na janela de {args.dias} dias · {len(candidatos)} nao avaliados")
    for midia in candidatos:
        legenda = midia.get("caption") or ""
        if not elegivel_para_dono(legenda):
            print(f"  [{midia['timestamp'][:10]}] fala com o vendedor, nao com o dono — fica fora")
            if not args.ensaio:
                estado[midia["id"]] = {"pulado": "sem numero/nome/resultado", "permalink": midia["permalink"]}
            continue
        texto = escrever(legenda)
        if not texto:
            continue
        print(f"\n[{midia['timestamp'][:10]}] {midia['permalink']}")
        print("-" * 60 + "\n" + texto + "\n" + "-" * 60)
        if args.ensaio:
            print("(ensaio: nada foi publicado)")
            return
        titulo = _linhas_uteis(legenda)[0][:100]
        agora = hoje.isoformat(timespec="seconds")
        try:
            with tempfile.TemporaryDirectory() as tmp:
                destino = pathlib.Path(tmp) / f"reel-{midia['id']}.mp4"
                urllib.request.urlretrieve(midia["media_url"], destino)
                print(f"  baixado: {destino.stat().st_size / 1e6:.1f} MB")
                video_urn = subir_video(destino)
            pid = publicar(video_urn, texto, titulo)
        except urllib.error.HTTPError as e:
            erro = f"{e.code}: {e.read().decode('utf-8', 'replace')[:300]}"
            reg = estado.get(midia["id"], {})
            estado[midia["id"]] = {"tentativas": reg.get("tentativas", 0) + 1, "erro": erro,
                                   "permalink": midia["permalink"], "tentado_em": agora}
            ESTADO.write_text(json.dumps(estado, ensure_ascii=False, indent=2), encoding="utf-8")
            sys.exit(f"LinkedIn recusou ({erro})")
        print(f"  LinkedIn: {pid}")
        print("LINKEDIN_VIDEO_PUBLICADO")
        estado[midia["id"]] = {"linkedin": pid, "permalink": midia["permalink"],
                               "publicado_ig": midia["timestamp"], "distribuido_em": agora}
        ESTADO.write_text(json.dumps(estado, ensure_ascii=False, indent=2), encoding="utf-8")
        return
    if not args.ensaio:
        ESTADO.write_text(json.dumps(estado, ensure_ascii=False, indent=2), encoding="utf-8")
    print("Nenhum Reel elegivel para o dono hoje; o post de texto segue.")


if __name__ == "__main__":
    main()

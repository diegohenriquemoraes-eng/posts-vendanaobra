"""Distribuidor — o Reel do @vendanaobra vira Short no YouTube.

POR QUE ISSO EXISTE (medido em 05/09/2026)
------------------------------------------
O canal @vendanaobra (UCU_nFNvsJfHAG2Vdfkyx1UQ) tem 78 videos, 74 inscritos e
27.111 views, e esta PARADO desde 02/05/2026. Os Shorts que estao la fazem de
560 a 956 views. No mesmo periodo, a mediana de ALCANCE de um post no Instagram
e 73. Mesmo conteudo, mesma pessoa, ~10x mais gente — e o YouTube ainda e
buscador: o video continua sendo achado meses depois, coisa que o Reel nao faz.

Nao ha producao nova aqui. O Reel ja existe; isto so o leva para a outra porta.

O DESENHO, E O MOTIVO DE CADA ESCOLHA
-------------------------------------
- A fonte e a CONTA, nao o motor. O coletor pergunta a Graph API "o que ha de
  novo em @vendanaobra". Assim entra tanto o Reel que o reel-diario.yml publica
  quanto o que o Diego posta na mao pelo celular. Se lesse a fila do motor,
  metade ficaria de fora.
- O video vem de `media_url` (a renditizacao da API), NAO do botao "salvar" do
  aplicativo: o salvar carimba a marca d'agua "@usuario", e video com marca de
  outra plataforma e penalizado no YouTube. Conferido em 05/09/2026 num quadro
  do Reel Dc4aPQKRIa2 — limpo, 720x1280.
- O TITULO e reescrito para BUSCA. A legenda do Instagram e ganho de retencao
  no feed; no YouTube quem traz gente e a frase que a pessoa digita. Sem chave
  de IA disponivel, cai numa extracao deterministica da primeira frase util.
- 1 video por execucao. Despejar 20 de uma vez num canal dormente e assinatura
  de robo; alem disso a cota (1.600 unidades por upload, teto de 10.000/dia)
  nao comporta rajada.
- `distribuidos.json` e versionado de proposito, como o `publicados_reels.json`:
  o runner e descartavel e sem esse arquivo commitado a proxima execucao
  republicaria o mesmo video.

Uso:
    python distribuir.py --ensaio          # mostra o que subiria
    python distribuir.py                   # sobe 1
    python distribuir.py --limite 2 --dias 60
"""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import re
import sys
import tempfile
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone

AQUI = pathlib.Path(__file__).parent
ESTADO = AQUI / "distribuidos.json"

IG_USER_ID = "17841470188725651"  # @vendanaobra
GRAPH = "https://graph.facebook.com/v21.0"

# Canal Venda na Obra no YouTube. Conferido por channels.list em 05/09/2026 —
# nao deduzir pela conta: vendanaobra@gmail.com devolve o @crmnaobra.
YT_CANAL = "UCU_nFNvsJfHAG2Vdfkyx1UQ"

# Categoria 27 = Education. O conteudo e didatico e a categoria ancora as
# recomendacoes no publico certo.
YT_CATEGORIA = "27"

LINK_RAIOX = "https://vendanaobra.com.br/r/ytd"

# TETO DIARIO: quem manda e a COTA da YouTube Data API, nao o gosto.
# `videos.insert` custa 1.600 unidades e o projeto vendanaobra-automacao tem
# 10.000 por dia. 5 uploads = 8.000, sobrando margem para um reenvio; 6 = 9.600,
# e ai um retry derruba o dia. Foi por isso que o teto ficou em 5, e nao porque
# publicar muito faca mal ao canal.
TETO_DIA = 5

# Bordao fixo que abre varias legendas: e marca, nao e o gancho. Como titulo de
# busca ele nao diz nada e ainda se repetiria em dezenas de videos. Aparece em
# duas formas ("venda e metodo" e so "e METODO"), por isso o meio e opcional.
BORDOES = [
    r"^\s*🎯?\s*venda n[ãa]o [ée] dom,?\s*(venda\s+)?[ée] m[ée]todo!?\s*",
    r"^\s*[🔴💡🎯👉⚠️]+\s*",
]

TAGS_FIXAS = [
    "vendas",
    "esquadrias",
    "construção civil",
    "vidraçaria",
    "serralheria",
    "venda na obra",
    "diego moraes",
]


# --------------------------------------------------------------------------- #
# Instagram
# --------------------------------------------------------------------------- #
def token_meta() -> str:
    tok = os.environ.get("META_TOKEN", "").strip()
    if not tok:
        sys.exit("META_TOKEN nao definido.")
    return tok


def coletar(dias: int) -> list[dict]:
    """Reels da conta nos ultimos `dias`, do mais novo para o mais antigo."""
    campos = "id,media_type,media_product_type,media_url,permalink,caption,timestamp"
    url = f"{GRAPH}/{IG_USER_ID}/media?" + urllib.parse.urlencode(
        {"fields": campos, "limit": 50, "access_token": token_meta()}
    )
    with urllib.request.urlopen(url, timeout=60) as r:
        dados = json.load(r)

    corte = datetime.now(timezone.utc) - timedelta(days=dias)
    reels = []
    for m in dados.get("data", []):
        if m.get("media_product_type") != "REELS":
            continue
        if not m.get("media_url"):
            continue
        quando = datetime.fromisoformat(m["timestamp"].replace("+0000", "+00:00"))
        if quando < corte:
            continue
        reels.append(m)
    return reels


# --------------------------------------------------------------------------- #
# Texto
# --------------------------------------------------------------------------- #
def _linhas_uteis(legenda: str) -> list[str]:
    """Linhas da legenda sem bordao, sem hashtag e sem chamada de episodio."""
    texto = legenda or ""
    for b in BORDOES:
        texto = re.sub(b, "", texto, flags=re.IGNORECASE)
    saida = []
    for linha in texto.split("\n"):
        for b in BORDOES:  # o bordao as vezes vem na 2a linha, nao na 1a
            linha = re.sub(b, "", linha, flags=re.IGNORECASE)
        linha = linha.strip()
        if not linha or linha.startswith("#"):
            continue
        if re.match(r"^epis[óo]dio completo", linha, flags=re.IGNORECASE):
            continue
        # Linha que e so mencao/creditos nao vira titulo ("@vendanaobra",
        # "com a @arq.audreydias") — foi o que saiu no primeiro ensaio.
        if re.fullmatch(r"[@\w.\s,\-–—]*@[\w.]+[\s,\-–—]*", linha):
            continue
        saida.append(linha)
    return saida


def titulo_para_busca(legenda: str) -> str | None:
    """Titulo do Short. Tenta a IA gratuita; se nao houver chave, extrai.

    Devolve None quando a legenda nao tem texto aproveitavel (acontece: o Reel
    DbS3O0NJ0GP tem "@vendanaobra" e mais nada). Num canal que vive de BUSCA,
    subir video com titulo generico e pior que nao subir — ele nao e achado por
    ninguem e ainda dilui o canal.
    """
    linhas = _linhas_uteis(legenda)
    if not linhas:
        return None

    # Groq e nao Gemini: a chave do Gemini que sustenta o blog vive SO no secret
    # do repo da LP (a copia local em Perffec\Claude nao e chave de API, e um
    # token de sessao do AI Studio — conferido em 05/09/2026, devolve 401). E o
    # prompt aqui e minusculo, entao o limite de 8 mil tokens/minuto do plano
    # gratuito do Groq, que impede o blog de rodar nele, aqui nao aperta.
    # `groq/compound-mini` responde em texto puro; os modelos de raciocinio
    # (gpt-oss-*) devolvem `content` vazio com a resposta em `reasoning`.
    chave = os.environ.get("GROQ_API_KEY", "").strip()
    if chave:
        pedido = (
            "Você escreve títulos de YouTube Shorts para um canal brasileiro sobre "
            "VENDAS na construção civil (esquadrias, vidraçaria, serralheria). "
            "Leia o texto abaixo e devolva UM título, e nada além dele.\n"
            "Regras: no máximo 80 caracteres; em português; use as palavras que um "
            "vendedor digitaria na busca (ex.: 'como responder tá caro', "
            "'orçamento', 'desconto', 'cliente sumiu'); sem emoji; sem hashtag; "
            "sem aspas; sem ponto final; não invente fato que não esteja no texto.\n\n"
            f"TEXTO:\n{chr(10).join(linhas[:6])}"
        )
        try:
            corpo = json.dumps(
                {
                    "model": "groq/compound-mini",
                    "temperature": 0.3,
                    "max_tokens": 120,
                    "messages": [{"role": "user", "content": pedido}],
                }
            ).encode("utf-8")
            req = urllib.request.Request(
                "https://api.groq.com/openai/v1/chat/completions",
                data=corpo,
                headers={
                    "Authorization": f"Bearer {chave}",
                    "Content-Type": "application/json",
                    # Sem User-Agent proprio o Groq devolve 403: a borda dele
                    # barra "Python-urllib". A mesma chamada por curl passa.
                    "User-Agent": "VendaNaObra-Distribuidor/1.0",
                },
            )
            with urllib.request.urlopen(req, timeout=45) as r:
                resp = json.load(r)
            bruto = resp["choices"][0]["message"]["content"].strip()
            bruto = bruto.strip('"').split("\n")[0].strip().rstrip(".")
            if 12 <= len(bruto) <= 100:
                return bruto[0].upper() + bruto[1:]  # o modelo as vezes volta minusculo
        except Exception as e:  # a falta de titulo nao pode travar a publicacao
            print(f"  (Groq indisponivel, usando extracao: {e})")

    # Extracao: a primeira frase util ja e o gancho, que e o que o Diego escreve
    # pensando em prender. Corta na pontuacao para nao levar meia ideia.
    frase = linhas[0]
    if len(frase) > 100:
        pedaco = re.split(r"(?<=[.!?])\s", frase)[0]
        frase = pedaco if 12 <= len(pedaco) <= 100 else frase[:97].rsplit(" ", 1)[0] + "..."
    return frase


def montar_descricao(legenda: str, permalink: str) -> str:
    linhas = _linhas_uteis(legenda)
    corpo = "\n\n".join(linhas[:5])
    return (
        f"{corpo}\n\n"
        "—\n"
        "Descubra em 3 minutos onde a sua venda está travando:\n"
        f"{LINK_RAIOX}\n\n"
        "Diego Moraes — Venda na Obra\n"
        "Método comercial para quem vende esquadria, vidro e material de construção "
        "para arquitetos, construtoras e cliente final.\n\n"
        f"Publicado também no Instagram: {permalink}\n\n"
        "#Shorts #vendas #esquadrias #construcaocivil"
    )


def montar_tags(legenda: str) -> list[str]:
    achadas = [t.lower() for t in re.findall(r"#(\w+)", legenda or "")]
    tags, vistas = [], set()
    for t in TAGS_FIXAS + achadas:
        if t not in vistas:
            vistas.add(t)
            tags.append(t)
    return tags[:15]


# --------------------------------------------------------------------------- #
# YouTube
# --------------------------------------------------------------------------- #
def credenciais_youtube():
    from google.oauth2.credentials import Credentials

    bruto = os.environ.get("YT_TOKEN", "").strip()
    if bruto:
        return Credentials.from_authorized_user_info(json.loads(bruto))

    local = pathlib.Path(
        os.environ.get(
            "YT_TOKEN_ARQUIVO",
            r"C:\Users\NOTE\Desktop\Perffec\Claude\token_youtube_vendanaobra.json",
        )
    )
    if not local.exists():
        sys.exit("Sem credencial do YouTube (YT_TOKEN ou arquivo local).")
    return Credentials.from_authorized_user_file(str(local))


def subir_youtube(caminho: pathlib.Path, titulo: str, descricao: str, tags: list[str]) -> str:
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload

    yt = build("youtube", "v3", credentials=credenciais_youtube())

    # Trava de seguranca: token errado publica no canal errado, e isso ja
    # aconteceu uma vez neste projeto (o @crmnaobra apareceu no lugar).
    canal = yt.channels().list(part="id", mine=True).execute()["items"][0]["id"]
    if canal != YT_CANAL:
        sys.exit(f"Token aponta para o canal {canal}, nao para o @vendanaobra.")

    corpo = {
        "snippet": {
            "title": titulo[:100],
            "description": descricao[:4900],
            "tags": tags,
            "categoryId": YT_CATEGORIA,
            "defaultLanguage": "pt-BR",
            "defaultAudioLanguage": "pt-BR",
        },
        "status": {"privacyStatus": "public", "selfDeclaredMadeForKids": False},
    }
    midia = MediaFileUpload(str(caminho), chunksize=-1, resumable=True, mimetype="video/mp4")
    req = yt.videos().insert(part="snippet,status", body=corpo, media_body=midia)

    resposta = None
    while resposta is None:
        _, resposta = req.next_chunk()
    return resposta["id"]


# --------------------------------------------------------------------------- #
def carregar_estado() -> dict:
    if ESTADO.exists():
        return json.loads(ESTADO.read_text(encoding="utf-8"))
    return {}


def gravar_estado(estado: dict) -> None:
    ESTADO.write_text(json.dumps(estado, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--ensaio", action="store_true", help="mostra sem publicar")
    p.add_argument("--limite", type=int, default=1, help="quantos por execucao")
    p.add_argument("--dias", type=int, default=45, help="janela de coleta")
    p.add_argument("--id", help="forcar um id de midia do Instagram")
    p.add_argument(
        "--ordem",
        choices=["novo", "antigo"],
        default="novo",
        help="'novo' (padrao) publica o Reel mais recente primeiro",
    )
    args = p.parse_args()

    estado = carregar_estado()
    reels = coletar(args.dias)
    if args.id:
        reels = [m for m in reels if m["id"] == args.id]

    # Do mais NOVO para o mais antigo (05/09/2026, corrigindo o desenho inicial).
    # A primeira versao ia do mais antigo para o mais novo, para deixar uma linha
    # do tempo bonita no perfil — e com 21 Reels de acervo na frente, o Reel de
    # HOJE so chegaria ao YouTube dez dias depois. Quem publica espera ver o
    # video do dia no ar no mesmo dia; ordem do acervo ninguem repara. O acervo
    # continua escoando, andando para tras.
    pendentes = [m for m in reels if m["id"] not in estado]
    if args.ordem == "antigo":
        pendentes = pendentes[::-1]

    # Quanto ja saiu HOJE (UTC), lido do proprio estado: o runner e descartavel
    # e nao tem memoria entre execucoes.
    hoje = datetime.now(timezone.utc).date().isoformat()
    saiu_hoje = sum(
        1
        for v in estado.values()
        if v.get("distribuido_em", "").startswith(hoje) and v.get("youtube")
    )
    resta = max(TETO_DIA - saiu_hoje, 0)

    print(
        f"{len(reels)} Reels na janela de {args.dias} dias · {len(pendentes)} ainda nao "
        f"distribuidos · {saiu_hoje}/{TETO_DIA} publicados hoje"
    )
    if not pendentes:
        print("Nada a fazer.")
        return
    if resta == 0:
        print(f"Teto diario de {TETO_DIA} atingido (cota da API). Volta na proxima rodada.")
        return

    for midia in pendentes[: min(args.limite, resta)]:
        legenda = midia.get("caption") or ""
        titulo = titulo_para_busca(legenda)
        print(f"\n[{midia['timestamp'][:10]}] {midia['permalink']}")

        if titulo is None:
            print("  pulado: legenda sem texto, nao da titulo de busca")
            if not args.ensaio:
                estado[midia["id"]] = {"pulado": "sem legenda"}
                gravar_estado(estado)
            continue

        descricao = montar_descricao(legenda, midia["permalink"])
        tags = montar_tags(legenda)
        print(f"  titulo: {titulo}")
        print(f"  tags:   {', '.join(tags[:6])}...")

        if args.ensaio:
            print("  (ensaio: nada foi publicado)")
            continue

        with tempfile.TemporaryDirectory() as tmp:
            destino = pathlib.Path(tmp) / "reel.mp4"
            urllib.request.urlretrieve(midia["media_url"], destino)
            print(f"  baixado: {destino.stat().st_size / 1e6:.1f} MB")
            video_id = subir_youtube(destino, titulo, descricao, tags)

        print(f"  YouTube: https://youtu.be/{video_id}")
        estado[midia["id"]] = {
            "youtube": video_id,
            "titulo": titulo,
            "permalink": midia["permalink"],
            "publicado_ig": midia["timestamp"],
            "distribuido_em": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        }
        gravar_estado(estado)


if __name__ == "__main__":
    main()

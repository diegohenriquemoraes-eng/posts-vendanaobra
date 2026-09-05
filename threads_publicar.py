"""Publica no Threads do @vendanaobra o que o Instagram NAO leva.

POR QUE ISSO EXISTE, E O QUE ELE NAO FAZ
----------------------------------------
O perfil do Threads ja existe (@vendanaobra, id 28496863436574063, 164
seguidores) e o Instagram JA espelha os Reels la sozinho. Entao republicar o
Reel pela API seria duplicar o que ja acontece — este script nao faz isso.

O que falta no Threads e o que so ele permite: **link**. No Instagram o link na
legenda nao clica e ainda derruba entrega; no Threads clica. Entao a esteira
daqui e o BLOG: uma resposta por dia, com o link do artigo carimbado com UTM.
E conteudo que ja existe, ja foi escrito na voz do Diego e nao custa gravacao.

A FONTE
-------
`https://vendanaobra.com.br/llms.txt`, que o proprio site gera e ja traz, por
artigo, titulo + URL + o campo `resposta` (2 a 4 frases autossuficientes,
escritas para a IA citar). Ler de la evita duplicar o parser do blog e nao
depende de token nenhum.

RECICLAGEM
----------
Sao 20 artigos e nasce 1 por semana; a 1 post/dia isso seca. Depois de esgotar
os ineditos, o script volta ao artigo publicado ha mais tempo, respeitando 90
dias de intervalo, e pede ao Groq um texto NOVO a partir do mesmo artigo — o
angulo muda, entao nao e o mesmo post outra vez.

TOKEN
-----
Token de longa duracao do gerador do app (60 dias). `--renovar` estende por mais
60 (a API so aceita renovar depois de 24 h de vida). O repositorio e PUBLICO:
o token vive em secret, nunca em arquivo versionado.

Uso:
    python threads_publicar.py --ensaio
    python threads_publicar.py
    python threads_publicar.py --renovar
"""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import re
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone

AQUI = pathlib.Path(__file__).parent
ESTADO = AQUI / "threads_publicados.json"

API = "https://graph.threads.net/v1.0"
LLMS = "https://vendanaobra.com.br/llms.txt"
DIAS_PARA_RECICLAR = 90
LIMITE_THREADS = 500  # caracteres por post


def token() -> str:
    t = os.environ.get("THREADS_TOKEN", "").strip()
    if t:
        return t
    local = pathlib.Path(
        r"C:\Users\NOTE\Desktop\Perffec\Claude\threads_token_vendanaobra.txt"
    )
    if local.exists():
        return local.read_text(encoding="utf-8").strip()
    sys.exit("Sem THREADS_TOKEN.")


def _abrir(url: str, dados: bytes | None = None) -> dict:
    req = urllib.request.Request(
        url,
        data=dados,
        headers={"User-Agent": "VendaNaObra-Threads/1.0"},
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)


# --------------------------------------------------------------------------- #
def artigos() -> list[dict]:
    """Titulo, url e resposta de cada artigo, lidos do /llms.txt do site."""
    req = urllib.request.Request(LLMS, headers={"User-Agent": "VendaNaObra/1.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        texto = r.read().decode("utf-8")

    saida = []
    for linha in texto.split("\n"):
        m = re.match(r"^- \[(.+?)\]\((https://[^)]+/blog/[^)]+)\): (.+)$", linha.strip())
        if not m:
            continue
        titulo, url, resto = m.groups()
        resposta = re.sub(r"\s*\(categoria:.*$", "", resto).strip()
        saida.append(
            {
                "slug": url.rstrip("/").split("/")[-1],
                "titulo": titulo,
                "url": url,
                "resposta": resposta,
            }
        )
    return saida


def com_utm(url: str) -> str:
    return url + ("&" if "?" in url else "?") + urllib.parse.urlencode(
        {"utm_source": "threads", "utm_medium": "post", "utm_campaign": "blog"}
    )


def escrever_post(art: dict, reciclado: bool) -> str:
    """Texto do post. Groq quando houver chave; senao, monta pela resposta."""
    link = com_utm(art["url"])
    chave = os.environ.get("GROQ_API_KEY", "").strip()

    if chave:
        angulo = (
            "Escreva de um ANGULO DIFERENTE do obvio: comece por um erro comum, "
            "por um numero ou por uma pergunta direta. "
            if reciclado
            else ""
        )
        pedido = (
            "Você escreve posts de Threads para um perfil brasileiro sobre VENDAS na "
            "construção civil (esquadrias, vidraçaria, serralheria). O leitor é vendedor "
            "ou dono de empresa do setor.\n"
            f"{angulo}"
            "Escreva UM post e nada além dele.\n"
            "Regras: no máximo 380 caracteres; português do Brasil; tom direto e seco, "
            "sem entusiasmo de anúncio; 2 a 4 frases curtas em linhas separadas; "
            "sem emoji; sem hashtag; sem aspas; não invente número nem caso que não "
            "esteja no texto; NÃO inclua link (ele é acrescentado depois).\n\n"
            f"ARTIGO: {art['titulo']}\n{art['resposta']}"
        )
        try:
            corpo = json.dumps(
                {
                    "model": "groq/compound-mini",
                    "temperature": 0.6 if reciclado else 0.4,
                    "max_tokens": 300,
                    "messages": [{"role": "user", "content": pedido}],
                }
            ).encode("utf-8")
            req = urllib.request.Request(
                "https://api.groq.com/openai/v1/chat/completions",
                data=corpo,
                headers={
                    "Authorization": f"Bearer {chave}",
                    "Content-Type": "application/json",
                    # Sem User-Agent proprio o Groq devolve 403 para Python.
                    "User-Agent": "VendaNaObra-Threads/1.0",
                },
            )
            with urllib.request.urlopen(req, timeout=45) as r:
                resp = json.load(r)
            texto = resp["choices"][0]["message"]["content"].strip().strip('"')
            # O modelo devolve espaco no fim da linha (quebra de markdown), que
            # no Threads vira sujeira visivel.
            texto = "\n".join(l.rstrip() for l in texto.split("\n"))
            if 40 <= len(texto) <= 400:
                return f"{texto}\n\n{link}"
        except Exception as e:
            print(f"  (Groq indisponivel, montando pela resposta: {e})")

    # Reserva: a propria resposta do artigo, cortada em frase inteira.
    corpo = art["resposta"]
    teto = LIMITE_THREADS - len(link) - 4
    if len(corpo) > teto:
        frases = re.split(r"(?<=[.!?])\s+", corpo)
        corpo, junto = "", ""
        for f in frases:
            if len(junto) + len(f) + 1 > teto:
                break
            junto = (junto + " " + f).strip()
        corpo = junto or art["titulo"]
    return f"{corpo}\n\n{link}"


# --------------------------------------------------------------------------- #
def publicar(texto: str) -> str:
    tok = token()
    criar = urllib.parse.urlencode(
        {"media_type": "TEXT", "text": texto, "access_token": tok}
    ).encode()
    caixa = _abrir(f"{API}/me/threads", criar)["id"]
    publicar_ = urllib.parse.urlencode(
        {"creation_id": caixa, "access_token": tok}
    ).encode()
    return _abrir(f"{API}/me/threads_publish", publicar_)["id"]


def renovar() -> None:
    tok = token()
    r = _abrir(
        f"{API}/refresh_access_token?"
        + urllib.parse.urlencode(
            {"grant_type": "th_refresh_token", "access_token": tok}
        )
    )
    novo, dias = r["access_token"], int(r.get("expires_in", 0)) // 86400

    # Quem decide onde gravar e o AMBIENTE, nao a existencia do caminho:
    # `pathlib.Path(r"C:\...")` no Linux vira nome relativo e `.parent` e ".",
    # que existe sempre — na primeira rodada na nuvem isso gravou um arquivo
    # chamado "C:\Users\..." dentro do runner e o token novo se perdeu.
    if not os.environ.get("GITHUB_ACTIONS"):
        destino = pathlib.Path(
            r"C:\Users\NOTE\Desktop\Perffec\Claude\threads_token_vendanaobra.txt"
        )
        destino.write_text(novo, encoding="utf-8")
        print(f"Token renovado por {dias} dias e gravado em {destino.name}.")
    else:
        # Na nuvem nao ha onde gravar: o repo e publico. Quem grava e o passo do
        # workflow que atualiza o secret.
        print(f"::add-mask::{novo}")
        # GITHUB_OUTPUT e um arquivo ACUMULATIVO: sobrescrever apaga o que os
        # passos anteriores escreveram.
        saida = pathlib.Path(os.environ.get("GITHUB_OUTPUT", "saida_token.txt"))
        with saida.open("a", encoding="utf-8") as f:
            f.write(f"token={novo}\n")
        print(f"Token renovado por {dias} dias.")


# --------------------------------------------------------------------------- #
def carregar() -> dict:
    return json.loads(ESTADO.read_text(encoding="utf-8")) if ESTADO.exists() else {}


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--ensaio", action="store_true")
    p.add_argument("--renovar", action="store_true")
    args = p.parse_args()

    if args.renovar:
        renovar()
        return

    estado = carregar()
    lista = artigos()
    if not lista:
        sys.exit("Nenhum artigo lido do /llms.txt — o formato mudou?")

    agora = datetime.now(timezone.utc)

    def visto_em(a: dict) -> datetime:
        reg = estado.get(a["slug"])
        if not reg:
            return datetime.min.replace(tzinfo=timezone.utc)
        return datetime.fromisoformat(reg["em"])

    lista.sort(key=visto_em)
    escolhido = lista[0]
    reciclado = escolhido["slug"] in estado

    if reciclado and agora - visto_em(escolhido) < timedelta(days=DIAS_PARA_RECICLAR):
        print(
            f"Nada devido: o artigo mais antigo saiu ha "
            f"{(agora - visto_em(escolhido)).days} dias (teto: {DIAS_PARA_RECICLAR})."
        )
        return

    texto = escrever_post(escolhido, reciclado)
    print(f"[{'reciclado' if reciclado else 'inedito'}] {escolhido['titulo']}")
    print("-" * 60)
    print(texto)
    print("-" * 60, f"{len(texto)} caracteres")

    if args.ensaio:
        print("(ensaio: nada foi publicado)")
        return
    if len(texto) > LIMITE_THREADS:
        sys.exit("Texto passou de 500 caracteres; nao publicado.")

    post_id = publicar(texto)
    print(f"Publicado: {post_id}")
    estado[escolhido["slug"]] = {
        "em": agora.isoformat(timespec="seconds"),
        "post": post_id,
        "titulo": escolhido["titulo"],
    }
    ESTADO.write_text(json.dumps(estado, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()

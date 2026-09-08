"""Publica no LinkedIn de Diego Moraes um artigo do blog por dia útil.

POR QUE O LINKEDIN, e por que ele é diferente dos outros canais
---------------------------------------------------------------
No Instagram e no TikTok quem está do outro lado é o VENDEDOR. No LinkedIn está
o dono da vidraçaria, o gerente da construtora, o industrial do alumínio — quem
compra consultoria, e não e-book de R$ 97. É o único canal do plano capaz de
gerar contrato em vez de venda de baixo ticket. Por isso o texto aqui é escrito
para decisor, não para quem executa.

Dias ÚTEIS só: o LinkedIn é rede de trabalho e post de sábado morre. Não é
preciosismo — é o mesmo motivo de o Reel do Instagram sair 9h e não 3h.

⚠ O TOKEN VENCE EM 60 DIAS E NÃO TEM RENOVAÇÃO AUTOMÁTICA
----------------------------------------------------------
O LinkedIn só entrega `refresh_token` para app de parceiro aprovado; o nosso é
autosserviço, então o que vem é um access token de 60 dias e ponto. Diferente do
Threads, que se renova sozinho todo dia, aqui **o Diego refaz o login a cada dois
meses**. Para isso não morrer em silêncio, o script avisa quando faltam 7 dias.

Uso:
    python linkedin_publicar.py --ensaio
    python linkedin_publicar.py
    python linkedin_publicar.py --validade      # quantos dias faltam do token
"""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone

AQUI = pathlib.Path(__file__).parent
ESTADO = AQUI / "linkedin_publicados.json"
LLMS = "https://vendanaobra.com.br/llms.txt"
API = "https://api.linkedin.com/rest/posts"
# A versão vai no cabeçalho e é obrigatória. Ela EXPIRA: a documentação atual
# cita 202411 e em 05/09/2026 essa já devolvia 426 NONEXISTENT_VERSION. As ativas
# hoje, sondadas uma a uma, são 202603, 202606 e 202608 (a 202609 ainda não
# existe). Quando 426 voltar, sondar de novo subindo o mês.
VERSAO = "202608"
DIAS_PARA_RECICLAR = 120
AVISAR_FALTANDO = 7  # dias


def credenciais() -> tuple[str, str]:
    """(token, urn do autor). Env na nuvem, arquivo no PC."""
    tok = os.environ.get("LINKEDIN_TOKEN", "").strip()
    urn = os.environ.get("LINKEDIN_URN", "").strip()
    if tok and urn:
        return tok, urn
    base = pathlib.Path(r"C:\Users\NOTE\Desktop\Perffec\Claude")
    a, b = base / "linkedin_token.json", base / "linkedin_urn.txt"
    if not (a.exists() and b.exists()):
        sys.exit("Sem LINKEDIN_TOKEN/LINKEDIN_URN.")
    return json.loads(a.read_text(encoding="utf-8"))["access_token"], b.read_text().strip()


def artigos() -> list[dict]:
    req = urllib.request.Request(LLMS, headers={"User-Agent": "VendaNaObra/1.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        texto = r.read().decode("utf-8")
    saida = []
    for linha in texto.split("\n"):
        m = re.match(r"^- \[(.+?)\]\((https://[^)]+/blog/[^)]+)\): (.+)$", linha.strip())
        if not m:
            continue
        titulo, url, resto = m.groups()
        saida.append(
            {
                "slug": url.rstrip("/").split("/")[-1],
                "titulo": titulo,
                "url": url,
                "resposta": re.sub(r"\s*\(categoria:.*$", "", resto).strip(),
            }
        )
    return saida


def com_utm(url: str) -> str:
    return url + ("&" if "?" in url else "?") + urllib.parse.urlencode(
        {"utm_source": "linkedin", "utm_medium": "post", "utm_campaign": "blog"}
    )


def escrever(art: dict, reciclado: bool) -> str:
    link = com_utm(art["url"])
    chave = os.environ.get("GROQ_API_KEY", "").strip()
    if chave:
        pedido = (
            "Você escreve posts de LinkedIn para Diego Moraes, que trabalha com estruturação "
            "comercial na construção civil. Quem lê é DONO de vidraçaria, serralheria ou "
            "fábrica de esquadrias, gerente de construtora ou industrial do alumínio — "
            "decisor, não executor.\n"
            + ("Escreva de um ângulo diferente do óbvio: comece por um erro caro, por uma "
               "conta ou por uma pergunta direta. " if reciclado else "")
            + "Escreva UM post e nada além dele.\n"
            "Regras: entre 500 e 900 caracteres; português do Brasil; primeira linha curta e "
            "forte, porque é a única que aparece antes do 'ver mais'; frases curtas em linhas "
            "separadas; tom seco, de quem opera, sem entusiasmo de anúncio; sem emoji; sem "
            "hashtag; sem aspas; não invente número nem caso que não esteja no texto; "
            "NÃO inclua link (é acrescentado depois).\n\n"
            f"ARTIGO: {art['titulo']}\n{art['resposta']}"
        )
        try:
            corpo = json.dumps(
                {
                    "model": "groq/compound-mini",
                    "temperature": 0.6 if reciclado else 0.4,
                    "max_tokens": 500,
                    "messages": [{"role": "user", "content": pedido}],
                }
            ).encode("utf-8")
            req = urllib.request.Request(
                "https://api.groq.com/openai/v1/chat/completions",
                data=corpo,
                headers={
                    "Authorization": f"Bearer {chave}",
                    "Content-Type": "application/json",
                    # Sem User-Agent próprio o Groq devolve 403 para Python.
                    "User-Agent": "VendaNaObra-LinkedIn/1.0",
                },
            )
            with urllib.request.urlopen(req, timeout=45) as r:
                resp = json.load(r)
            t = resp["choices"][0]["message"]["content"].strip().strip('"')
            t = "\n".join(l.rstrip() for l in t.split("\n"))
            if 200 <= len(t) <= 1200:
                return f"{t}\n\n{link}"
        except Exception as e:
            print(f"  (Groq indisponivel, usando a resposta do artigo: {e})")
    return f"{art['titulo']}\n\n{art['resposta']}\n\n{link}"


def publicar(texto: str) -> str:
    tok, urn = credenciais()
    corpo = json.dumps(
        {
            "author": urn,
            "commentary": texto,
            "visibility": "PUBLIC",
            "distribution": {
                "feedDistribution": "MAIN_FEED",
                "targetEntities": [],
                "thirdPartyDistributionChannels": [],
            },
            "lifecycleState": "PUBLISHED",
            "isReshareDisabledByAuthor": False,
        }
    ).encode("utf-8")
    req = urllib.request.Request(
        API,
        data=corpo,
        headers={
            "Authorization": f"Bearer {tok}",
            "Content-Type": "application/json",
            "LinkedIn-Version": VERSAO,
            "X-Restli-Protocol-Version": "2.0.0",
        },
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.headers.get("x-restli-id") or r.headers.get("x-linkedin-id") or "publicado"


def dias_de_token() -> int | None:
    """Quantos dias faltam, a partir de quando o arquivo do token foi escrito."""
    p = pathlib.Path(r"C:\Users\NOTE\Desktop\Perffec\Claude\linkedin_token.json")
    validade = os.environ.get("LINKEDIN_TOKEN_ATE", "").strip()
    if validade:
        return (datetime.fromisoformat(validade).date() - datetime.now(timezone.utc).date()).days
    if p.exists():
        nasceu = datetime.fromtimestamp(p.stat().st_mtime, timezone.utc)
        expira = nasceu + timedelta(days=json.loads(p.read_text(encoding="utf-8"))["expires_in"] // 86400)
        return (expira.date() - datetime.now(timezone.utc).date()).days
    return None


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--ensaio", action="store_true")
    p.add_argument("--validade", action="store_true")
    p.add_argument("--forcar", action="store_true", help="publica mesmo no fim de semana")
    args = p.parse_args()

    faltam = dias_de_token()
    if args.validade:
        print(f"faltam {faltam} dias" if faltam is not None else "validade desconhecida")
        return
    if faltam is not None and faltam <= AVISAR_FALTANDO:
        print(f"::warning::O token do LinkedIn vence em {faltam} dias e NAO se renova sozinho.")

    hoje = datetime.now(timezone.utc)
    if hoje.weekday() >= 5 and not args.forcar:
        print("Fim de semana: o LinkedIn e rede de trabalho e post de sabado morre.")
        return

    estado = json.loads(ESTADO.read_text(encoding="utf-8")) if ESTADO.exists() else {}
    lista = artigos()
    if not lista:
        sys.exit("Nenhum artigo lido do /llms.txt — o formato mudou?")

    def visto(a: dict) -> datetime:
        reg = estado.get(a["slug"])
        return datetime.fromisoformat(reg["em"]) if reg else datetime.min.replace(tzinfo=timezone.utc)

    lista.sort(key=visto)
    escolhido = lista[0]
    reciclado = escolhido["slug"] in estado
    if reciclado and hoje - visto(escolhido) < timedelta(days=DIAS_PARA_RECICLAR):
        print(f"Nada devido: o mais antigo saiu ha {(hoje - visto(escolhido)).days} dias.")
        return

    texto = escrever(escolhido, reciclado)
    print(f"[{'reciclado' if reciclado else 'inedito'}] {escolhido['titulo']}")
    print("-" * 60)
    print(texto)
    print("-" * 60, f"{len(texto)} caracteres")
    if args.ensaio:
        print("(ensaio: nada foi publicado)")
        return

    try:
        pid = publicar(texto)
    except urllib.error.HTTPError as e:
        sys.exit(f"LinkedIn recusou ({e.code}): {e.read().decode()[:400]}")
    print(f"Publicado: {pid}")
    estado[escolhido["slug"]] = {
        "em": hoje.isoformat(timespec="seconds"),
        "post": pid,
        "titulo": escolhido["titulo"],
    }
    ESTADO.write_text(json.dumps(estado, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()

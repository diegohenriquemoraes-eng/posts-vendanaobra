"""Assessoria de imprensa do setor — release do artigo para quem publica notícia.

POR QUE (05/09/2026)
--------------------
O vigia das IAs voltou **0 de 25**: quando um assistente responde uma pergunta
do mercado, ninguém cita o Venda na Obra. E o Google mostrou 0 impressão na
semana. Falta AUTORIDADE CITÁVEL — link e menção de fora —, e não mais um lugar
para postar. Portal do setor vive de conteúdo de terceiros e fala com o público
inteiro do Diego todo dia: é o caminho mais curto para isso.

DUAS METADES, E A SEGUNDA É A DIFÍCIL
-------------------------------------
Mandar release é fácil. Ter para QUEM mandar é que é trabalho — e chutar
endereço é spam, não assessoria. Por isso o script tem os dois modos:

    --descobrir   visita a página de contato dos veículos do setor e guarda
                  SÓ o e-mail que estiver publicado lá. Nada é inventado.
    --enviar      monta o release do artigo mais novo e manda para quem está
                  na lista, uma vez por veículo por release.

⚠ O envio sai do Gmail do Diego (API oficial, escopo `gmail.send`), com o nome
dele. Isso é de propósito: jornalista responde a pessoa, não a caixa de marca.
E o volume é baixo — uma dezena por semana —, dentro do que o Gmail comporta
sem estragar a reputação do endereço. Este script NÃO serve para disparo frio
em massa; para isso é preciso domínio separado e provedor de envio.

Uso:
    python imprensa.py --descobrir
    python imprensa.py --enviar --ensaio
    python imprensa.py --enviar
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import pathlib
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from email.message import EmailMessage

AQUI = pathlib.Path(__file__).parent
CONTATOS = AQUI / "imprensa_contatos.json"
ESTADO = AQUI / "imprensa_enviados.json"
LLMS = "https://vendanaobra.com.br/llms.txt"

# Veículos que falam com o público do Venda na Obra. A lista de DOMÍNIOS é
# curada à mão; os e-mails, não — eles só entram se estiverem publicados.
VEICULOS = [
    ("Abravidro", "abravidro.org.br"),
    ("AFEAL", "afeal.com.br"),
    ("AECweb", "aecweb.com.br"),
    ("Portal Metálica", "metalica.com.br"),
    ("ABAL", "abal.org.br"),
    ("Portal VGV", "portalvgv.com.br"),
    ("Massa Cinzenta", "cimentoitambe.com.br"),
]
CAMINHOS = ["/contato", "/contato/", "/fale-conosco", "/fale-conosco/", "/contact", "/"]

# Endereço genérico de plataforma não é redação: não adianta mandar release
# para o suporte do WordPress ou para o e-mail do certificado SSL.
LIXO = re.compile(
    r"(sentry|wixpress|example|godaddy|hostgator|locaweb|@2x|\.png|\.jpg|no-?reply|"
    r"abuse@|postmaster@|webmaster@|privacy@|dpo@|lgpd|encarregado|juridico|"
    r"financeiro|cobranca|rh@|vagas@|curriculo|eventos@|comercial@|anuncie)",
    re.I,
)
# Caixa de redacao vem antes de caixa geral: release para "eventos@" ou para o
# encarregado de LGPD nao e assessoria, e "encarregado.lgpd@" foi o que a
# primeira rodada trouxe de um dos veiculos.
REDACAO = re.compile(r"^(imprensa|redacao|redação|comunicacao|jornalismo|noticias|pauta|editor)", re.I)


def buscar(url: str) -> str:
    req = urllib.request.Request(
        url, headers={"User-Agent": "Mozilla/5.0 (compatible; VendaNaObra/1.0)"}
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", errors="ignore")


def descobrir() -> None:
    contatos = json.loads(CONTATOS.read_text(encoding="utf-8")) if CONTATOS.exists() else {}
    for nome, dominio in VEICULOS:
        if contatos.get(dominio, {}).get("emails"):
            print(f"{nome}: ja tem contato")
            continue
        achados: set[str] = set()
        for caminho in CAMINHOS:
            for esquema in ("https://www.", "https://"):
                try:
                    html = buscar(f"{esquema}{dominio}{caminho}")
                except Exception:
                    continue
                for e in re.findall(r"[\w.+-]+@[\w.-]+\.[a-zA-Z]{2,}", html):
                    e = e.lower()
                    if LIXO.search(e):
                        continue
                    # Só interessa e-mail DO veículo: contato@outrodominio é de
                    # anunciante ou de rodapé de terceiro.
                    if dominio.split(".")[0] in e.split("@")[1]:
                        achados.add(e)
                if achados:
                    break
            if achados:
                break
        ordenado = sorted(achados, key=lambda e: (0 if REDACAO.match(e) else 1, e))
        contatos[dominio] = {
            "nome": nome,
            "emails": ordenado[:2],
            "visto_em": datetime.now(timezone.utc).date().isoformat(),
        }
        print(f"{nome}: {ordenado[:2] or 'nada publicado'}")
    CONTATOS.write_text(json.dumps(contatos, ensure_ascii=False, indent=2), encoding="utf-8")


def artigo_mais_novo() -> dict:
    req = urllib.request.Request(LLMS, headers={"User-Agent": "VendaNaObra/1.0"})
    with urllib.request.urlopen(req, timeout=45) as r:
        texto = r.read().decode("utf-8")
    itens = []
    for linha in texto.split("\n"):
        m = re.match(r"^- \[(.+?)\]\((https://[^)]+/blog/[^)]+)\): (.+)$", linha.strip())
        if m:
            t, u, resto = m.groups()
            data = re.search(r"publicado em (\d{4}-\d{2}-\d{2})", resto)
            itens.append(
                {
                    "slug": u.rstrip("/").split("/")[-1],
                    "titulo": t,
                    "url": u,
                    "resposta": re.sub(r"\s*\(categoria:.*$", "", resto).strip(),
                    "data": data.group(1) if data else "",
                }
            )
    itens.sort(key=lambda x: x["data"], reverse=True)
    return itens[0]


def release(art: dict) -> tuple[str, str]:
    assunto = f"Sugestão de pauta: {art['titulo']}"
    # UTM no link do release: sem isso, o portal que publicar a materia traz
    # gente que chega como "direto", e a assessoria nunca prova que funcionou.
    link = art["url"] + ("&" if "?" in art["url"] else "?") + "utm_source=imprensa&utm_medium=release&utm_campaign=portais"
    corpo = f"""Olá,

Sou Diego Moraes, fundador da Perffec (esquadrias e vidro de alto padrão, em
Amparo/SP) e do Venda na Obra, onde publico material sobre o lado comercial do
setor — o que acontece depois que a esquadria está especificada e o orçamento
sai da fábrica.

Publiquei esta semana um material que talvez interesse ao público de vocês:

{art['titulo']}
{link}

{art['resposta']}

Fiquem à vontade para reproduzir no todo ou em parte, com crédito e link. Se
preferirem uma versão adaptada ao formato de vocês, ou dados e imagens em alta,
é só responder este e-mail que eu preparo.

Abraço,

Diego Moraes
Venda na Obra · vendanaobra.com.br
Perffec Esquadrias · Amparo/SP
"""
    return assunto, corpo


def enviar_gmail(para: str, assunto: str, corpo: str) -> str:
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build

    bruto = os.environ.get("GMAIL_TOKEN", "").strip()
    cred = (
        Credentials.from_authorized_user_info(json.loads(bruto))
        if bruto
        else Credentials.from_authorized_user_file(
            r"C:\Users\NOTE\Desktop\Perffec\Claude\token_gmail_vendanaobra.json"
        )
    )
    servico = build("gmail", "v1", credentials=cred)

    msg = EmailMessage()
    msg["To"] = para
    msg["Subject"] = assunto
    msg.set_content(corpo)
    cru = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    return servico.users().messages().send(userId="me", body={"raw": cru}).execute()["id"]


def enviar(ensaio: bool) -> None:
    if not CONTATOS.exists():
        sys.exit("Sem lista de contatos — rode --descobrir antes.")
    contatos = json.loads(CONTATOS.read_text(encoding="utf-8"))
    estado = json.loads(ESTADO.read_text(encoding="utf-8")) if ESTADO.exists() else {}

    art = artigo_mais_novo()
    assunto, corpo = release(art)
    print(f"Release: {art['titulo']}\n")

    destinos = [
        (d, dados["nome"], e)
        for d, dados in contatos.items()
        for e in dados.get("emails", [])
        if art["slug"] not in estado.get(e, [])
    ]
    if not destinos:
        print("Nenhum destino novo para este artigo.")
        return

    for dominio, nome, email in destinos:
        print(f"  -> {nome} <{email}>")
        if ensaio:
            continue
        try:
            enviar_gmail(email, assunto, corpo)
        except Exception as e:
            print(f"     falhou: {str(e)[:140]}")
            continue
        estado.setdefault(email, []).append(art["slug"])
        ESTADO.write_text(json.dumps(estado, ensure_ascii=False, indent=2), encoding="utf-8")

    if ensaio:
        print("\n--- release ---")
        print(corpo)
        print("(ensaio: nada foi enviado)")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--descobrir", action="store_true")
    p.add_argument("--enviar", action="store_true")
    p.add_argument("--ensaio", action="store_true")
    args = p.parse_args()
    if args.descobrir:
        descobrir()
    if args.enviar:
        enviar(args.ensaio)
    if not (args.descobrir or args.enviar):
        p.print_help()


if __name__ == "__main__":
    main()

# -*- coding: utf-8 -*-
"""CTA do dia: o 3o slide + a legenda que o reforca.

Regra (decidida em 21/07/2026; e-book acrescentado em 03/08/2026; Raio-X
virou o CTA dominante em 09/08/2026 — ver CLAUDE.md):
  - todo post tem um 3o slide de CTA, em fundo azul da marca;
  - o CTA do dia intercala numa ordem ciclica fixa, NUNCA repetindo dois dias
    seguidos:  seguir -> Raio-X -> e-book -> Raio-X -> Venda 10x -> Raio-X ->
    CRM -> seguir ... (7 posicoes, ver CICLO_CTA). A Venda Blindada saiu do
    ciclo: e vendida na trilha de e-mail do Raio-X (gargalo em Decisao/Oferta);
  - a rotacao tem memoria (estado_cta.json, gravado pelo publicar.py): avanca a
    partir da POSICAO do ultimo CTA publicado, entao um dia que falhe nao repete
    nem pula. E a posicao, nao o nome, porque "seguir" e "ebook" aparecem duas
    vezes no ciclo — buscar pelo nome sempre acharia a 1a ocorrencia e o ciclo
    ficaria preso num sub-loop, sem nunca chegar em Blindada e CRM;
  - a legenda usa o MESMO CTA do slide, para o post ficar coerente;
  - o tema da frase e escolhido depois de saber o CTA (ver publicar.py), para
    o conteudo puxar naturalmente para a chamada do dia.

Conversao de produto e por comment-to-DM: o slide traz uma explicacao breve do
produto e pede uma palavra (RAIOX / LIVRO / 10X / MAQUINA — palavra da Maquina
de Vendas, o CRM rebatizado em 12/08/2026; CRM segue ativa para posts
antigos); quem comenta recebe o
link no Direct — no Instagram o link so e clicavel no DM, nunca na legenda do
feed. Por ora o Diego responde a mao; depois liga a automacao nativa de
palavra-chave do Instagram. O CTA de seguir nao tem palavra nem link (e o post de
valor puro).
"""
from __future__ import annotations

# Ordem ciclica do CTA do dia. Nao reordenar sem querer mudar a sequencia.
#
# 7 posicoes (aprovado pelo Diego em 09/08/2026, substitui o ciclo com Venda
# Blindada): o Raio-X (diagnostico gratuito em vendanaobra.com.br/raio-x) vira o
# CTA dominante — 3 posicoes — porque captura e segmenta o lead; o proprio quiz
# recomenda o produto certo no final e por e-mail. A Venda Blindada saiu do
# ciclo: ela agora e vendida dentro da trilha de e-mail de quem tem gargalo em
# Decisao/Oferta. E-book segue como 1a compra; CRM segue por ser link direto.
CICLO_CTA = [
    "seguir",    # 0
    "raiox",     # 1
    "ebook",     # 2
    "raiox",     # 3
    "venda10x",  # 4
    "raiox",     # 5
    "crm",       # 6
]

# Cada CTA tem tres pecas:
#   slide   -> texto do 3o slide (blocos separados por \n\n viram linha em branco)
#   rodape  -> destino da acao, no rodape do slide
#   legenda -> reforco na legenda do post, casado com a frase
CTA = {
    "seguir": {
        "slide": "Gostou?\n\nSegue o @vendanaobra e vem vender mais na obra.",
        "rodape": "@vendanaobra",
        "legenda": (
            "Se isso fez sentido, segue o @vendanaobra — todo dia útil tem um "
            "card desses aqui, direto ao ponto sobre vender mais na obra."
        ),
    },
    "raiox": {
        "slide": (
            "Raio-X da Venda na Obra\n\n"
            "Descubra de graça, em 3 minutos, em qual etapa da venda a sua "
            "empresa está perdendo dinheiro. Nota de 0 a 100 + plano de ação.\n\n"
            "Comenta RAIOX que o link cai no seu Direct."
        ),
        "rodape": "@vendanaobra",
        "legenda": (
            "Você sabe ONDE a sua venda perde dinheiro — na atração, na proposta "
            "ou no fechamento?\n"
            "O Raio-X da Venda na Obra é o diagnóstico gratuito de 3 minutos: "
            "15 perguntas, nota de 0 a 100 e o plano de ação no seu e-mail.\n\n"
            "Comenta RAIOX aqui embaixo que eu te mando o link no seu Direct."
        ),
    },
    "ebook": {
        "slide": (
            "O Cliente Sumiu\n\n"
            "O e-book de R$ 19,90 com o protocolo D+1 · D+7 · D+30 para o "
            "orçamento enviado virar contrato assinado.\n\n"
            "Comenta LIVRO que o link cai no seu Direct."
        ),
        "rodape": "@vendanaobra",
        "legenda": (
            "Mandar o orçamento é o fim do seu trabalho e o começo do silêncio dele.\n"
            "“O Cliente Sumiu” é o protocolo D+1 · D+7 · D+30 que transforma "
            "orçamento enviado em contrato assinado — com 17 mensagens prontas "
            "para copiar. R$ 19,90.\n\n"
            "Comenta LIVRO aqui embaixo que eu te mando o link no seu Direct."
        ),
    },
    "venda-blindada": {
        "slide": (
            "Venda Blindada\n\n"
            "O contrato editável que fecha as brechas onde a esquadria perde "
            "dinheiro depois da venda.\n\n"
            "Comenta BLINDADA que o link cai no seu Direct."
        ),
        "rodape": "@vendanaobra",
        "legenda": (
            "Contrato genérico é onde a esquadria perde dinheiro depois da venda "
            "fechada.\nO Venda Blindada é o modelo editável que fecha essas brechas.\n\n"
            "Comenta BLINDADA aqui embaixo que eu te mando o link no seu Direct."
        ),
    },
    "venda10x": {
        "slide": (
            "Venda 10x\n\n"
            "O ao vivo semanal que transforma meta em rotina de execução comercial.\n\n"
            "Comenta 10X que o link cai no seu Direct."
        ),
        "rodape": "@vendanaobra",
        "legenda": (
            "Rotina comercial não nasce de motivação, nasce de cadência.\n"
            "É isso que eu destrincho toda quarta, 20h, no Venda 10x.\n\n"
            "Comenta 10X aqui embaixo que eu te mando o link no seu Direct."
        ),
    },
    "crm": {
        # Rebatizado em 12/08/2026: "CRM Venda na Obra" virou "Máquina de
        # Vendas" (a dor manda no nome; CRM é o qualificador técnico). A
        # chave interna continua "crm" — estado_cta.json e publicados.json
        # dependem dela. Palavra nova no Direct: MAQUINA (CRM segue ativa
        # para posts antigos).
        "slide": (
            "Máquina de Vendas\n\n"
            "O CRM da construção civil já configurado: funil pronto, follow-up "
            "automático e nenhum orçamento esquecido.\n\n"
            "Comenta MAQUINA que o link cai no seu Direct."
        ),
        "rodape": "@vendanaobra",
        "legenda": (
            "Orçamento enviado sem follow-up é venda morrendo em silêncio.\n"
            "A Máquina de Vendas é o CRM com o funil da construção civil pronto, "
            "follow-up automático e inteligência artificial — nenhum orçamento "
            "esquecido.\n\n"
            "Comenta MAQUINA aqui embaixo que eu te mando o link no seu Direct."
        ),
    },
}

# Qual produto o CTA do dia empurra (None = dia de valor/autoridade, sem produto).
# Serve para o publicar.py puxar uma frase que case com a dor do produto.
CTA_PRODUTO = {
    "seguir": None,
    "raiox": None,  # diagnostico gratuito serve a qualquer frase, sem viés de tema
    "ebook": "ebook",
    "venda-blindada": "venda-blindada",
    "venda10x": "venda10x",
    "crm": "crm",
}

# Qual produto responde a dor de cada tema, quando a frase nao manda o contrario.
# Usado para casar a frase com o CTA de produto do dia.
TEMA_PRODUTO = {
    "vendas": "venda10x",
    "emocional": "venda10x",
    "empreendedorismo": "venda10x",
    "metricas": "crm",
    "gestao": "crm",
    "ia": "crm",
}


def avancar_cta(estado: dict) -> tuple[int, str]:
    """CTA de hoje = o proximo do ciclo depois do ultimo publicado.

    Devolve `(indice, chave)`. Avanca pela POSICAO gravada, nunca pelo nome:
    'seguir' e 'ebook' aparecem duas vezes em CICLO_CTA, e `list.index()` so
    acha a 1a ocorrencia — o ciclo ficaria preso entre as posicoes 0-2 e
    Venda Blindada e CRM nunca sairiam.

    Estado sem `ultimo_indice` (formato antigo, ate 03/08/2026) cai no nome uma
    unica vez, so para migrar. Sem estado nenhum, comeca em 'seguir'.

    Como avanca a partir do ultimo *publicado*, um dia que falhe nao adianta o
    ciclo: o proximo dia pega o mesmo CTA que faltou, sem repetir nem pular.
    """
    i = estado.get("ultimo_indice")
    if not isinstance(i, int) or not 0 <= i < len(CICLO_CTA):
        ultimo = estado.get("ultimo_cta")
        i = CICLO_CTA.index(ultimo) if ultimo in CICLO_CTA else -1
    prox = (i + 1) % len(CICLO_CTA)
    return prox, CICLO_CTA[prox]


def produto_do_cta(cta_key: str) -> str | None:
    return CTA_PRODUTO.get(cta_key)


def produto_de(frase: dict) -> str:
    """Qual produto responde a dor desta frase."""
    return frase.get("produto") or TEMA_PRODUTO.get(frase["tema"], "venda10x")


def conteudo_cta(cta_key: str) -> dict:
    """Pecas do CTA (slide/rodape/legenda) para gerar imagem e legenda."""
    return CTA[cta_key]


def montar(frase: dict, cta_key: str) -> str:
    """Legenda do post: a frase + o reforco do CTA do dia (mesmo do slide)."""
    return f"{frase['texto']}\n\n{CTA[cta_key]['legenda']}"

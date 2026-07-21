# -*- coding: utf-8 -*-
"""CTA do dia: o 3o slide + a legenda que o reforca.

Regra (decidida em 21/07/2026, ver CLAUDE.md — substitui o esquema 80/20
anterior):
  - todo post tem um 3o slide de CTA, em fundo laranja da marca;
  - o CTA do dia intercala numa ordem ciclica fixa, NUNCA repetindo dois dias
    seguidos:  seguir -> Venda Blindada -> Venda 10x -> CRM -> seguir ...
  - a rotacao tem memoria (estado_cta.json, gravado pelo publicar.py): avanca a
    partir do ULTIMO CTA publicado, entao um dia que falhe nao repete nem pula;
  - a legenda usa o MESMO CTA do slide, para o post ficar coerente;
  - o tema da frase e escolhido depois de saber o CTA (ver publicar.py), para
    o conteudo puxar naturalmente para a chamada do dia.

Conversao de produto e por comment-to-DM: o slide traz uma explicacao breve do
produto e pede uma palavra (BLINDADA / 10X / CRM); quem comenta recebe o link no
Direct — no Instagram o link so e clicavel no DM, nunca na legenda do feed. Por
ora o Diego responde a mao; depois liga a automacao nativa de palavra-chave do
Instagram. O CTA de seguir nao tem palavra nem link (e o post de valor puro).
"""
from __future__ import annotations

# Ordem ciclica do CTA do dia. Nao reordenar sem querer mudar a sequencia.
CICLO_CTA = ["seguir", "venda-blindada", "venda10x", "crm"]

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
        "slide": (
            "CRM Venda na Obra\n\n"
            "Lead, follow-up e funil no mesmo lugar — o comercial fora da cabeça "
            "do vendedor.\n\n"
            "Comenta CRM que o link cai no seu Direct."
        ),
        "rodape": "@vendanaobra",
        "legenda": (
            "Se o seu funil vive na cabeça do vendedor e no WhatsApp, não é funil.\n"
            "O CRM Venda na Obra põe lead, follow-up e relatório no mesmo lugar.\n\n"
            "Comenta CRM aqui embaixo que eu te mando o link no seu Direct."
        ),
    },
}

# Qual produto o CTA do dia empurra (None = dia de valor/autoridade, sem produto).
# Serve para o publicar.py puxar uma frase que case com a dor do produto.
CTA_PRODUTO = {
    "seguir": None,
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


def avancar_cta(ultimo: str | None) -> str:
    """CTA de hoje = o proximo do ciclo depois do ultimo publicado.

    `None` (primeira vez, sem estado) comeca em 'seguir'. Como avanca a partir
    do ultimo *publicado*, um dia que falhe nao adianta o ciclo: o proximo dia
    pega o mesmo CTA que faltou, sem repetir nem pular.
    """
    if ultimo not in CICLO_CTA:
        return CICLO_CTA[0]
    return CICLO_CTA[(CICLO_CTA.index(ultimo) + 1) % len(CICLO_CTA)]


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

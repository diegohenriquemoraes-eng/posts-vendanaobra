# -*- coding: utf-8 -*-
"""Monta a legenda do post: a frase + o CTA.

Regra (decidida em 19/07/2026, ver CLAUDE.md):
  - todo post tem CTA;
  - 4 em cada 5 sao CTA leve (salvar / seguir / mandar para alguem), que e o
    que sustenta alcance — CTA de venda em todo post treina o publico a
    passar direto;
  - 1 em cada 5 e CTA de produto, escolhido pela dor da frase.

O CTA de produto NAO vira slide. O terceiro slide quebraria o formato
espelhado e derrubaria compartilhamento, que e a fonte de alcance aqui.
"""
from __future__ import annotations

# 1 CTA de produto a cada N posts
RITMO_OFERTA = 5

CTAS_LEVES = [
    "Salva esse aqui para lembrar na próxima negociação.",
    "Manda para o vendedor que precisa ler isso.",
    "Para vender mais, segue o @vendanaobra.",
    "Comenta aí: acontece na sua empresa?",
]

PRODUTOS = {
    "venda10x": (
        "Rotina comercial não nasce de motivação, nasce de cadência.\n"
        "É isso que eu destrincho toda quarta, 20h, no Venda 10x.\n"
        "Link na bio."
    ),
    "crm": (
        "Se o seu funil vive na cabeça do vendedor e no WhatsApp, não é funil.\n"
        "O CRM Venda na Obra põe lead, follow-up e relatório no mesmo lugar.\n"
        "Link na bio."
    ),
    "venda-blindada": (
        "Contrato genérico é onde a esquadria perde dinheiro depois da venda fechada.\n"
        "O Venda Blindada é o modelo editável que fecha essas brechas.\n"
        "Link na bio."
    ),
}

# Qual produto responde a dor de cada tema, quando a frase nao manda o contrario.
TEMA_PRODUTO = {
    "vendas": "venda10x",
    "emocional": "venda10x",
    "empreendedorismo": "venda10x",
    "metricas": "crm",
    "gestao": "crm",
    "ia": "crm",
}


# Nos dias de oferta os 3 produtos se revezam. Sem isso o Venda Blindada quase
# nao aparecia: a dor dele e estreita e raramente calhava de cair num dia desses.
RODIZIO = ["venda10x", "crm", "venda-blindada"]


def eh_dia_de_oferta(n_publicados: int) -> bool:
    return n_publicados % RITMO_OFERTA == RITMO_OFERTA - 1


def produto_do_dia(n_publicados: int) -> str:
    """Qual produto esta na vez, no dia de oferta de indice n_publicados."""
    return RODIZIO[(n_publicados // RITMO_OFERTA) % len(RODIZIO)]


def produto_de(frase: dict) -> str:
    """Qual produto responde a dor desta frase."""
    return frase.get("produto") or TEMA_PRODUTO.get(frase["tema"], "venda10x")


def escolher_cta(frase: dict, n_publicados: int) -> tuple[str, str]:
    """Devolve (texto_do_cta, rotulo) para o post de indice n_publicados."""
    if eh_dia_de_oferta(n_publicados):
        produto = produto_de(frase)
        return PRODUTOS[produto], f"produto:{produto}"

    # conta so os posts leves, senao o ritmo de 5 atropela o rodizio de 4 e
    # alguns CTAs quase nunca aparecem
    ja_ofertados = (n_publicados + 1) // RITMO_OFERTA
    indice = (n_publicados - ja_ofertados) % len(CTAS_LEVES)
    return CTAS_LEVES[indice], "leve"


def montar(frase: dict, n_publicados: int) -> tuple[str, str]:
    cta, rotulo = escolher_cta(frase, n_publicados)
    return f"{frase['texto']}\n\n{cta}", rotulo

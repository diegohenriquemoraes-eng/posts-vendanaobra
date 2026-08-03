# -*- coding: utf-8 -*-
"""CTA do dia: o 3o slide + a legenda que o reforca.

Regra (decidida em 21/07/2026, ver CLAUDE.md — substitui o esquema 80/20
anterior; e-book acrescentado ao ciclo em 03/08/2026):
  - todo post tem um 3o slide de CTA, em fundo laranja da marca;
  - o CTA do dia intercala numa ordem ciclica fixa, NUNCA repetindo dois dias
    seguidos:  seguir -> e-book -> Venda 10x -> seguir -> Venda Blindada ->
    e-book -> CRM -> seguir ... (7 posicoes, ver CICLO_CTA);
  - a rotacao tem memoria (estado_cta.json, gravado pelo publicar.py): avanca a
    partir da POSICAO do ultimo CTA publicado, entao um dia que falhe nao repete
    nem pula. E a posicao, nao o nome, porque "seguir" e "ebook" aparecem duas
    vezes no ciclo — buscar pelo nome sempre acharia a 1a ocorrencia e o ciclo
    ficaria preso num sub-loop, sem nunca chegar em Blindada e CRM;
  - a legenda usa o MESMO CTA do slide, para o post ficar coerente;
  - o tema da frase e escolhido depois de saber o CTA (ver publicar.py), para
    o conteudo puxar naturalmente para a chamada do dia.

Conversao de produto e por comment-to-DM: o slide traz uma explicacao breve do
produto e pede uma palavra (LIVRO / BLINDADA / 10X / CRM); quem comenta recebe o
link no Direct — no Instagram o link so e clicavel no DM, nunca na legenda do
feed. Por ora o Diego responde a mao; depois liga a automacao nativa de
palavra-chave do Instagram. O CTA de seguir nao tem palavra nem link (e o post de
valor puro).
"""
from __future__ import annotations

# Ordem ciclica do CTA do dia. Nao reordenar sem querer mudar a sequencia.
#
# 7 posicoes: 2x valor puro, 2x e-book, 1x cada produto caro. O e-book (R$ 19,90)
# tem peso dobrado por ser a porta de entrada — e o produto que fabrica comprador
# para os outros, e o de menor atrito. Os caros nunca caem em posicoes seguidas.
CICLO_CTA = [
    "seguir",          # 0
    "ebook",           # 1
    "venda10x",        # 2
    "seguir",          # 3
    "venda-blindada",  # 4
    "ebook",           # 5
    "crm",             # 6
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
        "slide": (
            "CRM Venda na Obra\n\n"
            "Controle total do setor comercial e dos clientes, com automações e "
            "inteligência artificial.\n\n"
            "Comenta CRM que o link cai no seu Direct."
        ),
        "rodape": "@vendanaobra",
        "legenda": (
            "Enquanto o concorrente controla o comercial no braço, você automatiza.\n"
            "O CRM Venda na Obra usa automações e inteligência artificial integrada "
            "para agilizar cada etapa da venda e te deixar na frente.\n\n"
            "Comenta CRM aqui embaixo que eu te mando o link no seu Direct."
        ),
    },
}

# Qual produto o CTA do dia empurra (None = dia de valor/autoridade, sem produto).
# Serve para o publicar.py puxar uma frase que case com a dor do produto.
CTA_PRODUTO = {
    "seguir": None,
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

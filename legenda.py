# -*- coding: utf-8 -*-
"""CTA do dia: o 3o slide + a legenda que o reforca.

Regra (decidida em 21/07/2026; e-book acrescentado em 03/08/2026; Raio-X
virou o CTA dominante em 09/08/2026; **ciclo refeito em 14/08/2026** para
cortar o excesso de CTA de produto — ver CLAUDE.md):
  - todo post tem um 3o slide de CTA, em fundo azul da marca;
  - o CTA do dia intercala numa ordem ciclica fixa de **14 posicoes**, com so
    **4 de produto (2 em 7)** e 10 de sinal (envio / pergunta / seguir):
    envio -> Raio-X -> pergunta -> seguir -> pergunta -> envio -> Venda 10x ->
    pergunta -> seguir -> envio -> Raio-X -> pergunta -> envio -> e-book ->
    volta ao inicio (ver CICLO_CTA). Produto nunca cai em posicoes seguidas.
    A Venda Blindada saiu do ciclo em 09/08 e o CRM saiu em 14/08: os dois sao
    vendidos na trilha de e-mail do Raio-X (gargalo em Decisao/Oferta);
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
# ---------------------------------------------------------------------------
# CICLO NOVO DE 14 POSICOES (14/08/2026) — substitui o de 7 posicoes com 6 CTAs
# de produto. Motivo, medido nos insights da conta:
#
#   - 6 dos 7 CTAs pediam palavra-chave de produto (RAIOX 3x, LIVRO, 10X,
#     MAQUINA). Somando os Reels, praticamente todo post do perfil pedia
#     alguma coisa — o perfil lia como loja e o publico parou de responder:
#     172 contas engajaram em 30 dias, de 9.296 seguidores (1,85%).
#   - Metricool 2026 (24,3 mi de posts): CTA pedindo comentario rende
#     +202,8% de comentarios; pergunta na legenda, +36,7%. E Mosseri
#     (22/01/2025) nomeou 3 sinais de ranqueamento — tempo de visualizacao,
#     curtidas e ENVIOS — sendo o envio o que mais pesa para alcancar quem
#     ainda nao segue. Nada disso e produzido por CTA de produto.
#   - O padrao do mercado confirma: Concer separa cirurgicamente (Reel = alcance
#     sem CTA; carrossel = CTA de palavra) e, em 72 legendas de perfis de
#     construcao civil e esquadria, CTA de Direct apareceu ZERO vezes — o
#     mecanismo do nicho e a pergunta aberta.
#
# Agora sao 4 CTAs de produto em 14 posicoes = exatamente 2 em 7, contra os 6
# em 7 de antes. As outras 10 posicoes se dividem em:
#   - "envio"    -> isca de compartilhamento no Direct (o sinal que mais falta:
#                   os Reels da conta estao com ZERO envios)
#   - "pergunta" -> isca de comentario, o mecanismo do nicho
#   - "seguir"   -> valor puro, sem pedir nada
#
# Produto nunca cai em posicoes seguidas. O Raio-X mantem o maior peso (2 das 4
# vagas de produto) porque captura e segmenta — o quiz e que recomenda o produto
# certo no resultado e nas trilhas de e-mail.
#
# ATENCAO — decisao de negocio embutida, conferir com o Diego: o CRM (Maquina de
# Vendas) SAIU do ciclo do carrossel, pela mesma logica que ja tinha tirado a
# Venda Blindada — e o produto mais caro (R$297/mes) e converte melhor na trilha
# de e-mail do Raio-X do que num slide de carrossel. A palavra MAQUINA segue
# ativa no Direct para os posts antigos e para os Reels.
# ---------------------------------------------------------------------------
CICLO_CTA = [
    "envio",     # 0
    "raiox",     # 1   <- produto
    "pergunta",  # 2
    "seguir",    # 3
    "pergunta",  # 4
    "envio",     # 5
    "venda10x",  # 6   <- produto
    "pergunta",  # 7
    "seguir",    # 8
    "envio",     # 9
    "raiox",     # 10  <- produto
    "pergunta",  # 11
    "envio",     # 12
    "ebook",     # 13  <- produto
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
    # --- CTAs de sinal, sem produto (criados em 14/08/2026) --------------------
    # "envio" existe para atacar o numero que esta zerado na conta: os Reels
    # auditados tinham 0 compartilhamento. Envio no Direct e o sinal que Mosseri
    # apontou como o mais forte para alcancar quem ainda nao segue.
    "envio": {
        "slide": (
            "Pensou em alguém agora?\n\n"
            "Manda esse post para a pessoa. Leva três segundos e pode evitar "
            "um prejuízo na próxima obra."
        ),
        "rodape": "@vendanaobra",
        "legenda": (
            "Se você pensou em alguém do seu time enquanto lia, manda esse post "
            "para a pessoa.\n"
            "É mais fácil combinar isso agora do que discutir depois que a venda "
            "já foi embora."
        ),
    },
    # "pergunta" e o mecanismo do nicho: em 72 legendas de perfis de construcao
    # civil e esquadria, CTA de Direct apareceu zero vezes e a pergunta aberta e
    # o padrao. Ideal futuro: pergunta escrita por frase no frases.json, casando
    # com a dor do post; por ora e generica, mas aberta e sem resposta obvia.
    "pergunta": {
        "slide": (
            "E aí na sua empresa?\n\n"
            "Me conta nos comentários como isso acontece no seu dia a dia. "
            "Eu respondo um por um."
        ),
        "rodape": "@vendanaobra",
        "legenda": (
            "E na sua empresa, como isso acontece?\n"
            "Comenta aqui embaixo — eu leio e respondo um por um."
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
    "envio": None,     # CTA de sinal: nao puxa tema, serve a qualquer frase
    "pergunta": None,  # idem
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

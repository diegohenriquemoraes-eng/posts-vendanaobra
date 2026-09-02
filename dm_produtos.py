# -*- coding: utf-8 -*-
"""Palavra comentada -> produto -> subpagina do site + texto do Direct.

Fonte de verdade dos slugs: `src/lib/site.ts` do repo da LP (lp-vendanaobra).
Se um slug mudar la, muda aqui — link errado no Direct e pior que nao mandar.

ATENCAO: comentario de codigo neste repo vai sem acento, mas o TEXTO QUE A
PESSOA RECEBE vai com acentuacao e pontuacao corretas. O Diego reprova
portugues capenga em qualquer peca publica, e o Direct e peca publica.

Regras embutidas aqui que nao devem ser "corrigidas" sem o Diego:

  - **LIVRO entrega o Raio-X.** O e-book "O Cliente Sumiu" saiu do portfolio em
    25/08/2026, mas os posts antigos ainda pedem a palavra. Quem comenta LIVRO
    hoje recebe o diagnostico gratuito, sem citar o e-book.
  - **CRM e MAQUINA sao o mesmo produto.** O CRM foi rebatizado Maquina de
    Vendas em 12/08/2026; a palavra CRM segue viva nos posts antigos.
  - **O destino e sempre a NOSSA subpagina, nunca o checkout direto.** Decisao
    de 26/08/2026: so a pagina do nosso dominio explica o diferencial (funil da
    construcao pronto, follow-up escrito, implantacao ao vivo) e so ela
    ranqueia. O botao dela e que leva ao checkout com o codigo de afiliado.
  - **UTM em todo link** (`utm_medium=dm`): sem isso nao da para separar o que
    o comment-to-DM traz do trafego geral do Instagram.
"""
from __future__ import annotations

SITE = "https://vendanaobra.com.br"

# utm_campaign entra por fora (miniaula / post), o resto e fixo
UTM = "utm_source=instagram&utm_medium=dm"


def link(caminho: str, campanha: str = "miniaula") -> str:
    return f"{SITE}{caminho}?{UTM}&utm_campaign={campanha}"


# ---------------------------------------------------------------------------
# Produtos. `palavras` sao comparadas com o comentario normalizado (sem acento,
# minusculo, sem pontuacao) — por isso "maquina" e nao "MAQUINA".
# ---------------------------------------------------------------------------
PRODUTOS = {
    "raiox": {
        "nome": "Raio-X da Venda na Obra",
        "caminho": "/raio-x",
        "palavras": ["raiox", "raio x", "raio-x", "livro", "ebook", "e-book"],
        "texto": (
            "Opa! Aqui está o Raio-X da Venda na Obra:\n\n"
            "{link}\n\n"
            "São 15 perguntas e leva 3 minutos. No fim você recebe uma nota de "
            "0 a 100 e o plano de ação da etapa em que a sua empresa está "
            "perdendo dinheiro — atração, proposta ou fechamento.\n\n"
            "Faz agora, enquanto está fresco. Depois me conta qual foi a sua nota."
        ),
    },
    "venda10x": {
        "nome": "Venda 10x",
        "caminho": "/venda-10x",
        "palavras": ["10x", "venda10x", "venda 10x"],
        "texto": (
            "Opa! O Venda 10x é aqui:\n\n"
            "{link}\n\n"
            "É aula ao vivo toda terça, às 20h, com empresários e vendedores da "
            "construção civil — da qualificação ao fechamento, com caso real na "
            "mesa.\n\n"
            "Dá uma olhada na página. Se ficar qualquer dúvida, me chama por aqui mesmo."
        ),
    },
    "blindada": {
        "nome": "Venda Blindada",
        "caminho": "/venda-blindada-esquadrias",
        "palavras": ["blindada", "vendablindada", "venda blindada"],
        "texto": (
            "Opa! O Venda Blindada é aqui:\n\n"
            "{link}\n\n"
            "É o contrato de esquadrias que eu uso na Perffec, em modelo "
            "editável, com cada cláusula explicada: por que ela existe e qual "
            "prejuízo ela evita depois da venda.\n\n"
            "Qualquer dúvida antes de decidir, me chama por aqui."
        ),
    },
    "maquina": {
        "nome": "Máquina de Vendas",
        "caminho": "/crm-venda-na-obra",
        "palavras": ["maquina", "crm", "maquina de vendas"],
        "texto": (
            "Opa! A Máquina de Vendas é aqui:\n\n"
            "{link}\n\n"
            "É o CRM da construção civil já configurado: cada orçamento com a "
            "próxima data marcada, follow-up automático e o funil inteiro numa "
            "tela só — para a venda parar de depender da sua memória.\n\n"
            "Na página tem o passo a passo da implantação. Dúvida, me chama."
        ),
    },
    "prospeccao": {
        "nome": "Prospecção Turbinada por IA",
        "caminho": "/prospeccao-turbinada-por-ia",
        "palavras": ["prospeccao", "prospecao", "prospeccao ia"],
        "texto": (
            "Opa! O curso de Prospecção Turbinada por IA é aqui:\n\n"
            "{link}\n\n"
            "Ele mostra como usar IA para achar as empresas certas da sua "
            "cidade, escrever a mensagem que recebe resposta e manter a rotina "
            "de follow-up sem depender de indicação.\n\n"
            "Dá uma olhada e me diz o que achou."
        ),
    },
}

# Como o robo casa a intencao quando a pessoa nao escreve a palavra exata:
# "quero", "link", "manda ai". Nesses casos o produto vem do POST (o cta.palavra
# da mini-aula), nunca de chute — se o post nao pede palavra, o robo nao manda.
INTENCAO = [
    "quero", "quero sim", "eu quero", "eu quero sim", "queria", "link",
    "o link", "manda", "manda ai", "manda o link", "me manda",
    "me manda o link", "envia", "envia ai", "interesse", "tenho interesse",
    "quero saber mais", "mais informacoes", "informacoes", "info", "eu",
]

# Contas da casa: nunca recebem DM automatica.
IGNORAR_USUARIOS = {
    "vendanaobra", "perffecesquadrias", "diegomoraesoficial", "diegohmoraes",
}

# Palavra pedida pelo post (cta.palavra do miniaulas.json, em maiusculo la)
# -> chave do produto aqui.
PALAVRA_POST = {
    "raiox": "raiox",
    "10x": "venda10x",
    "blindada": "blindada",
    "maquina": "maquina",
    "crm": "maquina",
    "livro": "raiox",
    "prospeccao": "prospeccao",
}

# Resposta publica no proprio comentario — LIGADA por padrao (--sem-publico
# desliga). Nao e enfeite, e o que evita mensagem repetida: e assim que o Diego
# ve, olhando o post, que aquele comentario ja foi atendido. Sem ela, ele
# responderia a mao o que o robo ja respondeu — que e exatamente o que ele fazia
# antes deste robo existir.
#
# O texto e igual ao que ele escreve a mao ("@fulano te chamei no direct"),
# minusculo e sem ponto final, para o post nao ter duas vozes diferentes.
RESPOSTA_PUBLICA = "@{usuario} te chamei no direct"


def texto_do_produto(chave: str, campanha: str = "miniaula") -> str:
    p = PRODUTOS[chave]
    return p["texto"].format(link=link(p["caminho"], campanha))

# -*- coding: utf-8 -*-
"""Comentario com palavra-chave -> link do produto no Direct, automatico.

O que faz, em uma frase: a cada rodada le os comentarios das mini-aulas que
estao no ar, descobre qual produto a pessoa pediu e manda a SUBPAGINA daquele
produto por mensagem privada, uma unica vez por pessoa.

Por que existe (02/09/2026, pedido do Diego): as duas mini-aulas da semana
terminam pedindo "comenta PALAVRA que eu te mando no Direct". Ate agora isso
dependia da automacao nativa da Meta ("Comentar para enviar mensagem"), que e
configurada publicacao a publicacao no Business Suite — mini-aula nova saia sem
cobertura ate alguem lembrar de configurar. Este robo cobre **toda mini-aula
publicada daqui para a frente**, sem configurar nada: o `publicar_miniaula.py`
ja grava o `media_id` no `publicados_miniaulas.json`, e e dali que ele le.

Caminho OFICIAL, nada de navegador: private reply da Graph API
(`POST /{ig-user-id}/messages` com `recipient={"comment_id": ...}`), com o mesmo
token de system user que publica os posts — ele ja tem `instagram_manage_comments`
e `instagram_manage_messages`, sem expiracao. Nao e o robo de DM encerrado em
31/08/2026 (aquele era `instagrapi`, nao oficial, e por isso deu problema).

Regras que a Meta impoe e que estao respeitadas aqui:
  - private reply so vale **ate 7 dias** depois do comentario;
  - **uma unica** private reply por comentario (a segunda e recusada);
  - a mensagem cai na caixa principal de quem segue e em "Solicitacoes" de quem
    nao segue — nos dois casos e entrega legitima, sem risco para o perfil.

Uso:
    python responder_dm.py                 # rodada normal (o que o Actions faz)
    python responder_dm.py --ensaio        # mostra o que enviaria, sem enviar
    python responder_dm.py --desde 2026-08-25   # olha mini-aulas mais antigas
    python responder_dm.py --todas-midias 12    # qualquer post recente, nao so mini-aula
    python responder_dm.py --sem-publico   # so a DM, sem responder no comentario
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta

import dm_produtos as prod
from publicar import (API, FUSO_BR, IG_USER_ID, _carregar, _log, _salvar,
                      _token)

BASE = os.path.dirname(os.path.abspath(__file__))
MINIAULAS = os.path.join(BASE, "miniaulas.json")
PUBLICADOS = os.path.join(BASE, "publicados_miniaulas.json")
ESTADO = os.path.join(BASE, "respondidos_dm.json")

# A private reply NAO sai pelo token de system user nem pelo IG User ID: sai
# pela PAGINA do Facebook vinculada ao @vendanaobra, com o token dela. Testado
# em 02/09/2026 — pelo IG User ID a Graph responde "(#3) Application does not
# have the capability to make this API call"; pela pagina, funciona. O token da
# pagina e derivado do de system user a cada rodada (`/me/accounts`), entao nao
# existe segredo novo para guardar.
PAGE_ID = "1272959582565285"          # Pagina "Venda na Obra"

# Mini-aula publicada a partir daqui entra no escopo. E 01/09 e nao 02/09 (o dia
# em que o robo nasceu) porque a aula 13 saiu em 01/09, ainda esta no ar, ainda
# recebe comentario e nao tinha nenhum atendido — deixa-la de fora seria pedir
# ao Diego que respondesse a mao justamente o que este robo veio resolver. O que
# e mais antigo fica de fora de proposito: aqueles comentarios ele ja respondeu.
DATA_CORTE = "2026-09-01"

# A Meta so aceita private reply ate 7 dias depois do comentario; 6 da folga
# para uma rodada perdida sem tentar um envio que ja nasce recusado.
JANELA_DIAS = 6

# Mesma pessoa, mesmo produto: nao repete dentro desse prazo, mesmo que ela
# comente a palavra em varios posts.
REPETIR_APOS_DIAS = 30

# Teto por rodada. Nao e medo de bloqueio (a API oficial nao pune private
# reply), e limite de estrago: se algo casar errado, para em 40.
MAX_ENVIOS = 40

# Comentario mais longo que isso e conversa, nao palavra-chave. Responder
# "MAQUINA" para quem escreveu tres linhas contando o caso dele e o jeito mais
# rapido de parecer robo.
MAX_PALAVRAS = 10


# --------------------------------------------------------------------------- http

def _api_get(endpoint: str, campos: dict) -> dict:
    url = f"{API}/{endpoint}?" + urllib.parse.urlencode(campos)
    try:
        with urllib.request.urlopen(url, timeout=60) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        return {"erro": json.loads(e.read().decode(errors="replace") or "{}")}
    except Exception as e:  # rede
        return {"erro": {"error": {"message": str(e)}}}


def _page_token(token: str) -> str:
    r = _api_get("me/accounts", {"fields": "id,access_token", "access_token": token})
    if "erro" in r:
        raise SystemExit(f"nao consegui o token da pagina: {r['erro']}")
    paginas = r.get("data", [])
    for p in paginas:
        if p.get("id") == PAGE_ID:
            return p["access_token"]
    if paginas:
        return paginas[0]["access_token"]
    raise SystemExit("o system user nao enxerga nenhuma pagina")


def _api_post(endpoint: str, campos: dict) -> dict:
    dados = urllib.parse.urlencode(campos).encode()
    req = urllib.request.Request(f"{API}/{endpoint}", data=dados, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        return {"erro": json.loads(e.read().decode(errors="replace") or "{}")}
    except Exception as e:
        return {"erro": {"error": {"message": str(e)}}}


# --------------------------------------------------------------------------- git

def commitar_estado() -> None:
    """Commita o estado com rebase antes do push.

    O `_commitar` do publicar.py empurra direto, e ali isso basta: cada robo de
    publicacao roda uma vez por dia. Este roda a cada 10 minutos e cruza com o
    reel diario e com a mini-aula — sem rebase, o push perde a corrida e o job
    quebra em dia de publicacao, justo quando ha mais comentario para atender.
    """
    subprocess.run(["git", "add", "respondidos_dm.json"], cwd=BASE, check=True)
    mudou = subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=BASE).returncode != 0
    if not mudou:
        return
    subprocess.run(["git", "-c", "user.name=vendanaobra-bot",
                    "-c", "user.email=bot@vendanaobra.com.br",
                    "commit", "-m", "dm: comentarios respondidos"],
                   cwd=BASE, check=True)
    for tentativa in range(3):
        if subprocess.run(["git", "push", "origin", "main"], cwd=BASE).returncode == 0:
            return
        _log(f"push recusado (tentativa {tentativa + 1}) — rebase e tenta de novo")
        subprocess.run(["git", "pull", "--rebase", "--autostash", "origin", "main"],
                       cwd=BASE, check=False)
    _log("AVISO: nao consegui empurrar o estado; a proxima rodada tenta de novo")


# --------------------------------------------------------------------------- pessoas

def id_pessoa(usuario: str) -> str:
    """Identidade so para deduplicar — nunca o @ da pessoa.

    Este repo e PUBLICO (a Graph API exige URL publica para as imagens, entao o
    raw.githubusercontent serve os slides). Gravar aqui "@fulano recebeu DM do
    Venda Blindada" publicaria um dado que nao existe em lugar nenhum: o
    comentario e publico, a mensagem privada nao. O hash resolve o dedup sem
    publicar nada. Os logs do Actions tambem sao publicos, por isso eles
    mostram o mesmo hash.
    """
    return hashlib.sha256(f"vno:{usuario}".encode()).hexdigest()[:12]


# --------------------------------------------------------------------------- texto

def normalizar(texto: str) -> str:
    """minusculo, sem acento, sem pontuacao e sem emoji — so letras e numeros."""
    t = unicodedata.normalize("NFD", texto or "")
    t = "".join(c for c in t if unicodedata.category(c) != "Mn")
    limpo = []
    for c in t.lower():
        if c.isalnum():
            limpo.append(c)
        elif c in "-_":
            limpo.append(c)
        else:
            limpo.append(" ")
    return " ".join("".join(limpo).split())


def casar_produto(texto: str) -> tuple[str | None, str | None]:
    """Devolve (chave do produto, palavra que casou) olhando so o comentario."""
    n = normalizar(texto)
    if not n:
        return None, None
    tokens = n.split()
    if len(tokens) > MAX_PALAVRAS:
        return None, None

    melhor = None  # (posicao no texto, chave, palavra)
    for chave, p in prod.PRODUTOS.items():
        for palavra in p["palavras"]:
            alvo = normalizar(palavra)
            if " " in alvo:
                pos = n.find(alvo)
                achou = pos >= 0
            else:
                achou = alvo in tokens
                pos = tokens.index(alvo) if achou else -1
            if achou and (melhor is None or pos < melhor[0]):
                melhor = (pos, chave, palavra)
    if melhor:
        return melhor[1], melhor[2]
    return None, None


def tem_intencao(texto: str) -> bool:
    """'quero', 'manda o link' — pede o material sem escrever a palavra."""
    n = normalizar(texto)
    return n in {normalizar(i) for i in prod.INTENCAO}


# --------------------------------------------------------------------------- escopo

def palavra_da_aula(aula_id: int) -> str | None:
    """A palavra que aquela mini-aula pediu no ultimo slide, se pediu alguma."""
    dados = _carregar(MINIAULAS, {"aulas": []})
    for a in dados.get("aulas", []):
        if a.get("id") == aula_id:
            cta = a.get("cta") or {}
            palavra = (cta.get("palavra") or "").strip().lower()
            return prod.PALAVRA_POST.get(palavra)
    return None


def midias_das_miniaulas(desde: str) -> list[dict]:
    """Mini-aulas publicadas de `desde` para ca, das mais novas para as velhas."""
    posts = _carregar(PUBLICADOS, {"posts": []}).get("posts", [])
    alvo = []
    for p in posts:
        if p.get("data", "") < desde or not p.get("media_id"):
            continue
        alvo.append({
            "media_id": p["media_id"],
            "rotulo": f"mini-aula {p['id']} ({p.get('data')})",
            "produto_do_post": palavra_da_aula(p["id"]),
            "campanha": "miniaula",
        })
    return list(reversed(alvo))


def midias_recentes(quantas: int, token: str) -> list[dict]:
    """Qualquer publicacao recente do perfil — para quando o Diego desligar as
    automacoes nativas e este robo passar a cobrir o feed inteiro."""
    r = _api_get(f"{IG_USER_ID}/media", {
        "fields": "id,timestamp,comments_count", "limit": quantas,
        "access_token": token,
    })
    if "erro" in r:
        _log(f"nao consegui listar as midias: {r['erro']}")
        return []
    return [{
        "media_id": m["id"],
        "rotulo": f"post {m['id']} ({m.get('timestamp','')[:10]})",
        "produto_do_post": None,
        "campanha": "post",
    } for m in r.get("data", [])]


# --------------------------------------------------------------------------- comentarios

def comentarios_da_midia(media_id: str, token: str) -> list[dict]:
    r = _api_get(f"{media_id}/comments", {
        "fields": "id,text,username,timestamp,replies{id,text,username,timestamp}",
        "limit": 50, "access_token": token,
    })
    if "erro" in r:
        _log(f"  comentarios de {media_id}: {r['erro']}")
        return []
    saida = []
    for c in r.get("data", []):
        respostas = (c.get("replies") or {}).get("data", [])
        # Se o perfil ja respondeu ali embaixo, esse comentario esta atendido —
        # ver `atendido_pela_casa`.
        c["_atendido"] = atendido_pela_casa(respostas)
        saida.append(c)
        for filho in respostas:
            filho["_atendido"] = False
            saida.append(filho)
    return saida


def atendido_pela_casa(respostas: list[dict]) -> bool:
    """O @vendanaobra ja respondeu esse comentario publicamente?

    Este e o unico ponto do robo que impede mensagem repetida, e ele resolve
    dois casos de uma vez:

      1. **O Diego respondendo a mao.** E o que acontece hoje: nos comentarios
         de agosto ele respondeu "@fulano te chamei no direct" e mandou a DM
         ele mesmo, 4 a 36 minutos depois do comentario.
      2. **As automacoes nativas da Meta**, que seguem ligadas no Business Suite
         (MAPEAMENTO, MAQUINA, RAIOX, CRM, BLINDADA, 10X, LIVRO) e respondem o
         comentario com "Enviei uma mensagem para voce!" quando disparam. Elas
         nao estao disparando — por isso este robo existe — mas se voltarem a
         funcionar, a resposta publica delas aparece aqui e o robo se cala em
         vez de mandar a segunda DM.

    E por isso que **nao foi preciso desligar nada** para ligar este robo: quem
    chegar primeiro atende, o outro fica quieto.
    """
    return any((r.get("username") or "").lower() in prod.IGNORAR_USUARIOS
               for r in respostas)


def dentro_da_janela(carimbo: str) -> bool:
    try:
        quando = datetime.strptime(carimbo, "%Y-%m-%dT%H:%M:%S%z")
    except (ValueError, TypeError):
        return False
    return datetime.now(quando.tzinfo) - quando <= timedelta(days=JANELA_DIAS)


# --------------------------------------------------------------------------- estado

def _estado() -> dict:
    return _carregar(ESTADO, {"comentarios": {}, "envios": []})


def ja_atendido(estado: dict, pessoa: str, chave: str) -> bool:
    """Mesma pessoa, mesmo produto, dentro do prazo de repeticao."""
    limite = datetime.now(FUSO_BR) - timedelta(days=REPETIR_APOS_DIAS)
    for e in reversed(estado.get("envios", [])):
        if e.get("pessoa") != pessoa or e.get("produto") != chave:
            continue
        try:
            quando = datetime.fromisoformat(e["quando"])
        except (ValueError, KeyError):
            return True
        return quando >= limite
    return False


# --------------------------------------------------------------------------- envio

# Subcodes que nao adianta repetir: o comentario passou dos 7 dias ou a pessoa
# nao aceita mensagem. Retentar so gastaria rodada e sujaria o log.
ERRO_DEFINITIVO = {2534024, 2534014, 551}


def enviar_dm(comment_id: str, texto: str, page_token: str) -> dict:
    return _api_post(f"{PAGE_ID}/messages", {
        "recipient": json.dumps({"comment_id": comment_id}),
        "message": json.dumps({"text": texto}),
        "access_token": page_token,
    })


def responder_publico(comment_id: str, usuario: str, token: str) -> None:
    r = _api_post(f"{comment_id}/replies", {
        "message": prod.RESPOSTA_PUBLICA.format(usuario=usuario),
        "access_token": token,
    })
    if "erro" in r:
        _log(f"  resposta publica falhou: {r['erro']}")


# --------------------------------------------------------------------------- rodada

def rodar(args) -> None:
    token = _token()
    page_token = None if args.ensaio else _page_token(token)
    estado = _estado()
    vistos = estado["comentarios"]

    if args.todas_midias:
        midias = midias_recentes(args.todas_midias, token)
    else:
        midias = midias_das_miniaulas(args.desde or DATA_CORTE)

    if not midias:
        _log("nenhuma mini-aula no escopo — nada a fazer")
        return

    enviados = 0
    novos = 0
    for m in midias:
        if enviados >= MAX_ENVIOS:
            break
        for c in comentarios_da_midia(m["media_id"], token):
            cid = c.get("id")
            if not cid or cid in vistos:
                continue
            novos += 1
            usuario = (c.get("username") or (c.get("from") or {}).get("username") or "").lower()
            texto = c.get("text") or ""
            pessoa = id_pessoa(usuario)
            registro = {
                "quando": datetime.now(FUSO_BR).isoformat(timespec="seconds"),
                "pessoa": pessoa, "midia": m["media_id"],
            }

            if usuario in prod.IGNORAR_USUARIOS:
                vistos[cid] = {**registro, "acao": "conta-da-casa"}
                continue
            if c.get("_atendido"):
                # o Diego (ou a automacao nativa) ja respondeu esse comentario
                vistos[cid] = {**registro, "acao": "ja-respondido-no-post"}
                continue
            if not dentro_da_janela(c.get("timestamp", "")):
                # fora dos 7 dias da Meta: marca para nunca mais tentar
                vistos[cid] = {**registro, "acao": "fora-da-janela"}
                continue

            chave, palavra = casar_produto(texto)
            if not chave and tem_intencao(texto) and m["produto_do_post"]:
                chave, palavra = m["produto_do_post"], "(intencao)"
            if not chave:
                vistos[cid] = {**registro, "acao": "sem-palavra"}
                continue

            if ja_atendido(estado, pessoa, chave):
                vistos[cid] = {**registro, "acao": "ja-atendido", "produto": chave}
                continue

            if enviados >= MAX_ENVIOS:
                _log(f"teto de {MAX_ENVIOS} envios na rodada — o resto fica para a proxima")
                break

            texto_dm = prod.texto_do_produto(chave, m["campanha"])
            if args.ensaio:
                print(f"\n[ENSAIO] @{usuario} comentou {texto!r} em {m['rotulo']}")
                print(f"         -> {prod.PRODUTOS[chave]['nome']}")
                print("         " + texto_dm.replace("\n", "\n         "))
                vistos.pop(cid, None)
                continue

            r = enviar_dm(cid, texto_dm, page_token)
            if "erro" in r:
                erro = r["erro"].get("error", {})
                tentativas = (vistos.get(cid, {}).get("tentativas", 0)) + 1
                definitivo = (erro.get("error_subcode") in ERRO_DEFINITIVO
                              or erro.get("code") in ERRO_DEFINITIVO)
                acao = "desisti" if definitivo or tentativas >= 3 else "erro"
                vistos[cid] = {**registro, "acao": acao, "produto": chave,
                               "tentativas": tentativas,
                               "erro": erro.get("message", "")[:200]}
                _log(f"  {pessoa} ({chave}): FALHOU — {erro.get('message','')}")
                continue

            enviados += 1
            vistos[cid] = {**registro, "acao": "enviado", "produto": chave,
                           "palavra": palavra}
            estado["envios"].append({
                "quando": registro["quando"], "pessoa": pessoa,
                "produto": chave, "palavra": palavra, "comentario": cid,
                "midia": m["media_id"],
            })
            _log(f"  {pessoa}: {prod.PRODUTOS[chave]['nome']} enviado "
                 f"(palavra {palavra!r})")
            if not args.sem_publico:
                responder_publico(cid, usuario, token)

    if args.ensaio:
        _log(f"ensaio: {novos} comentario(s) novo(s) vistos, nada enviado")
        return

    _salvar(ESTADO, estado)
    _log(f"rodada: {novos} comentario(s) novo(s), {enviados} DM(s) enviada(s)")
    if novos:
        commitar_estado()


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--ensaio", action="store_true",
                   help="mostra o que enviaria e nao envia nada")
    p.add_argument("--desde", default=None,
                   help="data minima da mini-aula (AAAA-MM-DD)")
    p.add_argument("--todas-midias", type=int, default=0, metavar="N",
                   help="olha as N publicacoes mais recentes, nao so mini-aulas")
    p.add_argument("--sem-publico", action="store_true",
                   help="nao responde no comentario (so manda a DM)")
    rodar(p.parse_args())


if __name__ == "__main__":
    main()

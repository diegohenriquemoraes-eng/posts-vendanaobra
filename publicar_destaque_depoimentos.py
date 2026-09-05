# -*- coding: utf-8 -*-
"""Sobe os Stories do destaque "Depoimentos" do @vendanaobra.

Rodada manual, pedida pelo Diego em 05/09/2026 — nao entra em cron nenhum.
O destaque em si (o circulo no perfil) **nao tem API**: a Graph API publica o
Story e para por ai. Depois de rodar isto, o destaque e montado a mao no
Instagram, escolhendo estes Stories do arquivo; a peca `0-capa` existe
justamente para virar a capa redonda.

Ordem importa: o destaque respeita a ordem de publicacao, entao a capa vai
primeiro e os depoimentos em seguida.

Uso:
    python publicar_destaque_depoimentos.py --ensaio   # so mostra o que faria
    python publicar_destaque_depoimentos.py            # publica os 4 Stories
"""
from __future__ import annotations

import argparse
import os
import time

from publicar import (IG_USER_ID, REPO_RAW, _commitar, _log, _post, _token,
                      conferir_token, esperar_container)
from gerar_destaque_depoimentos import SAIDA, gerar_tudo

PASTA_REL = "imagens/destaque-venda10x"
# A ordem do destaque e a ordem de publicacao: a capa vai primeiro. Peca nova
# entra no fim da lista e sobe sozinha com --apenas, sem repostar o resto.
ORDEM = ["0-capa.jpg", "1-gilliard.jpg", "2-nice.jpg", "3-sueli.jpg",
         "4-gabriel.jpg"]


def publicar(ensaio: bool = False, apenas: list = None) -> None:
    gerar_tudo()
    fila = [n for n in ORDEM if not apenas or n in apenas or
            n.rsplit(".", 1)[0] in apenas]
    if apenas and not fila:
        raise SystemExit(f"--apenas {apenas} nao casa com nenhuma peca de {ORDEM}")
    for nome in fila:
        if not os.path.exists(os.path.join(SAIDA, nome)):
            raise SystemExit(f"faltou a arte {nome}")

    if ensaio:
        for nome in fila:
            _log(f"ensaio: publicaria {REPO_RAW}/{PASTA_REL}/{nome}")
        return

    token = _token()
    conferir_token(token)

    # As artes precisam estar no ar antes: a Graph API baixa a imagem por URL,
    # nao aceita upload de arquivo local.
    _commitar("artes do destaque de depoimentos do Venda 10x", PASTA_REL)

    for nome in fila:
        url = f"{REPO_RAW}/{PASTA_REL}/{nome}"
        r = _post(f"{IG_USER_ID}/media", {
            "media_type": "STORIES", "image_url": url, "access_token": token,
        })
        esperar_container(r["id"], token)
        st = _post(f"{IG_USER_ID}/media_publish", {
            "creation_id": r["id"], "access_token": token,
        })
        _log(f"STORY {nome} publicado: {st['id']}")
        time.sleep(3)

    _log("pronto — agora monte o destaque no app/web escolhendo estes 4 Stories")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--ensaio", action="store_true", help="nao publica, so mostra")
    p.add_argument("--apenas", nargs="*", help="pecas a publicar (ex.: 4-gabriel)")
    a = p.parse_args()
    publicar(a.ensaio, a.apenas)

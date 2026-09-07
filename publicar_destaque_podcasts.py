# -*- coding: utf-8 -*-
"""Sobe os Stories do destaque "Podcasts" do @vendanaobra.

Rodada manual (07/09/2026), fora de cron — como o destaque de depoimentos.
O circulo do destaque nao tem API: a Graph API publica o Story e para ai; o
destaque e montado depois no instagram.com escolhendo estes Stories, e a peca
`0-capa` existe para virar a capa redonda.

A ordem do destaque e a ordem de publicacao, entao a fila sai em ordem
CRONOLOGICA dos episodios: capa, 2025 -> 2026, e o convite no fim.

Uso:
    python publicar_destaque_podcasts.py --ensaio
    python publicar_destaque_podcasts.py
    python publicar_destaque_podcasts.py --apenas 8-aluparts-25
"""
from __future__ import annotations

import argparse
import os
import time

from publicar import (IG_USER_ID, REPO_RAW, _commitar, _log, _post, _token,
                      conferir_token, esperar_container)
from gerar_destaque_podcasts import EPISODIOS, SAIDA, gerar_tudo

PASTA_REL = "imagens/destaque-podcasts"
ORDEM = (["0-capa.jpg"] + [e["arquivo"] + ".jpg" for e in EPISODIOS]
         + ["9-fecho.jpg"])


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

    # A Graph API baixa a imagem por URL — nao aceita upload de arquivo local.
    _commitar("artes do destaque de podcasts", PASTA_REL)

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

    _log(f"pronto — monte o destaque no web escolhendo estes {len(fila)} Stories")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--ensaio", action="store_true", help="nao publica, so mostra")
    p.add_argument("--apenas", nargs="*", help="pecas a publicar (ex.: 9-fecho)")
    a = p.parse_args()
    publicar(a.ensaio, a.apenas)

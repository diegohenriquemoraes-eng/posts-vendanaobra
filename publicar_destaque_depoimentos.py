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
ORDEM = ["0-capa.jpg", "1-gilliard.jpg", "2-nice.jpg", "3-sueli.jpg"]


def publicar(ensaio: bool = False) -> None:
    gerar_tudo()
    for nome in ORDEM:
        if not os.path.exists(os.path.join(SAIDA, nome)):
            raise SystemExit(f"faltou a arte {nome}")

    if ensaio:
        for nome in ORDEM:
            _log(f"ensaio: publicaria {REPO_RAW}/{PASTA_REL}/{nome}")
        return

    token = _token()
    conferir_token(token)

    # As artes precisam estar no ar antes: a Graph API baixa a imagem por URL,
    # nao aceita upload de arquivo local.
    _commitar("artes do destaque de depoimentos do Venda 10x", PASTA_REL)

    for nome in ORDEM:
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
    publicar(p.parse_args().ensaio)

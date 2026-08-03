# -*- coding: utf-8 -*-
"""Publica a mini-aula do dia (formato F2) no feed do @vendanaobra.

Roda TERCA e QUINTA, 12h BRT (o carrossel de frase ocupa seg/qua/sex — os dois
nunca caem no mesmo dia). Fluxo:

  1. escolhe a proxima aula da `sequencia` do miniaulas.json que ainda nao saiu
  2. gera os slides (gerar_miniaula.py) — a foto da capa precisa existir em
     fotos/; sem foto, a aula e PULADA (vai a proxima da sequencia) e o log avisa
  3. commita as imagens (raw.githubusercontent = URL publica que a Graph exige)
  4. publica o carrossel com a legenda da aula
  5. publica o STORY de reforco (a capa emoldurada, gerar_story.py)
  6. registra em publicados_miniaulas.json

Uso:
    python publicar_miniaula.py             # proxima da sequencia
    python publicar_miniaula.py --id 3      # aula especifica
    python publicar_miniaula.py --ensaio    # gera tudo e para (nao publica)
    python publicar_miniaula.py --garantir  # so publica se a de hoje nao saiu
"""
from __future__ import annotations

import argparse
import json
import os
from datetime import datetime

import gerar_miniaula
from gerar_story import gerar_story
from publicar import (FUSO_BR, IG_USER_ID, _carregar, _commitar, _log, _post,
                      _salvar, _subir_e_publicar, _token, conferir_token,
                      esperar_container)

BASE = os.path.dirname(os.path.abspath(__file__))
MINIAULAS = os.path.join(BASE, "miniaulas.json")
PUBLICADOS = os.path.join(BASE, "publicados_miniaulas.json")
REPO_RAW = "https://raw.githubusercontent.com/diegohenriquemoraes-eng/posts-vendanaobra/main"


def escolher(id_forcado: int | None) -> dict | None:
    dados = _carregar(MINIAULAS, {"aulas": [], "sequencia": []})
    aulas = {a["id"]: a for a in dados["aulas"]}
    if id_forcado is not None:
        if id_forcado not in aulas:
            raise SystemExit(f"Mini-aula id={id_forcado} nao existe")
        return aulas[id_forcado]

    ja = {p["id"] for p in _carregar(PUBLICADOS, {"posts": []})["posts"]}
    fila = [i for i in dados.get("sequencia", []) if i not in ja]
    # depois da sequencia curada, segue a ordem do banco
    fila += [a["id"] for a in dados["aulas"] if a["id"] not in ja and a["id"] not in fila]
    for i in fila:
        aula = aulas[i]
        foto = os.path.join(BASE, aula["foto"])
        if os.path.exists(foto):
            return aula
        _log(f"aula {i} SEM FOTO ({aula['foto']}) — pulando para a proxima")
    return None


def publicar_story(arte: str, hoje: str, slug: str, token: str) -> str:
    """Story de reforco: sobe a imagem e publica com media_type=STORIES."""
    caminho = os.path.join(BASE, "imagens", hoje, f"{slug}-story.jpg")
    gerar_story(arte, caminho)
    _commitar(f"story do post {slug}", "imagens")
    url = f"{REPO_RAW}/imagens/{hoje}/{os.path.basename(caminho)}"
    r = _post(f"{IG_USER_ID}/media", {
        "media_type": "STORIES", "image_url": url, "access_token": token,
    })
    esperar_container(r["id"], token)
    post = _post(f"{IG_USER_ID}/media_publish", {
        "creation_id": r["id"], "access_token": token,
    })
    _log(f"STORY publicado: {post['id']}")
    return post["id"]


def ja_postou_hoje() -> bool:
    hoje = datetime.now(FUSO_BR).strftime("%Y-%m-%d")
    return any(p["data"] == hoje for p in _carregar(PUBLICADOS, {"posts": []})["posts"])


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--id", type=int, default=None)
    p.add_argument("--ensaio", action="store_true")
    p.add_argument("--garantir", action="store_true")
    a = p.parse_args()

    hoje_dt = datetime.now(FUSO_BR)
    # terca=1, quinta=3 — a automacao respeita; --id e --ensaio ignoram
    if a.id is None and not a.ensaio and hoje_dt.weekday() not in (1, 3):
        _log("mini-aula so sai terca e quinta — nada a fazer")
        return
    if a.garantir and ja_postou_hoje():
        _log("mini-aula do dia ja esta no ar — nada a fazer")
        return

    aula = escolher(a.id)
    if aula is None:
        raise SystemExit("Nenhuma mini-aula com foto disponivel — repor o banco.")

    token = _token()
    conferir_token(token)
    hoje = hoje_dt.strftime("%Y-%m-%d")
    slug = f"{hoje}-aula{aula['id']:03d}"
    pasta = os.path.join(BASE, "imagens", hoje)

    caminhos = gerar_miniaula.gerar(aula, pasta, slug)
    _log(f"mini-aula {aula['id']} ({aula['titulo']}): {len(caminhos)} slides")

    if a.ensaio:
        print("\n--- legenda ---\n" + aula["legenda"] + "\n---------------\n")
        _log("ensaio: parando antes de publicar")
        return

    media_id = _subir_e_publicar(caminhos, hoje, slug, aula["legenda"], token)

    try:
        story_id = publicar_story(caminhos[0], hoje, slug, token)
    except SystemExit as e:
        # story e reforco: se falhar, o post principal ja esta no ar — registra
        # e avisa em vez de derrubar o job inteiro
        _log(f"AVISO: story falhou ({e}); o post do feed esta no ar")
        story_id = None

    registro = _carregar(PUBLICADOS, {"posts": []})
    registro["posts"].append({
        "id": aula["id"],
        "titulo": aula["titulo"],
        "produto": aula["produto"],
        "data": hoje,
        "media_id": media_id,
        "story_id": story_id,
    })
    _salvar(PUBLICADOS, registro)
    _commitar(f"mini-aula {slug} publicada", "publicados_miniaulas.json")


if __name__ == "__main__":
    main()

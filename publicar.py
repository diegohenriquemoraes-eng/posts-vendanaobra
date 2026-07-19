# -*- coding: utf-8 -*-
"""Publica o carrossel do dia no feed do @vendanaobra.

Fluxo:
  1. escolhe a proxima frase nao publicada de frases.json
  2. gera os 2 slides (claro + escuro)
  3. commita e sobe as imagens (raw.githubusercontent serve a URL publica
     que a Graph API exige — ela nao aceita upload de arquivo local)
  4. cria os 2 containers filhos, o container do carrossel e publica
  5. registra em publicados.json e commita

Uso:
    python publicar.py                 # proxima frase da fila
    python publicar.py --id 7          # frase especifica
    python publicar.py --ensaio        # gera as imagens e para (nao publica)
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone, timedelta

import urllib.request
import urllib.parse
import urllib.error

from gerar_carrossel import gerar_carrossel

BASE = os.path.dirname(os.path.abspath(__file__))
FRASES = os.path.join(BASE, "frases.json")
PUBLICADOS = os.path.join(BASE, "publicados.json")

IG_USER_ID = "17841470188725651"          # @vendanaobra
API = "https://graph.facebook.com/v21.0"

REPO_RAW = "https://raw.githubusercontent.com/diegohenriquemoraes-eng/posts-vendanaobra/main"

FUSO_BR = timezone(timedelta(hours=-3))


# --------------------------------------------------------------------------- util

def _log(msg: str) -> None:
    print(f"[{datetime.now(FUSO_BR):%H:%M:%S}] {msg}", flush=True)


def _token() -> str:
    tok = os.environ.get("META_TOKEN", "").strip()
    if tok:
        return tok
    caminho = r"C:\Users\NOTE\Desktop\Perffec\Claude\meta_system_user_token.txt"
    if os.path.exists(caminho):
        with open(caminho, encoding="utf-8") as f:
            return f.read().strip()
    raise SystemExit("Sem token: defina META_TOKEN ou salve meta_system_user_token.txt")


def _post(endpoint: str, campos: dict) -> dict:
    dados = urllib.parse.urlencode(campos).encode()
    req = urllib.request.Request(f"{API}/{endpoint}", data=dados, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        corpo = e.read().decode(errors="replace")
        raise SystemExit(f"Graph API falhou em {endpoint}: {corpo}")


def _get(endpoint: str, campos: dict) -> dict:
    url = f"{API}/{endpoint}?" + urllib.parse.urlencode(campos)
    try:
        with urllib.request.urlopen(url, timeout=60) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        corpo = e.read().decode(errors="replace")
        raise SystemExit(f"Graph API falhou em {endpoint}: {corpo}")


def _git(*args: str) -> None:
    subprocess.run(["git", *args], cwd=BASE, check=True)


# --------------------------------------------------------------------------- fila

def _carregar(caminho: str, padrao):
    if not os.path.exists(caminho):
        return padrao
    with open(caminho, encoding="utf-8") as f:
        return json.load(f)


def _salvar(caminho: str, dados) -> None:
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)
        f.write("\n")


def escolher(id_forcado: int | None) -> dict:
    banco = _carregar(FRASES, {"frases": []})["frases"]
    if id_forcado is not None:
        for fr in banco:
            if fr["id"] == id_forcado:
                return fr
        raise SystemExit(f"Frase id={id_forcado} nao existe")

    ja = {p["id"] for p in _carregar(PUBLICADOS, {"posts": []})["posts"]}
    restantes = [fr for fr in banco if fr["id"] not in ja]
    if not restantes:
        raise SystemExit(
            "Banco de frases esgotado — repor frases.json antes do proximo dia."
        )
    if len(restantes) <= 10:
        _log(f"AVISO: so restam {len(restantes)} frases no banco.")
    return restantes[0]


# --------------------------------------------------------------------------- publicacao

def esperar_container(container_id: str, token: str, tentativas: int = 30) -> None:
    """A Graph API precisa baixar a imagem antes de deixar publicar."""
    for _ in range(tentativas):
        r = _get(container_id, {"fields": "status_code,status", "access_token": token})
        estado = r.get("status_code")
        if estado == "FINISHED":
            return
        if estado == "ERROR":
            raise SystemExit(f"Container {container_id} falhou: {r.get('status')}")
        time.sleep(4)
    raise SystemExit(f"Container {container_id} nao ficou pronto a tempo")


def publicar(frase: dict, ensaio: bool) -> None:
    token = _token()
    hoje = datetime.now(FUSO_BR).strftime("%Y-%m-%d")
    slug = f"{hoje}-{frase['id']:03d}"
    pasta = os.path.join(BASE, "imagens", hoje)

    caminhos = gerar_carrossel(frase["texto"], pasta, slug)
    _log(f"slides gerados: {', '.join(os.path.basename(c) for c in caminhos)}")

    if ensaio:
        _log("ensaio: parando antes de publicar")
        return

    # 1) subir as imagens para o repo publico (a Graph API exige URL https publica)
    _git("add", "imagens")
    _git("-c", "user.name=vendanaobra-bot",
         "-c", "user.email=bot@vendanaobra.com.br",
         "commit", "-m", f"imagens do post {slug}")
    _git("push", "origin", "main")

    urls = [f"{REPO_RAW}/imagens/{hoje}/{os.path.basename(c)}" for c in caminhos]
    _log("imagens no ar: " + " | ".join(urls))
    time.sleep(5)  # folga para o CDN do raw responder

    # 2) containers filhos
    filhos = []
    for url in urls:
        r = _post(f"{IG_USER_ID}/media", {
            "image_url": url,
            "is_carousel_item": "true",
            "access_token": token,
        })
        filhos.append(r["id"])
        _log(f"container filho {r['id']}")

    for f in filhos:
        esperar_container(f, token)

    # 3) container do carrossel
    pai = _post(f"{IG_USER_ID}/media", {
        "media_type": "CAROUSEL",
        "children": ",".join(filhos),
        "caption": frase["texto"],
        "access_token": token,
    })["id"]
    esperar_container(pai, token)
    _log(f"container do carrossel {pai}")

    # 4) publicar
    post = _post(f"{IG_USER_ID}/media_publish", {
        "creation_id": pai,
        "access_token": token,
    })
    _log(f"PUBLICADO: {post['id']}")

    # 5) registrar
    registro = _carregar(PUBLICADOS, {"posts": []})
    registro["posts"].append({
        "id": frase["id"],
        "tema": frase["tema"],
        "data": hoje,
        "texto": frase["texto"],
        "media_id": post["id"],
    })
    _salvar(PUBLICADOS, registro)
    _git("add", "publicados.json")
    _git("-c", "user.name=vendanaobra-bot",
         "-c", "user.email=bot@vendanaobra.com.br",
         "commit", "-m", f"post {slug} publicado")
    _git("push", "origin", "main")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--id", type=int, default=None)
    p.add_argument("--ensaio", action="store_true")
    a = p.parse_args()
    publicar(escolher(a.id), a.ensaio)


if __name__ == "__main__":
    main()

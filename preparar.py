# -*- coding: utf-8 -*-
"""Prepara a peca do @vendanaobra para o Diego postar A MAO, do celular.

Desde 21/08/2026 este perfil nao publica mais por API (ver CLAUDE.md). O robo
so PREPARA: gera os slides e a legenda, monta a pasta de entrega no Desktop,
espelha no Google Drive e para por ai. Quem abre o app do Instagram e posta e
o Diego.

Uso:
    python preparar.py frase              # proxima frase da fila (3 slides 1:1)
    python preparar.py frase --id 42      # frase especifica
    python preparar.py aula               # proxima mini-aula da sequencia (4:5)
    python preparar.py aula --id 19       # aula especifica
    python preparar.py fila               # o que esta preparado e ainda nao foi postado
    python preparar.py confirmar          # marca a pendencia como postada
    python preparar.py confirmar <slug>   # confirma uma pendencia especifica

Confirmar importa: e o que avanca o ciclo de CTA e tira a frase/aula do banco.
Sem confirmar, a proxima preparacao repete a mesma peca.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime

import legenda
import publicar
import publicar_miniaula
import gerar_miniaula
from gerar_carrossel import gerar_carrossel

BASE = os.path.dirname(os.path.abspath(__file__))
FILA = os.path.join(BASE, "fila_manual.json")

ENTREGA = r"C:\Users\NOTE\Desktop\Perffec\Claude\Posts-Manuais"
DRIVE = "gdrive:MKT vendanaobra/Posts manuais"

FUSO_BR = publicar.FUSO_BR


def _log(msg: str) -> None:
    print(f"[{datetime.now(FUSO_BR):%H:%M:%S}] {msg}", flush=True)


def _hoje() -> str:
    return datetime.now(FUSO_BR).strftime("%Y-%m-%d")


def _fila() -> list[dict]:
    if not os.path.exists(FILA):
        return []
    with open(FILA, encoding="utf-8") as f:
        return json.load(f).get("pendentes", [])


def _salvar_fila(pendentes: list[dict]) -> None:
    with open(FILA, "w", encoding="utf-8") as f:
        json.dump({"pendentes": pendentes}, f, ensure_ascii=False, indent=2)
        f.write("\n")


def _pasta_entrega(slug: str) -> str:
    pasta = os.path.join(ENTREGA, slug)
    os.makedirs(pasta, exist_ok=True)
    return pasta


def _numerar(caminhos: list[str], pasta: str) -> list[str]:
    """Renomeia para 1.jpg, 2.jpg... — a ordem em que entram no carrossel."""
    finais = []
    for i, origem in enumerate(caminhos, start=1):
        destino = os.path.join(pasta, f"{i}.jpg")
        shutil.copyfile(origem, destino)
        finais.append(destino)
    return finais


def _instrucoes(tipo: str, n_slides: int, legenda_txt: str, slug: str) -> str:
    formato = "quadrado (1:1)" if tipo == "frase" else "retrato (4:5)"
    return f"""COMO POSTAR — {slug}

1. Abre o app do Instagram no celular, no @vendanaobra.
2. Novo post > seleciona as {n_slides} imagens NA ORDEM: 1, 2, 3...
   (o app numera na ordem em que voce toca — confere antes de avancar).
3. Formato {formato}: as artes ja estao no tamanho certo, nao cortar.
4. Sem filtro, sem edicao.
5. Cola a legenda do arquivo legenda.txt.
6. Publicar.

Depois de postar, me avisa (ou roda no PC):
    python preparar.py confirmar {slug}
Isso tira a peca da fila e avanca o ciclo de CTA. Sem isso, a proxima
preparacao repete essa mesma peca.

--- legenda (tambem em legenda.txt) ---
{legenda_txt}
"""


def _subir_drive(pasta: str, slug: str) -> None:
    try:
        subprocess.run(
            ["rclone", "copy", pasta, f"{DRIVE}/{slug}", "--quiet"],
            check=True, capture_output=True, text=True, timeout=300,
        )
        _log(f"Drive: {DRIVE}/{slug}")
    except FileNotFoundError:
        _log("AVISO: rclone nao encontrado — a pasta local esta pronta assim mesmo")
    except subprocess.CalledProcessError as e:
        _log(f"AVISO: rclone falhou ({e.stderr.strip()[:200]}) — pasta local esta pronta")
    except subprocess.TimeoutExpired:
        _log("AVISO: rclone demorou demais — pasta local esta pronta")


def _entregar(tipo: str, slug: str, caminhos: list[str], legenda_txt: str,
              extra: dict) -> None:
    pasta = _pasta_entrega(slug)
    finais = _numerar(caminhos, pasta)

    with open(os.path.join(pasta, "legenda.txt"), "w", encoding="utf-8") as f:
        f.write(legenda_txt.rstrip() + "\n")
    with open(os.path.join(pasta, "COMO-POSTAR.txt"), "w", encoding="utf-8") as f:
        f.write(_instrucoes(tipo, len(finais), legenda_txt, slug))

    pendentes = [p for p in _fila() if p["slug"] != slug]
    pendentes.append({"tipo": tipo, "slug": slug, "preparado_em": _hoje(),
                      "pasta": pasta, "legenda": legenda_txt, **extra})
    _salvar_fila(pendentes)

    _log(f"{len(finais)} slides + legenda em: {pasta}")
    _subir_drive(pasta, slug)
    print("\n--- legenda ---\n" + legenda_txt + "\n---------------")
    _log(f"depois de postar: python preparar.py confirmar {slug}")


# --------------------------------------------------------------------------- frase

def preparar_frase(id_forcado: int | None) -> None:
    indice_cta, cta_hoje = publicar.cta_do_dia()
    frase = publicar.escolher(id_forcado, cta_hoje)
    slug = f"{_hoje()}-{frase['id']:03d}"
    pasta_tmp = os.path.join(BASE, "saida", "manual", slug)
    os.makedirs(pasta_tmp, exist_ok=True)

    peca = legenda.conteudo_cta(cta_hoje)
    caminhos = gerar_carrossel(
        frase["texto"], pasta_tmp, slug,
        cta_texto=peca["slide"], cta_rodape=peca["rodape"],
    )
    texto = legenda.montar(frase, cta_hoje)
    _log(f"frase {frase['id']} ({frase['tema']}) — CTA: {cta_hoje}")
    _entregar("frase", slug, caminhos, texto,
              {"frase_id": frase["id"], "tema": frase["tema"],
               "texto": frase["texto"], "cta": cta_hoje, "indice_cta": indice_cta})


# --------------------------------------------------------------------------- aula

def preparar_aula(id_forcado: int | None) -> None:
    aula = publicar_miniaula.escolher(id_forcado)
    if aula is None:
        raise SystemExit("Nenhuma mini-aula com foto disponivel — repor o banco.")
    slug = f"{_hoje()}-aula{aula['id']:03d}"
    pasta_tmp = os.path.join(BASE, "saida", "manual", slug)
    os.makedirs(pasta_tmp, exist_ok=True)

    caminhos = gerar_miniaula.gerar(aula, pasta_tmp, slug)
    _log(f"mini-aula {aula['id']} ({aula['titulo']}) — {len(caminhos)} slides")
    _entregar("aula", slug, caminhos, aula["legenda"],
              {"aula_id": aula["id"], "titulo": aula["titulo"],
               "produto": aula.get("produto")})


# --------------------------------------------------------------------------- fila

def mostrar_fila() -> None:
    pendentes = _fila()
    if not pendentes:
        print("Nada preparado esperando postagem.")
        return
    print(f"{len(pendentes)} peca(s) preparada(s) e ainda nao confirmada(s):\n")
    for p in pendentes:
        print(f"  {p['slug']}  ({p['tipo']}, preparado em {p['preparado_em']})")
        print(f"    {p['pasta']}")


def confirmar(slug: str | None) -> None:
    pendentes = _fila()
    if not pendentes:
        raise SystemExit("Nada na fila para confirmar.")
    if slug is None:
        if len(pendentes) > 1:
            mostrar_fila()
            raise SystemExit("\nMais de uma pendencia: passe o slug.")
        alvo = pendentes[0]
    else:
        alvo = next((p for p in pendentes if p["slug"] == slug), None)
        if alvo is None:
            raise SystemExit(f"{slug} nao esta na fila.")

    hoje = _hoje()
    if alvo["tipo"] == "frase":
        registro = publicar._carregar(publicar.PUBLICADOS, {"posts": []})
        registro["posts"].append({
            "id": alvo["frase_id"], "tema": alvo["tema"], "data": hoje,
            "texto": alvo["texto"], "cta": alvo["cta"], "media_id": "manual",
        })
        publicar._salvar(publicar.PUBLICADOS, registro)
        publicar._salvar(publicar.ESTADO_CTA, {
            "ultimo_cta": alvo["cta"], "ultimo_indice": alvo["indice_cta"],
            "data": hoje,
        })
        arquivos = ("publicados.json", "estado_cta.json", "fila_manual.json")
    else:
        registro = publicar._carregar(publicar_miniaula.PUBLICADOS, {"posts": []})
        registro["posts"].append({
            "id": alvo["aula_id"], "titulo": alvo["titulo"], "data": hoje,
            "media_id": "manual", "story_id": None,
        })
        publicar._salvar(publicar_miniaula.PUBLICADOS, registro)
        arquivos = ("publicados_miniaulas.json", "fila_manual.json")

    _salvar_fila([p for p in pendentes if p["slug"] != alvo["slug"]])
    publicar._commitar(f"{alvo['slug']} postado a mao", *arquivos)
    _log(f"{alvo['slug']} registrado como postado.")


def main() -> None:
    p = argparse.ArgumentParser(description="Prepara a peca para postar a mao.")
    p.add_argument("acao", choices=["frase", "aula", "fila", "confirmar"])
    p.add_argument("slug", nargs="?", default=None)
    p.add_argument("--id", type=int, default=None)
    a = p.parse_args()

    if a.acao == "frase":
        preparar_frase(a.id)
    elif a.acao == "aula":
        preparar_aula(a.id)
    elif a.acao == "fila":
        mostrar_fila()
    else:
        confirmar(a.slug)


if __name__ == "__main__":
    main()

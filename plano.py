# -*- coding: utf-8 -*-
"""Calendario de publicacao dos Reels do EP25 — decidido pelo Diego em 27/08/2026.

Muda tudo o que valia antes. A cadencia continua 1 por dia, mas **quase todos
saem so na aba de Reels** (`share_to_feed=false`): postar todo dia no feed
encheria o perfil de corte. So os escolhidos por ele aparecem na grade.

Regras:
  * feed  -> aparece na grade, leva capa de IA e **tem colab com a Aluparts**;
  * reels -> so na aba de Reels, capa original (rosto + gancho) e **sem colab**.

A ordem dos dias sem escolha e' sorteada com semente fixa, para o calendario
ser sempre o mesmo se alguem rodar de novo.
"""
import json, io, os, random
from datetime import date, timedelta

BASE = os.path.dirname(os.path.abspath(__file__))
INICIO = date(2026, 8, 28)          # o 03 saiu em 27/08
SEMENTE = 2708

FEED = ["07", "13", "27", "14"]     # aprovados por ele para a grade
FIXOS = {0: "07", 1: "10", 2: "05", 3: "13", 8: "27", 13: "14"}

def montar():
    fila = json.load(io.open(os.path.join(BASE, "reels_ep25.json"), encoding="utf-8"))["cortes"]
    pub = json.load(io.open(os.path.join(BASE, "publicados_reels.json"), encoding="utf-8"))
    saiu = {r["id"] for r in pub}
    restantes = [c["id"] for c in fila if c["id"] not in saiu]

    escolhidos = set(FIXOS.values())
    sorteio = [c for c in restantes if c not in escolhidos]
    random.Random(SEMENTE).shuffle(sorteio)

    plano, i = [], 0
    for dia in range(len(restantes)):
        cid = FIXOS.get(dia)
        if cid is None:
            cid = sorteio[i]; i += 1
        plano.append({"id": cid, "dia": (INICIO + timedelta(days=dia)).isoformat(),
                      "feed": cid in FEED})
    return plano

if __name__ == "__main__":
    p = montar()
    json.dump(p, io.open(os.path.join(BASE, "plano_ep25.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    fila = {c["id"]: c for c in json.load(io.open(os.path.join(BASE, "reels_ep25.json"), encoding="utf-8"))["cortes"]}
    for d in p:
        onde = "FEED  (capa de IA + colab)" if d["feed"] else "so Reels"
        print(f"{d['dia']}  {d['id']}  {onde:26s} {fila[d['id']]['titulo'][:44]}")

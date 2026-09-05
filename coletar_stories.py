# -*- coding: utf-8 -*-
"""Fotografa os Stories do dia antes de eles expirarem.

O metodo do Afonso tem duas reguas de Story e as duas so' existem se alguem
medir todo dia: **o primeiro story do dia precisa passar de 10% dos seguidores**
e **o ultimo precisa ficar em pelo menos 40% do primeiro**. A API so' devolve
Stories enquanto eles estao no ar (24h), entao sem uma coleta diaria o numero
some — foi por isso que a meta existia no plano e nunca teve leitura.

Guarda em `dados/stories.json`, um registro por dia, versionado de proposito:
o runner e' descartavel e o historico e' o produto.

Uso: python coletar_stories.py            # fotografa agora
     python coletar_stories.py --ensaio   # mostra sem gravar
"""
import argparse
import json
import os
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

IG_USER_ID = "17841470188725651"          # @vendanaobra
API = "https://graph.facebook.com/v21.0"
FUSO_BR = timezone(timedelta(hours=-3))
ARQUIVO = Path(__file__).parent / "dados" / "stories.json"
# a v21 aposentou parte das metricas de story; pedimos uma a uma e ficamos com
# as que a conta aceita, em vez de perder a coleta inteira por causa de uma.
METRICAS = ["views", "reach", "replies", "navigation"]


def _token() -> str:
    tok = os.environ.get("META_TOKEN", "").strip()
    if tok:
        return tok
    caminho = r"C:\Users\NOTE\Desktop\Perffec\Claude\meta_system_user_token.txt"
    if os.path.exists(caminho):
        return open(caminho, encoding="utf-8").read().strip()
    raise SystemExit("Sem token: defina META_TOKEN ou salve meta_system_user_token.txt")


def _get(endpoint, campos):
    url = f"{API}/{endpoint}?" + urllib.parse.urlencode(campos)
    try:
        with urllib.request.urlopen(url, timeout=60) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        return {"__erro": e.read().decode(errors="replace")[:200]}


def stories(token):
    r = _get(f"{IG_USER_ID}/stories",
             {"fields": "id,media_type,timestamp,permalink", "access_token": token})
    if "__erro" in r:
        raise SystemExit("Graph API: " + r["__erro"])
    return r.get("data", [])


def metricas(token, story_id):
    out = {}
    for m in METRICAS:
        r = _get(f"{story_id}/insights", {"metric": m, "access_token": token})
        for d in r.get("data", []):
            v = d.get("values", [{}])[0].get("value")
            if isinstance(v, dict):
                out.update({f"{d['name']}_{k}": x for k, x in v.items()})
            elif v is not None:
                out[d["name"]] = v
    return out


def seguidores(token):
    r = _get(IG_USER_ID, {"fields": "followers_count", "access_token": token})
    return r.get("followers_count", 0)


def main():
    a = argparse.ArgumentParser()
    a.add_argument("--ensaio", action="store_true")
    o = a.parse_args()

    token = _token()
    hoje = datetime.now(FUSO_BR).strftime("%Y-%m-%d")
    itens = []
    for s in sorted(stories(token), key=lambda x: x["timestamp"]):
        t = datetime.fromisoformat(s["timestamp"].replace("+0000", "+00:00")).astimezone(FUSO_BR)
        itens.append({"id": s["id"], "hora": t.strftime("%H:%M"),
                      "tipo": s.get("media_type"), **metricas(token, s["id"])})

    registro = {"dia": hoje, "seguidores": seguidores(token),
                "colhido_em": datetime.now(FUSO_BR).strftime("%Y-%m-%d %H:%M"),
                "stories": itens}

    vistas = [i.get("views", i.get("reach", 0)) for i in itens]
    print(f"{hoje}: {len(itens)} stories no ar")
    for i in itens:
        print(f"  {i['hora']}  {i.get('views', i.get('reach', 0)):>6}  {i.get('replies', 0)} resp.")
    if vistas:
        piso = registro["seguidores"] * 0.10
        print(f"  1o: {vistas[0]} (meta {piso:.0f} = 10% dos seguidores) — "
              f"{'ok' if vistas[0] >= piso else 'ABAIXO'}")
        if vistas[0]:
            queda = vistas[-1] / vistas[0]
            print(f"  ultimo/1o: {queda:.0%} (meta 40%) — {'ok' if queda >= 0.40 else 'ABAIXO'}")

    if o.ensaio:
        return
    ARQUIVO.parent.mkdir(exist_ok=True)
    hist = json.loads(ARQUIVO.read_text(encoding="utf-8")) if ARQUIVO.exists() else []
    hist = [h for h in hist if h["dia"] != hoje] + [registro]
    hist.sort(key=lambda h: h["dia"])
    ARQUIVO.write_text(json.dumps(hist, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"gravado em {ARQUIVO} ({len(hist)} dias)")


if __name__ == "__main__":
    main()

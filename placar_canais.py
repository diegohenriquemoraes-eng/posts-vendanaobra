"""Placar semanal dos canais — o que cada porta trouxe, medido.

POR QUE EXISTE
--------------
Em 05/09/2026 havia tres canais publicando sozinhos (YouTube, Threads, blog) e
NENHUMA medicao. Foi exatamente assim que o canal do YouTube ficou quatro meses
parado sem ninguem notar, e que o Short do ES do outro projeto caiu 80% sem
alarme. Canal sem placar nao e canal, e fe.

A regra combinada com o Diego: **canal que em 60 dias nao trouxe nenhum lead sai
do motor**. Este arquivo e o que torna essa regra aplicavel.

O QUE ELE MEDE — E O QUE NAO MEDE, DE PROPOSITO
------------------------------------------------
Mede: Google (Search Console), YouTube (canal e videos da semana), Threads e
Instagram (contagem), e a SAUDE DA ESTEIRA (publicou o que a config manda?).

NAO mede, por falta de acesso e nao por esquecimento:
- **Visitas por canal**: o site nao tem Google Analytics. O que existe e a rota
  `/r/<origem>`, que carimba UTM mas nao guarda nada — Vercel serverless nao tem
  onde escrever. Ligar isso exige um contador (Vercel Analytics, no painel do
  Diego) ou fazer o `/r/` avisar o Apps Script.
- **Leads por origem**: ficam na planilha do Apps Script "Leads Venda na Obra".
  O web app so aceita POST; nao devolve relatorio. Para ler daqui, o Diego
  precisa colar no editor uma funcao `doGet` que exporte o resumo.
- **Vendas**: Kiwify, sem integracao. O caminho e um webhook da Kiwify.

Enquanto essas tres faltarem, o placar responde "quanta gente alcancei" e nao
"quanto vendi". Melhor dizer isso na cara do que fingir um numero.

Uso:
    python placar_canais.py                # semana corrente
    python placar_canais.py --dias 30
    python placar_canais.py --md placar.md
"""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import re
import urllib.parse
import urllib.request
from datetime import date, datetime, timedelta, timezone

AQUI = pathlib.Path(__file__).parent
IG_USER_ID = "17841470188725651"
SITE_GSC = "https://vendanaobra.com.br/"
CANAL_YT = "UCU_nFNvsJfHAG2Vdfkyx1UQ"


# --------------------------------------------------------------------------- #
# fontes
# --------------------------------------------------------------------------- #
def _google(perfil: str):
    """Credenciais Google a partir de env (nuvem) ou arquivo local."""
    from google.oauth2.credentials import Credentials

    bruto = os.environ.get(perfil, "").strip()
    if bruto:
        return Credentials.from_authorized_user_info(json.loads(bruto))
    nomes = {
        "GSC_TOKEN": "token_searchconsole_vendanaobra.json",
        "YT_TOKEN": "token_youtube_vendanaobra.json",
    }
    p = pathlib.Path(r"C:\Users\NOTE\Desktop\Perffec\Claude") / nomes[perfil]
    if not p.exists():
        return None
    return Credentials.from_authorized_user_file(str(p))


def google_busca(dias: int) -> dict | None:
    """Impressoes, cliques e as consultas do periodo, contra o periodo anterior."""
    cred = _google("GSC_TOKEN")
    if not cred:
        return None
    from googleapiclient.discovery import build

    sc = build("searchconsole", "v1", credentials=cred)
    # O Search Console leva ~2 dias para fechar os dados; pedir ate ontem
    # devolve periodo incompleto e a comparacao mente.
    fim = date.today() - timedelta(days=2)
    ini = fim - timedelta(days=dias - 1)
    ant_fim = ini - timedelta(days=1)
    ant_ini = ant_fim - timedelta(days=dias - 1)

    def puxar(a: date, b: date, dim: list[str], n: int = 10):
        return sc.searchanalytics().query(
            siteUrl=SITE_GSC,
            body={
                "startDate": a.isoformat(),
                "endDate": b.isoformat(),
                "dimensions": dim,
                "rowLimit": n,
            },
        ).execute().get("rows", [])

    agora = puxar(ini, fim, ["query"], 250)
    antes = puxar(ant_ini, ant_fim, ["query"], 250)
    paginas = puxar(ini, fim, ["page"], 10)

    soma = lambda rows, c: sum(r[c] for r in rows)
    return {
        "de": ini.isoformat(),
        "ate": fim.isoformat(),
        "impressoes": soma(agora, "impressions"),
        "cliques": soma(agora, "clicks"),
        "impressoes_antes": soma(antes, "impressions"),
        "cliques_antes": soma(antes, "clicks"),
        "consultas": sorted(agora, key=lambda r: -r["impressions"])[:8],
        "paginas": sorted(paginas, key=lambda r: -r["impressions"])[:6],
    }


def youtube(dias: int) -> dict | None:
    cred = _google("YT_TOKEN")
    if not cred:
        return None
    from googleapiclient.discovery import build

    yt = build("youtube", "v3", credentials=cred)
    canal = yt.channels().list(part="snippet,statistics", mine=True).execute()["items"][0]

    estado = {}
    p = AQUI / "distribuidos.json"
    if p.exists():
        estado = json.loads(p.read_text(encoding="utf-8"))

    corte = datetime.now(timezone.utc) - timedelta(days=dias)
    da_semana = [
        v
        for v in estado.values()
        if v.get("youtube")
        and datetime.fromisoformat(v["distribuido_em"]) >= corte
    ]

    videos = []
    if da_semana:
        ids = [v["youtube"] for v in da_semana]
        for i in range(0, len(ids), 50):
            r = yt.videos().list(part="snippet,statistics", id=",".join(ids[i : i + 50])).execute()
            for it in r.get("items", []):
                videos.append(
                    {
                        "titulo": it["snippet"]["title"],
                        "views": int(it["statistics"].get("viewCount", 0)),
                        "id": it["id"],
                    }
                )
    videos.sort(key=lambda v: -v["views"])
    return {
        "inscritos": int(canal["statistics"].get("subscriberCount", 0)),
        "views_totais": int(canal["statistics"].get("viewCount", 0)),
        "videos_totais": int(canal["statistics"].get("videoCount", 0)),
        "publicados": len(da_semana),
        "videos": videos,
        # A fila NAO esta no estado: o estado guarda o que ja saiu. Pendente e
        # Reel da conta que ainda nao aparece la. A primeira versao contava
        # dentro do estado e dava sempre zero.
        "pendentes": _reels_pendentes(estado),
    }


def _reels_pendentes(estado: dict, dias: int = 45) -> int:
    tok = os.environ.get("META_TOKEN", "").strip()
    if not tok:
        p = pathlib.Path(r"C:\Users\NOTE\Desktop\Perffec\Claude\meta_system_user_token.txt")
        tok = p.read_text().strip() if p.exists() else ""
    if not tok:
        return -1
    url = f"https://graph.facebook.com/v21.0/{IG_USER_ID}/media?" + urllib.parse.urlencode(
        {"fields": "id,media_product_type,timestamp", "limit": 50, "access_token": tok}
    )
    try:
        with urllib.request.urlopen(url, timeout=45) as r:
            dados = json.load(r)
    except Exception:
        return -1
    corte = datetime.now(timezone.utc) - timedelta(days=dias)
    return sum(
        1
        for m in dados.get("data", [])
        if m.get("media_product_type") == "REELS"
        and datetime.fromisoformat(m["timestamp"].replace("+0000", "+00:00")) >= corte
        and m["id"] not in estado
    )


def instagram(dias: int) -> dict | None:
    tok = os.environ.get("META_TOKEN", "").strip()
    if not tok:
        p = pathlib.Path(r"C:\Users\NOTE\Desktop\Perffec\Claude\meta_system_user_token.txt")
        tok = p.read_text().strip() if p.exists() else ""
    if not tok:
        return None

    def get(caminho: str, campos: dict) -> dict:
        url = f"https://graph.facebook.com/v21.0/{caminho}?" + urllib.parse.urlencode(
            {**campos, "access_token": tok}
        )
        with urllib.request.urlopen(url, timeout=45) as r:
            return json.load(r)

    perfil = get(IG_USER_ID, {"fields": "followers_count,media_count"})
    midias = get(
        f"{IG_USER_ID}/media", {"fields": "media_product_type,timestamp", "limit": 60}
    ).get("data", [])
    corte = datetime.now(timezone.utc) - timedelta(days=dias)
    recentes = [
        m
        for m in midias
        if datetime.fromisoformat(m["timestamp"].replace("+0000", "+00:00")) >= corte
    ]
    return {
        "seguidores": perfil.get("followers_count", 0),
        "publicacoes": len(recentes),
        "reels": sum(1 for m in recentes if m.get("media_product_type") == "REELS"),
    }


def threads(dias: int) -> dict:
    p = AQUI / "threads_publicados.json"
    if not p.exists():
        return {"semana": 0, "total": 0}
    d = json.loads(p.read_text(encoding="utf-8"))
    corte = datetime.now(timezone.utc) - timedelta(days=dias)
    return {
        "semana": sum(1 for v in d.values() if datetime.fromisoformat(v["em"]) >= corte),
        "total": len(d),
    }


def blog(dias: int) -> int:
    """Posts publicados no periodo, lidos do /llms.txt do proprio site."""
    try:
        req = urllib.request.Request(
            "https://vendanaobra.com.br/llms.txt", headers={"User-Agent": "VNO/1.0"}
        )
        with urllib.request.urlopen(req, timeout=45) as r:
            txt = r.read().decode("utf-8")
        datas = re.findall(r"publicado em (\d{4}-\d{2}-\d{2})", txt)
        corte = date.today() - timedelta(days=dias)
        return sum(1 for d in datas if date.fromisoformat(d) >= corte)
    except Exception:
        return -1


# --------------------------------------------------------------------------- #
def variacao(agora: int, antes: int) -> str:
    if antes == 0:
        return "novo" if agora else "—"
    pct = (agora - antes) / antes * 100
    return f"{pct:+.0f}%"


def montar(dias: int) -> str:
    g = google_busca(dias)
    y = youtube(dias)
    i = instagram(dias)
    t = threads(dias)
    b = blog(dias)
    hoje = date.today().isoformat()

    L = [f"# Placar dos canais — {hoje} (últimos {dias} dias)", ""]

    L += ["## Quanto cada porta publicou", "", "| Canal | No período | Total |", "|---|---:|---:|"]
    L.append(f"| YouTube Shorts | {y['publicados'] if y else '?'} | {y['videos_totais'] if y else '?'} |")
    L.append(f"| Threads (blog, com link) | {t['semana']} | {t['total']} |")
    L.append(f"| Instagram | {i['publicacoes'] if i else '?'} ({i['reels'] if i else '?'} Reels) | — |")
    L.append(f"| Blog | {b if b >= 0 else '?'} | — |")
    L.append("")

    if g:
        L += [
            "## Google — a Colheita",
            "",
            f"Período medido: {g['de']} a {g['ate']} (o Search Console fecha os dados com 2 dias de atraso).",
            "",
            "| | Agora | Antes | |",
            "|---|---:|---:|---|",
            f"| Impressões | {g['impressoes']} | {g['impressoes_antes']} | {variacao(g['impressoes'], g['impressoes_antes'])} |",
            f"| Cliques | {g['cliques']} | {g['cliques_antes']} | {variacao(g['cliques'], g['cliques_antes'])} |",
            "",
        ]
        if g["consultas"]:
            L += ["**O que trouxe gente**", "", "| consulta | impressões | cliques | posição |", "|---|---:|---:|---:|"]
            for r in g["consultas"]:
                L.append(
                    f"| {r['keys'][0]} | {r['impressions']} | {r['clicks']} | {r['position']:.0f} |"
                )
            L.append("")
        else:
            L += ["Nenhuma consulta no período — o site ainda é invisível para a busca.", ""]

    if y:
        L += [
            "## YouTube",
            "",
            f"{y['inscritos']} inscritos · {y['views_totais']} views no total · "
            f"{y['pendentes']} Reels ainda na fila para subir.",
            "",
        ]
        if y["videos"]:
            L += ["| vídeo da semana | views |", "|---|---:|"]
            for v in y["videos"]:
                L.append(f"| [{v['titulo']}](https://youtu.be/{v['id']}) | {v['views']} |")
            L.append("")

    if i:
        L += ["## Instagram", "", f"{i['seguidores']} seguidores.", ""]

    L += [
        "## O que este placar ainda NÃO sabe",
        "",
        "- **Visitas por canal** — o site não tem Google Analytics; a rota `/r/<origem>` "
        "carimba a origem mas não guarda nada.",
        "- **Leads por origem** — ficam na planilha do Apps Script, que só aceita escrita. "
        "Para ler daqui, é preciso publicar lá uma função que devolva o resumo.",
        "- **Vendas** — a Kiwify não está integrada; o caminho é um webhook dela.",
        "",
        "Enquanto isso, este placar responde *quanta gente alcancei*, não *quanto vendi*.",
    ]
    return "\n".join(L)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--dias", type=int, default=7)
    p.add_argument("--md", help="grava o placar num arquivo")
    args = p.parse_args()

    texto = montar(args.dias)
    print(texto)
    if args.md:
        pathlib.Path(args.md).write_text(texto, encoding="utf-8")


if __name__ == "__main__":
    main()

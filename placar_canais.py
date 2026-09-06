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

**Visitas e leads por canal entraram em 05/09/2026.** Sao lidos do coletor
(`medicao-webapp-url.txt`), um Apps Script SEPARADO do que recebe os leads — o
de leads esta em producao e nao foi tocado. O coletor nao guarda nada de
pessoal: so canal, midia, campanha e caminho da pagina.

⚠ A leitura so vale a partir de 05/09/2026, e a atribuicao e de PRIMEIRO TOQUE:
quem chegou pelo Short, voltou pelo Google e so entao preencheu o Raio-X conta
para o YouTube. Atribuir ao Google premiaria o canal errado.

NAO mede, por falta de acesso e nao por esquecimento:
- **Vendas**: Kiwify, sem integracao. O caminho e um webhook da Kiwify.

Enquanto essa faltar, o placar responde "quem trouxe gente" e nao "quanto
vendi". Melhor dizer isso na cara do que fingir um numero.

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
COLETOR = "https://script.google.com/macros/s/AKfycby7m9HPEKBHfWJqU1WJv8xr9RuK2TbyDdcN9Up7gJ0Y-t91VzCg2e13W8yJ7qKOx-4p/exec"


def origens(dias: int) -> dict | None:
    """Visitas e leads por canal, do coletor.

    Falhar aqui nao derruba o placar: o resto da medicao continua valendo, e um
    placar que nao chega e pior que um placar incompleto.
    """
    try:
        req = urllib.request.Request(
            f"{COLETOR}?dias={dias}", headers={"User-Agent": "VendaNaObra/1.0"}
        )
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read())
    except Exception as e:
        print(f"coletor indisponivel: {str(e)[:100]}")
        return None


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

    o = origens(dias)
    if o:
        visitas, leads = o.get("visitas", {}), o.get("leads", {})
        L += ["## De onde veio quem entrou no site", ""]
        if visitas:
            total = sum(visitas.values())
            L += [
                f"{total} sessão(ões) no período. Atribuição de **primeiro toque**.",
                "",
                "| origem | sessões | leads |",
                "|---|---:|---:|",
            ]
            for chave, n in sorted(visitas.items(), key=lambda x: -x[1]):
                L.append(f"| {chave} | {n} | {leads.get(chave, 0)} |")
            orfaos = [k for k in leads if k not in visitas]
            for chave in orfaos:
                L.append(f"| {chave} | — | {leads[chave]} |")
            L.append("")
        else:
            L += [
                "Nenhuma sessão registrada. Ou ninguém entrou, ou os links "
                "publicados ainda não passam pelo `/r/<origem>`.",
                "",
            ]
        if not leads:
            L += ["Nenhum lead no período.", ""]

    L += [
        "## O que este placar ainda NÃO sabe",
        "",
        "- **Vendas** — a Kiwify não está integrada; o caminho é um webhook dela. "
        "É a última peça que falta para o placar dizer *quanto vendi* e não só "
        "*quem trouxe gente*.",
        "- **Quem entra e não volta** — o coletor conta uma sessão, não a jornada. "
        "Saber que o visitante do LinkedIn lê três páginas e o do YouTube uma só "
        "exigiria rastrear navegação, que é justamente o que se decidiu não fazer.",
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

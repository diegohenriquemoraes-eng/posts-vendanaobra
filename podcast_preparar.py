"""Transforma os vídeos longos do canal em episódios de podcast.

POR QUE ISSO EXISTE
-------------------
O vendedor de esquadria passa o dia dirigindo entre obras. Ele não para para
ver um Reel, mas ouve — e não existe podcast de venda de esquadria no Brasil.
O custo de produção aqui é ZERO conteúdo novo: o canal do @vendanaobra tem 16
vídeos de 4 minutos ou mais, gravados pelo próprio Diego, que hoje somam
poucas dezenas de views cada. É acervo morto virando canal.

O DESENHO, E O MOTIVO DE CADA ESCOLHA
-------------------------------------
- **A hospedagem é a Release do GitHub**, não o repositório. MP3 commitado
  incha o Git para sempre; anexo de Release tem URL pública estável e não entra
  no histórico. Mesma decisão do Canteiro.
- **Ordem cronológica**: podcast tem começo. Diferente do YouTube, onde o vídeo
  do dia tem de sair no dia, aqui o acervo vira uma temporada.
- **Mono, 64 kbps**: é voz. Estéreo e 128 kbps dobram o arquivo sem mudar nada
  no ouvido de quem escuta no alto-falante do celular dentro do carro.
- O feed RSS NÃO mora aqui: quem serve é o `/podcast.xml` do site, que lê este
  `podcast_episodios.json` pela URL crua do GitHub. Assim o endereço do feed é
  do domínio do Diego (Spotify e Apple guardam esse endereço para sempre) e a
  produção continua onde estão as ferramentas.

Uso:
    python podcast_preparar.py --limite 3
    python podcast_preparar.py --listar
"""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import re
import subprocess
import sys
import tempfile
from datetime import datetime, timezone

AQUI = pathlib.Path(__file__).parent
ESTADO = AQUI / "podcast_episodios.json"
REPO = "diegohenriquemoraes-eng/posts-vendanaobra"
TAG = "podcast"
MINIMO_S = 240  # abaixo de 4 min não é episódio, é corte


def segundos(iso: str) -> int:
    m = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", iso)
    h, mi, s = [int(x or 0) for x in m.groups()]
    return h * 3600 + mi * 60 + s


def videos_longos() -> list[dict]:
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build

    bruto = os.environ.get("YT_TOKEN", "").strip()
    if bruto:
        cred = Credentials.from_authorized_user_info(json.loads(bruto))
    else:
        p = pathlib.Path(r"C:\Users\NOTE\Desktop\Perffec\Claude\token_youtube_vendanaobra.json")
        cred = Credentials.from_authorized_user_file(str(p))

    yt = build("youtube", "v3", credentials=cred)
    up = yt.channels().list(part="contentDetails", mine=True).execute()["items"][0][
        "contentDetails"
    ]["relatedPlaylists"]["uploads"]

    ids, tok = [], None
    while True:
        r = yt.playlistItems().list(
            part="contentDetails", playlistId=up, maxResults=50, pageToken=tok
        ).execute()
        ids += [i["contentDetails"]["videoId"] for i in r["items"]]
        tok = r.get("nextPageToken")
        if not tok:
            break

    saida = []
    for i in range(0, len(ids), 50):
        v = yt.videos().list(
            part="snippet,contentDetails", id=",".join(ids[i : i + 50])
        ).execute()
        for it in v["items"]:
            d = segundos(it["contentDetails"]["duration"])
            if d < MINIMO_S:
                continue
            saida.append(
                {
                    "id": it["id"],
                    "titulo": it["snippet"]["title"],
                    "descricao": (it["snippet"]["description"] or "").strip(),
                    "publicado": it["snippet"]["publishedAt"],
                    "duracao": d,
                }
            )
    saida.sort(key=lambda x: x["publicado"])  # cronológico: podcast tem começo
    return saida


def garantir_release(gh_env: dict) -> None:
    r = subprocess.run(
        ["gh", "release", "view", TAG, "--repo", REPO],
        capture_output=True, text=True, env=gh_env,
    )
    if r.returncode == 0:
        return
    subprocess.run(
        [
            "gh", "release", "create", TAG,
            "--repo", REPO,
            "--title", "Podcast Venda na Obra",
            "--notes",
            "Arquivos de audio dos episodios. Servem ao feed RSS "
            "https://vendanaobra.com.br/podcast.xml — nao apagar: os tocadores "
            "guardam estas URLs.",
        ],
        check=True, env=gh_env,
    )


def baixar_mp3(video_id: str, destino: pathlib.Path) -> pathlib.Path:
    saida = destino / f"{video_id}.mp3"
    subprocess.run(
        [
            "yt-dlp", "-f", "bestaudio", "-x",
            "--audio-format", "mp3",
            # Voz em mono a 64k: no alto-falante do celular dentro do carro,
            # estereo a 128k so dobra o arquivo.
            "--postprocessor-args", "ffmpeg:-b:a 64k -ac 1 -ar 44100",
            "-o", str(destino / f"{video_id}.%(ext)s"),
            f"https://www.youtube.com/watch?v={video_id}",
        ],
        check=True, capture_output=True, text=True,
    )
    if not saida.exists():
        raise RuntimeError(f"yt-dlp nao gerou {saida.name}")
    return saida


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--limite", type=int, default=3)
    p.add_argument("--listar", action="store_true")
    args = p.parse_args()

    estado = json.loads(ESTADO.read_text(encoding="utf-8")) if ESTADO.exists() else {}
    todos = videos_longos()
    pendentes = [v for v in todos if v["id"] not in estado]

    print(f"{len(todos)} videos com {MINIMO_S//60}min+ · {len(pendentes)} ainda sem episodio")
    if args.listar:
        for v in pendentes:
            print(f"  {v['publicado'][:10]} {v['duracao']//60:3d}min  {v['titulo'][:60]}")
        return
    if not pendentes:
        return

    gh_env = dict(os.environ)
    if "GH_TOKEN" not in gh_env:
        cred = subprocess.run(
            ["git", "credential", "fill"],
            input="protocol=https\nhost=github.com\n\n",
            capture_output=True, text=True,
        ).stdout
        m = re.search(r"^password=(.+)$", cred, re.M)
        if m:
            gh_env["GH_TOKEN"] = m.group(1)
    garantir_release(gh_env)

    with tempfile.TemporaryDirectory() as tmp:
        pasta = pathlib.Path(tmp)
        for v in pendentes[: args.limite]:
            print(f"\n[{v['publicado'][:10]}] {v['titulo']}")
            try:
                mp3 = baixar_mp3(v["id"], pasta)
            except Exception as e:
                print(f"  falhou o download: {str(e)[:150]}")
                continue
            tamanho = mp3.stat().st_size
            print(f"  audio: {tamanho/1e6:.1f} MB")
            subprocess.run(
                ["gh", "release", "upload", TAG, str(mp3), "--repo", REPO, "--clobber"],
                check=True, env=gh_env, capture_output=True, text=True,
            )
            url = f"https://github.com/{REPO}/releases/download/{TAG}/{v['id']}.mp3"
            estado[v["id"]] = {
                **v,
                "arquivo": url,
                "bytes": tamanho,
                "preparado_em": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            }
            ESTADO.write_text(
                json.dumps(estado, ensure_ascii=False, indent=2), encoding="utf-8"
            )
            print(f"  no ar: {url}")


if __name__ == "__main__":
    main()

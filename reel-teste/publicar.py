# Publica no @vendanaobra como REEL DE TESTE (so para quem nao segue), no dia e hora da fila_teste.json.
# Pedido do Diego, 25/11/2026: "sempre no reel teste", legenda so "Siga o @vendanaobra", 21h.
#
# Por que video_url e nao upload direto: em 22/11 o upload resumable com trial_params saiu como Reel comum
# (a API ignorou). A documentacao da Meta so mostra trial_params com video_url. O MP4 e a capa sobem por
# alguns minutos como asset do Release "reel-teste" do repo PUBLICO posts-vendanaobra; o Instagram baixa
# e o asset e apagado em seguida.
#
#   python reel-teste/publicar.py            publica o item cuja hora ja chegou e que ainda nao saiu
#   python reel-teste/publicar.py --ensaio   mostra o que sairia agora e para
import json, os, subprocess, sys, time, urllib.error, urllib.parse, urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

AQUI = Path(__file__).resolve().parent
FILA = AQUI / "fila.json"
LOG = AQUI / "log.txt"
IG = "17841470188725651"
API = "https://graph.facebook.com/v24.0/"
HOSPEDE = os.environ.get("GITHUB_REPOSITORY", "diegohenriquemoraes-eng/posts-vendanaobra")
TAG = "reel-teste"
BRT = timezone(timedelta(hours=-3))


def agora():
    return datetime.now(BRT)


def log(*a):
    linha = f"[{agora():%d/%m %H:%M:%S}] " + " ".join(str(x) for x in a)
    print(linha, flush=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(linha + "\n")


def token():
    if os.environ.get("IG_PUBLICAR_TOKEN"):
        return os.environ["IG_PUBLICAR_TOKEN"].strip()
    return (Path(os.environ["APPDATA"]) / "vno-direct-segredos" / "meta_token.txt").read_text().strip()


def chamada(url, dados=None, espera=180):
    try:
        return json.load(urllib.request.urlopen(urllib.request.Request(url, data=dados), timeout=espera))
    except urllib.error.HTTPError as e:
        return {"erro_http": e.code, "corpo": e.read().decode(errors="replace")[:500]}
    except Exception as e:
        return {"erro": str(e)[:300]}


def gh(*args):
    return subprocess.run(["gh", *args], capture_output=True, text=True)


def drive_token():
    d = urllib.parse.urlencode({"client_id": os.environ["DRIVE_CLIENT_ID"], "client_secret": os.environ["DRIVE_CLIENT_SECRET"],
                                "refresh_token": os.environ["DRIVE_REFRESH"], "grant_type": "refresh_token"}).encode()
    return json.load(urllib.request.urlopen("https://oauth2.googleapis.com/token", d))["access_token"]


def hospedar(item):
    """Baixa o video do Drive e sobe video + capa como asset publico. Devolve (url_video, url_capa, nomes)."""
    vid, capa = AQUI / f"{item['nome']}.mp4", AQUI / item["capa"]
    req = urllib.request.Request(f"https://www.googleapis.com/drive/v3/files/{item['video_drive']}?alt=media",
                                 headers={"Authorization": "Bearer " + drive_token()})
    with urllib.request.urlopen(req) as r, open(vid, "wb") as f:
        while True:
            b = r.read(8 << 20)
            if not b:
                break
            f.write(b)
    log("baixado do Drive:", vid.stat().st_size // 1000000, "MB")
    if gh("release", "view", TAG, "-R", HOSPEDE).returncode:
        gh("release", "create", TAG, "-R", HOSPEDE, "--title", "Reel de teste (temporario)",
           "--notes", "Arquivos temporarios para a Graph API do Instagram; apagados depois da publicacao.")
    r = gh("release", "upload", TAG, str(vid), str(capa), "-R", HOSPEDE, "--clobber")
    if r.returncode:
        raise SystemExit(f"upload do asset falhou: {r.stderr[:300]}")
    base = f"https://github.com/{HOSPEDE}/releases/download/{TAG}/"
    return base + vid.name, base + capa.name, [vid.name, capa.name]


def limpar(nomes):
    for n in nomes:
        gh("release", "delete-asset", TAG, n, "-R", HOSPEDE, "--yes")


def esperar(tok, cid, voltas=60):
    for _ in range(voltas):
        time.sleep(10)
        s = chamada(API + cid + "?" + urllib.parse.urlencode({"fields": "status_code,status", "access_token": tok}))
        if s.get("status_code") == "FINISHED":
            return True
        if s.get("status_code") in ("ERROR", "EXPIRED"):
            log("container:", s)
            return False
    return False


def salvar(fila):
    FILA.write_text(json.dumps(fila, ensure_ascii=False, indent=1), encoding="utf-8")


def devido(fila):
    hoje, hora = agora().strftime("%Y-%m-%d"), agora().strftime("%H:%M")
    return next((x for x in fila if not x.get("media_id") and x["data"] <= hoje
                 and (x["data"] < hoje or x["hora"] <= hora)), None)


def main():
    fila = json.loads(FILA.read_text(encoding="utf-8"))
    if "--checar" in sys.argv:   # confere Drive, Release e token do Instagram sem publicar nada
        at = drive_token()
        for x in fila:
            m = json.load(urllib.request.urlopen(urllib.request.Request(
                f"https://www.googleapis.com/drive/v3/files/{x['video_drive']}?fields=name,size",
                headers={"Authorization": "Bearer " + at})))
            print(x["nome"], "drive ok", int(m["size"]) // 1000000, "MB")
        if gh("release", "view", TAG, "-R", HOSPEDE).returncode:
            print("release criado:", gh("release", "create", TAG, "-R", HOSPEDE, "--title", "Reel de teste (temporario)",
                                         "--notes", "Arquivos temporarios para a Graph API do Instagram.").returncode == 0)
        else:
            print("release ok")
        print("instagram:", chamada(API + IG + "?" + urllib.parse.urlencode({"fields": "username", "access_token": token()})).get("username"))
        return
    item = devido(fila)
    if not item:
        log("nada devido agora")
        return
    if "--ensaio" in sys.argv:
        print(item["nome"], item["data"], item["hora"], "|", item["legenda"])
        return
    tok = token()
    if item.get("estado") in ("publicando", "falhou"):   # media_publish pode ter saido mesmo com erro (22/11): nao repetir
        log("ATENCAO: rodada anterior parou no meio; conferir no Instagram antes de tentar de novo")
        return
    url_v, url_c, nomes = hospedar(item)
    try:
        r = chamada(API + IG + "/media", urllib.parse.urlencode({
            "media_type": "REELS", "video_url": url_v, "cover_url": url_c, "caption": item["legenda"],
            "trial_params": json.dumps({"graduation_strategy": item.get("graduacao", "SS_PERFORMANCE")}),
            "access_token": tok}).encode())
        if "id" not in r:
            log("container recusado:", r)
            return
        cid = r["id"]
        log(item["nome"], "container", cid)
        if not esperar(tok, cid):
            log("FALHOU antes de publicar; a proxima rodada tenta de novo")
            return
        item["estado"] = "publicando"
        salvar(fila)
        p = {}
        for n in range(3):
            p = chamada(API + IG + "/media_publish", urllib.parse.urlencode(
                {"creation_id": cid, "access_token": tok}).encode())
            if "id" in p:
                break
            log("media_publish tentativa", n + 1, p)
            time.sleep(20)
        if "id" not in p:
            item["estado"] = "falhou"
            salvar(fila)
            return
        m = chamada(API + p["id"] + "?" + urllib.parse.urlencode(
            {"fields": "permalink,media_product_type,is_shared_to_feed", "access_token": tok}))
        item.update(media_id=p["id"], permalink=m.get("permalink"), estado="publicado",
                    publicado=agora().strftime("%d/%m %H:%M"))
        salvar(fila)
        log("PUBLICADO como teste", item["nome"], m.get("permalink"), m)
    finally:
        limpar(nomes)


if __name__ == "__main__":
    main()

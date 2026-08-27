# -*- coding: utf-8 -*-
"""Sobe para o GitHub, em lotes, os Reels que o `producao.py` vai deixando prontos.

Sem isto o Actions publica o arquivo **antigo**: o video vem de
`raw.githubusercontent`, nao da maquina. E o push nao pode ser feito de uma vez
so — o `.git` passou de 500 MB e um lote grande estoura qualquer tempo limite.

Roda junto com o `producao.py --daemon`. Pode ser interrompido e retomado.

Uso:
    python subir.py --daemon      # fica subindo enquanto houver coisa nova
    python subir.py               # sobe o que estiver pronto agora e sai
"""
import os, subprocess, sys, time

BASE = os.path.dirname(os.path.abspath(__file__))
LOTE = 4          # videos por commit: lotes maiores estouram o tempo do push


def _git(*args, timeout=3600):
    return subprocess.run(["git"] + list(args), cwd=BASE, capture_output=True,
                          text=True, timeout=timeout)


def novos():
    r = _git("status", "--porcelain", "midia/reels")
    out = []
    for linha in r.stdout.splitlines():
        caminho = linha[3:].strip().strip('"')
        if caminho.endswith((".mp4", ".jpg")):
            out.append(caminho)
    return sorted(out)


def subir_lote(arquivos):
    _git("add", *arquivos)
    ids = ", ".join(sorted({os.path.basename(a)[:2] for a in arquivos}))
    r = _git("-c", "user.email=diegohenriquemoraes@gmail.com", "commit", "-q",
             "-m", "Cortes %s no formato novo" % ids)
    if r.returncode != 0 and "nothing to commit" not in (r.stdout + r.stderr):
        print("commit falhou:", r.stdout[-300:], r.stderr[-300:], flush=True)
        return False
    print("commitado: %s — subindo..." % ids, flush=True)
    p = _git("push", "origin", "main")
    if p.returncode != 0:
        print("push falhou:", p.stderr[-400:], flush=True)
        return False
    print("no ar: %s" % ids, flush=True)
    return True


def uma_volta():
    arquivos = novos()
    if not arquivos:
        return False
    for i in range(0, len(arquivos), LOTE):
        if not subir_lote(arquivos[i:i + LOTE]):
            return False
    return True


if __name__ == "__main__":
    daemon = "--daemon" in sys.argv
    while True:
        try:
            fez = uma_volta()
        except subprocess.TimeoutExpired:
            print("push passou de 1h; tentando de novo", flush=True)
            fez = True
        if not daemon:
            break
        if not fez:
            time.sleep(180)

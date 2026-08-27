# -*- coding: utf-8 -*-
"""Refaz os Reels do EP25 na ordem da fila, um por vez, alimentando o painel.

Renderiza tudo que ja tem legenda revisada em `legendas_ep25.json` e ainda nao
esta pronto. Pode ser interrompido e retomado: o estado vive em `progresso.json`.
"""
import json, io, os, subprocess, sys, time
import painel

def ordem():
    """Ordem de render = ordem de publicacao: o proximo a sair fica pronto antes."""
    return [cid for cid, _, _ in painel.roteiro()]

def por_id():
    fila = json.load(io.open("reels_ep25.json", encoding="utf-8"))["cortes"]
    return {c["id"]: c for c in fila}

def pendentes():
    legs = json.load(io.open("legendas_ep25.json", encoding="utf-8"))
    est = painel.ler()
    mapa = por_id()
    out = []
    for cid in ordem():
        c = mapa.get(cid)
        if not c: continue
        arq = c["arquivo"]
        if arq not in legs: continue
        if est.get(arq, {}).get("status") in ("pronto", "publicado", "antigo"): continue
        out.append((cid, arq))
    return out

def render(cid, arq):
    painel.marcar(arq, status="rodando", legenda=True)
    t0 = time.time()
    r = subprocess.run([sys.executable, "montar_reel.py", "--id", cid, "--modo", "split"],
                       capture_output=True, text=True)
    if r.returncode != 0:
        painel.marcar(arq, status="erro", erro=(r.stderr or "")[-400:])
        print(f"{cid}: FALHOU\n{r.stderr[-800:]}", flush=True)
        return False
    gasto = time.time() - t0
    pronto = os.path.join("saida", "reels", arq)
    if not os.path.exists(pronto):
        painel.marcar(arq, status="erro", erro="arquivo nao saiu")
        return False
    # entra no lugar do antigo, que e' de onde o publicador serve
    subprocess.run(["cmd", "/c", "copy", "/y",
                    pronto.replace("/", "\\"), os.path.join("midia", "reels", arq)],
                   capture_output=True)
    painel.marcar(arq, status="pronto", render_s=round(gasto))
    print(f"{cid}: pronto em {gasto/60:.1f} min", flush=True)
    return True

if __name__ == "__main__":
    while True:
        p = pendentes()
        if not p:
            print("nada pendente; esperando legenda nova...", flush=True)
            if "--daemon" not in sys.argv: break
            time.sleep(120); continue
        for cid, arq in p:
            render(cid, arq)

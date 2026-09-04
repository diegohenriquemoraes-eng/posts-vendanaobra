# -*- coding: utf-8 -*-
"""Trava cada troca de camera de `cameras.json` no FRAME exato do master.

Por que existe (04/09/2026): o detector (`cameras.py`) roda a 5 fps e ainda
suaviza com moda movel de +-5 amostras, entao as fronteiras saiam em multiplos
de 0,2 s e erravam de 1 a 2 frames — medido nos cortes 27 e 14: -67 ms a +33 ms.
Como o recorte 9:16 muda junto com a camera, esse punhado de frames saia com o
crop do angulo VELHO sobre o frame do angulo NOVO: na tela vira um pisca com um
enquadramento que nao pega nenhum dos dois. Foi o que o Diego viu.

Corte de camera de podcast e' SECO (conferido no master, sem crossfade), entao a
troca e' o maior salto de diferenca entre frames vizinhos — pico de 50x a 680x a
mediana da janela, nao ha ambiguidade. Aqui a janela de +-0,6 s em volta da
fronteira antiga e' varrida no fps NATIVO (30000/1001, nao 30) e a fronteira
passa a ser o pts exato do primeiro frame do angulo novo.

Uso:  python analise/refinar_cameras.py            (relatorio, nao grava)
      python analise/refinar_cameras.py --gravar   (regrava cameras.json)
"""
import json, subprocess, argparse, shutil, os, sys
import numpy as np

MASTER = "master/ep25.mp4"
JANELA = 0.6        # quanto varrer de cada lado da fronteira antiga
W, H = 96, 54       # resolucao da comparacao: o salto de corte e' global
PICO_MIN = 8.0      # pico/mediana abaixo disso nao e' corte seco: nao mexe


def janela(ini, dur):
    """Pixels reduzidos + o pts REAL de cada frame, do mesmo comando.

    O casamento tem de vir do proprio ffmpeg: `ffprobe -read_intervals` comeca
    no keyframe ANTERIOR ao intervalo, entao a lista dele nao alinha com o que o
    `-ss` entrega — e quando as duas listas calhavam do mesmo tamanho o casamento
    saia deslocado, jogando a fronteira 0,5 a 0,9 s fora do lugar. Com
    `-copyts` + `showinfo` o pts sai do mesmo passe que gera os pixels.

    O corte da janela e' por `-frames:v`, nao por `-t`: com `-copyts` os
    timestamps de saida sao os do master (4317 s, e nao 0), e `-t` medido contra
    eles descarta o trecho inteiro — o que fazia o refinador devolver "sem corte
    claro" para tudo.
    """
    p = subprocess.run(
        ["ffmpeg", "-v", "info", "-copyts", "-ss", f"{ini:.3f}", "-i", MASTER,
         "-frames:v", str(int(dur * 30) + 4), "-vf", f"scale={W}:{H},showinfo",
         "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
        capture_output=True)
    n = W * H * 3
    px = np.frombuffer(p.stdout[:len(p.stdout) // n * n],
                       dtype=np.uint8).reshape(-1, H, W, 3).astype(np.float32)
    pts = []
    for lin in p.stderr.decode("utf-8", "ignore").splitlines():
        i = lin.find("pts_time:")
        if i >= 0:
            try: pts.append(float(lin[i + 9:].split()[0]))
            except ValueError: pass
    return px, pts


def refinar(t0, fim_antigo):
    """-> (fim_novo, pico_relativo) ou (fim_antigo, 0.0) se nao houver corte claro."""
    ini = t0 + fim_antigo - JANELA
    dur = 2 * JANELA
    px, pts = janela(ini, dur)
    if len(px) < 4 or len(pts) < len(px):
        return fim_antigo, 0.0
    d = np.abs(np.diff(px, axis=0)).mean(axis=(1, 2, 3))
    k = int(d.argmax())
    rel = float(d[k] / max(float(np.median(d)), 1e-6))
    if rel < PICO_MIN:
        return fim_antigo, rel
    # o frame k+1 e' o primeiro do angulo novo, no pts real do master
    return round(pts[k + 1] - t0, 6), rel   # 3 casas ja custaram um frame no render


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gravar", action="store_true", help="regrava analise/cameras.json")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")

    jan = json.load(open("analise/janelas.json"))
    cams = json.load(open("analise/cameras.json"))
    mexidos = duvidosos = 0

    for arq in sorted(cams):
        if arq not in jan:
            continue
        t0 = jan[arq]["inicio"]
        cs = cams[arq]
        for i in range(len(cs) - 1):
            antigo = cs[i]["fim"]
            novo, rel = refinar(t0, antigo)
            dif = (novo - antigo) * 30000 / 1001
            if rel < PICO_MIN:
                duvidosos += 1
                print(f"  ? {arq[:2]} {cs[i]['cam']}->{cs[i+1]['cam']} {antigo:7.2f} "
                      f"sem corte claro (pico {rel:.1f}x) — mantido")
                continue
            if abs(dif) >= 0.5:
                mexidos += 1
                print(f"  · {arq[:2]} {cs[i]['cam']}->{cs[i+1]['cam']} "
                      f"{antigo:7.2f} -> {novo:7.3f}  ({dif:+.1f} frames, pico {rel:.0f}x)")
            cs[i]["fim"] = novo
            cs[i + 1]["ini"] = novo

    print(f"\n{mexidos} fronteiras movidas, {duvidosos} sem corte claro.")
    if a.gravar:
        bkp = "analise/cameras.antes-do-refino.json"
        if not os.path.exists(bkp):
            shutil.copy("analise/cameras.json", bkp)
        json.dump(cams, open("analise/cameras.json", "w"), ensure_ascii=False, indent=1)
        print("gravado em analise/cameras.json (backup em " + bkp + ")")
    else:
        print("nada gravado — rode com --gravar")


if __name__ == "__main__":
    main()

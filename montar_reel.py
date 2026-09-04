# -*- coding: utf-8 -*-
"""Monta o Reel 9:16 de um corte do EP25 seguindo quem fala.

Regra de ouro (Diego, 27/08/2026):
  * quando ELE fala, o quadro tem de estar nele;
  * quando a AUDREY fala, o quadro vai para ela — ou fica nele ouvindo, se a
    unica camera disponivel naquele instante for a fechada nele;
  * quando os dois se revezam em ritmo parecido, entra o split empilhado
    (ele em cima, ela embaixo), que so existe enquanto o plano aberto esta no ar.

Ritmo: nenhum plano passa de PLANO_MAX; dentro de uma fala longa o corte
alterna entre plano medio e fechado (punch-in), que e' o beat de 2-3 s dos
cortes de podcast que rendem. Corte sempre seco.
"""
import json, os, subprocess, sys, argparse, math

MASTER = "master/ep25.mp4"
AUDIO = "master/ep25.m4a"
SAIDA = "saida/reels"
PASSO = 0.2          # resolucao da linha do tempo de fala
PLANO_MIN = 1.6      # nenhum plano mais curto que isso
PLANO_MAX = 3.2      # nenhum plano mais longo que isso
PLANO_CURTO = 0.7    # abaixo disso o plano vira piscada e some no plano vizinho
FALA_MIN = 1.2       # troca de falante so vale se durar isso
FPS_MASTER = 30000 / 1001   # o master e' 29,97, nao 30
MEIO_FRAME = 1 / (2 * FPS_MASTER)

# --- recortes no master 1920x1080 -------------------------------------------
# medio e fechado do mesmo angulo: a alternancia entre eles e' o punch-in
#
# MEDIDOS, nao chutados (04/09/2026). Ate aqui eram retangulos escritos a mao em
# agosto e nunca conferidos: no plano aberto a Audrey saia 168 px a esquerda do
# centro (encostada na borda do vertical) e na camera fechada dela o desvio era
# de 120 px. `analise/medir_enquadramento.py` roda o MediaPipe Face Detection em
# 50 frames sorteados de cada camera e devolve a mediana do centro do rosto e da
# linha dos olhos — 50/50 de deteccao, dispersao p10-p90 de ~50 px.
#
#   camera        centro do rosto   olhos
#   D  (fechada)      990            282
#   A  (fechada)      854            299
#   WA (aberto)       372            305
#   WD (aberto)      1525            252
#
# Regra de composicao, a mesma dos editores de video: x centraliza o rosto e y
# poe os OLHOS a ~1/3 do topo do quadro (nao no meio — o terco de baixo e' da
# legenda queimada). Onde o recorte ja usa a altura toda do master nao ha folga
# em y e ele fica em 0, com os olhos caindo em 26-28%.
#
# Nao ha "look room" (dar mais espaco para o lado que a pessoa olha): a tecnica
# existe e e' correta, mas desloca o rosto do centro de proposito — e centralizar
# foi justamente o que o Diego pediu. Se um dia entrar, sao ~5% da largura.
CROPS = {
    ("D", "medio"):  (608, 1080,  686,  0),
    ("D", "perto"):  (500,  889,  740,  0),
    ("A", "medio"):  (608, 1080,  550,  0),
    ("A", "perto"):  (500,  889,  604,  6),
    ("WD", "medio"): (540,  960, 1255,  0),
    ("WD", "perto"): (456,  810, 1297,  0),
    ("WA", "medio"): (540,  960,  102,  0),
    ("WA", "perto"): (456,  810,  144, 38),
}
SPLIT = {"D": (760, 675, 1145, 27), "A": (760, 675, 0, 80)}

def segmentos(linha, passo=PASSO, minimo=FALA_MIN):
    """String 'DDDAAA...' -> [(ini, fim, quem)] sem trechos menores que `minimo`."""
    segs, ini = [], 0
    for i in range(1, len(linha) + 1):
        if i == len(linha) or linha[i] != linha[ini]:
            segs.append([ini * passo, i * passo, linha[ini]])
            ini = i
    mudou = True
    while mudou and len(segs) > 1:
        mudou = False
        for i, s in enumerate(segs):
            if s[1] - s[0] >= minimo: continue
            if i == 0: segs[1][0] = s[0]
            elif i == len(segs) - 1: segs[-2][1] = s[1]
            else:
                meio = (s[0] + s[1]) / 2
                segs[i-1][1] = meio; segs[i+1][0] = meio
            segs.pop(i); mudou = True
            break
    # funde vizinhos iguais
    out = [segs[0]]
    for s in segs[1:]:
        if s[2] == out[-1][2]: out[-1][1] = s[1]
        else: out.append(s)
    return [(round(a, 2), round(b, 2), q) for a, b, q in out]

def fala_das_legendas(blocos, dur, reserva=None):
    """Quem fala, tirado da legenda revisada — que e' onde o falante e' certo.

    O detector de voz por timbre erra justamente na fronteira curta ("nao, total")
    e era ele que colocava o quadro na pessoa errada. A legenda ja passou por
    revisao humana, entao ela manda; o detector so preenche o que sobra.
    """
    n = int(round(dur / PASSO))
    linha = list(reserva[:n].ljust(n, "D")) if reserva else ["D"] * n
    for b in blocos:
        i, j = int(b["ini"] / PASSO), min(n, int(round(b["fim"] / PASSO)))
        for k in range(max(0, i), j):
            linha[k] = b.get("quem", "D")
    # o intervalo entre dois blocos segue o bloco anterior (respiro, nao troca)
    ult = None
    for k in range(n):
        if linha[k] in "DA": ult = linha[k]
        elif ult: linha[k] = ult
    return "".join(linha)

def camera_em(cams, t):
    for c in cams:
        if c["ini"] <= t < c["fim"]: return c["cam"]
    return cams[-1]["cam"] if cams else "D"

def dialogo(falas, a, b):
    """Ha revezamento parecido entre a e b?"""
    dentro = [(max(a, x), min(b, y), q) for x, y, q in falas if y > a and x < b]
    if len(dentro) < 3: return False
    tot = b - a
    td = sum(y - x for x, y, q in dentro if q == "D")
    ta = tot - td
    return min(td, ta) / tot >= 0.28

def plano_para(quem, cam):
    """Que fonte usar para mostrar `quem`, dado o que a camera mostra."""
    if cam == "W": return "WD" if quem == "D" else "WA"
    if cam == quem: return quem          # camera fechada em quem fala
    return cam                            # so ha o outro em quadro: fica nele

def unir_curtos(edl, cams, minimo=PLANO_CURTO):
    """Funde no vizinho todo plano curto demais para ser lido como plano.

    De onde vinham: quando uma troca de FALANTE cai poucos decimos antes de uma
    troca de CAMERA do master, o beat era cortado na camera e sobrava um caco de
    0,2 s — seis quadros. Na tela isso nao le como corte, le como piscada (o
    Diego pegou isso no corte 07, em 28/08/2026).

    So funde com o plano anterior quando os dois estao na MESMA camera do
    master; senao o recorte de um angulo cairia sobre o outro, que e' o bug do
    quadro vazio.
    """
    out = []
    for e in edl:
        if e["fim"] - e["ini"] >= minimo or not out:
            out.append(dict(e))
            continue
        ant = out[-1]
        if camera_em(cams, ant["ini"] + 0.1) == camera_em(cams, e["ini"] + 0.1):
            ant["fim"] = e["fim"]
        else:
            out.append(dict(e))
    # o que sobrou curto esta' no INICIO de uma camera nova (nao havia vizinho
    # anterior na mesma camera): esse funde com o seguinte
    i = 0
    while i < len(out) - 1:
        if out[i]["fim"] - out[i]["ini"] < minimo and \
           camera_em(cams, out[i]["ini"] + 0.1) == camera_em(cams, out[i+1]["ini"] + 0.1):
            out[i+1]["ini"] = out[i]["ini"]
            out.pop(i)
            continue
        i += 1
    # o ultimo tambem nao pode ficar curto
    while len(out) > 1 and out[-1]["fim"] - out[-1]["ini"] < minimo:
        if camera_em(cams, out[-2]["ini"] + 0.1) != camera_em(cams, out[-1]["ini"] + 0.1):
            break
        out[-2]["fim"] = out[-1]["fim"]
        out.pop()
    return out


def montar_edl(falas, cams, dur, modo="cameras"):
    edl = []
    for a, b, quem in falas:
        t = a
        alterna = 0
        while t < b - 0.05:
            fim = min(b, t + PLANO_MAX)
            # um plano nunca atravessa uma troca de camera do master: se atravessar,
            # o recorte do angulo velho cai sobre o angulo novo e o quadro fica vazio
            for c in cams:
                if t + 0.05 < c["fim"] < fim: fim = c["fim"]
            if b - fim < PLANO_MIN: fim = b
            for c in cams:
                if t + 0.05 < c["fim"] < fim: fim = c["fim"]
            cam = camera_em(cams, t + 0.1)
            # split so no plano aberto e so quando ha revezamento
            usa_split = cam == "W" and (modo == "split" or
                        dialogo(falas, max(0, t - 3), min(dur, fim + 3)))
            if usa_split:
                edl.append({"ini": round(t, 2), "fim": round(fim, 2), "tipo": "split"})
            else:
                fonte = plano_para(quem, cam)
                nivel = "perto" if alterna % 2 else "medio"
                edl.append({"ini": round(t, 2), "fim": round(fim, 2), "tipo": "solo",
                            "fonte": fonte, "nivel": nivel, "quem": quem, "cam": cam})
            alterna += 1
            t = fim
    return unir_curtos(edl, cams)

def filtro_solo(fonte, nivel, dur):
    """Recorte FIXO. O quadro so muda quando muda o plano.

    Ate 04/09/2026 havia um pan senoidal de +-6 px por plano
    (`{x}+6*sin(2*PI*t/dur)`), posto para o quadro nao parecer parado. Como
    cada plano dura 1,6 a 3,2 s, o seno fechava um ciclo inteiro dentro do
    plano: na tela isso nao le como movimento de camera, le como CAMERA
    TREMENDO — foi a reclamacao do Diego ao ver os cortes 27 e 14 prontos.
    Camera estatica dentro do plano, corte seco na troca: e' assim que o
    formato de podcast e' editado."""
    w, h, x, y = CROPS[(fonte, nivel)]
    return f"crop={w}:{h}:{x}:{y},scale=1080:1920:flags=bicubic,setsar=1"

def filtro_split():
    wd, hd, xd, yd = SPLIT["D"]
    wa, ha, xa, ya = SPLIT["A"]
    return (f"[0:v]crop={wd}:{hd}:{xd}:{yd},scale=1080:960:flags=bicubic,setsar=1[cima];"
            f"[0:v]crop={wa}:{ha}:{xa}:{ya},scale=1080:960:flags=bicubic,setsar=1[baixo];"
            f"[cima][baixo]vstack=inputs=2[v]")

def render(edl, t0, tmp):
    partes = []
    for i, e in enumerate(edl):
        dur = round(e["fim"] - e["ini"], 3)
        if dur <= 0.05: continue
        alvo = os.path.join(tmp, f"p{i:03d}.mp4")
        # comeca MEIO FRAME antes do pts alvo: assim a janela [ini, ini+dur)
        # sempre contem o primeiro frame do plano e nunca o primeiro do
        # seguinte. Sem essa folga, arredondar a fronteira para 3 casas (0,4 ms)
        # bastava para o ffmpeg entregar 1 frame do angulo NOVO ainda com o crop
        # do VELHO — o pisca que o Diego viu na troca de camera (04/09/2026).
        base = ["ffmpeg", "-v", "error", "-y",
                "-ss", f"{t0 + e['ini'] - MEIO_FRAME:.6f}",
                "-i", MASTER, "-t", f"{dur:.6f}", "-an"]
        if e["tipo"] == "split":
            cmd = base + ["-filter_complex", filtro_split(), "-map", "[v]"]
        else:
            cmd = base + ["-vf", filtro_solo(e["fonte"], e["nivel"], dur)]
        cmd += ["-r", "30", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
                "-pix_fmt", "yuv420p", alvo]
        subprocess.run(cmd, check=True)
        partes.append(alvo)
    return partes

# --- legenda queimada --------------------------------------------------------
CABECA = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: L,Instagram Sans Medium,72,&H00FFFFFF,&H00FFFFFF,&H90000000,&H00000000,0,0,0,0,100,100,0,0,1,4,0,2,90,90,470,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

def tempo_ass(t):
    h = int(t // 3600); m = int(t % 3600 // 60); s = t % 60
    return f"{h}:{m:02d}:{s:05.2f}"

def escrever_ass(blocos, alvo, margem_v=470):
    linhas = [CABECA.replace("MarginV, Encoding\nStyle: L,Instagram Sans Medium,72,&H00FFFFFF,&H00FFFFFF,&H90000000,&H00000000,0,0,0,0,100,100,0,0,1,4,0,2,90,90,470,1",
                             "MarginV, Encoding\nStyle: L,Instagram Sans Medium,72,&H00FFFFFF,&H00FFFFFF,&H90000000,&H00000000,0,0,0,0,100,100,0,0,1,4,0,2,90,90,%d,1" % margem_v)]
    for b in blocos:
        txt = b["txt"].replace("\n", "\\N")
        linhas.append(f"Dialogue: 0,{tempo_ass(b['ini'])},{tempo_ass(b['fim'])},L,,0,0,0,,{{\\blur6}}{txt}")
    open(alvo, "w", encoding="utf-8").write("\n".join(linhas) + "\n")

def finalizar(partes, t0, dur, ass, alvo, tmp):
    lista = os.path.join(tmp, "lista.txt")
    with open(lista, "w", encoding="utf-8") as f:
        for p in partes:
            f.write("file '%s'\n" % os.path.abspath(p).replace("\\", "/"))
    mudo = os.path.join(tmp, "mudo.mp4")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0",
                    "-i", lista, "-c", "copy", mudo], check=True)
    vf = "ass=" + ass.replace("\\", "/").replace(":", "\\:") + ":fontsdir=fontes"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", mudo,
                    "-ss", f"{t0:.3f}", "-i", AUDIO, "-t", f"{dur:.3f}",
                    "-vf", vf, "-map", "0:v", "-map", "1:a",
                    "-c:v", "libx264", "-preset", "medium", "-crf", "20",
                    "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k",
                    "-movflags", "+faststart", "-shortest", alvo], check=True)

def blocos_de(arq, legendas):
    if arq in legendas: return legendas[arq]
    raise SystemExit("Sem legenda revisada para " + arq)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--id", help="numero do corte, ex 03")
    ap.add_argument("--todos", action="store_true")
    ap.add_argument("--modo", default="cameras", choices=["cameras", "split"],
                    help="cameras: quadro segue quem fala · split: empilha os dois sempre que der")
    ap.add_argument("--sufixo", default="")
    a = ap.parse_args()
    jan = json.load(open("analise/janelas.json"))
    cams = json.load(open("analise/cameras.json"))
    fala = json.load(open("analise/fala.json"))
    legs = json.load(open("legendas_ep25.json", encoding="utf-8"))
    os.makedirs(SAIDA, exist_ok=True)
    alvos = sorted(jan) if a.todos else [k for k in sorted(jan) if k.startswith(a.id + "-")]
    for arq in alvos:
        j = jan[arq]
        blocos = blocos_de(arq, legs)
        falas = segmentos(fala_das_legendas(blocos, j["dur"], fala.get(arq)))
        edl = montar_edl(falas, cams[arq], j["dur"], a.modo)
        tmp = os.path.join("saida", "tmp", arq[:2] + a.modo)
        os.makedirs(tmp, exist_ok=True)
        for f in os.listdir(tmp): os.remove(os.path.join(tmp, f))
        ass = os.path.join(tmp, "leg.ass")
        escrever_ass(blocos, ass)
        partes = render(edl, j["inicio"], tmp)
        alvo = os.path.join(SAIDA, arq[:-4] + a.sufixo + ".mp4")
        finalizar(partes, j["inicio"], j["dur"], ass, alvo, tmp)
        tds = round(sum(e["fim"]-e["ini"] for e in edl if e["tipo"] == "split"), 1)
        print(f"{arq}: {len(edl)} planos, split {tds}s -> {alvo}", flush=True)

if __name__ == "__main__":
    main()

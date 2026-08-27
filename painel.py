# -*- coding: utf-8 -*-
"""Painel de acompanhamento da refacao dos 27 Reels do EP25.

Reescreve `painel.html` a cada peca que fica pronta. A pagina se atualiza
sozinha, entao basta deixar aberta.
"""
import json, io, os, time
from datetime import datetime, timedelta, timezone

BASE = os.path.dirname(os.path.abspath(__file__))
FUSO = timezone(timedelta(hours=-3))
ESTADO = os.path.join(BASE, "progresso.json")
ALVO = os.path.join(BASE, "painel.html")

# ja publicados, em ordem; daqui para a frente quem manda e' o plano_ep25.json
SAIRAM = ["01", "02", "04", "03"]
PLANO = os.path.join(BASE, "plano_ep25.json")

def ler():
    if os.path.exists(ESTADO):
        return json.load(io.open(ESTADO, encoding="utf-8"))
    return {}

def salvar(d):
    json.dump(d, io.open(ESTADO, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

def data_de(i):
    return datetime(2026, 8, 24, tzinfo=FUSO) + timedelta(days=i)

def roteiro():
    """[(id, data, vai_para_o_feed)] — os que ja sairam, depois o plano."""
    out = [(cid, data_de(i), True) for i, cid in enumerate(SAIRAM)]
    if os.path.exists(PLANO):
        for d in json.load(io.open(PLANO, encoding="utf-8")):
            a, m, dd = (int(x) for x in d["dia"].split("-"))
            out.append((d["id"], datetime(a, m, dd, tzinfo=FUSO), bool(d.get("feed"))))
    return out

def gerar():
    est = ler()
    fila = json.load(io.open(os.path.join(BASE, "reels_ep25.json"), encoding="utf-8"))["cortes"]
    por_id = {c["id"]: c for c in fila}
    agora = datetime.now(FUSO)

    linhas, prontos, seg_prontos, seg_total, tempo_gasto = [], 0, 0.0, 0.0, 0.0
    for cid, dia, no_feed in roteiro():
        c = por_id.get(cid)
        if not c: continue
        e = est.get(c["arquivo"], {})
        dur = float(c["duracao"])
        seg_total += dur
        st = e.get("status", "pendente")
        if st == "antigo":
            seg_total -= dur
        if st in ("pronto", "publicado"):
            prontos += 1; seg_prontos += dur
            tempo_gasto += float(e.get("render_s") or 0)
        linhas.append({"id": cid, "titulo": c["titulo"], "dur": dur, "status": st,
                       "quando": e.get("quando", ""), "render_s": e.get("render_s"),
                       "data": dia, "legenda": e.get("legenda", False), "feed": no_feed})

    ritmo = (tempo_gasto / seg_prontos) if seg_prontos else 14.0   # s de render por s de video
    faltam_s = seg_total - seg_prontos
    eta = timedelta(seconds=faltam_s * ritmo)
    fim = agora + eta

    def chip(l):
        if l["status"] == "antigo":    return ("já saiu (formato antigo)", "esp")
        if l["status"] == "publicado": return ("publicado", "pub")
        if l["status"] == "pronto":    return ("pronto", "ok")
        if l["status"] == "rodando":   return ("renderizando", "run")
        if l["legenda"]:               return ("legenda revisada", "leg")
        return ("na fila", "esp")

    trs = []
    for l in linhas:
        txt, cls = chip(l)
        no_prazo = l["data"].date() >= agora.date() or l["status"] in ("pronto", "publicado", "antigo")
        atraso = "" if no_prazo else " atrasado"
        rs = f"{l['render_s']/60:.0f} min" if l.get("render_s") else "—"
        onde = ('<span class="tag feed">feed + Reels</span>' if l["feed"]
                else '<span class="tag so">só Reels</span>')
        trs.append(
            f'<tr class="{cls}"><td class="id">{l["id"]}</td>'
            f'<td class="tit">{l["titulo"]}</td>'
            f'<td class="num">{l["dur"]:.0f}s</td>'
            f'<td class="dt{atraso}">{l["data"]:%d/%m}</td>'
            f'<td>{onde}</td>'
            f'<td><span class="tag {cls}">{txt}</span></td>'
            f'<td class="num">{rs}</td></tr>')

    no_escopo = [l for l in linhas if l["status"] != "antigo"]
    pct = 100.0 * prontos / len(no_escopo) if no_escopo else 0
    rodando = next((l for l in linhas if l["status"] == "rodando"), None)
    agora_txt = (f'Renderizando agora: <b>{rodando["id"]} · {rodando["titulo"]}</b>'
                 if rodando else "Nenhum render em andamento.")
    horas = eta.total_seconds() / 3600

    html = f"""<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8">
<meta http-equiv="refresh" content="30">
<title>Reels do EP25 — produção</title>
<style>
 :root {{ --navy:#071025; --champagne:#D8B888; --texto:#EAF0F8; --apoio:#A9B7CC; --linha:#1B2942; }}
 * {{ box-sizing:border-box; }}
 body {{ margin:0; padding:32px 24px 60px; background:var(--navy); color:var(--texto);
        font-family:"Segoe UI",system-ui,sans-serif; }}
 .wrap {{ max-width:900px; margin:0 auto; }}
 h1 {{ font-size:24px; margin:0 0 4px; font-weight:600; }}
 .sub {{ color:var(--apoio); font-size:15px; margin-bottom:28px; }}
 .cartoes {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(150px,1fr)); gap:14px; margin-bottom:26px; }}
 .cartao {{ background:#0C1A31; border:1px solid var(--linha); border-radius:12px; padding:16px 18px; }}
 .cartao .n {{ font-size:30px; font-weight:600; color:var(--champagne); line-height:1.1; }}
 .cartao .r {{ font-size:13px; color:var(--apoio); margin-top:6px; }}
 .barra {{ height:12px; background:#0C1A31; border:1px solid var(--linha); border-radius:99px; overflow:hidden; margin-bottom:10px; }}
 .barra i {{ display:block; height:100%; width:{pct:.1f}%; background:var(--champagne); }}
 .agora {{ color:var(--apoio); font-size:14px; margin-bottom:26px; }}
 .agora b {{ color:var(--texto); }}
 table {{ width:100%; border-collapse:collapse; font-size:14px; }}
 th {{ text-align:left; color:var(--apoio); font-weight:500; padding:8px 10px; border-bottom:1px solid var(--linha); font-size:13px; }}
 td {{ padding:9px 10px; border-bottom:1px solid #121F36; }}
 .id {{ color:var(--apoio); font-variant-numeric:tabular-nums; }}
 .tit {{ color:var(--texto); }}
 .num {{ text-align:right; color:var(--apoio); font-variant-numeric:tabular-nums; }}
 .dt {{ color:var(--apoio); font-variant-numeric:tabular-nums; }}
 .dt.atrasado {{ color:#FF9B8A; font-weight:600; }}
 .tag {{ font-size:12px; padding:3px 9px; border-radius:99px; white-space:nowrap; }}
 .tag.pub {{ background:#123A22; color:#7BE0A0; }}
 .tag.ok  {{ background:#0F2E4A; color:#7FC4F5; }}
 .tag.run {{ background:#3A2E0F; color:var(--champagne); }}
 .tag.leg {{ background:#1B2942; color:#C2D2E8; }}
 .tag.esp {{ background:#141F33; color:var(--apoio); }}
 .tag.feed {{ background:#2E2410; color:var(--champagne); font-weight:600; }}
 .tag.so {{ background:#141F33; color:var(--apoio); }}
 tr.run td {{ background:#0F1930; }}
 .rodape {{ margin-top:28px; color:var(--apoio); font-size:13px; line-height:1.6; }}
</style></head><body><div class="wrap">
<h1>Reels do EP25 — refação no formato novo</h1>
<div class="sub">Split empilhado, quadro seguindo quem fala, legenda revisada à mão.
Só os marcados <b>feed + Reels</b> aparecem na grade do perfil e levam capa de IA e colab
com a Aluparts; o resto sai só na aba de Reels. Esta página se atualiza sozinha a cada 30 s.</div>

<div class="barra"><i></i></div>
<div class="cartoes">
 <div class="cartao"><div class="n">{prontos}/{len(no_escopo)}</div><div class="r">peças prontas</div></div>
 <div class="cartao"><div class="n">{horas:.1f} h</div><div class="r">de trabalho restante</div></div>
 <div class="cartao"><div class="n">{fim:%d/%m %H:%M}</div><div class="r">previsão de término</div></div>
 <div class="cartao"><div class="n">{faltam_s/60:.0f} min</div><div class="r">de vídeo ainda por refazer</div></div>
</div>
<div class="agora">{agora_txt}</div>

<table>
<tr><th>#</th><th>Corte</th><th>Duração</th><th>Vai ao ar</th><th>Onde</th><th>Situação</th><th>Render</th></tr>
{chr(10).join(trs)}
</table>

<div class="rodape">
 Ritmo medido: {ritmo:.0f} segundos de máquina para cada segundo de vídeo.
 A previsão se ajusta sozinha conforme as peças saem.<br>
 Atualizado em {agora:%d/%m/%Y %H:%M:%S}.
</div>
</div></body></html>"""
    io.open(ALVO, "w", encoding="utf-8").write(html)
    return ALVO

def marcar(arq, **campos):
    est = ler()
    e = est.setdefault(arq, {})
    e.update(campos)
    e["quando"] = datetime.now(FUSO).strftime("%d/%m %H:%M")
    salvar(est)
    gerar()

if __name__ == "__main__":
    print(gerar())

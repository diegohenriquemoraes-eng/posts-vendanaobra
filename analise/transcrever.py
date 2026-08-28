# -*- coding: utf-8 -*-
"""Transcricao propria dos cortes, para revisar a legenda com duas fontes.

A legenda automatica do YouTube erra nome proprio e nao pontua; o Whisper erra
outras coisas. Onde as duas concordam a confianca e' alta; onde divergem, a
revisao humana decide. Modelo `small` porque `medium` nao cabe na RAM daqui.
"""
import json, io, os, sys, time
from faster_whisper import WhisperModel

ORDEM = ["10", "05", "09", "11", "06", "12", "08", "07", "24", "16", "23", "19",
         "17", "18", "20", "14", "22", "25", "15", "26", "21", "13", "27",
         "01", "02", "04"]

def arquivos():
    todos = sorted(f for f in os.listdir("midia/reels") if f.endswith(".mp4"))
    por_id = {f[:2]: f for f in todos}
    return [por_id[i] for i in ORDEM if i in por_id]

if __name__ == "__main__":
    alvo = "analise/whisper.json"
    feito = json.load(io.open(alvo, encoding="utf-8")) if os.path.exists(alvo) else {}
    m = WhisperModel("small", device="cpu", compute_type="int8", cpu_threads=3)
    for arq in arquivos():
        if arq in feito: continue
        t0 = time.time()
        segs, _ = m.transcribe(os.path.join("midia/reels", arq), language="pt",
                               beam_size=5, vad_filter=True, condition_on_previous_text=False)
        feito[arq] = [{"ini": round(s.start, 2), "fim": round(s.end, 2), "txt": s.text.strip()}
                      for s in segs]
        json.dump(feito, io.open(alvo, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
        print(f"{arq[:40]:40s} {len(feito[arq]):3d} falas em {time.time()-t0:5.0f}s", flush=True)

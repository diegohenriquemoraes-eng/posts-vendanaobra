# Cortes do Aluparts Podcast #EP25 — 27 Reels, no ar desde 24/08/2026

**Origem:** [#EP25 Construção Civil e Vendas: Como crescer com estratégia](https://www.youtube.com/watch?v=e6clG_KFAPA)
canal [Aluparts](https://www.youtube.com/@Aluparts) · publicado 21/08/2026 · 1h13m · host Audrey Dias.

**Mídia:** os 27 MP4 e as 27 capas vivem em `midia/reels/`. A pasta de trabalho no
Desktop foi apagada em 24/08/2026 — era cópia.

**Páginas de aprovação (capa, legenda e calendário de cada corte):**
lote 1 — https://claude.ai/code/artifact/f7d954b9-5a5b-4656-afff-8c563b86615f
lote 2 — https://claude.ai/code/artifact/2b4d3266-c2cf-4fb8-8a37-5aabd6112a67

---

## O que tem nesta pasta

| Item | O que é |
|---|---|
| `NN-slug.mp4` | Os Reels do lote 1 (01 a 12) — 1080x1920, legenda queimada, sem marca d'água |
| `capas/NN-slug.jpg` | A capa de cada um, com o gancho escrito |
| `lote2/` | Os 15 do lote 2 (13 a 27), com `capas/` e `legendas.json` próprios |
| `legendas.json` | A legenda de post e as hashtags de cada corte |

## Como os vídeos foram feitos

**Enquadramento 9:16 de verdade, sem tarja.** O master do podcast é 1920x1080.
As trocas de câmera foram detectadas quadro a quadro, e o recorte vertical
acompanha: câmera fechada no Diego, câmera fechada na Audrey, e no plano aberto
o recorte fica no lado direito da mesa, onde o Diego está.

**Legenda no padrão dos Reels dele.** Medida no Reel de 12/08/2026: legenda
automática do Instagram — Instagram Sans branca, bloco de 2 a 4 linhas
centralizado no terço inferior, halo escuro suave, caixa de frase normal.
Sem cor de destaque e sem fade: o bloco troca inteiro, e por isso não pisca.
O texto foi corrigido à mão onde o reconhecimento automático errava
("Aldre" → Audrey, "Aloparts" → Aluparts, "esquadrilha" → esquadria).

**Gancho na capa, não no vídeo.** Os Reels dele não têm texto sobreposto nem
assinatura no rodapé — o gancho vai na capa, no padrão da capa da mini-aula
(foto, degradê fechando em preto, etiqueta dourada, título branco).

## Publicação — no ar

O robô está escrito em `Desktop\Projetos\posts-vendanaobra`:
`publicar_reel.py` + `reels_ep25.json` + `.github/workflows/reel-diario.yml`.

- **1 Reel por dia, 09h BRT**, na ordem da fila (aprovado em 24/08/2026).
  09h porque a mini-aula ocupa terça e quinta às 12h — ficam 3h de folga.
- **Colaboração com a @aluparts.oficial** em todo post, gravada no `reels_ep25.json`.
- **Ligado em 24/08/2026.** Corte 01 publicado à mão no mesmo dia; o cron pega o
  próximo a partir de 25/08 e roda sozinho até 19/09.

⚠️ **Collab não se adiciona depois de publicado** — só apagando o post. Alguém da
Aluparts precisa **aceitar o convite em cada post**; enquanto não aceita, o Reel
fica só no perfil do Diego. No corte 01 o convite ficou como *Pending*.

## Ordem de publicação — 27 cortes

| # | Dia | Arquivo | Dur. |
|---|---|---|---|
| 1 | seg 24/08 | `01-5-minutos-para-chorar` | 37s |
| 2 | ter 25/08 | `02-melhor-oferta-nao-melhor-produto` | 60s |
| 3 | qua 26/08 | `04-quem-faz-tudo-nao-faz-nada` | 58s |
| 4 | qui 27/08 | `03-3-segundos-prova-de-fogo-paulista` | 84s |
| 5 | sex 28/08 | `10-nao-culpe-ninguem-pelos-resultados` | 38s |
| 6 | sáb 29/08 | `05-venda-nao-e-dom` | 40s |
| 7 | dom 30/08 | `09-presente-anticiclico` | 60s |
| 8 | seg 31/08 | `11-atendimento-dura-20-minutos` | 34s |
| 9 | ter 01/09 | `06-nunca-marco-no-mesmo-dia` | 87s |
| 10 | qua 02/09 | `12-instagram-com-cara-de-arquitetura` | 51s |
| 11 | qui 03/09 | `08-2-perguntas-antes-do-orcamento` | 88s |
| 12 | sex 04/09 | `07-pedir-x-pegar-indicacao` | 111s |
| 13 | sáb 05/09 | `24-ninguem-sabe-quantos-orcamentos-faz` | 38s |
| 14 | dom 06/09 | `16-aviso-que-nao-vou-fechar-nada` | 43s |
| 15 | seg 07/09 | `23-instagram-e-uma-novela` | 30s |
| 16 | ter 08/09 | `19-network-interessado-nao-interesseiro` | 58s · véspera da Fesqua |
| 17 | qua 09/09 | `17-ninguem-me-ensinou-a-vender` | 60s · **Fesqua** |
| 18 | qui 10/09 | `18-nao-me-posicionava-como-autoridade` | 42s · **Fesqua** |
| 19 | sex 11/09 | `20-posicionamento-antes-de-abrir-a-boca` | 37s · **Fesqua** |
| 20 | sáb 12/09 | `14-demitir-cliente` | 74s · **Fesqua** |
| 21 | dom 13/09 | `22-vai-com-medo` | 39s |
| 22 | seg 14/09 | `25-por-onde-chegam-x-por-onde-fecham` | 68s |
| 23 | ter 15/09 | `15-gestao-emocional-do-vendedor` | 40s |
| 24 | qua 16/09 | `26-funil-de-arquiteto-45-dias` | 59s |
| 25 | qui 17/09 | `21-medo-de-produzir-conteudo` | 41s |
| 26 | sex 18/09 | `13-territorio-x-mapa` | 79s |
| 27 | sáb 19/09 | `27-dois-mentores` | 39s |

Lote 1 (cortes 01 a 12) ordenado por potencial: regra numérica e emoção primeiro,
depois senso comum contrariado, depois história pessoal. Lote 2 (13 a 27) entra em
05/09, e a ordem dele foi montada em cima da **Fesqua, de 9 a 12 de setembro** — os
cortes que falam de feira, stand e network caem na véspera e dentro do evento.

**Duração fora da regra, com aval.** A regra de 28/07 é 25–45s e só 4 dos 12
cabem. Aprovado publicar assim em 24/08/2026: corte de podcast vive do
começo-meio-fim, e cortar em 45s quebra a história.

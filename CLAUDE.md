# posts-vendanaobra

Prepara as peças do Instagram **@vendanaobra** (IG User ID `17841470188725651`).

> ## Quem publica o quê — desde 24/08/2026
>
> | Formato | Como sai hoje |
> |---|---|
> | **Carrossel longo (mini-aula, 4:5)** | **AUTOMÁTICO por API** — `miniaula.yml`, terça e quinta, 12h BRT, com story de reforço. Religado em 24/08/2026 a pedido do Diego: o formato longo está trazendo retorno de comentários. |
> | **Carrossel curto (frase, 1:1)** | **MANUAL** — `preparar.py frase` monta a peça, o Diego posta do celular. Continua assim, sem previsão de voltar. |
>
> Em 21/08/2026 o Diego tinha tirado os dois formatos da API (receio de a
> publicação automática prejudicar a entrega). Em 24/08/2026 ele mandou o
> carrossel longo voltar exatamente à estratégia de antes — mesmo formato,
> leitura, cores, CTA, dias e horários — e manter o curto na mão.
>
> **Travas hoje:** `post-diario.yml` e `rede-de-seguranca.yml` seguem
> `disabled_manually` **e** com o `schedule` comentado, e `publicar.py` só
> publica com `VNO_PUBLICAR_API=1`. `miniaula.yml` e `publicar_miniaula.py`
> estão livres de novo. Não religar o carrossel de frase sem pedido explícito.
>
> Contraponto já registrado, para quando o assunto voltar: a Graph API é o
> caminho oficial (mLabs, Later e Buffer usam) e não há sinal de penalização —
> a queda medida foi de **formato** (mesmo carrossel de frase: 415 views em
> 19/07 contra 135 em 14/08). O que arrisca perfil de verdade é automação
> **não oficial** (robô clicando no Instagram Web) — por isso o `preparar.py`
> nunca posta por navegador.

## Banco de mini-aulas (24/08/2026)

**13 das 40 aulas da pauta estão prontas** (texto + foto): 1, 2, 3, 4, 6, 7, 9, 10,
13, 16, 18, 19, 29. Seis foram escritas em 24/08/2026, no mesmo dia em que o
carrossel longo voltou ao automático — o banco tinha só a aula 7 sobrando e a
quinta seguinte ficaria sem post. Fontes no campo `fonte` de cada aula (e-book
O Cliente Sumiu, Venda Blindada, transcrições). Fila em `sequencia`:
7 → 10 → 13 → 6 → 18 → 16 → 4, sem dois produtos iguais seguidos. Isso cobre
ter/qui até meados de setembro/2026 — **repor antes disso**, senão o workflow
falha com "Nenhuma mini-aula com foto disponivel" e abre issue.

Fotos novas geradas no Gemini com o padrão documental de sempre; a capa da aula
18 saiu com o logotipo "Sesc" no colete dos trabalhadores e o enquadramento foi
recortado para o prédio e a grua (retoque local no logo não funciona: o remendo
fica visível). **Conferir marca de terceiro em toda foto gerada antes de commitar.**

## Fluxo manual (`preparar.py`) — hoje só o carrossel de frase

| Comando | O que faz |
|---|---|
| `python preparar.py frase` | próxima frase da fila → 3 slides 1:1 + legenda |
| `python preparar.py aula --forcar` | mini-aula à mão — só em emergência, ela sai sozinha ter/qui |
| `python preparar.py fila` | o que está preparado e ainda não foi postado |
| `python preparar.py confirmar <slug>` | registra como postado |

Aceita `--id N` para forçar frase/aula específica.

**Entrega em duas mãos:** pasta local
`Desktop\Perffec\Claude\Posts-Manuais\<slug>\` e espelho no Drive
(`gdrive:MKT vendanaobra/Posts manuais/<slug>`, via rclone) — é de lá que o
Diego pega no celular. Dentro: `1.jpg`, `2.jpg`, … na ordem do carrossel,
`legenda.txt` e `COMO-POSTAR.txt`.

**`confirmar` não é opcional.** É o que grava em `publicados.json` /
`publicados_miniaulas.json` e avança o ciclo de CTA (`estado_cta.json`). Sem
confirmar, a próxima preparação repete a mesma peça; enquanto pendente, ela
fica em `fila_manual.json`.

**Story:** a mini-aula volta a publicar o story de reforço por API logo depois
do feed (`gerar_story.py`). No carrossel de frase, que é manual, não há story —
se o Diego quiser, é postar a arte do slide 1 à mão.

## Calendário (referência — hoje é sugestão, não cron)

| Dia | Formato | Preparador |
|---|---|---|
| Seg / Qua / Sex | Carrossel de frase (3 slides, 1080x1080) | manual — `preparar.py frase` |
| Ter / Qui, 12h BRT | Mini-aula (7–9 slides, 4:5, capa com foto) | automático — `miniaula.yml` |

Sem sábado/domingo. Dias fixos porque a cadência antiga ("a cada 2 dias úteis")
derivava e ia colidir com a mini-aula.

## O que rodava até 21/08/2026

Publicava 12h em ponto BRT, com rede de segurança às 13h e 17h. O
`post-diario.yml` estava com o cron comentado desde 17/08 (frase saturada), mas
a **pausa nunca pegou**: a `rede-de-seguranca.yml` seguiu chamando
`publicar.py --garantir` seg/qua/sex e publicou 17/08 e 19/08 assim mesmo.
Lição: pausar um workflow sem olhar quem mais chama o mesmo script não pausa
nada.

> ### ⏸️ Por que o carrossel de frase já estava pausado desde 17/08/2026
>
> Motivo, medido nos insights: o formato saturou. Views do mesmo formato —
> 19/07 = 415 · **20/07 = 539 (pico)** · 23/07 = 479 · 27/07 = 413 · 03/08 = 299 ·
> 12/08 = 183 · **14/08 = 135**. Queda de 75% em 3 semanas.
>
> A **mini-aula continua rodando**: carrossel é o formato mais eficiente da conta
> (índice 2,10 de interação por view, contra 0,85 do Reel). O que saturou foi a
> **frase**, não o carrossel. Ao voltar, **não repetir o formato idêntico** — rever
> diagramação e estrutura de legenda, e voltar 1×/semana em vez de 3×.
>
> **Horário fica 12h.** Cheguei a recomendar 15h com base no painel "Horários mais
> ativos" e estava errado: aquela curva marca 3.961 seguidores ativos às 3h da
> manhã e 575 às 21h, o que não descreve público brasileiro (provavelmente UTC).
> Cruzando a hora real de publicação de 65 posts com as views, e isolando o período
> orgânico (jul/ago, sem tráfego pago): **12h = mediana 545 (a melhor)**, 9h = 427,
> 8h = 366, 15h = 206, 13h = 153. **Regra: nunca trocar horário de robô pelo painel
> de horários mais ativos — só por desempenho real por hora, controlando pela época
> (abril a junho está contaminado por tráfego pago).**

Cada post são **3 slides**. Regra definida pelo Diego em **10/08/2026** (substitui
o formato antigo de frase repetida): o **slide 1 é o gancho** (1º bloco da frase,
fundo branco/letra preta) e o **slide 2 é a continuação do assunto** (blocos
restantes, fundo preto/letra branca) — os dois **nunca repetem** o mesmo texto.
A frase no banco continua sendo um texto só com blocos separados por linha em
branco; `gerar_carrossel.py` corta no 1º bloco. As 49 frases que eram de bloco
único ganharam continuação escrita em 10/08/2026 — **frase nova no banco precisa
ter 2+ blocos**. Referência de formato: `@juliopereira.oficial` — frase
centralizada entre aspas tipográficas, assinatura discreta no rodapé
(`Para vender mais siga o @vendanaobra`). O **slide 3 é o CTA do dia**, em fundo
azul da marca (`#18406F`, amostrado do hero de `vendanaobra.com.br`) e letra
branca — fecha o carrossel com a cor do site (ver seção CTA abaixo).

## Arquivos

| Arquivo | Papel |
|---|---|
| `preparar.py` | **O que se usa hoje**: gera slides + legenda e entrega para postar à mão |
| `fila_manual.json` | Peças preparadas e ainda não confirmadas como postadas |
| `frases.json` | Banco de 120 frases revisadas (vendas, emocional, métricas, gestão) |
| `publicados.json` | O que já foi ao ar — a fila é "banco menos publicados" |
| `estado_cta.json` | Memória do ciclo de CTA: último CTA publicado + data |
| `legenda.py` | Ciclo do CTA do dia + textos do slide 3 e da legenda |
| `gerar_carrossel.py` | Pillow → os 3 JPEGs 1080x1080 (claro, escuro, CTA azul) |
| `publicar.py` | Publicador por API — **desligado 21/08/2026** (exige `VNO_PUBLICAR_API=1`) |
| `miniaulas.json` | Banco das mini-aulas (7 de 40 escritas; pauta em `PAUTA-MINIAULAS.md`) |
| `publicar_miniaula.py` | Mini-aula por API — **no ar de novo desde 24/08/2026** (ter/qui 12h BRT) |
| `gerar_miniaula.py` | Pillow → slides 4:5 (âncoras fixas + fonte única por peça) |
| `gerar_story.py` | Story 1080x1920 com a arte do dia emoldurada |
| `limpar_marca.py` | Remove a marca d'água do Gemini (fundo de textura contínua) |
| `.github/workflows/miniaula.yml` | **Ativo** desde 24/08/2026 — ter/qui 12h BRT + repescagens 13h/17h |
| `.github/workflows/post-diario.yml`, `rede-de-seguranca.yml` | **Disabled + cron comentado** (carrossel de frase é manual) |

## Por que o repositório é público

Herança da publicação por API: a Graph API **não aceita upload de arquivo
local**, exige URL https pública, e as imagens eram servidas por
`raw.githubusercontent.com`. Com a postagem manual isso deixou de importar — o
`preparar.py` não commita imagem nenhuma (as peças vão para `saida/manual/`,
ignorada pelo git, e daí para a pasta de entrega e o Drive). O repo pode virar
privado quando o Diego quiser; hoje segue público só porque ninguém precisou
mudar.

## Rodar na mão

```bash
python preparar.py frase        # prepara a próxima frase para postar no celular
python preparar.py aula --forcar # mini-aula à mão (normalmente sai sozinha)
python preparar.py fila         # o que está esperando ser postado
```

Nada disso precisa de token. O `META_TOKEN` (secret do repo e o arquivo
`Desktop\Perffec\Claude\meta_system_user_token.txt`) só é usado pelo caminho de
API, que está desligado — continua válido caso um dia se volte atrás.

## Armadilhas já pagas

- **Aspas tipográficas no código**: usar `“ ”` literais funciona (o arquivo é
  UTF-8), mas o console do Windows mostra `?` ao imprimir — não é bug.
- **Fonte**: **Instagram Sans** (`tipografia.py`), a mesma das legendas
  automáticas dos Reels do Diego — identidade visual unificada, decidida por
  ele em 12/08/2026. São arquivos **estáticos** por peso em `fontes/`
  (Regular/Medium/Bold; pesos ≥600 usam Bold) — nada de
  `set_variation_by_axes`, que era coisa da Inter variável antiga.
- **JPEG, não PNG**: a Graph API só aceita JPEG para imagem.
- **Layout**: fonte de **tamanho fixo (52px)** para todo post sair com a mesma
  letra, na mesma posição — o bloco é **centralizado no meio da imagem (540)** e
  a margem lateral é folgada (`MARGEM_X = 150`, texto em 780px). A fonte só
  encolhe (até 28) se uma frase excepcionalmente longa não couber em 700px de
  altura; no banco atual nenhuma precisa. Ideal ~180 caracteres, 2 blocos.
- **Banco esgotado**: `publicar.py` aborta e o workflow abre issue. Repor
  `frases.json` antes disso.

## Regras de conteúdo

- **Escopo fechado: vendas, gestão comercial ou empreendedorismo.** Toda frase
  precisa aterrissar em um desses três. Nada de frase de efeito genérica sobre
  disciplina ou produtividade sem âncora comercial — "constância vence talento"
  sozinho está fora; "em vendas, constância vence talento" está dentro.
  Gestão emocional entra sempre pela ótica do vendedor (meta, funil, o não).
- **Inteligência artificial é tema válido** — e desejado, sempre ligada ao
  comercial (prospecção, follow-up, proposta, atendimento).
- **Reforma tributária, política, macroeconomia: fora.** O Diego não trata
  desses assuntos (dito por ele em 19/07/2026). Cenário do setor só entra como
  pano de fundo de uma tese de venda, nunca como assunto do post.
- Escrever "inteligência artificial" por extenso — "IA" fica seco no slide.
- Português impecável — o banco é revisado à mão, não gerado na hora.
- **Slides 1 e 2**: sem hashtag, sem emoji, sem CTA de venda — só a frase. O CTA
  fica no **slide 3** (e é reforçado na legenda).

## CTA — 3º slide, ciclo com memória (`legenda.py`)

Decidido em 21/07/2026 (substitui o esquema 80/20 anterior, a pedido do Diego).
O Diego pediu CTA em 100% dos posts, agora **num 3º slide azul** (`#18406F`, o
azul do site `vendanaobra.com.br`, letra branca) que fecha o carrossel. A regra:

- **O CTA do dia intercala numa ordem cíclica fixa de 14 posições** (refeito em
  **14/08/2026**, substitui o ciclo de 7 com 6 CTAs de produto):
  `envio → Raio-X → pergunta → seguir → pergunta → envio → Venda 10x →
  pergunta → seguir → envio → Raio-X → pergunta → envio → e-book →` volta ao
  início (`CICLO_CTA`). São **4 CTAs de palavra-chave em 14 = exatamente 2 em 7**,
  contra 6 em 7 de antes.

  **Por que mudou:** 6 dos 7 CTAs pediam produto. Somando os Reels, todo post do
  perfil pedia alguma coisa, e o perfil lia como loja — 172 contas engajaram em
  30 dias, de 9.296 seguidores (1,85%). Metricool 2026 (24,3 mi de posts): CTA
  pedindo comentário rende **+202,8% de comentários**; pergunta na legenda, +36,7%.
  Mosseri (22/01/2025) nomeou 3 sinais — tempo de visualização, curtidas e
  **envios** — e o envio é o que mais pesa para alcançar quem **não** segue.
  Nenhum desses sinais é produzido por CTA de produto. O padrão do mercado
  confirma: Concer separa **Reel = alcance sem CTA / carrossel = CTA de palavra**,
  e em 72 legendas de perfis de construção civil e esquadria o CTA de Direct
  apareceu **zero vezes** — o mecanismo do nicho é a **pergunta aberta**.

  **Dois CTAs novos, sem produto:** `envio` (isca de compartilhamento no Direct —
  ataca o número que está zerado: os Reels auditados têm 0 compartilhamento) e
  `pergunta` (isca de comentário). Somados ao `seguir`, são 10 das 14 posições.

  O **Raio-X** mantém o maior peso entre os produtos (2 das 4 vagas) porque
  captura e segmenta: o quiz recomenda o produto certo no resultado e nas trilhas
  de e-mail. A **Venda Blindada saiu do ciclo em 09/08** e o **CRM (Máquina de
  Vendas) saiu em 14/08** — pela mesma lógica: são vendidos na trilha de e-mail
  de quem tem gargalo em Decisão/Oferta (`scripts/leads/Code.gs` na LP). A palavra
  `MAQUINA` **segue ativa no Direct** para os posts antigos e para os Reels.
  ⚠️ **A saída do CRM é decisão de negócio — conferir com o Diego.**
  Produto nunca cai em posições seguidas.

  **Pendência conhecida:** a legenda do CTA `pergunta` é genérica ("E na sua
  empresa, como isso acontece?"). O ideal é uma pergunta escrita **por frase** no
  `frases.json`, casando com a dor do post — fica como melhoria futura.
- **Rotação com memória** (`estado_cta.json`): o publicador avança a partir da
  **posição** do último CTA publicado (não da data). Assim um dia que falhe não
  repete nem pula — o próximo dia pega o CTA que faltou. O estado só é gravado
  quando o post publica de fato.
- **É a POSIÇÃO (`ultimo_indice`), não o nome.** "seguir" e "ebook" aparecem duas
  vezes no ciclo; `CICLO_CTA.index(nome)` só acha a 1ª ocorrência, e o ciclo
  ficaria preso entre as posições 0–2 — **Venda Blindada e CRM nunca mais
  sairiam**. `ultimo_cta` fica no arquivo só para leitura humana. Estado no
  formato antigo (sem `ultimo_indice`) cai no nome uma única vez, para migrar.
- **O tema da frase segue o CTA do dia** (escolhido *depois* de saber o CTA):
  dia de "seguir" é post de valor/autoridade (próxima da fila, sem viés); dia de
  produto puxa para a frente a próxima frase que fale da dor daquele produto
  (`produto_do_cta` + `produto_de`) — o CTA só converte se casar com a frase.
- **A legenda usa o mesmo CTA do slide**, para o post ficar coerente
  (`legenda.montar`).
- **Conversão de produto por comment-to-DM**: o slide 3 traz uma explicação
  breve do produto + o pedido de uma palavra (`RAIOX` / `LIVRO` / `10X` /
  `MAQUINA` — a palavra da Máquina de Vendas desde 12/08/2026; `CRM` e
  `BLINDADA` continuam ativas no Direct para posts antigos); quem comenta
  recebe o link no Direct. No Instagram o link só é clicável no DM, nunca
  na legenda do feed — por isso não colocamos URL no post. Por ora o Diego
  responde à mão; depois liga a automação nativa de palavra-chave do Instagram.
  O CTA de seguir não tem palavra nem link (é o post de valor puro).

Mapa dor→produto em `TEMA_PRODUTO`; frases de esquadria/obra são marcadas com
`"produto": "venda-blindada"` no `frases.json`.

**Mini-aulas e o Raio-X**: o CTA da mini-aula continua amarrado ao produto de onde
a aula saiu (aula tirada do e-book chama `LIVRO` etc.) — casamento conteúdo→produto
converte melhor que CTA genérico. `RAIOX` é opção válida para aulas novas de
diagnóstico/processo geral sem produto natural (regra em `miniaulas.json`).

**Ordem da `sequencia` em 14/08/2026:** as aulas 3 e 9 foram trocadas de lugar
(`[1, 19, 2, 29, 9, 3, 7]`). A aula 3 chama `LIVRO` e cairia na quinta 20/08, no
dia seguinte a um Reel que também pede `LIVRO` — duas chamadas da mesma palavra
em 24h. Com a troca, quinta sai a aula 9 (`MAQUINA`) e a 3 vai para 25/08.
**Regra que fica: conferir a palavra da mini-aula contra a do Reel do dia seguinte
antes de publicar.**

## Os 4 produtos (fonte: vendanaobra.com.br, preços conferidos 03/08/2026)

| Produto | Formato | Preço | Dor |
|---|---|---|---|
| **O Cliente Sumiu** (e-book) | PDF + folhas de trabalho | R$ 19,90 | Orçamento enviado e o cliente some |
| **Venda Blindada** | Contrato editável | R$ 347 único | Prejuízo/brecha em contrato de esquadria |
| **Venda 10x** | Ao vivo semanal, terça 20h | R$ 497/ano | Falta de rotina/consistência comercial |
| **Máquina de Vendas** (o CRM, rebatizado 12/08/2026) | Assinatura, sem fidelidade | R$ 297/mês | Orçamento enviado, cliente some, ninguém cobra |

O e-book é a **porta de entrada** (ver `project_ebook_cliente_sumiu` na memória):
o papel dele não é lucrar, é fabricar comprador para o Venda 10x. Por isso tem
peso dobrado no ciclo de CTA. Frases da dor dele (follow-up, silêncio pós-orçamento,
tempo de resposta) estão marcadas com `"produto": "ebook"` no `frases.json`.

O link de cada produto (a LP `vendanaobra.com.br`, que distribui) é entregue **no
Direct** para quem comenta a palavra do produto — não vai no post (link na legenda
do feed não é clicável). Decidido pelo Diego em 21/07/2026. Não uso URL de
checkout. "Prospecção de Arquitetos" foi **arquivado**; não citar. (Atenção:
"Máquina de Vendas" era um produto antigo arquivado, mas desde 12/08/2026 é o
**nome oficial do CRM** — citar normalmente com esse sentido.)

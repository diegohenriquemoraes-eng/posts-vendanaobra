# posts-vendanaobra

Prepara as peças do Instagram **@vendanaobra** (IG User ID `17841470188725651`).

> ## Quem publica o quê — desde 04/09/2026
>
> | Formato | Como sai hoje |
> |---|---|
> | **Carrossel longo (mini-aula, 4:5)** | **PAUSADO em 04/09/2026** a pedido do Diego — nada mais sai por API, nem terça nem quinta. Nenhum banco foi apagado: ver "Mini-aula pausada" abaixo. |
> | **Carrossel curto (frase, 1:1)** | **MANUAL** — `preparar.py frase` monta a peça, o Diego posta do celular. Continua assim, sem previsão de voltar. |
> | **Reel diário (9:16)** | **NO AR desde 24/08/2026** — `reel-diario.yml` + `publicar_reel.py`, 9h BRT. Desde 27/08/2026 quase todo Reel sai **só na aba de Reels**; a ordem e o destino de cada um vivem em `plano_ep25.json`. |
>
> **Armadilha do cron (27/08/2026):** o Reel do dia não saiu porque o GitHub
> simplesmente **não disparou nenhum dos dois crons** — sem run, sem erro, sem
> issue (o aviso de falha só nasce quando o job roda e quebra). Cron do Actions
> é "best effort" e some em horário de fila. Desde então há **três** horários
> (11:45, 14:07 e 17:23 UTC) e nenhum no minuto 0. Se um dia faltar de novo:
> `gh run list --workflow=reel-diario.yml` e, se não houver run do dia,
> `gh workflow run reel-diario.yml` — o `--garantir` da repescagem impede post duplo.
>
> Em 21/08/2026 o Diego tinha tirado os dois formatos da API (receio de a
> publicação automática prejudicar a entrega). Em 24/08/2026 ele mandou o
> carrossel longo voltar exatamente à estratégia de antes — mesmo formato,
> leitura, cores, CTA, dias e horários — e manter o curto na mão.
>
> **Travas hoje:** `post-diario.yml` e `rede-de-seguranca.yml` seguem
> `disabled_manually` **e** com o `schedule` comentado, e `publicar.py` só
> publica com `VNO_PUBLICAR_API=1`. Desde 04/09/2026 o `miniaula.yml` está na
> mesma condição — `schedule` comentado e `publicar_miniaula.py` exigindo
> `VNO_MINIAULA_ATIVA=1`. **Só o Reel diário (`reel-diario.yml`) publica
> sozinho.** Não religar nada sem pedido explícito do Diego.
>
> Contraponto já registrado, para quando o assunto voltar: a Graph API é o
> caminho oficial (mLabs, Later e Buffer usam) e não há sinal de penalização —
> a queda medida foi de **formato** (mesmo carrossel de frase: 415 views em
> 19/07 contra 135 em 14/08). O que arrisca perfil de verdade é automação
> **não oficial** (robô clicando no Instagram Web) — por isso o `preparar.py`
> nunca posta por navegador.

## Reel do EP25 — refeito em 27/08/2026 (formato, calendário e capas)

Três decisões do Diego no mesmo dia mudaram o Reel de ponta a ponta. O que valia
antes (enquadramento fixo, 1 por dia sempre no feed, capa sempre com o rosto dele)
**não vale mais**.

### 1. O quadro segue quem fala

O corte antigo era um recorte fixo de 84 segundos — a câmera ficava nele mesmo
quando a Audrey falava. Agora, `montar_reel.py` monta o Reel plano a plano:

- **Regra de ouro:** quando o Diego fala, o quadro está nele; quando a Audrey
  fala, vai para ela — ou fica nele ouvindo, quando naquele instante o master só
  tem a câmera fechada nele. Isso ele autorizou explicitamente.
- **Split empilhado** (ele em cima, ela embaixo) quando os dois se revezam. **Só
  existe enquanto o master está no plano aberto**: a edição da Aluparts já vem
  cortada, então em cada instante existe **um** ângulo só — não há imagem dos
  dois em ângulos separados para empilhar. Foi o formato que ele escolheu
  (`--modo split`).
- **Ritmo:** nenhum plano passa de 3,2 s, com punch-in alternado (plano médio e
  fechado do mesmo ângulo) e corte sempre seco. É o beat de 2-3 s dos cortes de
  podcast que rendem.

**O falante vem da legenda revisada, não do detector de voz.** O detector por
timbre (`analise/voz.py`) acerta as falas longas e erra na fronteira curta — foi
ele que pôs o quadro na Audrey enquanto o Diego dizia "não, total". Cada bloco de
`legendas_ep25.json` tem o campo `quem` (`D`/`A`), escrito à mão, e é ele que manda.

**Armadilha paga:** um plano não pode atravessar uma troca de câmera do master.
Quando atravessa, o recorte do ângulo velho cai sobre o ângulo novo e o quadro
fica vazio (parede e cadeira, sem ninguém). `montar_edl` quebra o beat na troca.

### A fila virou SÓ FEED em 31/08/2026

**Decisão do Diego, depois de ver os números.** Dos 19 cortes que ainda faltavam,
**17 eram de aba de Reels e foram excluídos da fila** — não desativados,
removidos do `plano_ep25.json`. Sobraram os dois de feed, **nas datas que já
estavam marcadas**:

| Dia | Corte | |
|---|---|---|
| 05/09/2026, 9h | 27 · Você precisa de dois mentores | feed + colab @aluparts.oficial |
| 10/09/2026, 9h | 14 · Empresa que não demite cliente | feed + colab @aluparts.oficial |

**Não repor os 17 na fila.** Os MP4 deles continuam em `midia/reels/`, prontos e
já com o formato novo — apagá-los não devolveria espaço (o git guarda os blobs no
histórico de qualquer jeito) e jogaria fora horas de render. Se um dia ele quiser
um deles, é só voltar a linha no plano.

**O publicador passou a olhar a DATA.** Era posicional ("o próximo da fila"), e
com dois cortes restando isso publicaria os dois em dias seguidos, ignorando o
calendário. Agora: dia sem nada marcado sai com **código 0** e a mensagem "nada
marcado para hoje" — de propósito, para o Actions não abrir issue todos os dias
entre 31/08 e 05/09.

### 2. Calendário: feed x só Reels

Postar todo dia no feed encheria o perfil de corte. A cadência continua **1 por
dia**, mas quase tudo sai com `share_to_feed=false` — só na aba de Reels, fora da
grade. Ordem e destino em `plano_ep25.json`, gerado por `plano.py` (sorteio de
semente fixa: o calendário é sempre o mesmo).

- **No feed:** 07 (28/08), 13 (31/08), 27 (05/09), 14 (10/09).
- **Colab com a @aluparts.oficial só nos do feed.** Nos de aba de Reels o post
  não entra no feed de ninguém, então marcar a Aluparts não entrega nada a eles.
- A Meta trata `share_to_feed` como **indicação de preferência, não garantia** —
  funciona na prática, mas não é contrato.

### 3. Capas

**Decisão final do Diego (27/08/2026): só o corte 07 leva capa de IA.**
Os outros três do feed — 13, 27 e 14 — ficam com a **capa original (rosto dele +
gancho)**, igual aos de aba de Reels. Ele decidiu assim depois de ver o 07 pronto.
**Não gerar capa de IA para eles achando que ficou pendente** — não ficou.

- **Corte 07:** capa de IA (`gerar_capa_ia.py`), foto do Gemini, **sem a etiqueta
  "ALUPARTS PODCAST"** — a pessoa só descobre que é corte depois de clicar. No
  lugar da etiqueta do podcast vai uma etiqueta de tema, em dourado, que mantém a
  peça dentro da identidade do grid.
- **Todos os outros:** capa original (rosto do Diego + gancho).
- O `gerar_capa_ia.py` fica no repo para quando ele quiser voltar ao formato.

⚠️ **O Gemini não obedece "sem marca" nem "sem texto legível".** Ele pôs o
logotipo da Dell na moldura do notebook e escreveu "CONTRACT" em letra grande no
papel, nas duas vezes **depois** de eu pedir explicitamente que não. Pedir de novo
não resolve: ele regera a cena e mantém. O que funciona é **clonar um pedaço
vizinho por cima**, e só em superfície lisa. **Conferir toda foto ampliada antes
de publicar.** O campo de texto do Gemini também embaralha acentuação — mandar o
comando sem acento.

### Como se produz hoje

| Peça | Papel |
|---|---|
| `plano.py` → `plano_ep25.json` | O calendário: ordem, dia e se vai ao feed |
| `montar_reel.py` | Monta o Reel plano a plano (`--id 07 --modo split`) |
| `legendas_ep25.json` | Legenda revisada à mão, com o falante de cada bloco |
| `producao.py --daemon` | Renderiza tudo que tem legenda, na ordem de publicação |
| `painel.py` → `painel.html` | Acompanhamento (atalho na Área de Trabalho) |
| `gerar_capa_ia.py` | Capa dos que vão ao feed |
| `analise/*.py` | Alinhamento no master, câmeras, falante, transcrição |

**A legenda foi revisada cruzando duas transcrições** — a automática do YouTube
(acerta contexto e nome próprio) e uma própria por Whisper (pontua melhor). Onde
divergem, decide o contexto. Correções que só aparecem no cruzamento: "Aldre" é
**Audrey**, "Lopart" é **Aluparts**, "esquadrilha" é **esquadria**, "criança
limitante" é **crença limitante**, "custo de questão de cliente" é **custo de
aquisição de cliente**. A transcrição própria também **inventou** uma linha de
crédito de legendagem que não existe no áudio — conferir o fim de cada corte.

### Armadilha paga: PUXAR antes de agir (31/08/2026)

**Publiquei o corte 10 duas vezes.** Ao retomar depois de dois dias, li o
`publicados_reels.json` **local**, que estava parado em 28/08, concluí que nada
tinha saído e republiquei. O robô do GitHub tinha publicado normalmente em 29 e
30/08 e gravado **no remoto**.

A trava `--garantir` existe e funciona, mas ela lê o arquivo local — e o arquivo
local estava desatualizado.

**Regra: neste repositório o robô da nuvem também escreve. `git pull` ANTES de
qualquer decisão sobre o que publicar**, e antes de confiar em qualquer arquivo de
estado. Vale para `publicados_reels.json`, `publicados_miniaulas.json` e
`estado_cta.json`.

A Graph API não apaga post do Instagram — o duplicado teve de ser removido à mão.

### Armadilha: o tamanho do repositório

O `.git` passou de 500 MB e cada lote de vídeo novo é ~100 MB. **`git push`
estoura 10 minutos** e precisa rodar em segundo plano. Sem o push, o Actions
publica o arquivo **antigo** — o vídeo vem de `raw.githubusercontent`, não da
máquina. Subir em lotes, e conferir `git status -sb` antes de dar a fila por
pronta.

## ⏸️ Mini-aula PAUSADA em 04/09/2026 — "interrompe, mas mantém o estudo"

Decisão do Diego, palavra dele: interromper a mini-aula em carrossel (as duas
por semana), **manter o estudo até ele pedir para voltar**, e já tirar o que
sairia na semana seguinte. Não veio motivo, e não foi inventado nenhum aqui.

**O que parou (trava dupla, a lição de 17/08 aplicada):**

- `miniaula.yml` com o bloco `schedule` inteiro comentado — os três crons
  (12h, 13h e 17h BRT de terça e quinta) não existem mais.
- `publicar_miniaula.py` recusa publicar sem `VNO_MINIAULA_ATIVA=1`, e o
  workflow **não define** essa variável. Um `workflow_dispatch` clicado por
  engano não põe nada no ar.
- Só o cron não bastava: em 17/08 o carrossel de frase foi "pausado" no cron e
  saiu assim mesmo, porque outro workflow chamava o mesmo script. Aqui o
  script é a segunda trava.

**O que a semana de 08/09 perde, e que já está retirado:** terça 08/09 sairia a
aula **18** ("Construtora não compra igual a cliente final", venda10x) e quinta
10/09 a **16** ("3 mensagens para a carteira que está parada há meses", crm).
Nenhuma das duas foi consumida: a `sequencia` do `miniaulas.json` não foi
tocada e `publicados_miniaulas.json` para nas 10 que foram ao ar — a última é a
aula 6, de 03/09, a peça que fecha a série. Quando
o Diego mandar voltar, a próxima peça é exatamente a que sairia agora — não há
buraco na fila nem aula queimada.

**O que continua de pé (é isto o "manter o estudo"):**

- `miniaulas.json` — as 33 aulas escritas, com `fonte`, legenda e CTA.
- `PAUTA-MINIAULAS.md`, `cenas_miniaulas.json` e as fotos em `fotos/`.
- `gerar_miniaula.py`, `preparar_foto.py`, `gerar_story.py` e o
  `publicar_miniaula.py --ensaio`, que gera os slides e imprime a legenda sem
  publicar. Dá para continuar escrevendo, ilustrando e conferindo peça.
- `python preparar.py aula --forcar` para o Diego postar do celular, se um dia
  quiser uma avulsa sem religar a automação (esse caminho passa pelo
  `preparar.py`, não pela trava).
- **`dm-comentarios.yml` fica LIGADO.** Os comentários da mini-aula de 01/09
  ainda estão dentro da janela de 7 dias da Meta; desligar o robô agora
  deixaria gente pedindo o link sem resposta. Se a pausa passar de meados de
  setembro, aí sim ele fica rodando 144 vezes por dia sem nada a fazer — custo
  zero (repo público), mas pode ser desligado.

**Efeito na conta, dito sem enfeite:** o feed fica só com o **Reel diário**
(9h BRT, fila do EP25) e com o carrossel de frase manual, que está parado desde
17/08. Ou seja, **nenhum carrossel sai do @vendanaobra enquanto a pausa durar**
— e carrossel é o formato mais eficiente medido da conta (índice 2,10 de
interação por view, contra 0,85 do Reel). É consequência aceita da decisão, não
descuido.

**Para voltar** (só com pedido explícito): descomentar o `schedule` do
`miniaula.yml`, devolver `VNO_MINIAULA_ATIVA: "1"` ao step de publicar e, se o
workflow estiver desabilitado na UI, `gh workflow enable miniaula.yml`.

## Banco de mini-aulas — 20 aulas novas em 31/08/2026

**33 aulas no banco.** O Diego mandou escrever a fila até dezembro; escrevi **20**,
que é o que o material dele cobre. Fontes: o contrato do **Venda Blindada** (9),
as **transcrições dos vídeos** dele (9), o **blog** (2) e o banco de frases no tema
inteligência artificial (1). Cada aula traz a origem em `fonte` — nenhuma foi
escrita de fora do material dele, que é a regra do banco.

**Faltam 11 para fechar dezembro, e elas dependem do Diego.** Sete saem de
"O Cliente Sumiu" e **o texto do e-book não está mais no disco** (a pasta
`Perffec\Claude\Ebook-Cliente-Sumiu` está vazia; o arquivado da LP só tem as
imagens de capa). As outras quatro precisam de tema novo. Sem uma das duas coisas,
escrever essas 11 seria inventar — e o banco proíbe.

### O CTA das mini-aulas agora é um ciclo

`palavra → salvar → palavra → envio → palavra → pergunta`, no campo `cta.tipo`.
Só o tipo `palavra` tem `cta.palavra`.

Antes era palavra-chave em **100%** das aulas — o mesmo padrão que o Diego já
tinha corrigido no carrossel de frase em agosto, quando o perfil passou a ler como
loja. A pesquisa de mercado (set/2026) confirma: em carrossel educativo, CTA de
salvar e compartilhar rende mais, e carrossel é o formato de maior engajamento
(0,50% contra 0,48% do Reel).

⚠️ **A entrega automática do link NÃO está ligada.** O objetivo declarado é
"comenta e recebe o link", mas hoje só existe o robô do RAIOX; o resto o Diego
responde à mão. Ligar isso vale mais que escrever aula nova.

### Capas: o gargalo real

**A fila publica até 29/09 e para.** O `escolher()` **pula** aula sem foto e vai
para a próxima com foto — não falha, mas também não espera. Então saem nove posts
(13, 6, 18, 16, 4, 37, 31, 35, 27) e depois o job passa a falhar.

**16 aulas escritas estão esperando capa.**

Em 31/08 reaproveitei as **4 fotos livres em alta** — das aulas já publicadas 07,
09, 10 e 19 — nas aulas 35, 37, 31 e 27, casadas por cena. `foto_reaproveitada_de`
registra a origem. Não dava para reaproveitar mais: 04, 06, 13, 16 e 18 são das
aulas que ainda vão ao ar, e 01, 02, 03 e 29 estão em 928x1152, abaixo do slide.

**A API do Gemini não resolve hoje:** `gerar_foto_ia.py` e `cenas_miniaulas.json`
(as 20 cenas escritas) estão prontos e testados, mas **todos os modelos de imagem
devolvem HTTP 429 nas duas chaves** — geração de imagem não tem free tier, ao
contrário da geração de texto que o blog e o LinkedIn usam com a mesma chave.
Para destravar: ligar faturamento na chave, e aí é um comando só.

⚠️ O arquivo `Perffec\Claude\gemini_api_token.txt` guarda **duas chaves**, e uma
delas apareceu na tela num erro de execução em 31/08 — vale rotacionar.

## Banco de mini-aulas (24/08/2026)

**13 das 40 aulas da pauta estão prontas** (texto + foto): 1, 2, 3, 4, 6, 7, 9, 10,
13, 16, 18, 19, 29. Seis foram escritas em 24/08/2026, no mesmo dia em que o
carrossel longo voltou ao automático — o banco tinha só a aula 7 sobrando e a
quinta seguinte ficaria sem post. Fontes no campo `fonte` de cada aula (material
arquivado O Cliente Sumiu, Venda Blindada, transcrições). Fila em `sequencia`:
7 → 10 → 13 → 6 → 18 → 16 → 4, sem dois produtos iguais seguidos. Isso cobre
ter/qui até meados de setembro/2026 — **repor antes disso**, senão o workflow
falha com "Nenhuma mini-aula com foto disponivel" e abre issue.

Fotos novas geradas no Gemini com o padrão documental de sempre; a capa da aula
18 saiu com o logotipo "Sesc" no colete dos trabalhadores e o enquadramento foi
recortado para o prédio e a grua (retoque local no logo não funciona: o remendo
fica visível). **Conferir marca de terceiro em toda foto gerada antes de commitar.**

## Foto de capa: resolução e foco — trava automática (27/08/2026)

**O que aconteceu:** o post da aula 10 (27/08) foi ao ar com a capa borrada e o
Diego reclamou. Duas causas somadas, as duas na foto:

1. **Resolução.** As seis fotos feitas em 24/08 (04, 06, 10, 13, 16, 18) foram
   salvas do **preview** do Gemini (928x1152) em vez do "tamanho original"
   (1856x2304). Como o slide é 1080x1350, `_cobrir()` **ampliava** a foto — capa
   macia no feed. Todas foram reexportadas dos masters, que já existiam em alta.
2. **Foco.** A foto da aula 10 era desfocada na origem (bokeh forte em toda a
   cena; nitidez medida em 109 contra 700–970 das boas). Foto nova gerada com o
   pedido explícito de **f/11, profundidade de campo grande, sem bokeh** —
   `miniaula-10-v2-nitida.png`, nitidez 2.222.

**A trava, para não repetir:**

- `preparar_foto.py` é a porta de entrada de qualquer foto nova:
  `python preparar_foto.py 10` exporta o master (prefere a versão `-v2-*`) para
  `fotos/miniaula-10.jpg` em qualidade 95 e **recusa** master menor que
  1080x1350. `python preparar_foto.py --conferir` audita a pasta inteira e sai
  com código 1 se houver foto pequena.
- `gerar_miniaula.gerar_capa()` levanta erro se a foto for menor que o slide, e
  `gerar_capa_ia.py` faz o mesmo para a capa de Reel (1080x1920).
- `publicar_miniaula.escolher()` trata foto em baixa **como "aula sem foto"**:
  pula para a próxima da fila e loga o motivo — o robô nunca publica capa
  ampliada e também nunca trava o job por causa disso.

**Ainda em 928x1152: as fotos 01, 02, 03 e 29** (as capas v2 de 12/08, cujo
master alto é a cena antiga de esquadria). São de aulas **já publicadas** e a
fila não as repete; se um dia forem reaproveitadas, refazer a foto no Gemini.

**Regra que fica:** foto de capa sai do Gemini pelo botão **"Baixar imagem no
tamanho original"** (1856x2304), nunca pelo preview, e o prompt pede nitidez em
toda a cena — capa é foto de fundo com texto grande por cima, bokeh forte lê
como foto ruim no feed.

**Republicação (27/08/2026):** a aula 10 saiu de novo às 22h33 com a capa nova
(`media_id 18097587371048145`). **A Graph API não apaga post nem story do
Instagram** (`DELETE` devolve erro 100/subcode 33) — a primeira versão tem de ser
excluída à mão no app. O slug da republicação leva sufixo `-v2`: reusar o mesmo
caminho no `raw.githubusercontent` arrisca o Instagram baixar a imagem antiga do
cache do CDN.

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
| ~~Ter / Qui, 12h BRT~~ | ~~Mini-aula (7–9 slides, 4:5, capa com foto)~~ | **pausada em 04/09/2026** — ter/qui estão vagas |

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

## DM por comentário — robô próprio, no ar desde 02/09/2026

Toda mini-aula termina pedindo "comenta PALAVRA que eu te mando o link no
Direct". A automação nativa da Meta atende isso — **mas só quem escreve a
palavra exatamente como ela está cadastrada**. Medido no post do dia, mesma
conta, mesmo carrossel:

| Comentário | Nativa | Nosso robô |
|---|---|---|
| `Blindada` | respondeu no **mesmo segundo** | ficou calado (já atendido) |
| `Máquina` (com acento) | **ficou muda** | atendeu **15 segundos** depois |

Era o buraco por onde a conversão vazava sem ninguém ver: os três comentários
"Máquina" de agosto ficaram sem resposta automática, e o Diego respondeu à mão
de 4 a 36 minutos depois. O `responder_dm.py` normaliza acento, pontuação e
emoji antes de comparar, entende "quero"/"manda o link" pelo produto do próprio
post, e cobre **toda mini-aula publicada daqui para a frente** — sem configurar
nada por post, porque o `publicados_miniaulas.json` já guarda o `media_id`.

| Palavra comentada | O que cai no Direct |
|---|---|
| `RAIOX` · `RAIO X` · `LIVRO` (aposentada) | `/raio-x` |
| `10X` | `/venda-10x` |
| `BLINDADA` | `/venda-blindada-esquadrias` |
| `MAQUINA` · `CRM` | `/crm-venda-na-obra` |
| `PROSPECCAO` | `/prospeccao-turbinada-por-ia` |
| `quero`, `link`, `manda aí`… | o produto **daquele post** (`cta.palavra`), nunca chute |

Todo link sai com `utm_medium=dm` — é o único jeito de separar o que o
comment-to-DM traz do resto do tráfego do Instagram. E o destino é sempre a
**nossa subpágina**, nunca o checkout: a página do nosso domínio é a que explica
o diferencial e a que ranqueia (decisão de 26/08/2026).

### As automações nativas continuam ligadas — e devem continuar

No Business Suite existem 7 automações "Comentar para enviar mensagem"
(MAPEAMENTO, MAQUINA, RAIOX, CRM, BLINDADA, 10X, LIVRO), todas ativadas e
valendo para qualquer post. Elas **funcionam** e são instantâneas — só não
toleram acento nem variação. Os dois mecanismos se dividem sozinhos: a nativa
pega o caso exato, o robô pega o resto.

**Não desligar nenhuma delas.** O robô lê as respostas do comentário antes de
agir: se o @vendanaobra já respondeu ali embaixo — a nativa ou o Diego na mão —
ele se cala. Quem chega primeiro atende; nunca sai DM em dobro. Foi assim no
teste de 02/09: o comentário `Blindada` foi atendido pela nativa e o robô não
mandou nada.

Uma consequência prática: o link da nativa vai **sem UTM**, e o do robô vai com.
Então o `utm_medium=dm` mede o que o robô atendeu, não o total do
comentário→Direct. Fechar essa diferença exigiria editar as 7 automações à mão
no Business Suite.

Pela mesma razão a **resposta pública fica ligada por padrão** ("@fulano te
chamei no direct", igual ao que ele escreve à mão): é olhando o post que o Diego
vê que aquele comentário já foi atendido. Sem ela, ele responderia de novo o que
o robô já respondeu.

### Detalhes que custaram tempo

- **A private reply não sai pelo IG User ID.** Pelo `{ig-user-id}/messages` a
  Graph responde `(#3) Application does not have the capability to make this API
  call`, mesmo com o token tendo `instagram_manage_messages`. Sai pela **Página**
  (`{page-id}/messages`, `PAGE_ID = 1272959582565285`) com o **token da página**,
  derivado do de system user em `/me/accounts` a cada rodada. Nenhum segredo novo.
- **7 dias e uma resposta só.** A Meta recusa private reply em comentário mais
  velho que isso (subcode 2534024) e recusa a segunda resposta ao mesmo
  comentário. O robô trata os dois como definitivos e não insiste.
- **O estado é anônimo de propósito.** Este repo é público e os logs do Actions
  também: `respondidos_dm.json` guarda um hash de 12 caracteres no lugar do @ da
  pessoa. O comentário é público; a mensagem privada não, e "@fulano recebeu DM
  do Venda Blindada" seria um dado novo exposto.
- **Comentário com mais de 10 palavras não recebe DM.** É conversa, não
  palavra-chave — responder "MAQUINA" para quem escreveu três linhas contando o
  caso dele é o jeito mais rápido de parecer robô.
- **Checkout esparso no workflow.** `midia/` tem quase 500 MB de MP4; baixar
  isso 144 vezes por dia seria absurdo, então o job clona só `*.py`, `*.json` e
  `.github`.
- **O cron de 10 minutos não é garantia.** Nas primeiras horas o Actions não
  honrou nenhum disparo de `*/10`. Por isso o atendimento tem três camadas: o
  cron de 10 em 10, um cron horário no minuto 7, e — a que realmente importa —
  **12 passadas de 5 em 5 minutos dentro do próprio `miniaula.yml`**, logo
  depois de publicar, que é quando chega quase todo comentário.
- **Nenhum horário no minuto redondo.** O primeiro `*/10` não disparou nenhuma
  vez em meia hora — minuto 0/10/20 é pico de fila do Actions, a mesma
  armadilha do reel diário em 27/08. Hoje roda em `4,14,24,34,44,54`.
- **Polling, não webhook.** Se uma rodada não disparar (e o cron do Actions some
  sem avisar, ver 27/08), a próxima pega os mesmos comentários — a janela é de 7
  dias e o estado sabe quem já foi atendido. Webhook seria instantâneo, mas
  exigiria servidor de pé e um endpoint público só para isso.

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
| `publicar_miniaula.py` | Mini-aula por API — **pausada desde 04/09/2026** (trava `VNO_MINIAULA_ATIVA=1`) |
| `gerar_miniaula.py` | Pillow → slides 4:5 (âncoras fixas + fonte única por peça) |
| `preparar_foto.py` | Master do Gemini → `fotos/miniaula-XX.jpg`, com trava de resolução (`--conferir` audita) |
| `gerar_story.py` | Story 1080x1920 com a arte do dia emoldurada |
| `limpar_marca.py` | Remove a marca d'água do Gemini (fundo de textura contínua) |
| `.github/workflows/miniaula.yml` | **Pausado** em 04/09/2026 — `schedule` comentado; `workflow_dispatch` só faz ensaio |
| `.github/workflows/post-diario.yml`, `rede-de-seguranca.yml` | **Disabled + cron comentado** (carrossel de frase é manual) |
| `responder_dm.py` | **Ativo** desde 02/09/2026 — comentário com palavra → link do produto no Direct |
| `dm_produtos.py` | Palavra → produto → subpágina + o texto que a pessoa recebe |
| `respondidos_dm.json` | Quem já foi atendido (identidade em hash — o repo é público) |
| `.github/workflows/dm-comentarios.yml` | **Ativo** — roda de 10 em 10 minutos |
| `medir_alcance.py` | Linha de base: alcance por post e efeito de publicar mais de uma peça no dia |
| `top_posts.py` | Os campeões medidos (Graph API) — é de onde saem as "referências do dia" do app Canteiro |
| `coletar_stories.py` | **Diário**: fotografa os Stories antes de expirarem (a API só os devolve por 24h) |
| `placar.py` | O placar de sexta: posts, réguas de Story e comentários em forma de pergunta |
| `dados/stories.json` | Histórico dos Stories — **versionado**, o runner é descartável |
| `.github/workflows/placar-semanal.yml` | **Ativo** — coleta 01:10 UTC diário; placar sexta 12:10 UTC como issue |

## Medição da ROTA 100K (04/09/2026) — as réguas que não existiam

O Diego mandou seguir o método do Afonso à risca. Duas exigências dele são de
MEDIÇÃO e nunca tinham sido cumpridas, porque o dado some sozinho:

- **Story vive 24h na Graph API.** Sem uma coleta diária, as duas réguas do
  Destrave Story (1º story ≥ 10% dos seguidores; último ≥ 40% do primeiro) não
  podem sequer ser calculadas. `coletar_stories.py` roda 01:10 UTC e **commita**
  `dados/stories.json`.
- **O post que vai ao tráfego se escolhe por SALVOS, não por views.** `placar.py`
  ordena por salvamento e mostra os três; também lista os comentários em forma de
  pergunta, que é a terceira fonte de gancho do método e não era usada.

Primeira leitura, 04/09 — sem maquiagem: 1º story **82** contra meta de 928;
último/primeiro **24%** contra 40%; mediana de alcance dos posts na semana **73**;
**3** salvos na semana inteira; **zero** comentários em forma de pergunta. A
estrutura está no formato do Afonso, a audiência ainda não.

⚠ As métricas de Story mudam de nome entre versões da API (`views` substituiu
`impressions`). O coletor pede **uma métrica por vez** e fica com as que a conta
aceita — pedir todas de uma vez faz a coleta inteira falhar por causa de uma.

## O Reel do EP25 passou para o slot das 15h (04/09/2026)

Saiu das 14h15. Com a grade da Rota 100K (dias 2–4: 09/12/15/18; dias 5–7:
09/15/18/21), **15h é o único horário presente nas duas grades** — antes o corte
era um 5º post fora de hora. Cron: `58 17 * * *`. No app Canteiro esse Reel
aparece com o chip "robô" e o aviso de que sai sozinho, e o bloco de produção do
dia já desconta ele da conta de gravações.

⚠️ **Trocar o cron custa o primeiro dia (05/09/2026).** O corte 27 não saiu às
15h: o GitHub **não disparou nenhum dos três crons novos** — nem o das 17:58,
nem as repescagens. Não foi erro de código (o `--ensaio` local escolhia o corte
certo, com mídia e legenda prontas) nem falta de mídia: o agendador do repo
estava vivo o dia inteiro (o `dm-comentarios.yml` rodou 10 vezes), só o
`reel-diario.yml` ficou mudo — e era o **primeiro dia** com o horário novo,
commitado na véspera às 22h40 BRT. Mesmo sintoma de 27/08: sem run não há
falha, e sem falha não nasce issue. **Sempre que mexer no `schedule`, conferir
o dia seguinte** (`gh run list --workflow=reel-diario.yml`) e, se não houver run
do dia, `gh workflow run reel-diario.yml` — o `--garantir` das repescagens
impede post duplo. Foi assim que o 27 saiu, 18h35 UTC:
https://www.instagram.com/reel/Dc6naPIkZR9/

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
- **Tipografia (25/08/2026) — a letra nova vive SÓ NA CAPA.** `tipografia.py`:
  `titulo()` = **Playfair Display** (gancho da capa do carrossel e da capa do
  Reel), `rotulo()` = **Archivo** (etiqueta dourada e assinatura, dentro da
  capa) e `fonte()` = **Instagram Sans** (todo o resto: slides de conteúdo,
  corpo, número, CTA, rodapé, story e carrossel de frase).
  - Veio do print de um Reel dele (legenda de destaque em serifada didone) com
    o pedido de "identidade mais profissional no tipo da letra". Na primeira
    volta a dupla nova pegou a peça inteira; **ao ver pronto, o Diego aprovou a
    capa e mandou limitar a mudança às capas** — o miolo lê melhor na letra de
    antes. Não reabrir: serifada só em texto grande sobre foto.
  - A **legenda queimada dos 27 Reels do EP25 nunca entrou nessa troca** —
    sempre foi Instagram Sans (os `.ass` foram renderizados em 24/08).
  - **Algarismos**: a Playfair vem com figuras **old-style** (o 3, o 4 e o 7
    descem abaixo da linha) e o Pillow desta máquina é **sem libraqm**, então
    não dá para ligar a feature `lnum` na hora. `fontes/preparar_playfair.py`
    gera `PlayfairDisplay-Lining.ttf` apontando o cmap dos dígitos para os
    glifos `.lf` — é esse arquivo que `tipografia.py` carrega. Sem ele, o número
    do slide dança de altura entre os slides (a reprovação de 03/08/2026).
  - As duas são **variáveis**: peso vai direto no eixo `wght`, sem arquivo
    estático por peso como era com a Instagram Sans.
  - `escrever_espacado()` desenha letra a letra porque o Pillow não tem
    tracking — é o que dá cara de etiqueta de revista ao rótulo dourado.
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
  pergunta → seguir → envio → Raio-X → pergunta → envio → pergunta →` volta ao
  início (`CICLO_CTA`). São **3 CTAs de palavra-chave em 14** (eram 4 até
  25/08/2026, quando o e-book saiu do portfólio e a vaga dele virou `pergunta`),
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
  `pergunta` (isca de comentário). Somados ao `seguir`, são 11 das 14 posições.

  O **Raio-X** mantém o maior peso entre os produtos (2 das 3 vagas) porque
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
- **É a POSIÇÃO (`ultimo_indice`), não o nome.** "seguir", "envio" e "pergunta"
  se repetem no ciclo; `CICLO_CTA.index(nome)` só acha a 1ª ocorrência, e o ciclo
  ficaria preso entre as posições 0–2 — **Raio-X e Venda 10x nunca mais
  sairiam**. `ultimo_cta` fica no arquivo só para leitura humana. Estado no
  formato antigo (sem `ultimo_indice`) cai no nome uma única vez, para migrar.
- **O tema da frase segue o CTA do dia** (escolhido *depois* de saber o CTA):
  dia de "seguir" é post de valor/autoridade (próxima da fila, sem viés); dia de
  produto puxa para a frente a próxima frase que fale da dor daquele produto
  (`produto_do_cta` + `produto_de`) — o CTA só converte se casar com a frase.
- **A legenda usa o mesmo CTA do slide**, para o post ficar coerente
  (`legenda.montar`).
- **Conversão de produto por comment-to-DM**: o slide 3 traz uma explicação
  breve do produto + o pedido de uma palavra (`RAIOX` / `10X` / `MAQUINA` — a
  palavra da Máquina de Vendas desde 12/08/2026; `CRM` e `BLINDADA` continuam
  ativas no Direct para posts antigos; `LIVRO` foi **aposentada em 25/08/2026**); quem comenta
  recebe o link no Direct. No Instagram o link só é clicável no DM, nunca
  na legenda do feed — por isso não colocamos URL no post. Por ora o Diego
  responde à mão; depois liga a automação nativa de palavra-chave do Instagram.
  O CTA de seguir não tem palavra nem link (é o post de valor puro).

Mapa dor→produto em `TEMA_PRODUTO`; frases de esquadria/obra são marcadas com
`"produto": "venda-blindada"` no `frases.json`.

**Mini-aulas e o Raio-X**: o CTA da mini-aula continua amarrado ao produto que
responde a dor da aula (aula de contrato chama `BLINDADA` etc.) — casamento
conteúdo→produto converte melhor que CTA genérico. As 9 aulas que fechavam no
e-book foram redistribuídas em 25/08/2026 entre `RAIOX`, `MAQUINA`, `10X` e
`BLINDADA`. `RAIOX` é opção válida para aulas novas de
diagnóstico/processo geral sem produto natural (regra em `miniaulas.json`).

**Ordem da `sequencia` em 14/08/2026:** as aulas 3 e 9 foram trocadas de lugar
(`[1, 19, 2, 29, 9, 3, 7]`). A aula 3 chamava `LIVRO` (palavra aposentada em
25/08/2026) e cairia na quinta 20/08, no dia seguinte a um Reel que pedia a mesma
palavra — duas chamadas iguais em 24h. Com a troca, quinta saiu a aula 9
(`MAQUINA`) e a 3 foi para 25/08.
**Regra que fica: conferir a palavra da mini-aula contra a do Reel do dia seguinte
antes de publicar.**

## Os 3 produtos (fonte: vendanaobra.com.br, preços conferidos 03/08/2026)

O e-book "O Cliente Sumiu" (R$ 19,90) **saiu do portfólio em 25/08/2026** e não
entra mais em post nenhum.

| Produto | Formato | Preço | Dor |
|---|---|---|---|
| **Venda Blindada** | Contrato editável | R$ 147 único | Prejuízo/brecha em contrato de esquadria |
| **Venda 10x** | Ao vivo semanal, terça 20h | R$ 497/ano | Falta de rotina/consistência comercial |
| **Máquina de Vendas** (o CRM, rebatizado 12/08/2026) | Assinatura, sem fidelidade | R$ 297/mês | Orçamento enviado, cliente some, ninguém cobra |

**O e-book "O Cliente Sumiu" saiu do portfólio em 25/08/2026** (decisão do
Diego). Ele era a porta de entrada de R$ 19,90; sem ele, a porta de entrada
passou a ser o **Raio-X** (diagnóstico gratuito), que captura e segmenta.
As frases que tinham `"produto": "ebook"` no `frases.json` ficaram sem produto —
continuam no banco, servindo a qualquer CTA. **Não recriar a marcação nem a
palavra `LIVRO`.**

O link de cada produto (a LP `vendanaobra.com.br`, que distribui) é entregue **no
Direct** para quem comenta a palavra do produto — não vai no post (link na legenda
do feed não é clicável). Decidido pelo Diego em 21/07/2026. Não uso URL de
checkout. "Prospecção de Arquitetos" foi **arquivado**; não citar. (Atenção:
"Máquina de Vendas" era um produto antigo arquivado, mas desde 12/08/2026 é o
**nome oficial do CRM** — citar normalmente com esse sentido.)

## Reel diário — fila do Aluparts Podcast #EP25 (24/08/2026)

O Diego participou do **#EP25 do Aluparts Podcast** (1h13m, publicado 21/08/2026,
host Audrey Dias). Tirei **27 cortes** dali — 12 no lote 1 e 15 no lote 2, aprovados
em 24/08/2026 —, um por dia, como **colaboração** com a @aluparts.oficial: aparece
nos dois feeds e soma os dois públicos. Juntos usam 25 dos 73 minutos do episódio.

**A fila é posicional, não por data.** O corte 01 saiu à mão em 24/08 e o cron pega
o próximo todo dia — item N publica em 24/08 + (N−1) dias, terminando em 19/09.
Foi por isso que o lote 2 teve de ser reordenado: com o 01 saindo um dia antes do
previsto, os cortes de feira cairiam antes da **Fesqua (9 a 12/09)**. Hoje o de
network cai na véspera (08/09) e os três de stand/posicionamento dentro do evento.
**Mexer na ordem da fila desloca todas as datas seguintes — conferir a Fesqua antes.**

| Peça | Papel |
|---|---|
| `reels_ep25.json` | A fila: ordem, duração, arquivo, capa e legenda de cada corte |
| `capas_ep25.json` | Instante do frame, recorte (x da câmera) e gancho de cada capa |
| `gerar_capa_reel.py` | Refaz a capa de qualquer corte (`--restantes --master ep25_full.mp4`) |
| `publicar_reel.py` | Publica o próximo da fila por API (`media_type=REELS`) |
| `publicados_reels.json` | O que já foi ao ar — a fila é "banco menos publicados" |
| `midia/reels/` | Os 27 MP4 + as 27 capas JPEG (394 MB), servidos por `raw.githubusercontent` |
| `.github/workflows/reel-diario.yml` | Cron diário 09h BRT + repescagem 11h — **ativo** |

**Horário 09h BRT, não 12h.** A mini-aula ocupa terça e quinta às 12h. 09h é o
segundo melhor horário medido da conta (mediana 427 views contra 545 das 12h no
período orgânico de jul/ago) e deixa 3h de folga do carrossel. Terça e quinta
ficam com dois posts — decisão do Diego em 24/08/2026, formatos diferentes.

**Ligado em 24/08/2026** — cron ativo e `VNO_REEL_ATIVO=1` no workflow. A trava
do script continua valendo para quem rodar na mão sem querer publicar.

⚠️ **Collab não se adiciona depois de publicado**, só apagando o post — por isso o
`colaboradores` tem de estar preenchido antes de qualquer publicação. E o convite
precisa ser **aceito por alguém da Aluparts em cada post**: no corte 01 ele ficou
como `Pending`. Consultar com `GET /{media-id}?fields=collaborators`.

**Duração fora da regra, com aval.** A regra de 28/07 é 25–45s por Reel. Só 10 dos
27 cabem; os outros vão de 51s a 111s. O Diego aprovou publicar assim em
24/08/2026: corte de podcast vive do começo-meio-fim, e cortar em 45s quebra a
história.

### Legenda queimada — o padrão real dele

Medido no Reel de 12/08/2026 (`instagram.com/reel/Db85xTDpw3b`), não no que a
estratégia de julho dizia. O padrão é a **legenda automática do Instagram**:
Instagram Sans branca, ~72px em 1080x1920, bloco de 2 a 4 linhas centralizado em
y=1400, halo escuro suave (`\bord4 \blur6`), caixa de frase normal, **sem cor de
destaque e sem fade**. O bloco troca inteiro.

⚠️ **Nada de karaokê palavra a palavra.** A primeira versão destacava a palavra
falada em amarelo com `\fad` — e o Diego devolveu com "a legenda está piscando".
O que pisca é a troca de cor e o fade por palavra, não a legenda em si. A
estratégia de 28/07 (`Perffec\Claude\Instagram-vendanaobra`) ainda descreve
"bold, 3 palavras por bloco, última em amarelo" como padrão atual — **está
desatualizada**; conferir no Reel mais recente antes de acreditar nela.

### Enquadramento 9:16 sem tarja

O master do podcast é 1920x1080. Em vez de encaixar o 16:9 numa moldura
desfocada, o corte é **9:16 de verdade** (`crop=608:1080`), com o x seguindo a
câmera: fechada no Diego (x=656), fechada na Audrey (x=470), plano aberto
(x=1330, que enquadra o lado dele da mesa). As trocas de câmera foram detectadas
quadro a quadro pela luminância da TV ao fundo, que só aparece no plano aberto.

### Armadilha paga: media_publish mente quando falha

Em **24/08/2026**, ao publicar o corte 01, o `media_publish` devolveu
`OAuthException code 2 · is_transient: true` — e **o Reel foi publicado assim
mesmo**. Se o robô tivesse confiado no erro, o dia seguinte republicaria o mesmo
corte. Desde então `publicar_reel.py` usa `_publicar_conferindo()`: no erro, ele
espera 20s, lê o último Reel do feed e só falha de verdade se o feed não mudou.

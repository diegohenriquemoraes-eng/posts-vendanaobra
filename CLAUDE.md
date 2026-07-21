# posts-vendanaobra

Posta 1 carrossel por dia útil (**seg–sex, 12h em ponto BRT**) no feed do
Instagram **@vendanaobra** (IG User ID `17841470188725651`). Sem sábado/domingo
— decisão do Diego em 19/07/2026.

Cada post são **3 slides**. Slides 1 e 2 trazem a **mesma frase**: slide 1 fundo
branco/letra preta, slide 2 fundo preto/letra branca. Referência de formato:
`@juliopereira.oficial` — frase centralizada entre aspas tipográficas, blocos
separados por linha em branco, assinatura discreta no rodapé
(`Para vender mais siga o @vendanaobra`). O **slide 3 é o CTA do dia**, em fundo
azul da marca (`#18406F`, amostrado do hero de `vendanaobra.com.br`) e letra
branca — fecha o carrossel com a cor do site (ver seção CTA abaixo).

## Arquivos

| Arquivo | Papel |
|---|---|
| `frases.json` | Banco de 120 frases revisadas (vendas, emocional, métricas, gestão) |
| `publicados.json` | O que já foi ao ar — a fila é "banco menos publicados" |
| `estado_cta.json` | Memória do ciclo de CTA: último CTA publicado + data |
| `legenda.py` | Ciclo do CTA do dia + textos do slide 3 e da legenda |
| `gerar_carrossel.py` | Pillow → os 3 JPEGs 1080x1080 (claro, escuro, CTA azul) |
| `publicar.py` | CTA do dia → fila → imagens → push → Graph API → registro |
| `.github/workflows/post-diario.yml` | Cron `0 15 * * *` (15h UTC = 12h BRT) |

## Por que o repositório é público

A Graph API **não aceita upload de arquivo local** para imagem: ela exige uma
URL https pública e busca o arquivo por conta própria. As imagens são commitadas
e servidas por `raw.githubusercontent.com`. Repositório privado quebraria isso.

## Rodar na mão

```bash
python publicar.py --ensaio     # só gera as imagens, não publica
python publicar.py              # próxima frase da fila
python publicar.py --id 7       # frase específica
```

Token: `META_TOKEN` no ambiente, ou o arquivo
`Desktop\Perffec\Claude\meta_system_user_token.txt`. Na nuvem é o secret
`META_TOKEN` do repositório.

## Armadilhas já pagas

- **Aspas tipográficas no código**: usar `“ ”` literais funciona (o arquivo é
  UTF-8), mas o console do Windows mostra `?` ao imprimir — não é bug.
- **Fonte**: `fontes/Inter-Regular.ttf` é variável; o peso é escolhido por
  `set_variation_by_axes([14, peso])`. Sem isso o texto sai mais pesado.
- **JPEG, não PNG**: a Graph API só aceita JPEG para imagem.
- **Layout**: o tamanho da fonte é automático (58 → 28) até a frase caber em
  860px de largura e 700px de altura. Frase muito longa encolhe o texto — o
  ideal é no máximo ~180 caracteres, 2 blocos.
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

- **O CTA do dia intercala numa ordem cíclica fixa, nunca repetindo dois dias
  seguidos:** `seguir → Venda Blindada → Venda 10x → CRM → seguir …`
  (`CICLO_CTA`). Depois de CRM volta pra "seguir".
- **Rotação com memória** (`estado_cta.json`): o publicador avança a partir do
  **último CTA publicado** (não da data). Assim um dia que falhe não repete nem
  pula — o próximo dia pega o CTA que faltou. O estado só é gravado quando o post
  publica de fato.
- **O tema da frase segue o CTA do dia** (escolhido *depois* de saber o CTA):
  dia de "seguir" é post de valor/autoridade (próxima da fila, sem viés); dia de
  produto puxa para a frente a próxima frase que fale da dor daquele produto
  (`produto_do_cta` + `produto_de`) — o CTA só converte se casar com a frase.
- **A legenda usa o mesmo CTA do slide**, para o post ficar coerente
  (`legenda.montar`).
- **Conversão de produto por comment-to-DM**: o slide 3 traz uma explicação
  breve do produto + o pedido de uma palavra (`BLINDADA` / `10X` / `CRM`); quem
  comenta recebe o link no Direct. No Instagram o link só é clicável no DM, nunca
  na legenda do feed — por isso não colocamos URL no post. Por ora o Diego
  responde à mão; depois liga a automação nativa de palavra-chave do Instagram.
  O CTA de seguir não tem palavra nem link (é o post de valor puro).

Mapa dor→produto em `TEMA_PRODUTO`; frases de esquadria/obra são marcadas com
`"produto": "venda-blindada"` no `frases.json`.

## Os 3 produtos (fonte: vendanaobra.com.br, conferido 19/07/2026)

| Produto | Formato | Preço | Dor |
|---|---|---|---|
| **Venda 10x** | Programa ao vivo, quarta 20h | não público | Falta de rotina/consistência comercial |
| **Venda Blindada** | Contrato editável | R$ 197 único | Prejuízo/brecha em contrato de esquadria |
| **CRM Venda na Obra** | Assinatura, sem fidelidade | R$ 297/mês | Lead/funil/follow-up espalhados |

O link de cada produto (a LP `vendanaobra.com.br`, que distribui) é entregue **no
Direct** para quem comenta a palavra do produto — não vai no post (link na legenda
do feed não é clicável). Decidido pelo Diego em 21/07/2026. Não uso URL de
checkout. "Máquina de Vendas" e "Prospecção de Arquitetos" foram **arquivados**;
não citar.

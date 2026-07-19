# posts-vendanaobra

Posta 1 carrossel por dia, **12h em ponto (BRT)**, no feed do Instagram
**@vendanaobra** (IG User ID `17841470188725651`).

Cada post são 2 slides com a **mesma frase**: slide 1 fundo branco/letra preta,
slide 2 fundo preto/letra branca. Referência de formato: `@juliopereira.oficial`
— frase centralizada entre aspas tipográficas, blocos separados por linha em
branco, assinatura discreta no rodapé (`Para vender mais siga o @vendanaobra`).

## Arquivos

| Arquivo | Papel |
|---|---|
| `frases.json` | Banco de 120 frases revisadas (vendas, emocional, métricas, gestão) |
| `publicados.json` | O que já foi ao ar — a fila é "banco menos publicados" |
| `gerar_carrossel.py` | Pillow → os 2 JPEGs 1080x1080 |
| `publicar.py` | Fila → imagens → push → Graph API → registro |
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
- Sem hashtag, sem emoji, sem CTA de venda **no slide** (o CTA vai na legenda).

## CTA — todo post tem, mas com intensidade variável (`legenda.py`)

Decidido em 19/07/2026, atuando como especialista de Instagram. O Diego pediu
CTA em 100% dos posts. A regra:

- **O CTA vai na LEGENDA, nunca num 3º slide.** Um terceiro slide de oferta
  quebraria o formato espelhado (o que torna o post reconhecível no feed) e
  derrubaria compartilhamento/salvamento — que é a fonte de alcance aqui. O
  slide já carrega o CTA de seguir no rodapé.
- **80% CTA leve** (salvar / seguir / "manda pro vendedor" / comentar). CTA de
  venda em todo post treina o público a passar direto; o leve sustenta alcance.
  "Manda pro vendedor" é o mais forte no B2B: circula entre dono e vendedor e
  cai na frente de quem decide de graça.
- **20% CTA de produto** (1 a cada 5 posts, `RITMO_OFERTA`), casado com a dor da
  frase. Nos dias de oferta os 3 produtos se revezam (`RODIZIO`) e a fila puxa
  para a frente uma frase que fale da dor do produto da vez — CTA só converte se
  casar com o que a frase levantou.

Mapa dor→produto em `TEMA_PRODUTO`; frases de esquadria/obra são marcadas com
`"produto": "venda-blindada"` no `frases.json`.

## Os 3 produtos (fonte: vendanaobra.com.br, conferido 19/07/2026)

| Produto | Formato | Preço | Dor |
|---|---|---|---|
| **Venda 10x** | Programa ao vivo, quarta 20h | não público | Falta de rotina/consistência comercial |
| **Venda Blindada** | Contrato editável | R$ 197 único | Prejuízo/brecha em contrato de esquadria |
| **CRM Venda na Obra** | Assinatura, sem fidelidade | R$ 297/mês | Lead/funil/follow-up espalhados |

Todos os produtos apontam para "link na bio" — não uso URL de checkout no post
(a bio do @vendanaobra manda para a LP, que distribui). "Máquina de Vendas" e
"Prospecção de Arquitetos" foram **arquivados**; não citar.

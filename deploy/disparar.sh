#!/bin/sh
# Despertador do Reel diario do @vendanaobra — roda no servidor da Hostinger.
#
# Por que existe: o agendador do GitHub Actions deixou de ser confiavel neste
# repositorio. Medido em 27 e 28/08/2026: a mini-aula, que tem horario fixo,
# rodou com ~9h de atraso, e o Reel teve dias sem disparo nenhum. O GitHub
# Actions em si esta saudavel — o disparo manual roda na hora. O que falha e' o
# relogio dele. Entao o relogio passou a ser o cron daqui, e quem publica
# continua sendo o workflow `reel-diario.yml`, no GitHub.
#
# Nenhuma credencial da Meta mora aqui. So um token do GitHub restrito a
# disparar aquele workflow, naquele repositorio.
#
# A trava --garantir do workflow impede post duplo caso um disparo atrasado do
# proprio agendador do GitHub ainda chegue depois deste.
#
# Instalacao: ver deploy/LEIA-ME.md no repositorio.

DIR=$(dirname "$0")
TOKEN=$(cat "$DIR/token" 2>/dev/null)
LOG="$DIR/log.txt"
REPO="diegohenriquemoraes-eng/posts-vendanaobra"
NTFY="https://ntfy.sh/vna-vendas-86b646387589741881e1c28f"

quando=$(date -u "+%Y-%m-%d %H:%M UTC")

if [ -z "$TOKEN" ]; then
  echo "$quando  ERRO: token ausente em $DIR/token" >> "$LOG"
  curl -s -H "Title: Reel diario sem token" \
    -d "O despertador da Hostinger nao achou o token do GitHub. O Reel de hoje nao foi disparado." \
    "$NTFY" > /dev/null
  exit 1
fi

codigo=$(curl -s -o "$DIR/resposta.txt" -w "%{http_code}" -X POST \
  -H "Authorization: Bearer $TOKEN" \
  -H "Accept: application/vnd.github+json" \
  -H "X-GitHub-Api-Version: 2022-11-28" \
  "https://api.github.com/repos/$REPO/actions/workflows/reel-diario.yml/dispatches" \
  -d '{"ref":"main"}')

if [ "$codigo" = "204" ]; then
  echo "$quando  ok - workflow disparado" >> "$LOG"
else
  detalhe=$(head -c 300 "$DIR/resposta.txt" | tr -d '\n')
  echo "$quando  ERRO $codigo - $detalhe" >> "$LOG"
  curl -s -H "Title: Reel diario nao disparou" \
    -d "Erro $codigo ao chamar o GitHub. O Reel de hoje pode nao ter saido - conferir o perfil." \
    "$NTFY" > /dev/null
fi

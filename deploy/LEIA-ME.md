# Despertador do Reel diário (Hostinger)

## Por que existe

O agendador do GitHub Actions parou de ser confiável neste repositório. Medido
em **27 e 28/08/2026**:

| Workflow | Devia rodar (UTC) | Rodou (UTC) | Atraso |
|---|---|---|---|
| Mini-aula, ter 25/08 | 14:45 · 16:00 · 20:00 | 15:26 · 16:41 · 20:21 | 41 min · 41 min · 21 min |
| Mini-aula, qui 27/08 | 14:45 · 16:00 · 20:00 | 23:59 · 00:47 · 03:58 | **~9 h · ~9 h · ~8 h** |
| Reel, 27 e 28/08 | 11:45 · 14:07 · 17:23 | nenhuma execução | — |

O **GitHub Actions em si está saudável**: disparo manual roda na hora e publica
em ~90 s. O que falha é o **relógio**. Então o relógio passou a ser o cron da
Hostinger, e quem publica continua sendo o `reel-diario.yml`.

**Nenhuma credencial da Meta mora no servidor.** Só um token do GitHub restrito
a disparar aquele workflow, naquele repositório. Se vazasse, o estrago possível
seria alguém disparar o Reel — não acesso à conta do Instagram.

## O que está instalado

- `~/reel-diario/disparar.sh` (cópia versionada em `deploy/disparar.sh`), modo 700
- `~/reel-diario/token` — o token, modo 600, **não vai para o git**
- `~/reel-diario/log.txt` — uma linha por disparo
- Falha manda push por **ntfy** no mesmo tópico das vendas: sem isso a falha
  seria invisível, que é exatamente o problema que estamos consertando.

O servidor roda em **UTC**. 9h BRT = **12:00 UTC**.

## Instalação (o que é feito à mão)

### 1. Token no GitHub — só pelo navegador

Token fine-grained não pode ser criado por API; tem de ser pela interface.

1. GitHub → **Settings** → **Developer settings** → **Personal access tokens** →
   **Fine-grained tokens** → **Generate new token**
2. **Repository access:** Only select repositories → `posts-vendanaobra`
3. **Permissions** → Repository permissions → **Actions: Read and write**
4. **Expiration:** escolher uma data **depois do fim da fila** (a do EP25 termina
   em 19/09/2026). Quando expirar, o disparo falha e o ntfy avisa.

### 2. Guardar o token no servidor

O token **não deve passar por conversa nem ficar em arquivo no Desktop**. Colar
num arquivo temporário e enviar:

```bash
scp -P 65002 -i ~/.ssh/hostinger_perffec token.txt u350552167@195.35.41.85:~/reel-diario/token
ssh -p 65002 -i ~/.ssh/hostinger_perffec u350552167@195.35.41.85 'chmod 600 ~/reel-diario/token'
```

Apagar o `token.txt` local depois.

### 3. Cron no hPanel

O servidor **não tem `crontab` por linha de comando** — é pelo painel:
`perffec.com.br` → **Avançado** → **Cron Jobs**.

- Comando: `/bin/sh /home/u350552167/reel-diario/disparar.sh`
- Horário: **12:00 UTC, todo dia** (= 9h BRT)

### 4. Conferir

```bash
ssh -p 65002 -i ~/.ssh/hostinger_perffec u350552167@195.35.41.85 'sh ~/reel-diario/disparar.sh; cat ~/reel-diario/log.txt'
```

Deve escrever `ok - workflow disparado`. Atenção: isso **publica de verdade** o
próximo da fila, a menos que o dia já tenha post (a trava `--garantir`).

## Os crons do GitHub continuam ligados

De propósito, como rede de segurança: se a Hostinger falhar, eles ainda tentam.
Desde 28/08/2026 **todos** os disparos agendados usam `--garantir`, então não
existe cenário de dois posts no mesmo dia, venha o disparo de onde vier.

## Quando a fila do EP25 acabar (19/09/2026)

Sem corte novo, o workflow falha e abre issue **todo dia**. Ou repor a fila, ou
desligar o cron no hPanel.

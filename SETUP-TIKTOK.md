# TikTok @vendanaobra — o que falta para ligar (3 passos do Diego, ~10 min, uma vez)

O código está pronto (`distribuir_tiktok.py` + workflow `Distribuir Reel no TikTok`).
Ele lê a conta do Instagram pela Graph API, baixa o Reel limpo (sem marca d'água) e
publica no TikTok pelo **Zernio** (zernio.com), que tem o app do TikTok já auditado e
dá 2 contas grátis com posts ilimitados. Enquanto a chave não existir, o cron roda e sai
em silêncio.

## 1. Conta do TikTok

Se o `@vendanaobra` ainda não existe no TikTok: criar no app, com o login
`vendanaobra@gmail.com` (é o do canal do YouTube; canal em conta errada não se transfere).
Depois, em **Configurações → Conta → Mudar para Conta Comercial**: é o que libera o campo
**"site"** clicável na bio, para o link `https://vendanaobra.com.br/r/tt`. Link em legenda
de vídeo não é clicável e o TikTok penaliza; por isso o distribuidor nunca escreve URL.

## 2. Zernio (onde o TikTok fica conectado)

1. `https://zernio.com` → criar conta (e-mail `vendanaobra@gmail.com`; sem cartão).
2. **Connect account → TikTok** → logar no TikTok e autorizar. O TikTok pede para
   escolher a conta e aceitar as permissões de publicar.
3. **Settings → API keys → Create** → copiar a chave (começa com `sk_`).

## 3. Entregar a chave

Salvar a chave em `C:\Users\NOTE\Desktop\Perffec\Claude\zernio_api_key.txt` (pasta
gitignorada, mesmo lugar do token da Meta) e me avisar — eu gravo o secret e disparo o
primeiro vídeo em ensaio. Ou, se preferir fazer direto:

```bash
gh secret set ZERNIO_API_KEY --repo diegohenriquemoraes-eng/posts-vendanaobra < "C:/Users/NOTE/Desktop/Perffec/Claude/zernio_api_key.txt"
```

## O que acontece depois

- Todo Reel novo do @vendanaobra vai para o TikTok na janela seguinte (5 por dia:
  10h29, 13h47, 15h53, 18h19 e 21h31 BRT), **até 3 vídeos por dia** — do mais novo para
  o mais antigo; o acervo dos últimos 45 dias escoa aos poucos.
- Legenda = a do Instagram sem URL, sem `@` (no TikTok marcaria outra pessoa) e com até
  5 hashtags. Reel sem legenda é pulado, como no YouTube.
- Estado em `distribuidos_tiktok.json`; falha abre issue no repo, e o mesmo Reel não é
  tentado mais de 2 vezes.
- Conferir contas ligadas: `python distribuir_tiktok.py --contas`.

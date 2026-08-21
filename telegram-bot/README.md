# HubVision Prompt Collector Bot

Bot que monitora grupos do Telegram e coleta prompts + imagens quando voce reage com 👍.

## Instalacao

```bash
cd telegram-bot
pip install -r requirements.txt
```

## Configuracao

1. Abra o Telegram e va em @BotFather
2. Crie um bot novo com /newbot
3. Copie o token
4. Abra `config.py` e cole o token:

```python
BOT_TOKEN = "123456789:ABCdefGHIjklMNOpqrsTUVwxyz"
```

5. Adicione o bot como ADMINISTRADOR nos grupos
6. Em cada grupo, envie /id para pegar o ID
7. Adicione os IDs no config.py:

```python
CHAT_IDS = [
    -1001234567890,  # Grupo IA Midjourney
    -1009876543210,  # Grupo DALL-E
]
```

## Uso

```bash
python bot.py
```

## Comandos do Bot

| Comando | Descricao |
|---------|-----------|
| `/start` | Boas-vindas |
| `/id` | ID do chat atual |
| `/stats` | Estatisticas |
| `/list` | Ultimos prompts |
| `/export` | Exportar JSON |
| `/help` | Ajuda |

## Como Funciona

1. Bot monitora os grupos configurados
2. Salva no cache todas as mensagens com imagem
3. Quando voce reage com 👍 (emoji configurado):
   - Baixa a imagem
   - Salva o texto do prompt
   - Adiciona ao banco de dados
4. Use `/list` para ver coletados
5. Use `/export` para gerar JSON para o site

## Arquivos

- `config.py` - Configuracoes (token, grupos, emoji)
- `bot.py` - Codigo principal
- `storage.py` - Gerenciamento de dados
- `collected_prompts/` - Imagens e JSON salvos
- `collected_prompts/prompts.json` - Banco de dados

## Solucao de Problemas

**Bot nao ve reacoes:**
- Bot precisa ser ADMINISTRADOR do grupo
- Grupo precisa ter reacoes habilitadas

**Bot nao responde:**
- Verifique se o token esta correto
- Reinicie o bot

**Imagens nao baixam:**
- Verifique conexao com internet
- Permissoes do bot no grupo

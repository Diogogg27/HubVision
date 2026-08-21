# Coletor Telegram por Reações: Especificação de Design

## Objetivo

Permitir que o proprietário da conta HubVision marque mensagens com qualquer reação nos chats contidos na pasta `PROMPTS/IA` do Telegram. Cada reação deve iniciar automaticamente a coleta da imagem e do prompt, sem exigir que um bot seja adicionado aos grupos ou que interaja com administradores e membros.

## Escopo aprovado

- Usar uma sessão local da conta pessoal do Telegram via Telethon.
- Monitorar somente os grupos e canais dentro da pasta `PROMPTS/IA`.
- Aceitar qualquer reação feita pelo proprietário da conta.
- Processar apenas mensagens que tenham imagem e texto.
- Baixar a imagem original disponível.
- Limpar o texto e traduzi-lo para inglês.
- Organizar os arquivos por pasta e grupo de origem.
- Adicionar o prompt automaticamente à biblioteca existente.
- Ignorar mensagens já processadas.
- Não enviar mensagens, reações, convites ou qualquer outro conteúdo ao Telegram.

## Arquitetura

Será criado um coletor independente dentro de `telegram-bot/`:

- `telegram_collector.py`: autentica a sessão, descobre os chats da pasta e recebe eventos de reação.
- `telegram_config.py`: concentra configuração e caminhos locais.
- Arquivo `.env`: armazena `API_ID`, `API_HASH` e dados de execução; nunca será versionado.
- Sessão Telethon: arquivo local ignorado pelo Git.
- Índice local: registra IDs de chat e mensagem já processados.

O fluxo principal será:

`reação do proprietário -> localizar mensagem -> validar imagem e texto -> baixar imagem -> limpar texto -> traduzir -> organizar por grupo -> atualizar biblioteca`

## Organização dos dados

As imagens serão salvas no formato:

```text
prompts_library/
  prompts_ia/
    nome-do-grupo/
      pair_0001.jpg
```

Cada item da biblioteca manterá, no mínimo:

- caminho da imagem;
- prompt traduzido;
- categoria da pasta `PROMPTS/IA`;
- grupo ou canal de origem;
- ID do chat;
- ID da mensagem;
- data da coleta;
- link interno da mensagem, quando disponível.

O índice de mensagens processadas será consultado antes de qualquer gravação. Isso evita duplicações quando uma mensagem recebe mais de uma reação ou quando o coletor é reiniciado.

## Tratamento de falhas

- Mensagem sem texto ou imagem: ignorar e registrar no log.
- Falha de tradução: preservar o texto limpo original.
- Falha no download: registrar o erro para nova tentativa.
- Falha na escrita da biblioteca: usar gravação segura para evitar JSON parcialmente escrito.
- Encerramento ou perda de conexão: reconectar automaticamente e continuar o monitoramento.

## Segurança e operação

- O login inicial será interativo e ocorrerá somente uma vez.
- A sessão local, `API_ID`, `API_HASH` e número de telefone não serão commitados.
- O coletor terá execução manual pelo `iniciar_bot.bat`.
- Os logs exibirão grupo, mensagem, status e erros, mas não credenciais.
- Um modo de teste processará uma única mensagem antes da execução contínua.

## Validação

Os testes devem confirmar:

1. Login e persistência da sessão local.
2. Descoberta correta da pasta `PROMPTS/IA`.
3. Detecção de qualquer reação feita pela conta configurada.
4. Download e armazenamento da imagem.
5. Limpeza e tradução do prompt.
6. Separação dos arquivos por grupo.
7. Bloqueio de duplicatas.
8. Atualização válida da biblioteca existente.
9. Reconexão após interrupção.
10. Ausência de ações de escrita ou interação no Telegram.

## Fora do escopo

- Monitoramento de chats fora da pasta `PROMPTS/IA`.
- Uso de bot token para entrar ou ler grupos.
- Publicação de mensagens no Telegram.
- Revisão manual obrigatória antes de adicionar à biblioteca.
- Alteração da interface pública da biblioteca nesta etapa.


# Aplicativo para envio de mensagens e arquivos para o Slack

Este aplicativo permite enviar mensagens e arquivos para os usuários do Slack com base nas informações do arquivo CSV e por meio de uma interface da Web.

## Funcionalidades

1. **Interface de upload:** Permite que os usuários façam upload de arquivos CSV e enviem mensagens e arquivos para o Slack.
2. **Seleção de bots:** Os usuários podem selecionar diferentes bots para os quais enviar mensagens.
3. **Integração com o Slack:** Usa o SDK do Slack para se comunicar com a API e enviar mensagens e arquivos.
4. **Enviar resumo:** Após processar as postagens, ele gera um arquivo do Excel com um resumo e o envia para um e-mail específico no Slack.

## Pré-requisitos

Você precisa ter as seguintes bibliotecas e ferramentas instaladas:

- Python
- Flask
- slack_sdk
- pandas
- chardet
- dotenv

## Instalação

1. clone este repositório:

git clone [URL_REPOSITÓRIO_URL]

```
2) Entre no diretório do projeto:
````bash
cd [PROJECT_DIRECTORY] ````
```

3. Instale as dependências:

````bash
pip install flask slack_sdk pandas chardet python-dotenv
```
## Configuração
1. crie um arquivo `.env` na raiz do projeto.
2. Adicione seu token do Slack ao arquivo `.env`:
````bash
SLACK_TOKEN=   #Token onde vai enviar o resumo do envio
SLACK_TOKEN_BOT1= #Token primero bot
SLACK_TOKEN_BOT2= #Token segundo bot
```
## Uso
1. Execute o aplicativo:
````bash
python [NOME_DO_ARQUIVO].py
```
Navegue até `http://127.0.0.1:5000/` no seu navegador e siga as instruções na tela para carregar um arquivo e enviar mensagens.
## Contribuições
As contribuições são bem-vindas. P
````

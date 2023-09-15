from flask import Flask, render_template, request, flash, redirect, url_for
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from werkzeug.utils import secure_filename
import os
import pandas as pd
import time
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()
app = Flask(__name__)  # Corrección aquí
app.config['UPLOAD_FOLDER'] = './uploads'
app.secret_key = os.urandom(24).hex()
ALLOWED_EXTENSIONS = {'csv'}

slack_token = os.environ.get('SLACK_TOKEN')
client = WebClient(token=slack_token)
@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('Arquivo não encontrado')
            return redirect(request.url)
        file = request.files['file']
        mensaje = request.form.get('message', '')  
        if file.filename == '':
            flash('Nenhum arquivo foi selecionado')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            process_file(file_path, mensaje)  
            flash('Mensaje enviado exitosamente')  
            return redirect(url_for('upload_file'))
    return render_template('upload.html')
def process_file(file_path, mensaje):  
    destinatarios_enviados = []
    destinatarios_errores = []
    try:
        df = pd.read_csv(file_path, sep=';', encoding='utf-8')
        for index, row in df.iterrows():
            destinatario = row['Destinatário'] 
            while True:
                try:
                    user = client.users_lookupByEmail(email=destinatario)
                    client.chat_postMessage(channel=user['user']['id'], text=mensaje)  
                    print(f"Mensagem enviada para {destinatario}")
                    destinatarios_enviados.append(destinatario)
                    break
                except SlackApiError as e:
                    if e.response['error'] == 'ratelimited':
                        print(f"Limite de taxa atingido, aguardando nova tentativa de envio para {destinatario}")
                        time.sleep(60)
                    else:
                        print(f"Erro ao enviar mensagem para {destinatario}: {e.response['error']}")
                        destinatarios_errores.append((destinatario, e.response['error']))
                        break
        enviar_resumen(destinatarios_enviados, destinatarios_errores)
    except FileNotFoundError:
        print("Error: Não foi possível encontrar o arquivo CSV.")
    except PermissionError:
        print("Erro: Você não tem permissão para ler o arquivo CSV.")
    except Exception as e:
        print(f"Erro inesperado: {str(e)}")
def enviar_resumen(destinatarios_enviados, destinatarios_errores):
    data = {'Destinatários enviados': destinatarios_enviados,
            'Erros dos destinatários': [f'{destinatario}: {error}' for destinatario, error in destinatarios_errores],
            'Data e Hora': [datetime.now().strftime('%Y-%m-%d %H:%M:%S') for _ in range(len(destinatarios_enviados) + len(destinatarios_errores))]}
    df = pd.DataFrame(dict([(k, pd.Series(v)) for k, v in data.items()]))
    # Salvar o DataFrame em um arquivo do Excel
    resumen_excel = 'resumo_envio.xlsx'
    df.to_excel(resumen_excel, index=False)
    # Envie o arquivo do Excel como um anexo em uma mensagem do Slack
    email_resumen = "esteban.gonzalez@neon.com.br"
    try:
        user = client.users_lookupByEmail(email=email_resumen)
        client.files_upload(
            channels=user['user']['id'],
            file=resumen_excel,
            title='Resumo de Envio',
            initial_comment='Resumo das mensagens enviadas e não enviadas.'
        )
        print(f"Resumo enviado para {email_resumen}")
    except SlackApiError as e:
        print(f"Erro ao enviar resumo para {email_resumen}: {e.response['error']}")
    # Eliminar el archivo Excel después de enviarlo
    if os.path.exists(resumen_excel):
        os.remove(resumen_excel)
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
if __name__ == '__main__': 
    app.run(debug=True)
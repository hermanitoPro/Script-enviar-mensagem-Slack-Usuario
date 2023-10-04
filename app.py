from flask import Flask, render_template, request, flash, redirect, url_for
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from werkzeug.utils import secure_filename
import os
import pandas as pd
import time
from datetime import datetime
from dotenv import load_dotenv
import chardet
load_dotenv()
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = './uploads'
app.secret_key = os.urandom(24).hex()
ALLOWED_EXTENSIONS = {'csv', 'png', 'jpg', 'jpeg', 'gif'}
slack_token = os.environ.get('SLACK_TOKEN')
client = WebClient(token=slack_token)
@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        # Aquí, verifica y crea la carpeta si no existe
        if not os.path.exists(app.config['UPLOAD_FOLDER']):
            os.makedirs(app.config['UPLOAD_FOLDER'])
        bot_choice = request.form.get('botChoice', 'BOT1')
        slack_token = os.environ.get(f'SLACK_TOKEN_{bot_choice}')
        client = WebClient(token=slack_token)
        canal_id = request.form.get('canalId', '').strip()
        mensaje = request.form.get('message', '')
        imagen = request.files.get('imagen')       
        # Recoger el valor del nuevo input
        imagen_primero = request.form.get('imagenPrimero') == 'true'
        # Si se proporciona un ID de canal, enviar el mensaje directamente al canal
        if canal_id:
            try:
                imagen_path = None  # Inicializamos imagen_path
                if imagen and allowed_file(imagen.filename):
                    imagen_filename = secure_filename(imagen.filename)
                    imagen_path = os.path.join(app.config['UPLOAD_FOLDER'], imagen_filename)
                    imagen.save(imagen_path)                   
                    # Si imagen_primero es True, enviamos la imagen antes del mensaje
                    if imagen_primero:
                        client.files_upload(channels=canal_id, file=imagen_path, title="Imagen Adjunta")
                        if os.path.exists(imagen_path):
                            os.remove(imagen_path)               
                # Enviamos el mensaje
                if mensaje.strip():
                    client.chat_postMessage(channel=canal_id, text=mensaje)              
                # Si imagen_primero es False, enviamos la imagen después del mensaje
                if imagen and not imagen_primero:
                    client.files_upload(channels=canal_id, file=imagen_path, title="Imagen Adjunta")
                    if os.path.exists(imagen_path):
                        os.remove(imagen_path)               
                flash('Mensaje enviado exitosamente al canal')
                return redirect(url_for('upload_file'))
            except SlackApiError as e:
                flash(f'Error al enviar mensaje al canal: {e.response["error"]}')
                return redirect(request.url)
        # Si no se proporciona un ID de canal, seguir el flujo original
        if 'file' not in request.files:
            flash('Arquivo não encontrado')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('Nenhum arquivo foi selecionado')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            imagen_path = None
            if imagen and allowed_file(imagen.filename):
                imagen_filename = secure_filename(imagen.filename)
                imagen_path = os.path.join(app.config['UPLOAD_FOLDER'], imagen_filename)
                imagen.save(imagen_path)
            process_file(file_path, mensaje, client, imagen_path, imagen_primero)  # Pasamos imagen_primero
            flash('Mensaje enviado exitosamente')
            return redirect(url_for('upload_file'))
    return render_template('upload.html')
def process_file(file_path, mensaje, client, imagen_path=None, imagen_primero=False):
    destinatarios_enviados = []
    destinatarios_errores = []
    with open(file_path, 'rb') as f:
        result = chardet.detect(f.read())
    try:
        df = pd.read_csv(file_path, sep=';', encoding=result['encoding'])
        for index, row in df.iterrows():
            destinatario = row['Destinatário']
            numero_mensaje = row.get('Posição', None)
            mensaje_especifico = mensaje.replace("{aqui}", str(numero_mensaje)) if numero_mensaje else mensaje
            while True:
                try:
                    user = client.users_lookupByEmail(email=destinatario)                   
                    # Si imagen_primero es True, enviamos la imagen antes del mensaje
                    if imagen_path and imagen_primero:
                        client.files_upload(channels=user['user']['id'], file=imagen_path, title="Imagen Adjunta")                       
                    if mensaje_especifico.strip():
                        client.chat_postMessage(channel=user['user']['id'], text=mensaje_especifico)                   
                    # Si imagen_primero es False, enviamos la imagen después del mensaje
                    if imagen_path and not imagen_primero:
                        client.files_upload(channels=user['user']['id'], file=imagen_path, title="Imagen Adjunta")                       
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
        if imagen_path and os.path.exists(imagen_path):
            os.remove(imagen_path)
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
    # Lista de correos electrónicos a los que se enviará el resumen
    emails_resumen = ["esteban.gonzalez@neon.com.br"]
    for email_resumen in emails_resumen:
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
if __name__ == '__main__':  # Corrección aquí
    app.run(debug=True)
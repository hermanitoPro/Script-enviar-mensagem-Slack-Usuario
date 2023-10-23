import os
import csv
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from dotenv import load_dotenv
# Cargar variables desde .env
load_dotenv()
# Obtén el token de Slack de las variables de entorno
slack_token = os.environ.get("SLACK_TOKEN")
if not slack_token:
    print("Error: La variable de ambiente SLACK_TOKEN no está definida.")
    exit(1)
# Crea un cliente de Slack
client = WebClient(token=slack_token)
# Nombre o ID del canal del que deseas obtener los correos electrónicos
channel_name_or_id = ""
try:
    # Si conoces el nombre del canal, pero no el ID, puedes usar el método conversations_info
    # para obtener el ID primero. Si ya conoces el ID, puedes omitir este paso.
    channel_info = client.conversations_info(channel=channel_name_or_id)
    if not channel_info["ok"]:
        print("Error al obtener información del canal:", channel_info["error"])
        exit(1)
    channel_id = channel_info["channel"]["id"]
    # Iniciar una lista vacía para todos los miembros
    all_members = []
    # Paginación para obtener todos los miembros del canal
    next_cursor = None
    while True:
        response = client.conversations_members(channel=channel_id, limit=1000, cursor=next_cursor)
        if response["ok"]:
            all_members.extend(response["members"])
            next_cursor = response.get("response_metadata", {}).get("next_cursor")
            if not next_cursor:
                break
        else:
            print(f"Error al obtener miembros del canal {channel_id} con cursor {next_cursor}:", response["error"])
            exit(1)
    print(f"Total de miembros en el canal: {len(all_members)}")
    # Abre el archivo CSV para escribir
    with open("emails.csv", "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["Destinatário"])
        # Obtén los correos electrónicos de los miembros y escribe en el CSV
        for member_id in all_members:
            user_info = client.users_info(user=member_id)
            if user_info["ok"]:
                try:
                    email = user_info["user"]["profile"]["email"]
                    writer.writerow([email])
                    print(f"Correo electrónico copiado: {email}")
                except KeyError:
                    print(f"El usuario {member_id} no tiene una dirección de correo electrónico en su perfil.")
            else:
                print(f"Error al obtener información del usuario {member_id}:", user_info["error"])
except SlackApiError as e:
    print("Error al acceder a la API de Slack:", e)
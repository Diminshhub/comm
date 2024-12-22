import os
import sys
import json
import time
import requests
import websocket
import schedule  # Biblioteca para agendar tarefas
from keep_alive import keep_alive

# Configurações de status e token
status = os.getenv("status")  # online/dnd/idle
custom_status = os.getenv("custom_status")  # Exemplo: "youtube.com/@SealedSaucer"
usertoken = os.getenv("token")
daily_channel_id = os.getenv("DAILY_CHANNEL_ID")  # ID do canal onde o comando será enviado

if not usertoken:
    print("[ERROR] Please add a token inside Secrets.")
    sys.exit()

headers = {"Authorization": usertoken, "Content-Type": "application/json"}

validate = requests.get("https://canary.discordapp.com/api/v9/users/@me", headers=headers)
if validate.status_code != 200:
    print("[ERROR] Your token might be invalid. Please check it again.")
    sys.exit()

userinfo = requests.get("https://canary.discordapp.com/api/v9/users/@me", headers=headers).json()
username = userinfo["username"]
discriminator = userinfo["discriminator"]
userid = userinfo["id"]

def onliner(token, status):
    ws = websocket.WebSocket()
    ws.connect("wss://gateway.discord.gg/?v=9&encoding=json")
    start = json.loads(ws.recv())
    heartbeat = start["d"]["heartbeat_interval"]
    auth = {
        "op": 2,
        "d": {
            "token": token,
            "properties": {
                "$os": "Windows 10",
                "$browser": "Google Chrome",
                "$device": "Windows",
            },
            "presence": {"status": status, "afk": False},
        },
        "s": None,
        "t": None,
    }
    ws.send(json.dumps(auth))
    cstatus = {
        "op": 3,
        "d": {
            "since": 0,
            "activities": [
                {
                    "type": 4,
                    "state": custom_status,
                    "name": "Custom Status",
                    "id": "custom",
                }
            ],
            "status": status,
            "afk": False,
        },
    }
    ws.send(json.dumps(cstatus))
    online = {"op": 1, "d": "None"}
    time.sleep(heartbeat / 1000)
    ws.send(json.dumps(online))

def join_voice_channel():
    """Função para conectar o bot ao canal de voz especificado no servidor"""
    if not guild_id or not voice_channel_id:
        print("[ERROR] Please set GUILD_ID and VOICE_CHANNEL_ID in environment variables.")
        return

    url = f"https://discord.com/api/v9/guilds/{guild_id}/voice-states/@me"
    payload = {"channel_id": voice_channel_id}
    response = requests.patch(url, headers=headers, json=payload)

    if response.status_code == 204:
        print(f"Successfully connected to voice channel {voice_channel_id} in guild {guild_id}")
    else:
        print(f"[ERROR] Could not connect to voice channel: {response.status_code} - {response.text}")

def send_daily_command():
    """Função para enviar o comando /daily no canal configurado"""
    if not daily_channel_id:
        print("[ERROR] DAILY_CHANNEL_ID not set.")
        return

    url = f"https://discord.com/api/v9/channels/{daily_channel_id}/messages"
    payload = {"content": "/daily"}
    response = requests.post(url, headers=headers, json=payload)

    if response.status_code == 200:
        print(f"Successfully sent '/daily' in channel {daily_channel_id}")
    else:
        print(f"[ERROR] Could not send '/daily': {response.status_code} - {response.text}")

def schedule_daily_command():
    """Agendar o envio do comando /daily para as 11h"""
    schedule.every().day.at("11:00").do(send_daily_command)

def run_onliner():
    os.system("clear")
    print(f"Logged in as {username}#{discriminator} ({userid}).")
    join_voice_channel()  # Conecta ao canal de voz ao iniciar
    schedule_daily_command()  # Agenda o envio diário do comando /daily
    while True:
        onliner(usertoken, status)
        schedule.run_pending()  # Executa tarefas agendadas
        time.sleep(1)

keep_alive()
run_onliner()

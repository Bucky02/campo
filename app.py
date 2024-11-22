import os
import json
from datetime import datetime
import asyncio
import nest_asyncio
from flask import Flask, jsonify, render_template
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

# Applica nest_asyncio per permettere l'esecuzione di asyncio nel thread principale
nest_asyncio.apply()

app = Flask(__name__)

# Funzioni Flask (app.py)
def carica_prenotazioni():
    try:
        file_path = os.path.join(os.path.dirname(__file__), 'prenotazioni.json')
        with open(file_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Errore nel caricamento delle prenotazioni: {e}")
        return {}

@app.route("/prenotazioni")
def prenotazioni():
    prenotazioni = carica_prenotazioni()
    eventi = []
    for data, lista_prenotazioni in prenotazioni.items():
        for prenotazione in lista_prenotazioni:
            evento = {
                "title": prenotazione["cognome"],
                "start": f"{data}T{prenotazione['orario']}:00:00",
                "end": f"{data}T{prenotazione['orario'] + 1}:00:00"
            }
            eventi.append(evento)
    return jsonify(eventi)

@app.route('/')
def index():
    return render_template('index.html')

# Funzioni Telegram Bot (bot.py)
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Ciao! Come posso aiutarti?")

async def main() -> None:
    app = ApplicationBuilder().token('YOUR_BOT_TOKEN').build()
    app.add_handler(CommandHandler("start", start))
    await app.run_polling()

# Funzione per avviare sia Flask che il bot in parallelo
def run():
    # Avvia Flask in un processo separato
    from multiprocessing import Process
    p = Process(target=app.run, kwargs={"debug": True, "host": '0.0.0.0', "port": 5000})
    p.start()

    # Avvia il bot Telegram
    asyncio.run(main())

if __name__ == '__main__':
    run()

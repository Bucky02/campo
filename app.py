from flask import Flask, render_template, jsonify
import json
import os
from datetime import datetime

app = Flask(__name__)

# Funzione per caricare le prenotazioni dal file JSON
def carica_prenotazioni():
    try:
        # Percorso completo al file prenotazioni.json
        file_path = os.path.join(os.path.dirname(__file__), 'prenotazioni.json')
        with open(file_path, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print(f"Errore nel parsing di JSON: {e}")
        return {}
    except FileNotFoundError as e:
        print(f"File non trovato: {e}")
        return {}

@app.route("/prenotazioni")
def prenotazioni():
    try:
        prenotazioni = carica_prenotazioni()
        print("Prenotazioni caricate:", prenotazioni)  # Log per debug
        eventi = []

        for data, lista_prenotazioni in prenotazioni.items():
            try:
                # Converte la data nel formato ISO
                data_iso = datetime.strptime(data, "%d-%m-%Y").strftime("%Y-%m-%d")
            except ValueError as e:
                print(f"Errore nella conversione della data {data}: {e}")
                continue

            # Cicla su ogni prenotazione nella lista di prenotazioni per

            # Cicla su ogni prenotazione nella lista di prenotazioni per il giorno
            for prenotazione in lista_prenotazioni:
                orario = prenotazione['orario']
                cognome = prenotazione['cognome']
                telefono = prenotazione['telefono']
                
                evento = {
                    "title": cognome,  # Mostra il cognome nel titolo dell'evento
                    "start": f"{data_iso}T{str(orario).zfill(2)}:00:00",
                    "end": f"{data_iso}T{str(orario + 1).zfill(2)}:00:00" if orario < 23 else f"{data_iso}T23:59:59",
                    "description": f"Telefono: {telefono}"  # Descrizione con il numero di telefono
                }
                eventi.append(evento)

        return jsonify(eventi)
    except Exception as e:
        print(f"Errore nel caricamento delle prenotazioni: {e}")
        return jsonify([])

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    # Avvia il server web
    app.run(debug=True, host='0.0.0.0', port=5000)


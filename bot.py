import nest_asyncio
import asyncio
import json
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler, MessageHandler, filters
from datetime import datetime, timedelta


# Applica nest_asyncio
nest_asyncio.apply()

# Inserisci qui il tuo token
TOKEN = '8000421880:AAG80u8i_7O9CMMpVHz-DfEDkcBhOol_i_k'

# Dizionario per memorizzare le prenotazioni
prenotazioni = {}

def salva_prenotazioni():
    with open("prenotazioni.json", "w") as file:
        json.dump(prenotazioni, file, indent=4)


def carica_prenotazioni():
    if os.path.exists('prenotazioni.json') and os.path.getsize('prenotazioni.json') > 0:
        with open('prenotazioni.json', 'r') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}  # Ritorna un dizionario vuoto se il file non è un JSON valido
    return {}



# Funzione per ottenere gli orari disponibili dalle 16 alle 24
def orari_disponibili(data):
    orari = []
    prenotati = prenotazioni.get(data, [])

    for orario in range(16, 24):
        # Verifica se esiste una prenotazione per l'orario corrente
        if not any(prenotazione["orario"] == orario for prenotazione in prenotati):
            orari.append(f"{orario}:00 - {orario + 1}:00")
    
    return orari


def giorni_disponibili():
    today = datetime.now()
    giorni = []

    # Se oggi è domenica, iniziare da lunedì
    if today.weekday() == 6:  # 6 rappresenta la domenica
        today += timedelta(days=1)

    # Genera i prossimi 7 giorni, escludendo le domeniche
    for i in range(7):
        giorno = today + timedelta(days=i)
        if giorno.weekday() != 6:  # Esclude la domenica
            giorni.append(giorno.strftime('%d-%m-%Y'))

    return giorni




# Funzione per il comando /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [
        [InlineKeyboardButton("Prenota", callback_data="prenota")],
        [InlineKeyboardButton("Disdici", callback_data="disdici")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Ciao! Scegli un'opzione:", reply_markup=reply_markup)

# Funzione per gestire la prenotazione
async def start_prenotazione(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.callback_query.message.reply_text("Inserisci il tuo cognome per procedere con la prenotazione:")
    context.user_data.clear()  # Pulisce user_data per evitare confusione tra stati
    context.user_data['inserisci_cognome_prenotazione'] = True

# Funzione per gestire l'inserimento del cognome e mostrare gli orari disponibili
async def processa_prenotazione(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if context.user_data.get('inserisci_cognome_prenotazione'):
        cognome = update.message.text
        context.user_data['cognome'] = cognome
        today = datetime.now()

        # Se oggi è domenica, seleziona lunedì come giorno iniziale
        giorno_selezionato = (today + timedelta(days=1)).strftime('%d-%m-%Y') if today.weekday() == 6 else today.strftime('%d-%m-%Y')

        context.user_data['giorno_selezionato'] = giorno_selezionato
        await mostra_orari(update.message, giorno_selezionato)
        context.user_data['inserisci_cognome_prenotazione'] = False

async def ricevi_telefono(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if context.user_data.get('richiesta_telefono'):
        numero_telefono = update.message.text
        cognome = context.user_data.get('cognome')
        giorno_selezionato = context.user_data.get('giorno_selezionato')
        orario_selezionato = int(context.user_data.get('orario_selezionato').split(":")[0])

        # Inizializza una lista di prenotazioni per il giorno se non esiste
        prenotazioni.setdefault(giorno_selezionato, [])

        # Controlla se esiste già una prenotazione per l'orario e telefono
        if not any(prenotazione["orario"] == orario_selezionato and prenotazione["telefono"] == numero_telefono for prenotazione in prenotazioni[giorno_selezionato]):
            # Aggiunge la nuova prenotazione come dizionario
            # Aggiunge la nuova prenotazione come dizionario
            prenotazioni[giorno_selezionato].append({
                "orario": orario_selezionato,
                "cognome": cognome,
                "telefono": numero_telefono
            })


            # Salva nel file JSON
            salva_prenotazioni()

            await update.message.reply_text(
                f"Prenotazione confermata per {giorno_selezionato} alle {orario_selezionato}:00. Numero registrato: {numero_telefono}."
            )
        else:
            await update.message.reply_text(f"Mi dispiace, l'orario {orario_selezionato}:00 è già prenotato.")

        context.user_data.clear()


# Funzione per mostrare gli orari disponibili per un giorno specifico
async def mostra_orari(message, giorno_selezionato: str) -> None:
    orari = orari_disponibili(giorno_selezionato)

    # Crea la tastiera con gli orari disponibili (se ce ne sono)
    keyboard = []
    if orari:
        keyboard = [[InlineKeyboardButton(orario, callback_data=f"conferma_{orario}")] for orario in orari]
    else:
        await message.reply_text("Non ci sono orari disponibili per questo giorno.")

    # Aggiungi sempre il bottone "Cambio giorno"
    keyboard.append([InlineKeyboardButton("Cambio giorno", callback_data="cambio_giorno")])

    # Mostra la tastiera
    reply_markup = InlineKeyboardMarkup(keyboard)
    await message.reply_text(f"Ecco gli orari disponibili per {giorno_selezionato}:", reply_markup=reply_markup)


# Funzione per confermare la prenotazione
async def conferma_prenotazione(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    orario_selezionato = update.callback_query.data.split("_")[1]
    giorno_selezionato = context.user_data.get('giorno_selezionato')

    # Recupera le prenotazioni per il giorno selezionato, o un elenco vuoto se non ci sono
    orari_prenotati = prenotazioni.get(giorno_selezionato, [])

    # Controlla se l'orario è già prenotato per il giorno selezionato
    if any(prenotazione["orario"] == int(orario_selezionato.split(":")[0]) for prenotazione in orari_prenotati):
        await update.callback_query.message.reply_text(
            f"Mi dispiace, l'orario {orario_selezionato} è già prenotato per il {giorno_selezionato}. "
            "Per favore scegli un altro orario."
        )
        return

    # Se l'orario è disponibile, salva la scelta e chiedi conferma
    context.user_data['orario_selezionato'] = orario_selezionato
    keyboard = [
        [InlineKeyboardButton("Si", callback_data="conferma_si")],
        [InlineKeyboardButton("No", callback_data="conferma_no")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.message.reply_text(
        f"Sicuro di voler prenotare per le {orario_selezionato}?",
        reply_markup=reply_markup
    )




###############################################
async def finalizza_prenotazione(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.callback_query.answer()  # Conferma immediata per evitare blocchi
    conferma = update.callback_query.data.split("_")[1]  # Accedi alla conferma

    if conferma == "si":
        # Dopo conferma, chiedi il numero di telefono
        await update.callback_query.message.reply_text("Per favore, inserisci il tuo numero di telefono per completare la prenotazione:")
        context.user_data['richiesta_telefono'] = True  # Imposta richiesta telefono
    else:
        await update.callback_query.message.reply_text("Prenotazione annullata.")
        context.user_data.clear()  # Pulisce i dati dell'utente






# Funzione per gestire la disdetta
async def start_disdetta(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.callback_query.message.reply_text("Inserisci il tuo numero di telefono per procedere con la disdetta:")
    context.user_data.clear()
    context.user_data['richiesta_disdetta'] = True


async def mostra_giorni(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    giorni = giorni_disponibili()
    keyboard = [[InlineKeyboardButton(giorno, callback_data=f"giorno_{giorno}")] for giorno in giorni]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.message.reply_text("Seleziona un giorno per la prenotazione:", reply_markup=reply_markup)


async def seleziona_giorno(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    giorno_selezionato = update.callback_query.data.split("_")[1]
    context.user_data['giorno_selezionato'] = giorno_selezionato
    await mostra_orari(update.callback_query.message, giorno_selezionato)

# Funzione per processare la disdetta basata sul cognome
async def processa_disdetta(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if context.user_data.get('richiesta_disdetta'):
        numero_telefono = update.message.text
        context.user_data['numero_telefono'] = numero_telefono

        # Ottieni la data di oggi
        today = datetime.now().strftime('%d-%m-%Y')

        # Cerca le prenotazioni associate a questo numero di telefono a partire da oggi
        prenotazioni_utente = []
        for giorno, prenotati in prenotazioni.items():
            if giorno >= today:  # Controlliamo solo le prenotazioni future
                for prenotazione in prenotati:
                    if prenotazione["telefono"] == numero_telefono:
                        orario = prenotazione["orario"]
                        prenotazioni_utente.append(f"{giorno} {orario}:00 - {orario + 1}:00")

        if prenotazioni_utente:
            keyboard = [[InlineKeyboardButton(orario, callback_data=f"annulla_{orario}")] for orario in prenotazioni_utente]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text("Seleziona una prenotazione da annullare:", reply_markup=reply_markup)
        else:
            await update.message.reply_text("Non ci sono prenotazioni future con questo numero di telefono.")

        context.user_data['richiesta_disdetta'] = False





# Funzione per confermare la disdetta
async def conferma_disdetta(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.callback_query.answer()
    orario_da_annullare = update.callback_query.data.split("_")[1]
    numero_telefono = context.user_data.get('numero_telefono')
    
    # Dividi il testo "giorno orario" per ottenere separatamente il giorno e l'orario
    giorno_selezionato = orario_da_annullare.split(" ")[0]
    orario_int = int(orario_da_annullare.split(" ")[1].split(":")[0])

    # Controlla se il giorno e l'orario esistono nel dizionario delle prenotazioni
    if giorno_selezionato in prenotazioni:
        # Trova la prenotazione con lo specifico numero di telefono e orario
        prenotazioni_giorno = prenotazioni[giorno_selezionato]
        prenotazione_da_annullare = None

        # Cicla attraverso le prenotazioni del giorno per trovare quella da annullare
        for prenotazione in prenotazioni_giorno:
            if prenotazione["telefono"] == numero_telefono and prenotazione["orario"] == orario_int:
                prenotazione_da_annullare = prenotazione
                break

        # Se troviamo la prenotazione, la rimuoviamo
        if prenotazione_da_annullare:
            prenotazioni_giorno.remove(prenotazione_da_annullare)
            
            # Se non ci sono più prenotazioni per il giorno, rimuoviamo l'intero giorno dal dizionario
            if not prenotazioni_giorno:
                del prenotazioni[giorno_selezionato]
            
            salva_prenotazioni()  # Aggiorna il file JSON dopo la rimozione
            await update.callback_query.message.reply_text(
                f"Disdetta effettuata per il {giorno_selezionato} alle {orario_int}:00."
            )
        else:
            await update.callback_query.message.reply_text("Errore: la prenotazione non esiste più.")
    else:
        await update.callback_query.message.reply_text("Errore: la prenotazione non esiste più.")





# Aggiungi un nuovo callback per finalizzare la disdetta
async def finalizza_disdetta(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    data = update.callback_query.data.split("_")
    conferma = data[1]
    
    if conferma == "si":
        giorno_selezionato = data[2]
        orario_int = int(data[3])
        numero_telefono = context.user_data.get('numero_telefono')  # Usa il numero di telefono invece del cognome

        # Rimuovi l'orario dalla prenotazione se esiste
        if giorno_selezionato in prenotazioni and numero_telefono in prenotazioni[giorno_selezionato] and orario_int in prenotazioni[giorno_selezionato][numero_telefono]:
            prenotazioni[giorno_selezionato][numero_telefono].remove(orario_int)
            # Se non ci sono più orari per questo numero di telefono, rimuovilo completamente
            if not prenotazioni[giorno_selezionato][numero_telefono]:
                del prenotazioni[giorno_selezionato][numero_telefono]
            await update.callback_query.message.reply_text(f"Disdetta effettuata per il {giorno_selezionato} alle {orario_int}:00.")
        else:
            await update.callback_query.message.reply_text("Errore: la prenotazione non esiste più.")
    
    else:
        await update.callback_query.message.reply_text("Disdetta annullata. Seleziona un'altra azione.")

        



async def mostra_prenotazioni(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    numero_telefono = context.user_data.get('numero_telefono')
    prenotazioni_utente = []
    
    for giorno, prenotati in prenotazioni.items():
        if numero_telefono in prenotati:
            orari = [f"{giorno} {o}:00 - {o + 1}:00" for o in prenotati[numero_telefono]]
            prenotazioni_utente.extend(orari)

    if prenotazioni_utente:
        keyboard = [[InlineKeyboardButton(orario, callback_data=f"annulla_{orario}")] for orario in prenotazioni_utente]
        keyboard.append([InlineKeyboardButton("Annulla", callback_data="annulla")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.callback_query.message.reply_text("Ecco le tue prenotazioni attuali:", reply_markup=reply_markup)
    else:
        await update.callback_query.message.reply_text("Non hai prenotazioni attive.")





async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if context.user_data.get('inserisci_cognome_prenotazione'):
        await processa_prenotazione(update, context)
    elif context.user_data.get('richiesta_disdetta'):
        await processa_disdetta(update, context)
    elif context.user_data.get('richiesta_telefono'):
        await ricevi_telefono(update, context)







# Funzione principale per gestire il bot
async def main() -> None:
    app = ApplicationBuilder().token(TOKEN).build()
    global prenotazioni
    prenotazioni = carica_prenotazioni()

    

    # Aggiungi gli handler
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(start_prenotazione, pattern="^prenota$"))
    app.add_handler(CallbackQueryHandler(start_disdetta, pattern="^disdici$"))
    
    
    # Aggiungi handler per testo quando siamo in fase di prenotazione o disdetta
    app.add_handler(MessageHandler(filters.TEXT & filters.ChatType.PRIVATE, handle_text))
    app.add_handler(CallbackQueryHandler(mostra_giorni, pattern="^cambio_giorno$"))
    app.add_handler(CallbackQueryHandler(seleziona_giorno, pattern=r"^giorno_\d{2}-\d{2}-\d{4}$"))
    app.add_handler(CallbackQueryHandler(finalizza_disdetta, pattern=r"^disdici_(si|no)_\d{2}-\d{2}-\d{4}_\d{1,2}$"))
    
    app.add_handler(CallbackQueryHandler(conferma_prenotazione, pattern=r"^conferma_\d{1,2}:\d{2} - \d{1,2}:\d{2}$"))
    app.add_handler(CallbackQueryHandler(finalizza_prenotazione, pattern=r"^conferma_(si|no)$"))
    app.add_handler(CallbackQueryHandler(conferma_disdetta, pattern=r"^annulla_\d{2}-\d{2}-\d{4} \d{1,2}:\d{2} - \d{1,2}:\d{2}$"))

    await app.run_polling()



if __name__ == '__main__':
    asyncio.run(main())

from pymongo import MongoClient
import logging

# Verbindung zu MongoDB einrichten
client = MongoClient('mongodb://localhost:27017/')
db = client['scrapy_database']  # Ersetze 'scrapy_database' durch deinen Datenbanknamen
collection = db['antifaRaw']  # Ersetze 'test' durch den Namen deiner Sammlung

# Logging konfigurieren
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


# Funktion zum Entfernen von Einträgen mit URLs, die ein '#' enthalten
def remove_entries_with_fragment():
    try:
        # Finde alle Einträge, deren URLs ein '#' enthalten
        entries_with_fragment = collection.find({'url': {'$regex': '#'}})

        # Anzahl der Einträge mit '#' in der URL zählen
        count = collection.count_documents({'url': {'$regex': '#'}})

        if count == 0:
            logging.info("Keine Einträge mit '#' in der URL gefunden.")
            return

        # Lösche die Einträge
        result = collection.delete_many({'url': {'$regex': '#'}})

        # Zeige die Anzahl der gelöschten Dokumente an
        logging.info(f"{result.deleted_count} Einträge mit '#' in der URL wurden erfolgreich gelöscht.")

    except Exception as e:
        logging.error(f"Fehler beim Löschen der Einträge: {e}")


# Hauptfunktion ausführen
if __name__ == '__main__':
    remove_entries_with_fragment()

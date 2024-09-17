'''import requests

# Basis-URL der libleipzig API
base_url = "https://api.wortschatz-leipzig.de/ws"

# Setze den Korpus und das Wort
corpus_name = "deu_news_2022"  # Beispiel-Korpusname
word = "Anstrengungsbereitschaft"

# Parameter für die Anfrage
offset = 0
limit = 10

# Endpunkt für Beispielsätze für ein Wort
endpoint = f"/sentences/{corpus_name}/sentences/{word}"

# Vollständige URL mit Query-Parameter
url = f"{base_url}{endpoint}?offset={offset}&limit={limit}"

# Sende eine GET-Anfrage
response = requests.get(url, headers={"accept": "application/json"})

# Überprüfen, ob die Anfrage erfolgreich war
if response.status_code == 200:
    data = response.json()  # JSON-Daten aus der Antwort extrahieren

    # Prüfen, ob 'sentences' im zurückgegebenen JSON enthalten ist
    if 'sentences' in data:
        sentences = data['sentences']
        print(f"Beispielsätze für '{word}':")
        for sentence_data in sentences:
            sentence = sentence_data.get('sentence')
            if sentence:
                print(sentence)
            else:
                print("Kein Satz gefunden.")
    else:
        print("Keine Sätze gefunden oder unvollständige Daten:", data)
else:
    print(f"Fehler beim Abrufen der Sätze: {response.status_code} - {response.text}")
'''
'''

import odenet

def check_word_in_odenet(word):
    # Verwende die Methode synonyms_word, um Synonyme des Wortes zu finden
    synonyms = odenet.synonyms_word(word)

    # Überprüfe, ob die Liste der Synonyme nicht leer ist
    if synonyms:
        print(f"Das Wort '{word}' ist in OdeNet enthalten.")
        print(f"Synonyme für '{word}': {synonyms}")
    else:
        print(f"Das Wort '{word}' ist nicht in OdeNet enthalten.")

# Überprüfen, ob das Wort 'Haus' in OdeNet enthalten ist
check_word_in_odenet('Anstrengungsbereitschaft')

'''
import time
import odenet

# Cache für Odenet-Abfragen
odenet_cache = {}


class OdenetCacheTester:
    def __init__(self):
        self.cache = {}

    def is_word_in_odenet(self, word):
        # Überprüfen, ob das Wort bereits im Cache vorhanden ist
        if word in self.cache:
            return self.cache[word]

        # Wenn das Wort noch nicht im Cache ist, führen wir die Abfrage durch
        start_time = time.time()
        synonyms = odenet.synonyms_word(word)
        duration = time.time() - start_time
        print(f"Zeit für is_word_in_odenet: {duration} Sekunden")

        # Speichern des Ergebnisses im Cache
        self.cache[word] = bool(synonyms)
        return self.cache[word]


# Testen der Klasse
if __name__ == '__main__':
    tester = OdenetCacheTester()

    # Liste von Wörtern zum Testen
    words_to_test = ['Apfel', 'Zeit', 'Geist', 'Apfel', 'Geist', 'test']

    for word in words_to_test:
        result = tester.is_word_in_odenet(word)
        print(f"Ergebnis für '{word}': {result}")

    # Zeige die Größe des Caches
    print(f"Cache-Größe: {len(tester.cache)}")
'''
# Listet alle Funktionen und Attribute der odenet-Bibliothek auf
odenet_functions = dir(odenet)

# Ausgabe der Funktionen und Attribute
print("Verfügbare Funktionen und Attribute in OdeNet:")
for function in odenet_functions:
    print(function)
    '''
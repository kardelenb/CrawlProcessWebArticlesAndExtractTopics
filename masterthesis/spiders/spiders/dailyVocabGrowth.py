import matplotlib.pyplot as plt
from pymongo import MongoClient
import pandas as pd

# Verbindung zur MongoDB herstellen
client = MongoClient('mongodb://localhost:27017/')
db = client['scrapy_database']
vocabulary_growth_collection = db['SZvocabulary_growth']

# Daten extrahieren
data = list(vocabulary_growth_collection.find())
df = pd.DataFrame(data)

# Konvertiere das Datum in ein geeignetes Format und sortiere nach Datum
df['date'] = pd.to_datetime(df['date'])
df = df.sort_values(by='date')

# Erstellen der Grafik mit logarithmischer Skalierung
plt.figure(figsize=(12, 6))
plt.plot(df['date'], df['new_words_count'], marker='o', label="Neue Wörter pro Tag")
plt.plot(df['date'], df['repeated_words_count'], marker='s', label="Wiederholte Wörter pro Tag")
plt.yscale('log')  # Setzt die Y-Achse auf eine logarithmische Skalierung
plt.xlabel("Datum")
plt.ylabel("Anzahl Wörter (logarithmisch)")
plt.title("Tägliches Vokabelwachstum: Neue und Wiederholte Wörter")
plt.xticks(rotation=45)
plt.legend()
plt.tight_layout()
plt.savefig("daily_vocabulary_growth_logarithmic.png")  # Speichert das Diagramm als Bild
plt.show()

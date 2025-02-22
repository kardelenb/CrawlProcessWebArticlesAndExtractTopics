import matplotlib.pyplot as plt
from pymongo import MongoClient
import pandas as pd

# Verbindung zur MongoDB herstellen
client = MongoClient('mongodb://localhost:27017/')
db = client['scrapy_database']
# Ersetze mit den tatsächlichen Namen der Kollektionen
vocabulary_growth_collection = db['im_growth_en']

# Daten aus der Kollektion abrufen
data = list(vocabulary_growth_collection.find({}, {"_id": 0, "date": 1, "new_words_count": 1, "repeated_words_count": 1}))

# In ein DataFrame umwandeln
df = pd.DataFrame(data)

# Sicherstellen, dass das Datum als Datumsformat erkannt wird
df['date'] = pd.to_datetime(df['date'])

# Nach Datum sortieren
df = df.sort_values('date')

# Daten ohne den ersten Tag filtern
df_filtered = df.iloc[1:]  # Entferne die erste Zeile

# Liniendiagramm erstellen ohne den ersten Tag
plt.figure(figsize=(12, 8))
plt.plot(df_filtered['date'], df_filtered['new_words_count'], label='Neue Schlüsselwörter und -phrasen', marker='o')
plt.plot(df_filtered['date'], df_filtered['repeated_words_count'], label='Wiederholte Schlüsselwörter und -phrasen', marker='o')

plt.title('Vokabularwachstum über die Zeit (ohne ersten Tag)')
plt.xlabel('Datum')
plt.ylabel('Anzahl der Schlüsselwörter und -phrasen')
plt.legend()
plt.grid(True)
plt.tight_layout()

# Diagramm anzeigen
plt.show()
import matplotlib.pyplot as plt
from pymongo import MongoClient
import pandas as pd
import os

# Verbindung zur MongoDB herstellen
client = MongoClient('mongodb://localhost:27017/')
db = client['scrapy_database']
vocabulary_growth_collection = db['AI2vocabulary_growth']

# Daten extrahieren und in ein DataFrame umwandeln
data = list(vocabulary_growth_collection.find())
df = pd.DataFrame(data)

# Konvertiere das Datum in ein geeignetes Format und sortiere nach Datum
df['date'] = pd.to_datetime(df['date'])
df = df.sort_values(by='date')

# Erstelle das Ausgabeverzeichnis, falls nicht vorhanden
output_dir = 'output/'
os.makedirs(output_dir, exist_ok=True)

# 1. Gesamtes Vokabelwachstum einschließlich des ersten Tages
plt.figure(figsize=(10, 6))
plt.bar(df['date'], df['new_words_count'], label='Neue Wörter', color='skyblue')
plt.bar(df['date'], df['repeated_words_count'], bottom=df['new_words_count'], label='Wiederholte Wörter', color='salmon')
plt.xlabel('Datum')
plt.ylabel('Anzahl Wörter')
plt.title('Tägliches Vokabelwachstum (Gesamt)')
plt.xticks(rotation=45)
plt.legend()
plt.tight_layout()
plt.savefig(f"{output_dir}/AItaegliches_vokabelwachstum_gesamt.png")
plt.show()

# 2. Vokabelwachstum ohne den ersten Tag
df_without_first = df.iloc[1:]  # Alle Tage außer dem ersten

plt.figure(figsize=(10, 6))
plt.bar(df_without_first['date'], df_without_first['new_words_count'], label='Neue Wörter', color='skyblue')
plt.bar(df_without_first['date'], df_without_first['repeated_words_count'], bottom=df_without_first['new_words_count'], label='Wiederholte Wörter', color='salmon')
plt.xlabel('Datum')
plt.ylabel('Anzahl Wörter')
plt.title('Tägliches Vokabelwachstum (ohne den ersten Tag)')
plt.xticks(rotation=45)
plt.legend()
plt.tight_layout()
plt.savefig(f"{output_dir}/AItaegliches_vokabelwachstum_ohne_ersten_tag.png")
plt.show()

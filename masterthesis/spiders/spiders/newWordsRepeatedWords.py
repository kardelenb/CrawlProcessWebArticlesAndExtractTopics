import matplotlib.pyplot as plt
from pymongo import MongoClient
import pandas as pd
import os

# Verbindung zur MongoDB
client = MongoClient('mongodb://localhost:27017/')
db = client['scrapy_database']
daily_summary_collection = db['daily_sezessionWithoutGN']

# Erstelle ein Verzeichnis für die Diagramme, falls noch nicht vorhanden
output_dir = 'output/'
os.makedirs(output_dir, exist_ok=True)

# Daten aus MongoDB extrahieren
data = []
for entry in daily_summary_collection.find():
    data.append({
        'date': entry['date'],
        'new_word_count': entry['new_word_count'],
        'repeated_word_count': entry['repeated_word_count']
    })

# In ein DataFrame umwandeln und nach Datum sortieren
df = pd.DataFrame(data)
df['date'] = pd.to_datetime(df['date'])
df = df.sort_values(by='date')

# 1. Plot für den Trend der neuen und wiederholten Wörter über die Zeit
plt.figure(figsize=(10, 5))
plt.plot(df['date'], df['new_word_count'], label='Neue Wörter', marker='o')
plt.plot(df['date'], df['repeated_word_count'], label='Wiederholte Wörter', marker='o')
plt.xlabel('Datum')
plt.ylabel('Anzahl Wörter')
plt.title('Neue vs. Wiederholte Wörter pro Tag')
plt.legend()
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig(os.path.join(output_dir, 'new_vs_repeated_words_trend.png'))
plt.close()

# 2. Anteil neuer Wörter pro Tag
df['new_word_ratio'] = df['new_word_count'] / (df['new_word_count'] + df['repeated_word_count'])
plt.figure(figsize=(10, 5))
plt.bar(df['date'], df['new_word_ratio'], color='skyblue')
plt.xlabel('Datum')
plt.ylabel('Anteil neuer Wörter')
plt.title('Anteil neuer Wörter pro Tag')
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig(os.path.join(output_dir, 'new_word_ratio_per_day.png'))
plt.close()

# 3. Gesamtanzahl neuer und wiederholter Wörter
total_new_words = df['new_word_count'].sum()
total_repeated_words = df['repeated_word_count'].sum()

plt.figure(figsize=(6, 6))
plt.pie(
    [total_new_words, total_repeated_words],
    labels=['Neue Wörter', 'Wiederholte Wörter'],
    autopct='%1.1f%%',
    startangle=140,
    colors=['skyblue', 'salmon']
)
plt.title('Gesamtanzahl neuer vs. wiederholter Wörter')
plt.savefig(os.path.join(output_dir, 'total_new_vs_repeated_words.png'))
plt.close()

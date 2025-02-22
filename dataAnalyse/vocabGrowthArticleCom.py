from pymongo import MongoClient
import matplotlib.pyplot as plt
import pandas as pd

# Verbindung zur MongoDB herstellen
client = MongoClient('mongodb://localhost:27017/')
db = client['scrapy_database']
# Ersetze mit den tatsächlichen Namen der Kollektionen
daily_summary_collection = db['imDailyGe']

# Daten aus der Kollektion abrufen
data = []
for entry in daily_summary_collection.find({}, {"_id": 0, "date": 1, "article_word_frequencies": 1,
                                                "comment_word_frequencies": 1}):
    date = entry['date']
    article_words_total = sum(entry.get("article_word_frequencies", {}).values())
    comment_words_total = sum(entry.get("comment_word_frequencies", {}).values())

    data.append({
        "date": pd.to_datetime(date),
        "article_words": article_words_total,
        "comment_words": comment_words_total
    })

# Daten in ein DataFrame umwandeln
df = pd.DataFrame(data)

# Nach Datum sortieren
df = df.sort_values('date')

# Daten ohne den ersten Tag filtern
df_filtered = df.iloc[1:]  # Entferne die erste Zeile

# Liniendiagramm erstellen
plt.figure(figsize=(14, 8))
plt.plot(df_filtered['date'], df_filtered['article_words'], label='Schlüsselwörter und -phrasen aus Artikeln', marker='o', color='blue')
plt.plot(df_filtered['date'], df_filtered['comment_words'], label='Schlüsselwörter und -phrasen aus Kommentaren', marker='x', color='green')

# Titel und Achsenbeschriftungen
plt.title('Entwicklung der Schlüsselwörter und -phrasen in Artikeln und Kommentaren über die Zeit (ohne ersten Tag)', fontsize=16)
plt.xlabel('Datum (Verarbeitungstage)', fontsize=14)
plt.ylabel('Anzahl der Schlüsselwörter und -phrasen', fontsize=14)
plt.legend(fontsize=12)
plt.grid(True, linestyle="--", alpha=0.6)

# Nur jeden 5. Tag als Beschriftung anzeigen
plt.xticks(df_filtered['date'][::5], rotation=45, ha='right')
plt.tight_layout()

# Diagramm anzeigen
plt.show()

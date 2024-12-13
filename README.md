# Topic Extraction and Query Generation From Websites

Dieses Projekt besteht aus zwei Hauptteilen:

1. **Web Scraping**: Ein Python-Skript zum Scraping von Artikeln und Kommentaren von Websites, die Sitemaps bereitstellen. Die Daten werden in einer MongoDB-Datenbank gespeichert.
2. **Textanalyse**: Ein zweites Python-Skript, das extrahierte Artikel und Kommentare aus der MongoDB analysiert und neue Wörter oder Phrasen basierend auf einem Wörterbuch vergleicht.

## Teil 1: Web Scraping

### Funktionsweise

- Das Skript durchsucht die Sitemap der angegebenen Website (falls vorhanden), um Artikel-URLs zu finden.
- Es crawlt Inhalte wie Titel, Text und Kommentare der Artikel und speichert die Daten in MongoDB.
- Websites ohne Sitemaps werden durch einen rekursiven Crawling-Ansatz verarbeitet.

### Voraussetzungen

- Python 3.7+
- MongoDB (lokal oder Remote)
- Python-Bibliotheken (siehe `requirements.txt`)

### Installation

1. Klone dieses Repository:
   ```bash
   git clone https://github.com/kardelenb/CrawlProcessWebArticlesAndExtractTopics/tree/master
2. Navigiere in das Projektverzeichnis:
   ```bash
    cd dein_repository
3. Installiere die Abhängigkeiten:
   ```bash
     pip install -r requirements.txt

4. Stelle sicher, dass MongoDB läuft und du eine Verbindung zur Datenbank hast.
   
### Verwendung
1. Starte das Skript crawler.py:
   ```bash
    python crawler.py

3. Gib die Basis-URL der Website ein, von der du Artikel und Kommentare extrahieren möchtest.

4. Das Skript durchsucht die Sitemap oder crawlt die Website direkt, extrahiert die Artikel und/oder Komementare und speichert sie in MongoDB.
## Teil 2: Textanalyse
### Funktionsweise
- Dieses Modul analysiert Artikel und Kommentare, die zuvor in MongoDB gespeichert wurden.
- Es verwendet NLP-Tools (z. B. spaCy), um Schlüsselwörter und Mehrwortphrasen basierend auf POS-Tags (Part-of-Speech) zu extrahieren.
- Extrahierte Wörter und Phrasen werden mit einer Referenzdatei (wortschatzLeipzig.txt) oder WordNet verglichen, um neue Begriffe zu identifizieren.

### Voraussetzungen
- Die Daten aus Teil 1 müssen bereits in MongoDB gespeichert sein.
- Eine Referenzdatei (wortschatzLeipzig.txt) oder ein Wörterbuch für den Vergleich muss vorhanden sein.

### Verwendung
1. Starte das Skript zur Textanalyse:
   ```bash
   python processor.py

### Funktionsweise
- Extrahiert Schlüsselwörter und relevante Phrasen aus dem Artikeltext.
- Vergleicht die extrahierten Begriffe mit der Referenzdatei und speichert neue Wörter in der MongoDB.

### Ergebnisse
- Neue Wörter und Phrasen werden in der vocabulary-Kollektion gespeichert.
- Eine tägliche Zusammenfassung der neu erkannten Begriffe wird erstellt.

## Projektstruktur
### Dateien
- crawler.py: Hauptskript für das Web Scraping.
- processor.py: Hauptskript für die Textanalyse.
- checksum.py: Für die Verarbeitung von Webseiten mit regelmäßig angepassten Artikeln.
- processorMixLanguages.py: Für die Verarbeitung von mehrsprachigen Webseiten.
- processorWithGermanet.py: Für die Verarbeitung mit GermaNet und WortschatzLeipzig.
- requirements.txt: Liste der benötigten Python-Bibliotheken.
- wortschatzLeipzig.txt: Referenzdatei für den Vergleich.

### MongoDB-Kollektionen für Hauptskripte
- collection: Diese Kollektion speichert die Rohdaten, die vom Crawler gesammelt werden.
- processed_collection: Diese Kollektion speichert die bereits verarbeiteten Artikel.
- vocabulary_collection: Diese Kollektion speichert alle neu erkannten Wörter und Phrasen.
- daily_summary_collection: Diese Kollektion enthält tägliche Zusammenfassungen der Textanalyse.
- vocabulary_growth_collection:  Diese Kollektion verfolgt das Wachstum des Vokabulars über die Zeit.
- progress_collection: Diese Kollektion dient der Speicherung des Fortschritts während der Verarbeitung. Sie hilft dabei, den Punkt zu verfolgen, an dem die Verarbeitung zuletzt gestoppt wurde, sodass das System später an der gleichen Stelle fortsetzen kann. Das Feld last_processed_id speichert die ID des zuletzt verarbeiteten Artikels.

## Erweiterungen für besondere Anforderungen bestimmter Websites

### Verfügbare Verarbeitungs-Skripte
Je nach Anforderungen der Website können die folgenden Skripte verwendet werden:

---

### **`checksum.py`**
- **Beschreibung**: Für Webseiten wie **Sezession.de**, bei denen bestehende Artikel regelmäßig angepasst werden. Dieses Skript überprüft mithilfe von Checksummen, ob sich Artikel verändert haben, und verarbeitet nur neue Inhalte.
- **Verwendung**:
  ```bash
  python checksum.py


### **`processorMixLanguages.py`**
- **Beschreibung**: Für Webseiten wie **Indymedia.de**, die Inhalte in mehreren Sprachen enthalten (z. B. Russisch, Polnisch). Dieses Skript verarbeitet ausschließlich Artikel in Deutsch und Englisch, wobei die Sprachen getrennt analysiert werden, um die Wartbarkeit der Daten zu verbessern.
- **Verwendung**:
  ```bash
  python processorMixLanguages.py
  

### **`processorWithGermanet.py`**
- **Beschreibung**: Für Webseiten, die mithilfe von WortschatzLeipzig und GermaNet analysiert werden sollen. Dieses Skript erfordert eine gültige GermaNet-Lizenz.
- **Verwendung**:
  ```bash
  python processorWithGermanet.py


# Beispiel Datenbankschema für die Webseite `schweizerZeit` / Hauptskript Outputs

Dieses Dokument beschreibt die Datenbanksammlungen und ihre Felder, die im Projekt verwendet werden. Jede Sammlung ist für spezifische Daten und Operationen konzipiert.

---

## 1. Sammlung: `schweizerZeit`
Speichert die Rohdaten der Artikel, die aus verschiedenen Quellen gecrawlt werden.

| **Feld**    | **Typ**      | **Beschreibung**                                     |
|-------------|--------------|-----------------------------------------------------|
| `_id`       | `ObjectId`   | Automatisch generierter eindeutiger Bezeichner.     |
| `url`       | `String`     | URL des Artikels.                                   |
| `title`     | `String`     | Titel des Artikels.                                 |
| `full_text` | `String`     | Vollständiger Text des Artikels.                    |
| `comments`  | `Array`      | Liste der Kommentare, die dem Artikel zugeordnet sind. |

---

## 2. Sammlung: `schweizerZeitProcessed`
Speichert die verarbeiteten Artikel nach der Textfilterung und Keyword-Extraktion.

| **Feld**               | **Typ**      | **Beschreibung**                                                    |
|-------------------------|--------------|----------------------------------------------------------------------|
| `_id`                  | `ObjectId`   | Automatisch generierter eindeutiger Bezeichner.                     |
| `url`                  | `String`     | URL des Artikels.                                                   |
| `title`                | `String`     | Titel des Artikels.                                                 |
| `full_text`            | `String`     | Gefilterter (bereinigter) Text des Artikels ohne generische Sätze.  |
| `new_article_phrases`  | `Array`      | Neue Phrasen, die aus dem Artikeltext extrahiert wurden.             |
| `new_comment_phrases`  | `Array`      | Neue Phrasen, die aus Kommentaren extrahiert wurden.                 |
| `first_processed`      | `Date`       | Datum, an dem der Artikel zum ersten Mal verarbeitet wurde.          |
| `last_processed`       | `Date`       | Datum, an dem der Artikel zuletzt verarbeitet wurde.                 |

---

## 3. Sammlung: `schweizerZeitVocab`
Speichert die Schlüsselwörter und Phrasen, die aus Artikeln und Kommentaren extrahiert wurden.

| **Feld**               | **Typ**      | **Beschreibung**                                                    |
|-------------------------|--------------|----------------------------------------------------------------------|
| `_id`                  | `ObjectId`   | Automatisch generierter eindeutiger Bezeichner.                     |
| `word`                 | `String`     | Das extrahierte Schlüsselwort oder die Phrase.                      |
| `first_seen`           | `Date`       | Datum, an dem das Wort zum ersten Mal entdeckt wurde.               |
| `last_seen`            | `Date`       | Datum, an dem das Wort zuletzt gesehen wurde.                       |
| `article_occurrences`  | `Integer`    | Häufigkeit des Wortes in Artikeln.                                  |
| `comment_occurrences`  | `Integer`    | Häufigkeit des Wortes in Kommentaren.                               |

---

## 4. Sammlung: `SchweizerZeitDaily`
Speichert tägliche Statistiken über Schlüsselwörter und Phrasen.

| **Feld**                  | **Typ**      | **Beschreibung**                                                    |
|----------------------------|--------------|----------------------------------------------------------------------|
| `_id`                     | `ObjectId`   | Automatisch generierter eindeutiger Bezeichner.                     |
| `date`                    | `Date`       | Datum der Zusammenfassung.                                          |
| `article_word_frequencies`| `Object`     | Häufigkeiten der Wörter in Artikeln (als `{wort: anzahl}`).         |
| `comment_word_frequencies`| `Object`     | Häufigkeiten der Wörter in Kommentaren (als `{wort: anzahl}`).      |
| `new_words_today`         | `Array`      | Liste der Wörter/Phrasen, die heute neu entdeckt wurden.            |
| `repeated_words_today`    | `Array`      | Liste der Wörter/Phrasen, die heute wiederholt aufgetreten sind.    |
| `new_word_count`          | `Integer`    | Anzahl der neu entdeckten Wörter/Phrasen.                          |
| `repeated_word_count`     | `Integer`    | Anzahl der wiederholten Wörter/Phrasen.                            |

---

## 5. Sammlung: `SZvocabulary_growth`
Speichert das Wachstum des Vokabulars.

| **Feld**               | **Typ**      | **Beschreibung**                                                    |
|-------------------------|--------------|----------------------------------------------------------------------|
| `_id`                  | `ObjectId`   | Automatisch generierter eindeutiger Bezeichner.                     |
| `date`                 | `Date`       | Datum der Zusammenfassung.                                          |
| `new_words_count`      | `Integer`    | Anzahl der neuen Wörter/Phrasen für das Datum.                      |
| `repeated_words_count` | `Integer`    | Anzahl der wiederholten Wörter/Phrasen für das Datum.               |

---

## 6. Sammlung: `SZprocess_progress`
Speichert den Fortschritt des Verarbeitungsprozesses.

| **Feld**               | **Typ**      | **Beschreibung**                                                    |
|-------------------------|--------------|----------------------------------------------------------------------|
| `_id`                  | `ObjectId`   | Automatisch generierter eindeutiger Bezeichner.                     |
| `last_processed_id`    | `ObjectId`   | ID des zuletzt verarbeiteten Artikels.                              |


## Sammlung: Datenbank-Output von `checksum.py` - Beispiel: `sezessionProcessed`

**Beschreibung**: Speichert verarbeitete Artikel nach der Textfilterung.

| **Feld**             | **Typ**    | **Beschreibung**                                      |
|-----------------------|------------|------------------------------------------------------|
| `url`                | `String`   | URL des Artikels.                                    |
| `title`              | `String`   | Titel des Artikels.                                  |
| `full_text`          | `String`   | Gefilterter Text des Artikels.                      |
| `new_article_phrases`| `Array`    | Neue Schlüsselphrasen aus dem Artikeltext.          |
| `new_comment_phrases`| `Array`    | Neue Schlüsselphrasen aus den Kommentaren.          |
| `static_checksum`    | `String`   | Checksumme, um Änderungen zu erkennen.              |
| `first_processed`    | `Date`     | Datum der ersten Verarbeitung.                      |
| `last_processed`     | `Date`     | Datum der letzten Verarbeitung.                     |




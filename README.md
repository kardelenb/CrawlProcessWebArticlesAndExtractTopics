# Topic Extraction and Query Generation From Websites

Dieses Projekt besteht aus zwei Hauptteilen:

1. **Web Scraping**: Ein Python-Skript zum Scraping von Artikeln und Kommentaren von Websites, die Sitemaps bereitstellen. Die Daten werden in einer MongoDB-Datenbank gespeichert.
2. **Textanalyse**: Ein zweites Python-Skript, das extrahierte Artikel und Kommentare aus der MongoDB analysiert und neue Wörter oder Phrasen basierend auf einem Wörterbuch vergleicht.

## Teil 1: Web Scraping

### Funktionsweise

- Das Skript durchsucht Sitemaps der angegebenen Website, um Artikel-URLs zu extrahieren.
- Es crawlt den Inhalt (Titel, Text, Kommentare) der Artikel und speichert die Daten in MongoDB.

### Voraussetzungen

- Python 3.7+
- MongoDB (lokal oder Remote)
- Python-Bibliotheken (siehe `requirements.txt`)

### Installation

1. Klone dieses Repository:
   ```bash
   git clone https://github.com/kardelenb/MasterArbeit.git
2. Navigiere in das Projektverzeichnis:
   ```bash
    cd dein_repository
3. Installiere die Abhängigkeiten:
   ```bash
     pip install -r requirements.txt

4. Stelle sicher, dass MongoDB läuft und du eine Verbindung zur Datenbank hast.
   
### Verwendung
1. Starte das Skript justSitemaps.py:
   ```bash
    python justSitemaps.py

3. Gib die Basis-URL der Website ein, von der du Artikel und Kommentare extrahieren möchtest (die Website muss eine Sitemap haben).

4. Der Scraper durchsucht die Sitemap der Website, extrahiert die URLs, lädt den Inhalt und speichert die Daten in MongoDB.

## Teil 2: Textanalyse
### Funktionsweise
- Dieses Skript lädt Artikel und Kommentare aus der MongoDB.
- Es analysiert den Text, extrahiert relevante Phrasen (basierend auf POS-Tags) und vergleicht diese mit einem vorgegebenen Wörterbuch.
- Neue Wörter oder Phrasen werden erkannt und in einer MongoDB-Datenbank gespeichert.

### Voraussetzungen
- Die in Teil 1 gesammelten Daten müssen in MongoDB verfügbar sein.
- Ein Wörterbuch zum Vergleich der Phrasen muss im Projektverzeichnis als output3.txt gespeichert sein.

### Verwendung
1. Starte das Skript zur Textanalyse:
   ```bash
   python processor.py
2. Das Skript vergleicht die extrahierten Phrasen aus den Artikeln mit dem Wörterbuch und speichert die Ergebnisse in MongoDB.

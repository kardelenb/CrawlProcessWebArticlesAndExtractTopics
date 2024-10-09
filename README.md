# Web Scraping und Textverarbeitung für Artikel und Kommentare

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

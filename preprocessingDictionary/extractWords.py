# Datei öffnen und verarbeiten
with open('/masterthesis/spiders/spiders/deu_news_2020_1M-words.txt', 'r', encoding='utf-8') as file, open('deu-news-2020.txt', 'w', encoding='utf-8') as output_file:
    for line in file:
        # Zeilen splitten
        parts = line.split('\t')
        if len(parts) >= 2:
            # Zweite Spalte (das Wort) in die Ausgabedatei schreiben
            output_file.write(parts[1] + '\n')
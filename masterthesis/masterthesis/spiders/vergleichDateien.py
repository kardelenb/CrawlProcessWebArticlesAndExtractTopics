# Zwei Dateien einlesen
with open('/home/kardelenbilir/Dokumente/Projekt/MasterArbeit/masterthesis/masterthesis/spiders/newwords.txt', 'r', encoding='utf-8') as file1, open('/home/kardelenbilir/Dokumente/Projekt/MasterArbeit/masterthesis/masterthesis/spiders/deu-news-2020_5.txt', 'r', encoding='utf-8') as file2:
    # Wörter in beiden Dateien sammeln
    woerter1 = set([line.strip() for line in file1])
    woerter2 = set([line.strip() for line in file2])

# Die Vereinigungsmenge beider Sets bilden, um doppelte Wörter zu eliminieren
alle_woerter = woerter1.union(woerter2)

# Die einzigartigen Wörter in eine neue Datei schreiben
with open('newwordsNew.txt', 'w', encoding='utf-8') as output_file:
    for wort in sorted(alle_woerter):  # optional sortiert
        output_file.write(wort + '\n')
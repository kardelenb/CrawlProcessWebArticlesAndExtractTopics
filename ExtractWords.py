# Datei öffnen und verarbeiten
with open('C:/Users/karde/PycharmProjects/pythonProject/masterthesis/masterthesis/deu_mixed-typical_2011_1M-words.txt', 'r', encoding='utf-8') as file, open('deu_mixedtypical_2011.txt', 'w', encoding='utf-8') as output_file:
    for line in file:
        # Zeilen splitten
        parts = line.split('\t')
        if len(parts) >= 2:
            # Zweite Spalte (das Wort) in die Ausgabedatei schreiben
            output_file.write(parts[1] + '\n')
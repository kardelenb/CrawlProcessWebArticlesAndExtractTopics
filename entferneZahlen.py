'''
import re

# Funktion, um Zahlen und Zahlen mit Kommas, Punkten oder Bindestrichen zu entfernen
def remove_numbers_from_text(text):
    # Entfernt Zahlen, die auch Kommas, Punkte oder Bindestriche enthalten können
    return re.sub(r'[\d,.+-]+', '', text)

# Liest die Eingabedatei, entfernt Zahlen und speichert das Ergebnis in einer neuen Datei
def remove_numbers_from_file(input_file, output_file):
    with open(input_file, 'r', encoding='utf-8') as infile, open(output_file, 'w', encoding='utf-8') as outfile:
        for line in infile:
            cleaned_line = remove_numbers_from_text(line)
            outfile.write(cleaned_line)

# Beispielverwendung
input_file = 'C:/Users/karde/PycharmProjects/pythonProject/zusammengefasst4Files.txt'  # Ersetze mit deinem Dateipfad
output_file = 'zahlenEntfernt.txt'  # Datei, in der das Ergebnis gespeichert wird
remove_numbers_from_file(input_file, output_file)
'''

'''
import re

def remove_numbers_from_file(input_file, output_file):
    # Regulärer Ausdruck zum Erkennen von Zeilen, die nur Zahlen (inklusive Dezimalzahlen und Prozentsätze) enthalten
    number_pattern = re.compile(r'^\s*\d+[\.,\d%]*\s*$')

    with open(input_file, 'r', encoding='utf-8') as file:
        lines = file.readlines()

    with open(output_file, 'w', encoding='utf-8') as file:
        for line in lines:
            # Wenn die Zeile keine Zahlen ausschließlich enthält, schreibe sie in die Ausgabedatei
            if not number_pattern.match(line):
                file.write(line)


# Beispielaufruf
input_file = 'C:/Users/karde/PycharmProjects/pythonProject/zusammengefasst5Files.txt'
output_file = ''
remove_numbers_from_file(input_file, output_file)
'''

import re

'''
import re

def remove_leading_quotes(input_file, output_file):
    # Regulärer Ausdruck für das typografische Anführungszeichen ‚ am Anfang von Wörtern
    leading_quote_pattern = re.compile(r'‚(\w)')

    with open(input_file, 'r', encoding='utf-8') as file:
        lines = file.readlines()

    with open(output_file, 'w', encoding='utf-8') as file:
        for line in lines:
            # Entfernen des typografischen Anführungszeichens ‚ vor Wörtern
            cleaned_line = leading_quote_pattern.sub(r'\1', line)
            file.write(cleaned_line)

# Beispielaufruf
input_file = 'C:/Users/karde/PycharmProjects/pythonProject/outputjk.txt'
output_file = 'zusammengefasst.txt'
remove_leading_quotes(input_file, output_file)'''

import re

def remove_numbers_and_words_with_numbers(input_file, output_file):
    # Regulärer Ausdruck zum Erkennen von Zeilen, die nur Zahlen oder Wörter mit Zahlen enthalten
    # Diese Zeilen werden entfernt
    line_pattern = re.compile(r'^\s*\d+[\.,\d%]*\s*$|.*\d+.*')

    with open(input_file, 'r', encoding='utf-8') as file:
        lines = file.readlines()

    with open(output_file, 'w', encoding='utf-8') as file:
        for line in lines:
            # Wenn die Zeile keine reinen Zahlen und keine Wörter mit Zahlen enthält, schreibe sie in die Ausgabedatei
            if not line_pattern.match(line):
                file.write(line)

# Beispielaufruf
input_file = '/masterthesis/spiders/spiders/deu-news-2020_4.txt'
output_file = 'deu-news-2020_5.txt'
remove_numbers_and_words_with_numbers(input_file, output_file)


'''
import re


def clean_file(input_file, output_file):
    # Regulärer Ausdruck für die Zeichen, die entfernt werden sollen
    # Entfernt die spitzen Klammern, das Zeichen †, und die typografischen Anführungszeichen
    unwanted_pattern = re.compile(r'[‹›†‘’]')

    # Regulärer Ausdruck für das Zeichen ž
    weird_char_pattern = re.compile(r'\bž|\b')

    with open(input_file, 'r', encoding='utf-8') as file:
        lines = file.readlines()

    with open(output_file, 'w', encoding='utf-8') as file:
        for line in lines:
            # Entfernen der unerwünschten Zeichen
            line = unwanted_pattern.sub('', line)
            # Entfernen des Zeichen ž
            line = weird_char_pattern.sub('', line)
            file.write(line)


# Beispielaufruf
input_file = '/home/kardelenbilir/Dokumente/Projekt/CrawlProcessWebArticlesAndExtractTopics/masterthesis/masterthesis/spiders/deu-news-2020_3.txt'
output_file = 'deu-news-2020_4.txt'
clean_file(input_file, output_file)
'''
'''
import re

def clean_special_characters(input_file, output_file):
    """
    Entfernt typografische Anführungszeichen ‚ am Anfang von Wörtern und ähnliche Zeichen,
    ohne Bindestriche oder andere Wortbestandteile zu löschen.

    :param input_file: Pfad zur Eingabedatei.
    :param output_file: Pfad zur Ausgabedatei.
    """
    # Regulärer Ausdruck: Entfernt ‚ am Anfang und ‚ oder ' am Ende eines Wortes
    pattern = re.compile(r"(?<!\S)[‚‘“”]+|[‚‘“”]+(?!\S)")

    with open(input_file, 'r', encoding='utf-8') as infile, open(output_file, 'w', encoding='utf-8') as outfile:
        for line in infile:
            # Entfernen der unerwünschten Zeichen
            cleaned_line = pattern.sub('', line)
            outfile.write(cleaned_line)

# Beispielaufruf
input_file = '/home/kardelenbilir/Dokumente/Projekt/CrawlProcessWebArticlesAndExtractTopics/masterthesis/masterthesis/spiders/deu-news-2020_2.txt'
output_file = 'deu-news-2020_3.txt'
clean_special_characters(input_file, output_file)
'''

import re

def remove_trailing_character(input_file, output_file, char_to_remove):
    """
    Entfernt ein bestimmtes Zeichen am Ende von Wörtern in einer Datei.

    :param input_file: Pfad zur Eingabedatei.
    :param output_file: Pfad zur Ausgabedatei.
    :param char_to_remove: Das Zeichen, das entfernt werden soll (z. B. â).
    """
    # Erstellen des regulären Ausdrucks, um das Zeichen am Ende der Wörter zu entfernen
    pattern = re.compile(rf'{re.escape(char_to_remove)}\b')

    with open(input_file, 'r', encoding='utf-8') as infile, open(output_file, 'w', encoding='utf-8') as outfile:
        for line in infile:
            # Entfernen des unerwünschten Zeichens
            cleaned_line = pattern.sub('', line)
            outfile.write(cleaned_line)

# Beispielaufruf
input_file = '/masterthesis/spiders/spiders/newwordsNew.txt'
output_file = 'wortschatzLeipzig.txt'
char_to_remove = 'â'  # Das zu entfernende Zeichen
remove_trailing_character(input_file, output_file, char_to_remove)

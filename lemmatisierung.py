'''from spellchecker import SpellChecker

# Funktion zur Rechtschreibkorrektur
def correct_spelling(text, language):
    if language == 'de':
        spell = SpellChecker(language='de')
    else:
        spell = SpellChecker(language='en')

    corrected_text = []
    for word in text.split():
        corrected_word = spell.correction(word)
        # Füge entweder das korrigierte Wort oder das ursprüngliche Wort hinzu, wenn `None` zurückgegeben wird
        corrected_text.append(corrected_word if corrected_word is not None else word)
    return ' '.join(corrected_text)

# Testtext für Deutsch und Englisch
test_text_de = "weitergereichen"
test_text_en = "I have read the book and it was very intersting."

# Rechtschreibkorrektur anwenden
corrected_text_de = correct_spelling(test_text_de, 'de')
corrected_text_en = correct_spelling(test_text_en, 'en')

# Ausgabe der korrigierten Texte
print("Originaler deutscher Text:")
print(test_text_de)
print("Korrigierter deutscher Text:")
print(corrected_text_de)
print()

print("Originaler englischer Text:")
print(test_text_en)
print("Korrigierter englischer Text:")
print(corrected_text_en)
'''
from HanTa import HanoverTagger as ht

hannover = ht.HanoverTagger('morphmodel_ger.pgz')

word = 'weitergereicht'

print('HanTa:' + str(hannover.analyze(word)[0]))


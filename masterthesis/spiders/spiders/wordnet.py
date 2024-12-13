import nltk
from nltk.corpus import wordnet

# Stelle sicher, dass die WordNet-Daten heruntergeladen sind
nltk.download('wordnet')

def check_word_in_wordnet(word):
    # Prüfe, ob das Wort in WordNet existiert
    synsets = wordnet.synsets(word)
    if synsets:
        return True
    return False

# Testwörter, um zu überprüfen, ob sie in WordNet vorhanden sind
test_words = ['organize']

# Schleife durch die Testwörter und überprüfe sie in WordNet
for word in test_words:
    if check_word_in_wordnet(word):
        print(f"Das Wort '{word}' ist in WordNet vorhanden.")
    else:
        print(f"Das Wort '{word}' ist NICHT in WordNet vorhanden.")

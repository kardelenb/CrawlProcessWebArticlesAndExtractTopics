import odenet

def check_word_in_odenet(word):
    # Verwende die Methode synonyms_word, um Synonyme des Wortes zu finden
    synonyms = odenet.synonyms_word(word)

    # Überprüfe, ob die Liste der Synonyme nicht leer ist
    if synonyms:
        print(f"Das Wort '{word}' ist in OdeNet enthalten.")
        print(f"Synonyme für '{word}': {synonyms}")
    else:
        print(f"Das Wort '{word}' ist nicht in OdeNet enthalten.")

# Überprüfen, ob das Wort 'Haus' in OdeNet enthalten ist
check_word_in_odenet('Migration')
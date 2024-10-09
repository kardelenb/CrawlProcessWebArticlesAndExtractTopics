from germanetpy import germanet
from germanetpy.filterconfig import Filterconfig

# Lade GermaNet-Daten
germanet_object = germanet.Germanet("/home/kardelenbilir/Downloads/GN_V180/GN_V180_XML")


# Funktion, um verwandte Formen in GermaNet zu finden
def check_related_forms_in_germanet(word):
    # Suche nach dem Wort in GermaNet
    synsets = germanet_object.get_synsets_by_orthform(word)
    if synsets:
        print(f"Das Wort '{word}' hat folgende verwandte Formen in GermaNet:")
        for synset in synsets:
            print(f"\nSynset ID: {synset.id}")
            print(f"Lexical Units (Wortformen): {[lu.orthform for lu in synset.lexunits]}")
            # Falls es verwandte Formen in den Synsets gibt, gib diese aus
            if synset.relations:
                for relation, related_synsets in synset.relations.items():
                    print(f"\n  Relation: {relation}")
                    for related_synset in related_synsets:
                        print(f"    {related_synset}")

            # Prüfe, ob das Wort ein Kompositum ist
            for lexunit in synset.lexunits:
                if hasattr(lexunit, 'compound_info') and lexunit.compound_info:
                    compound_info = lexunit.compound_info
                    print(f"Kompositum: {lexunit.orthform}")
                    print(f"  Modifikator: {compound_info.modifier}, Kopf: {compound_info.head}")
    else:
        print(f"Das Wort '{word}' wurde nicht in GermaNet gefunden.")

    # Suche nach ähnlichen Wörtern basierend auf einer Fall-unabhängigen Suche
    filterconfig = Filterconfig(word, ignore_case=True)
    similar_synsets = filterconfig.filter_synsets(germanet_object)
    if similar_synsets:
        print(f"\nÄhnliche Wörter basierend auf '{word}':")
        for synset in similar_synsets:
            print(f"\nSynset ID: {synset.id}")
            print(f"Lexical Units: {[lu.orthform for lu in synset.lexunits]}")


# Benutzer nach einem Wort fragen
word_to_check = input("Gib ein Wort ein, um verwandte Formen und ähnliche Wörter in GermaNet zu prüfen: ")
check_related_forms_in_germanet(word_to_check)
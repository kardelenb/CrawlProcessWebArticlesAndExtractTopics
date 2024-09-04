import spacy
import odenet
from sklearn.feature_extraction.text import TfidfVectorizer
from nltk.corpus import stopwords, wordnet
import nltk
import re
from HanTa import HanoverTagger as ht
from pymongo import MongoClient

# Verbindung zur MongoDB und Zugriff auf gespeicherte Artikel
client = MongoClient('mongodb://localhost:27017/')
db = client['scrapy_database']
collection = db['raw_articles']
processed_collection = db['processed_articles']

# Lade den HanTa-Tagger mit dem deutschen Modell
hannover = ht.HanoverTagger('morphmodel_ger.pgz')

# Lade deutsche und englische spaCy-Modelle
nlp_de = spacy.load('de_core_news_sm')
nlp_en = spacy.load('en_core_web_sm')

nltk.download('stopwords')
nltk.download('wordnet')

german_stop_words = set(stopwords.words('german'))
english_stop_words = set(stopwords.words('english'))

def is_word_in_odenet(word):
    synonyms = odenet.synonyms_word(word)
    return bool(synonyms)

def lemmatize_with_hanta(word):
    lemma = hannover.analyze(word)[0]
    return lemma

def extract_keywords_by_pos(text, language, pos_tags=['NOUN', 'ADJ', 'VERB']):
    if language == 'de':
        doc = nlp_de(text)
        lemmatizer = lemmatize_with_hanta
    else:
        doc = nlp_en(text)
        lemmatizer = lambda token: token.lemma_

    only_letters = re.compile(r'^[^\W\d_]+$')

    return [
        lemmatizer(token.text)
        for token in doc
        if token.pos_ in pos_tags
           and not token.is_stop
           and only_letters.match(token.lemma_)
    ]

def detect_language(text):
    if any(word in german_stop_words for word in text.split()):
        return 'de'
    return 'en'

def process_articles():
    for article in collection.find():
        full_text = article['full_text']
        language = detect_language(full_text)

        filtered_words = extract_keywords_by_pos(full_text, language)

        vectorizer = TfidfVectorizer(lowercase=False)
        tfidf_matrix = vectorizer.fit_transform([' '.join(filtered_words)])
        tfidf_scores = zip(vectorizer.get_feature_names_out(), tfidf_matrix.toarray()[0])
        ranked_keywords = sorted(tfidf_scores, key=lambda x: x[1], reverse=True)

        new_words = []
        for word, score in ranked_keywords:
            if wordnet.synsets(word):
                continue
            if is_word_in_odenet(word):
                continue
            new_words.append({
                'word': word,
                'score': score
            })

        processed_collection.insert_one({
            'title': article['title'],
            'url': article['url'],
            'full_text': full_text,
            'ranked_keywords': [{'word': word, 'score': score} for word, score in ranked_keywords],
            'new_words': new_words
        })

if __name__ == '__main__':
    process_articles()
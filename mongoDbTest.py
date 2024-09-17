from pymongo import MongoClient

# Verbindung zu MongoDB
client = MongoClient('mongodb://localhost:27017/')
db = client['scrapy_database']
collection = db['scrapy_collection']

# Test-Dokument einfügen
test_document = {
    "title": "Test Title",
    "url": "http://example.com",
    "full_text": "Dies ist ein Test.",
    "ranked_keywords": [],
    "new_words": []
}

result = collection.insert_one(test_document)
print(f"Inserted document ID: {result.inserted_id}")
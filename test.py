import nltk
from bs4 import BeautifulSoup
import requests
from collections import Counter
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
#nltk.download('punkt')
#nltk.download('stopwords')

# Web-Scraping
url = 'https://sezession.de/'
response = requests.get(url)
html = response.text
soup = BeautifulSoup(html, 'html.parser')
text = soup.get_text()

# Textanalyse
tokens = word_tokenize(text)
words = [word.lower() for word in tokens if word.isalnum()]
filtered_words = [word for word in words if word not in stopwords.words('english')]

# Ranking
word_freq = Counter(filtered_words)
top_keywords = word_freq.most_common(10)

print("Top Keywords:", top_keywords)
print(text)

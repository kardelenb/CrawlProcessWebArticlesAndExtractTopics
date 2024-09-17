import requests

# URL der Seite, die du herunterladen möchtest
url = 'https://sezession.de/703/was-keiner-ahnt'

# HTML-Inhalt der Seite abrufen
response = requests.get(url)

# HTML-Inhalt in einer Datei speichern
with open('webpage.html', 'w', encoding='utf-8') as file:
    file.write(response.text)

print("HTML-Inhalt wurde erfolgreich in 'webpage.html' gespeichert.")
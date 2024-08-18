import requests

proxy = "http://220226e5d4b7f18dcc1ab9672024bafb97c6dd7a:premium_proxy=true@proxy.zenrows.com:8001"
proxies = {
    "http": proxy,
    "https": proxy,
}

try:
    response = requests.get("https://sezession.de", proxies=proxies)
    print(response.status_code)
    print(response.text[:500])  # Nur die ersten 500 Zeichen der Antwort drucken
except requests.exceptions.RequestException as e:
    print(f"Fehler bei der Anfrage: {e}")
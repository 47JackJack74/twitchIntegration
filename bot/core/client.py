import requests

def send_to_webserver(endpoint: str, data: str):
    url = f"{endpoint}"
    try:
        response = requests.post(url, data=data)
        response.raise_for_status()
        return True
    except requests.exceptions.RequestException as e:
        print(f"HTTP Error to {url}: {e}")
        return False
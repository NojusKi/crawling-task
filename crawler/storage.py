import requests

def download(url, destination):
    if destination.exists():
        return True, ""
    try:
        response = requests.get(url, timeout=40)
        if response.status_code != 200:
            return False, f"HTTP {response.status_code}"
        if not response.content.startswith(b"%PDF-"):
            return False, "ne pdf failas"
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(response.content)
        return True, ""
    except Exception as e:
        return False, str(e)
    
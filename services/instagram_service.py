import requests
from utils import logger

def check_profile_privacy(username):
    url = f"https://instagram-looter2.p.rapidapi.com/web-profile?username={username}"
    headers = {
        "X-Rapidapi-Key": "bb099aa633mshc32e5a3e833a238p1ba333jsn4e4ed3a7d3ce",
        "X-Rapidapi-Host": "instagram-looter2.p.rapidapi.com"
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        return "private" if data.get("is_private") else "public"
    except Exception as e:
        logger.error(f"Erro ao verificar perfil {username}: {str(e)}")
        return "error"

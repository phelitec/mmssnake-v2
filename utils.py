import re
import logging
import requests

# Configuração básica do logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Configuração da API SMM
SMM_CONFIG = {
    'machinesmm': {'base_url': 'https://machinesmm.com/api/v2', 'api_key': '7933dcebc18d85d7486c1666a1ae3d4d'},
    'worldsmm': {'base_url': 'https://worldsmm.com.br/api/v2', 'api_key': '1287cfd6baf5e432500591201bc121e3'},
    'smmclouduk': {'base_url': 'https://smmcloud.uk/api/v2', 'api_key': '1c900607f193909296d6c8a5573fa4c1'}
}

logger = logging.getLogger(__name__)  # Para usar com from utils import logger





def check_profile_privacy(username):
    # Tenta primeiro com o pool de contas
    client = None
    try:
        client = pool.get_client()
        if client:
            profile = client.account_info_by_username(username)
            return "private" if profile.is_private else "public"
            
    except (LoginRequired, ClientError) as e:
        logger.warning(f"Erro no pool de contas: {str(e)}")
        if client:
            pool.release_client(client)
        return _check_profile_backup(username)
        
    except Exception as e:
        logger.error(f"Erro inesperado: {str(e)}")
        if client:
            pool.release_client(client)
        return _check_profile_backup(username)
        
    finally:
        if client:
            pool.release_client(client)
    
    # Se não conseguiu usar o pool, usa a API
    return _check_profile_backup(username)

def _check_profile_backup(username):
    """Método de fallback usando API externa"""
    url = f"https://instagram-looter2.p.rapidapi.com/web-profile?username={username}"
    headers = {
        "X-Rapidapi-Key": "f0755ae8acmsh12cfb31062c056cp1ef4dbjsn53d93beab1cb",
        "X-Rapidapi-Host": "instagram-looter2.p.rapidapi.com"
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        return "private" if data.get("is_private") else "public"
    except Exception as e:
        logger.error(f"Erro no backup API para {username}: {str(e)}")
        return "error"

#Sanitizar username conforme a Yampi 
def sanitize_customization(customization):
    # Padrão atualizado para capturar os casos específicos
    match = re.match(
        r'^(?:@|httpswww\.instagram\.com|www\.instagram\.com)([^?]*)', 
        customization
    )
    
    if match:
        # Retorna o username capturado (grupo 1)
        return match.group(1)
    else:
        # Remove caracteres não permitidos (exceto letras, números, underscores e pontos)
        return re.sub(r'[^\w\.]', '', customization)

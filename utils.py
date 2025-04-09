import re
import logging
import requests
from services.instagram_pool import get_instagram_pool

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
    """
    Verifica se o perfil do Instagram é público ou privado.
    Utiliza o pool de contas do Instagram.
    """
    pool = get_instagram_pool()
    return pool.check_profile_privacy(username)


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

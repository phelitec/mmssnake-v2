import logging
import requests
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class InstagramService:
    """
    Serviço para interagir com o Instagram via APIs externas,
    substituindo a dependência do instagrapi
    """
    
    # Chaves de API
    LOOTER_API_KEY = os.getenv("LOOTER_API")
    INSTAGRAM230_API_KEY = os.getenv("INSTAGRAM230_API")
    
    @staticmethod
    def check_profile_privacy(username):
        """
        Verifica se o perfil do Instagram é público ou privado usando API externa.
        
        Args:
            username (str): Nome de usuário do Instagram a ser verificado
            
        Returns:
            str: 'public', 'private' ou 'error'
        """
        url = f"https://instagram-looter2.p.rapidapi.com/web-profile?username={username}"
        headers = {
            "X-Rapidapi-Key": InstagramService.LOOTER_API_KEY,
            "X-Rapidapi-Host": "instagram-looter2.p.rapidapi.com"
        }
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            is_private = data.get("data", {}).get("user", {}).get("is_private", True)
        
            return "private" if is_private else "public"
        except Exception as e:
            logger.error(f"Erro ao verificar perfil {username} com API: {str(e)}")
            return "error"
    
    @staticmethod
    def get_user_media(username, amount=10):
        """
        Obtém posts recentes de um usuário.
        
        Args:
            username (str): Nome de usuário
            amount (int): Quantidade de posts a serem obtidos
            
        Returns:
            list: Lista de posts ou None em caso de erro
        """
        url = f"https://instagram230.p.rapidapi.com/user/posts"
        
        headers = {
            "X-Rapidapi-Key": InstagramService.INSTAGRAM230_API_KEY,
            "X-Rapidapi-Host": "instagram230.p.rapidapi.com"
        }
        
        params = {"username": username}
        
        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()
            
            # Extrair apenas os dados relevantes (limitando ao número solicitado)
            results = []
            posts = data.get("data", {}).get("user", {}).get("edge_owner_to_timeline_media", {}).get("edges", [])
            
            for i, post in enumerate(posts):
                if i >= amount:
                    break
                    
                node = post.get("node", {})
                post_data = {
                    "code": node.get("shortcode"),
                    "url": f"https://www.instagram.com/p/{node.get('shortcode')}/",
                    "timestamp": node.get("taken_at_timestamp"),
                    "id": node.get("id")
                }
                results.append(post_data)
            
            return results
        except Exception as e:
            logger.error(f"Erro ao obter mídia do usuário {username}: {str(e)}")
            return None
    
    @staticmethod
    def send_notification(admin_username, message):
        """
        Método para enviar notificações (substitui o envio direto de DM do Instagram)
        Este é um placeholder - você precisará implementar seu próprio método de notificação
        """
        logger.info(f"NOTIFICAÇÃO para {admin_username}: {message}")
        # Aqui você poderia integrar com outra API de mensagens, Email, SMS, etc.
        return True

# Singleton para facilitar o acesso ao serviço em várias partes do código
_instance = InstagramService()

def get_instagram_service():
    """Retorna a instância global do serviço Instagram"""
    return _instance

import logging
import requests
import functools
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from instagrapi import Client
from threading import Lock
from models.base import InstagramCredentials
from database import Session as DBSession

logger = logging.getLogger(__name__)

class InstagramAccountPool:
    _instance = None
    
    @classmethod
def get_instance(cls):
    """Thread-safe singleton para obter a instância global do pool"""
    if cls._instance is None:
        with cls._lock:  # Class-level lock for thread safety
            if cls._instance is None:  # Double-check pattern
                logger.info("Criando nova instância do pool de contas Instagram")
                session = DBSession()
                cls._instance = InstagramAccountPool(session)
    return cls._instance
    
    def __init__(self, db_session: Session):
        """Inicializa o pool de contas do Instagram"""
        self.db = db_session
        self.active_accounts = {}
        self.lock = Lock()
        self._load_initial_accounts()

    def _load_initial_accounts(self):
    """Carrega todas as contas ativas do banco de dados"""
    with self.lock:
        try:
            # Limpa o pool atual
            old_accounts = len(self.active_accounts)
            self.active_accounts = {}
            
            # Carrega novas contas
            accounts = self.db.query(InstagramCredentials).filter_by(is_active=True).all()
            logger.info(f"Encontradas {len(accounts)} contas ativas no banco de dados")
            
            success_count = 0
            for account in accounts:
                if self._initialize_account(account):
                    success_count += 1
                    
            logger.info(f"Pool inicializado: {success_count}/{len(accounts)} contas ativas (antes: {old_accounts})")
            
            if success_count == 0:
                logger.critical("NENHUMA CONTA ATIVA NO POOL! Verifique as credenciais no banco de dados.")
        except Exception as e:
            logger.error(f"Erro ao carregar contas iniciais: {str(e)}")
    def _initialize_account(self, account):
    """Cria uma nova instância do cliente Instagram"""
    logger.info(f"Inicializando conta {account.username} (ID: {account.id})")
    try:
        cl = Client()
        cl.delay_range = [1, 3]
        
        # Configurando proxy se disponível
        if account.proxy:
            logger.info(f"Configurando proxy para {account.username}: {account.proxy}")
            cl.set_proxy(account.proxy)
        
        login_successful = False
        if account.session_id:
            try:
                logger.info(f"Tentando login por session_id para {account.username}")
                cl.login_by_sessionid(account.session_id)
                login_successful = True
                logger.info(f"Login por session_id bem-sucedido para {account.username}")
            except Exception as se:
                logger.warning(f"Falha no login por session_id para {account.username}: {str(se)}")
        
        if not login_successful:
            try:
                logger.info(f"Tentando login com credenciais para {account.username}")
                cl.login(account.username, account.password)
                account.session_id = cl.sessionid
                self.db.commit()
                login_successful = True
                logger.info(f"Login com credenciais bem-sucedido para {account.username}")
            except Exception as le:
                logger.error(f"Falha no login com credenciais para {account.username}: {str(le)}")
                raise  # Re-raise to be caught by outer try/except
        
        # Verificando se o login foi bem-sucedido antes de adicionar ao pool
        if login_successful:
            self.active_accounts[account.id] = {
                'client': cl,
                'account': account,
                'in_use': False,
                'last_used': datetime.now()
            }
            logger.info(f"Conta {account.username} inicializada com sucesso e adicionada ao pool")
            return True
        return False

    except Exception as e:
        logger.error(f"Falha ao inicializar conta {account.username}: {str(e)}")
        self._disable_account(account.id)
        return False

    def _disable_account(self, account_id):
        """Desativa conta problemática"""
        account = self.db.query(InstagramCredentials).get(account_id)
        if account:
            account.is_active = False
            self.db.commit()
            logger.warning(f"Conta {account.username} desativada")
            
            # Remover do pool se existir
            if account_id in self.active_accounts:
                del self.active_accounts[account_id]

    def _get_account(self):
        """Obtém uma conta disponível do pool"""
        with self.lock:
            try:
                # Encontra a conta mais antiga não em uso
                available = sorted(
                    [acc for acc in self.active_accounts.values() if not acc['in_use']],
                    key=lambda x: x['last_used']
                )

                if not available:
                    logger.warning("Nenhuma conta disponível no pool")
                    return None

                selected = available[0]
                selected['in_use'] = True
                selected['last_used'] = datetime.now()
                selected['account'].usage_count += 1
                selected['account'].last_used = datetime.now()

                # Rotaciona sessão se necessário
                if selected['account'].usage_count % selected['account'].rotation_interval == 0:
                    self._rotate_session(selected['account'].id)

                self.db.commit()
                return selected['client']

            except Exception as e:
                logger.error(f"Erro ao obter conta: {str(e)}")
                return None

    def _rotate_session(self, account_id):
        """Força novo login para renovar sessão"""
        try:
            account_data = self.active_accounts[account_id]
            cl = Client()
            cl.login(account_data['account'].username, account_data['account'].password)
            
            account_data['client'] = cl
            account_data['account'].session_id = cl.sessionid
            self.db.commit()
            logger.info(f"Sessão renovada para {account_data['account'].username}")

        except Exception as e:
            logger.error(f"Falha ao rotacionar sessão: {str(e)}")
            self._disable_account(account_id)

    def _release_account(self, client):
        """Libera uma conta de volta para o pool"""
        with self.lock:
            for acc_id, acc_data in self.active_accounts.items():
                if acc_data['client'] == client:
                    acc_data['in_use'] = False
                    acc_data['account'].last_used = datetime.now()
                    self.db.commit()
                    logger.debug(f"Conta {acc_data['account'].username} liberada")
                    break

    def execute(self, func, *args, **kwargs):
        """
        Executa uma função usando uma conta do pool.
        
        Args:
            func: Função que receberá o cliente do Instagram como primeiro argumento
            *args: Argumentos adicionais para a função
            **kwargs: Argumentos nomeados para a função
            
        Returns:
            O resultado da função ou None em caso de erro
        """
        client = self._get_account()
        if not client:
            logger.error("Não foi possível obter uma conta do Instagram para executar a função")
            return None
            
        try:
            result = func(client, *args, **kwargs)
            return result
        except Exception as e:
            logger.error(f"Erro ao executar função com cliente Instagram: {str(e)}")
            return None
        finally:
            self._release_account(client)
    
    def check_profile_privacy(self, username):
        """
        Verifica se o perfil do Instagram é público ou privado usando o instagrapi.
        
        Args:
            username (str): Nome de usuário do Instagram a ser verificado
            
        Returns:
            str: 'public', 'private' ou 'error'
        """
        def _check(client, username):
            try:
                user_info = client.user_info_by_username(username)
                return "private" if user_info.is_private else "public"
            except Exception as e:
                logger.error(f"Erro ao verificar perfil {username} com instagrapi: {str(e)}")
                return self._check_profile_privacy_api(username)
        
        result = self.execute(_check, username)
        if result is None:
            return self._check_profile_privacy_api(username)
        return result
    
    def _check_profile_privacy_api(self, username):
        """Método de backup que verifica a privacidade do perfil usando a API externa."""
        url = f"https://instagram-looter2.p.rapidapi.com/web-profile?username={username}"
        headers = {
            "X-Rapidapi-Key": "29def6eec7msh8d994ba439bbd1ap153df5jsn3924152b9568",
            "X-Rapidapi-Host": "instagram-looter2.p.rapidapi.com"
        }
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            return "private" if data.get("is_private") else "public"
        except Exception as e:
            logger.error(f"Erro ao verificar perfil {username} com API backup: {str(e)}")
            return "error"
    
    def send_direct_message(self, username, message):
        """
        Envia uma mensagem direta para um usuário do Instagram.
        
        Args:
            username (str): Nome de usuário do destinatário
            message (str): Mensagem a ser enviada
            
        Returns:
            bool: True se a mensagem foi enviada com sucesso, False caso contrário
        """
        def _send_message(client, username, message):
            try:
                user_id = client.user_id_from_username(username)
                result = client.direct_send(message, [user_id])
                logger.info(f"Mensagem enviada para {username} com sucesso")
                return True
            except Exception as e:
                logger.error(f"Erro ao enviar mensagem para {username}: {str(e)}")
                return False
                
        return self.execute(_send_message, username, message) or False
    
    def follow_user(self, username):
        """
        Segue um usuário do Instagram.
        
        Args:
            username (str): Nome de usuário a ser seguido
            
        Returns:
            bool: True se o usuário foi seguido com sucesso, False caso contrário
        """
        def _follow(client, username):
            try:
                user_info = client.user_info_by_username(username)
                user_id = user_info.pk
                result = client.user_follow(user_id)
                logger.info(f"Usuário {username} seguido com sucesso")
                return True
            except Exception as e:
                logger.error(f"Erro ao seguir usuário {username}: {str(e)}")
                return False
                
        return self.execute(_follow, username) or False
    
    def get_user_media(self, username, amount=10):
        """
        Obtém posts recentes de um usuário.
        
        Args:
            username (str): Nome de usuário
            amount (int): Quantidade de posts a serem obtidos
            
        Returns:
            list: Lista de posts ou None em caso de erro
        """
        def _get_media(client, username, amount):
            try:
                user_id = client.user_id_from_username(username)
                media_list = client.user_medias(user_id, amount=amount)
                return media_list
            except Exception as e:
                logger.error(f"Erro ao obter mídia do usuário {username}: {str(e)}")
                return None
                
        return self.execute(_get_media, username, amount)


        def reset_pool():
    """Reseta completamente o pool de contas do Instagram"""
    try:
        # Forçar a recriação da instância singleton
        InstagramAccountPool._instance = None
        
        # Criar uma nova instância do pool
        pool = InstagramAccountPool.get_instance()
        
        # Verificar quantas contas foram carregadas
        status = pool.get_pool_status()
        return f"Pool resetado com {status['available_accounts']} contas disponíveis"
    except Exception as e:
        logger.error(f"Erro ao resetar pool: {str(e)}")
        return f"Erro ao resetar pool: {str(e)}"

# Função auxiliar para obter a instância global do pool
def get_instagram_pool():
    return InstagramAccountPool.get_instance()

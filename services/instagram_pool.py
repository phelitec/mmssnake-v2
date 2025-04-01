import logging
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from instagrapi import Client
from threading import Lock
from models.base import InstagramCredentials

logger = logging.getLogger(__name__)

class InstagramAccountPool:
    def __init__(self, db_session: Session):
        self.db = db_session
        self.active_accounts = {}
        self.lock = Lock()
        self._load_initial_accounts()

    def _load_initial_accounts(self):
        """Carrega todas as contas ativas do banco de dados"""
        with self.lock:
            accounts = self.db.query(InstagramCredentials).filter_by(is_active=True).all()
            for account in accounts:
                self._initialize_account(account)
            logger.info(f"Pool inicializado com {len(accounts)} contas")

    def _initialize_account(self, account):
        """Cria uma nova instância do cliente Instagram"""
        try:
            cl = Client()
            cl.delay_range = [1, 3]
            
            if account.session_id:
                cl.login_by_sessionid(account.session_id)
            else:
                cl.login(account.username, account.password)
                account.session_id = cl.sessionid
                self.db.commit()

            self.active_accounts[account.id] = {
                'client': cl,
                'account': account,
                'in_use': False,
                'last_used': datetime.now()
            }

        except Exception as e:
            logger.error(f"Falha ao inicializar conta {account.username}: {str(e)}")
            self._disable_account(account.id)

    def _disable_account(self, account_id):
        """Desativa conta problemática"""
        account = self.db.query(InstagramCredentials).get(account_id)
        if account:
            account.is_active = False
            self.db.commit()
            logger.warning(f"Conta {account.username} desativada")

    def get_account(self):
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

    def release_account(self, client):
        """Libera uma conta de volta para o pool"""
        with self.lock:
            for acc_id, acc_data in self.active_accounts.items():
                if acc_data['client'] == client:
                    acc_data['in_use'] = False
                    acc_data['account'].last_used = datetime.now()
                    self.db.commit()
                    break
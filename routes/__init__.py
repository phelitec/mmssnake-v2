from .webhooks import webhook_bp
from .payments import payments_bp
# Adicione outros blueprints conforme necessário

__all__ = ['webhook_bp', 'payments_bp']
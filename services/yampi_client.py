# services/yampi_client.py
import os
import requests
import logging
from typing import Dict, Optional
from sqlalchemy.orm import Session

class YampiClient:
    STATUS_MAP = {
        'cancelled': (8, "cancelled"),
        'delivered': (7, "delivered"),
        'handling_products': (5, "handling_products"),
        'invoiced': (10, "invoiced"),
        'on_carriage': (6, "on_carriage"),
        'ready_for_shipping': (12, "ready_for_shipping"),
        'refused': (9, "refused"),
        'shipment_exception': (11, "shipment_exception")
    }

    def __init__(self):
        self.base_url = os.getenv("YAMPI_BASE_URL")
        self.api_key = os.getenv("YAMPI_API_KEY")
        self.secret_key = os.getenv("YAMPI_SECRET_KEY")
        self._validate_credentials()

    def _validate_credentials(self):
        if not all([self.api_key, self.secret_key]):
            raise ValueError("Credenciais Yampi não configuradas no .env")

    @property
    def headers(self) -> Dict[str, str]:
        return {
            "User-Token": self.api_key,
            "User-Secret-Key": self.secret_key,
            "Content-Type": "application/json"
        }

    def update_status(self, session: Session, order_id: str, status_alias: str) -> bool:
        # Validação do status
        if status_alias not in self.STATUS_MAP:
            valid_statuses = ", ".join(self.STATUS_MAP.keys())
            raise ValueError(f"Status inválido. Valores permitidos: {valid_statuses}")

        # 1. Atualiza na Yampi
        status_id, desire_status = self.STATUS_MAP[status_alias]
        
        try:
            # Chamada à API Yampi
            response = requests.put(
                f"{self.base_url}/{order_id}",
                headers=self.headers,
                json={
                    "status_id": status_id,
                    "desire_status": desire_status
                }
            )
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            logging.error(f"Falha na API Yampi: {e.response.text}")
            return False

        # 2. Atualiza o banco de dados local
        try:
            payment = session.query(Payments).filter_by(yampi_order_id=order_id).first()
            if not payment:
                logging.error(f"Pedido {order_id} não encontrado no banco local")
                return False
            
            payment.status_alias = status_alias
            session.commit()
            logging.info(f"Status atualizado para {status_alias} no pedido {order_id}")
            return True
            
        except Exception as db_error:
            session.rollback()
            logging.error(f"Erro ao atualizar banco de dados: {str(db_error)}")
            return False
import os
import requests
import logging
from typing import Dict
from sqlalchemy.orm import Session
from models.base import Payments, ProductServices


class YampiClient:
    _instance = None

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

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(YampiClient, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self.base_url = os.getenv("YAMPI_BASE_URL")
        self.api_key = os.getenv("YAMPI_API_KEY")
        self.secret_key = os.getenv("YAMPI_SECRET_KEY")
        self._validate_credentials()
        self._initialized = True

    def _validate_credentials(self):
        if not all([self.api_key, self.secret_key, self.base_url]):
            raise ValueError("Credenciais Yampi não configuradas no .env")

    @property
    def headers(self) -> Dict[str, str]:
        return {
            "User-Token": self.api_key,
            "User-Secret-Key": self.secret_key,
            "Content-Type": "application/json"
        }

    def update_order_status(self, order_id: str, status_alias: str) -> bool:
        if status_alias not in self.STATUS_MAP:
            logging.error(f"Status '{status_alias}' inválido. Use um dos permitidos: {list(self.STATUS_MAP.keys())}")
            return False

        status_id, desire_status = self.STATUS_MAP[status_alias]
        url = f"{self.base_url}/{order_id}"
        data = {
            "status_id": status_id
        }

        try:
            response = requests.put(url, headers=self.headers, json=data)
            response.raise_for_status()
            logging.info(f"Pedido {order_id} atualizado para '{status_alias}' com sucesso.")
            return True
        except requests.RequestException as e:
            logging.error(f"Erro ao atualizar pedido {order_id}: {e}")
            return False
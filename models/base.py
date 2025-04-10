from sqlalchemy import Column, String, Integer, Boolean, DateTime, func, Text
from sqlalchemy.orm import declarative_base
from sqlalchemy.sql import expression
from datetime import datetime

Base = declarative_base()

# Tabela de Produtos/Serviços
class ProductServices(Base):
    __tablename__ = 'product_services'
    sku = Column(String(255), primary_key=True)
    service_id = Column(Integer)
    api = Column(String(100))
    base_quantity = Column(Integer)
    type = Column(String(50))

# Tabela de pedidos
class Payments(Base):
    __tablename__ = 'payments'
    id = Column(String(255), primary_key=True)  # Usaremos o order_id como chave primária
    order_id = Column(String(255))
    status_alias = Column(String(100))
    customer_name = Column(String(255))
    email = Column(String(255))
    phone_full_number = Column(String(50))
    item_sku = Column(String(255))
    item_quantity = Column(Integer)
    customization = Column(String(255))
    finished = Column(Integer, default=0)
    profile_status = Column(String(50), default='pending')

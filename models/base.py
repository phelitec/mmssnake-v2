from sqlalchemy import Column, String, Integer, Boolean, DateTime, func
from sqlalchemy.orm import declarative_base
from database import engine


Base = declarative_base()

# Tabela de Produtos/Serviços
class ProductServices(Base):
    __tablename__ = 'product_services'
    sku = Column(String, primary_key=True)
    service_id = Column(Integer)
    api = Column(String)
    base_quantity = Column(Integer)
    type = Column(String)

# Tabela de pedidos
class Payments(Base):
    __tablename__ = 'payments'
    id = Column(String, primary_key=True)  # Usaremos o order_id como chave primária
    order_id = Column(String)
    status_alias = Column(String)
    customer_name = Column(String)
    email = Column(String)
    phone_full_number = Column(String)
    item_sku = Column(String)
    item_quantity = Column(Integer)
    customization = Column(String)
    finished = Column(Integer, default=0)
    profile_status = Column(String, default='pending')

# Tabela de Credenciais Instagrapi
class InstagramCredentials(Base):
    __tablename__ = 'instagram_credentials'
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True)
    password = Column(String)
    session_id = Column(String(255))
    proxy = Column(String(255))
    is_active = Column(Boolean, default=True)
    last_used = Column(DateTime)
    usage_count = Column(Integer, default=0)
    rotation_interval = Column(Integer, default=10)


# Criar tabelas
Base.metadata.create_all(engine)    
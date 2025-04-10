from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
import logging

# Configurar logger
logger = logging.getLogger(__name__)

# Obter a URL do banco de dados do Railway (PostgreSQL)
DATABASE_URL = os.getenv("DATABASE_URL")

# Verificar e ajustar a URL para SQLAlchemy, se necessário
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Sempre usar PostgreSQL no Railway, sem fallback para SQLite
engine = create_engine(DATABASE_URL, echo=True)
Session = sessionmaker(bind=engine)

def initialize_database():
    from models.base import Base
    try:
        Base.metadata.drop_all(bind=engine)  # Apaga todas as tabelas
        Base.metadata.create_all(bind=engine)  # Recria as tabelas vazias
        logger.info("Tabelas criadas com sucesso no PostgreSQL")
    except Exception as e:
        logger.error(f"Erro ao criar tabelas: {str(e)}")
        raise

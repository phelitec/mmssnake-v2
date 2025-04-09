from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
import logging

# Configurar logger
logger = logging.getLogger(__name__)

# Obter a URL do banco de dados do ambiente ou usar SQLite como fallback
DATABASE_URL = os.getenv("DATABASE_URL", None)
db_path = os.path.join(os.path.dirname(__file__), 'app.db')
sqlite_url = f'sqlite:///{db_path}'

# Usar PostgreSQL se configurado, caso contrário SQLite
engine = create_engine(DATABASE_URL or sqlite_url, echo=True)
Session = sessionmaker(bind=engine)

def initialize_database():
    """
    Inicializa o banco de dados criando todas as tabelas definidas nos modelos.
    """
    from models.base import Base
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Tabelas criadas com sucesso")
    except Exception as e:
        logger.error(f"Erro ao criar tabelas: {str(e)}")
        raise

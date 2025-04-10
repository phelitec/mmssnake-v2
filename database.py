from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
import logging

# Configurar logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)  # Define o nível de log globalmente

# Obter a URL do banco de dados do Railway (PostgreSQL)
DATABASE_URL = os.getenv("DATABASE_URL")

# Verificar se a URL foi encontrada
if not DATABASE_URL:
    logger.error("DATABASE_URL não encontrada nas variáveis de ambiente!")
    raise ValueError("DATABASE_URL não está definida no ambiente!")

# Ajustar a URL para SQLAlchemy, se necessário (postgres:// -> postgresql://)
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Criar o engine do SQLAlchemy com a URL ajustada
try:
    engine = create_engine(DATABASE_URL, echo=True)  # echo=True para debug
except Exception as e:
    logger.error(f"Erro ao criar o engine do SQLAlchemy: {str(e)}")
    raise

# Criar a fábrica de sessões
Session = sessionmaker(bind=engine)

def initialize_database():
    """
    Inicializa o banco de dados criando todas as tabelas definidas nos modelos.
    """
    from models.base import Base  # Importa aqui para evitar circularidade
    try:
        # Remova todas as tabelas existentes e crie novas (cuidado em produção!)
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)
        logger.info("Tabelas criadas com sucesso no PostgreSQL")
    except Exception as e:
        logger.error(f"Erro ao criar tabelas: {str(e)}")
        raise

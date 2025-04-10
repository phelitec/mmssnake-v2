from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Obter a URL do banco de dados
DATABASE_URL=postgresql://postgres:yRasjEscyfQlvUkAfNuhxqwLPZJVifxt@postgres-production-4a22.up.railway.app:5432/railway
if not DATABASE_URL:
    logger.error("DATABASE_URL não encontrada!")
    raise ValueError("DATABASE_URL não está definida!")

# Ajustar a URL, se necessário
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

logger.info(f"Conectando ao banco com: {DATABASE_URL}")

# Criar o engine e testar a conexão
try:
    engine = create_engine(DATABASE_URL, echo=True)
    with engine.connect() as conn:
        conn.execute("SELECT 1")
    logger.info("Conexão com PostgreSQL estabelecida com sucesso!")
except Exception as e:
    logger.error(f"Erro ao conectar ao banco: {str(e)}")
    raise

# Configurar a sessão
Session = sessionmaker(bind=engine)

def initialize_database():
    from models.base import Base
    try:
        Base.metadata.drop_all(bind=engine)  # Cuidado em produção!
        Base.metadata.create_all(bind=engine)
        logger.info("Tabelas criadas com sucesso no PostgreSQL")
    except Exception as e:
        logger.error(f"Erro ao criar tabelas: {str(e)}")
        raise

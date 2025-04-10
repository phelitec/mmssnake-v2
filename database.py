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
    from models.product import Product
    try:
        # Criar tabelas se não existirem
        Base.metadata.create_all(bind=engine)

        # Verificar se já existem produtos (evitar duplicatas)
        with Session() as session:
            if session.query(Product).count() == 0:  # Só insere se vazio
                initial_products = [
                    {"api":"machinesmm","base_quantity":200,"service_id":3079,"sku":"SS2SXTQ2A","type":"followers"},{"api":"machinesmm","base_quantity":300,"service_id":3079,"sku":"G73Y6J33D","type":"followers"},{"api":"machinesmm","base_quantity":500,"service_id":3079,"sku":"X8M545USL","type":"followers"},{"api":"machinesmm","base_quantity":1000,"service_id":3079,"sku":"BDBWVUAC4","type":"followers"},{"api":"machinesmm","base_quantity":2000,"service_id":3079,"sku":"7SS78J27P","type":"followers"},{"api":"machinesmm","base_quantity":3000,"service_id":3079,"sku":"A7T6GWDKG","type":"followers"},{"api":"machinesmm","base_quantity":4000,"service_id":3079,"sku":"PTW8XZJZ5","type":"followers"},{"api":"machinesmm","base_quantity":5000,"service_id":3079,"sku":"RB72M4G7M","type":"followers"},{"api":"machinesmm","base_quantity":10000,"service_id":3079,"sku":"ETQHP9FKU","type":"followers"},{"api":"machinesmm","base_quantity":30000,"service_id":3079,"sku":"JB8ZBHEW5","type":"followers"},{"api":"worldsmm","base_quantity":200,"service_id":1122,"sku":"GU5RKZYXT","type":"followers"},{"api":"worldsmm","base_quantity":500,"service_id":1122,"sku":"52SC9A3GB","type":"followers"},{"api":"worldsmm","base_quantity":1000,"service_id":1122,"sku":"VDX2CPC63","type":"followers"},{"api":"worldsmm","base_quantity":2000,"service_id":1122,"sku":"LS6E5EJK7","type":"followers"},{"api":"worldsmm","base_quantity":3000,"service_id":1122,"sku":"ZE63XLHVN","type":"followers"},{"api":"worldsmm","base_quantity":4000,"service_id":1122,"sku":"HXJAK2Z7D","type":"followers"},{"api":"worldsmm","base_quantity":5000,"service_id":1122,"sku":"N65KMA7SD","type":"followers"},{"api":"worldsmm","base_quantity":10000,"service_id":1122,"sku":"T3ZUGMPPQ","type":"followers"},{"api":"worldsmm","base_quantity":20000,"service_id":1122,"sku":"VC6DXMNEB","type":"followers"},{"api":"worldsmm","base_quantity":30000,"service_id":1122,"sku":"DT5568S35","type":"followers"},{"api":"machinesmm","base_quantity":500,"service_id":2492,"sku":"9R628ZD4Y","type":"likes"},{"api":"machinesmm","base_quantity":100,"service_id":2492,"sku":"43437FY86","type":"likes"},{"api":"machinesmm","base_quantity":1000,"service_id":2492,"sku":"SRV42XNAF","type":"likes"}]

                
                for prod in initial_products:
                    session.add(Product(**prod))
                session.commit()
                logger.info("Produtos iniciais adicionados com sucesso!")
            else:
                logger.info("Produtos já existem no banco, pulando inserção.")
    except Exception as e:
        logger.error(f"Erro ao inicializar o banco: {str(e)}")
        raise

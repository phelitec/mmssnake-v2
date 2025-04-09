from flask import Flask
from database import engine
from models.base import Base
from services.scheduler import start_scheduler
from routes import webhook_bp, payments_bp  # Importe todos os blueprints
from routes.instagram import instagram_bp


app = Flask(__name__)

def initialize_database():
    """
    Inicializa o banco de dados criando todas as tabelas definidas nos modelos.
    """
    from models.base import Base
    from sqlalchemy import inspect
    
    try:
        inspector = inspect(engine)
        
        # Verificar se a tabela instagram_credentials existe e se precisa ser recriada
        if 'instagram_credentials' in inspector.get_table_names():
            # Verificar se a coluna session_id existe
            columns = [column['name'] for column in inspector.get_columns('instagram_credentials')]
            if 'session_id' not in columns:
                # Recrie a tabela
                Base.metadata.tables['instagram_credentials'].drop(engine)
                logger.info("Tabela instagram_credentials excluída para recriação")
        
        # Criar todas as tabelas
        Base.metadata.create_all(bind=engine)
        logger.info("Tabelas criadas com sucesso")
    except Exception as e:
        logger.error(f"Erro ao criar tabelas: {str(e)}")
        raise



# Registrar blueprints
app.register_blueprint(webhook_bp, url_prefix='/api')
app.register_blueprint(payments_bp, url_prefix='/api')
app.register_blueprint(instagram_bp)
# Registre outros blueprints conforme necessário

# Iniciar agendador
start_scheduler()

if __name__ == '__main__':
    app.run(debug=True)

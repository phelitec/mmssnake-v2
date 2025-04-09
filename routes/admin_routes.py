from flask import Blueprint, jsonify, request
from sqlalchemy import text
from database import engine
import os
import logging

admin_bp = Blueprint('admin', __name__)
logger = logging.getLogger(__name__)

# Chave de segurança para proteger o endpoint - use uma variável de ambiente em produção
ADMIN_KEY = os.environ.get('ADMIN_KEY', 'chave-secreta-temporaria')

@admin_bp.route('/fix_database', methods=['POST'])
def fix_database():
    # Verificar a chave de segurança
    auth_key = request.headers.get('X-Admin-Key')
    if not auth_key or auth_key != ADMIN_KEY:
        return jsonify({'error': 'Acesso não autorizado'}), 401
    
    try:
        # Verificar estrutura da tabela
        with engine.connect() as conn:
            # Verificar se a tabela existe
            result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='instagram_credentials'"))
            table_exists = result.fetchone() is not None
            
            if table_exists:
                # Verificar colunas existentes
                result = conn.execute(text("PRAGMA table_info(instagram_credentials)"))
                columns = [row[1] for row in result.fetchall()]
                
                # Colunas a verificar
                needed_columns = ['session_id', 'proxy', 'rotation_interval']
                missing_columns = [col for col in needed_columns if col not in columns]
                
                # Adicionar colunas que faltam
                for column in missing_columns:
                    if column == 'rotation_interval':
                        conn.execute(text(f"ALTER TABLE instagram_credentials ADD COLUMN {column} INTEGER DEFAULT 10"))
                    else:
                        conn.execute(text(f"ALTER TABLE instagram_credentials ADD COLUMN {column} TEXT"))
                    logger.info(f"Coluna {column} adicionada à tabela instagram_credentials")
                
                return jsonify({
                    'message': 'Banco de dados atualizado com sucesso!',
                    'added_columns': missing_columns
                })
            else:
                # Se a tabela não existir, cria todas as tabelas
                from models.base import Base
                Base.metadata.create_all(engine)
                return jsonify({'message': 'Tabelas criadas com sucesso!'})
                
    except Exception as e:
        logger.error(f"Erro ao atualizar banco de dados: {str(e)}")
        return jsonify({'error': str(e)}), 500

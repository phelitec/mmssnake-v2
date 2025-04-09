from flask import Blueprint, jsonify, request
from sqlalchemy import text
from database import engine
import os
import logging

admin_bp = Blueprint('admin', __name__)
logger = logging.getLogger(__name__)

# Chave de segurança para proteger o endpoint
ADMIN_KEY = os.environ.get('ADMIN_KEY', 'chave-secreta-temporaria')

@admin_bp.route('/fix_database', methods=['POST'])
def fix_database():
    # Verificar a chave de segurança
    auth_key = request.headers.get('X-Admin-Key')
    if not auth_key or auth_key != ADMIN_KEY:
        return jsonify({'error': 'Acesso não autorizado'}), 401
    
    try:
        # Verificar se a tabela existe
        with engine.connect() as conn:
            # Verificar tabelas existentes
            result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='instagram_credentials'"))
            table_exists = result.fetchone() is not None
            
            if table_exists:
                # Opção 1: Apagar e recriar a tabela (isso perderá dados existentes)
                conn.execute(text("DROP TABLE instagram_credentials"))
                logger.info("Tabela instagram_credentials excluída")
                
                # Recriar a tabela com todas as colunas necessárias
                conn.execute(text("""
                CREATE TABLE instagram_credentials (
                    id INTEGER PRIMARY KEY,
                    username TEXT NOT NULL,
                    password TEXT NOT NULL,
                    session_id TEXT,
                    proxy TEXT,
                    is_active INTEGER DEFAULT 1,
                    last_used TIMESTAMP,
                    usage_count INTEGER DEFAULT 0,
                    rotation_interval INTEGER DEFAULT 10
                )
                """))
                logger.info("Tabela instagram_credentials recriada com sucesso")
                
                return jsonify({
                    'message': 'Banco de dados recriado com sucesso!',
                    'action': 'recreated'
                })
            else:
                # Criar tabela do zero
                conn.execute(text("""
                CREATE TABLE instagram_credentials (
                    id INTEGER PRIMARY KEY,
                    username TEXT NOT NULL,
                    password TEXT NOT NULL,
                    session_id TEXT,
                    proxy TEXT,
                    is_active INTEGER DEFAULT 1,
                    last_used TIMESTAMP,
                    usage_count INTEGER DEFAULT 0,
                    rotation_interval INTEGER DEFAULT 10
                )
                """))
                logger.info("Tabela instagram_credentials criada do zero")
                
                return jsonify({
                    'message': 'Tabela criada com sucesso!',
                    'action': 'created'
                })
                
    except Exception as e:
        logger.error(f"Erro ao atualizar banco de dados: {str(e)}")
        return jsonify({'error': str(e)}), 500

# Endpoint alternativo para adicionar colunas sem recriar a tabela
@admin_bp.route('/add_columns', methods=['POST'])
def add_columns():
    # Verificar a chave de segurança
    auth_key = request.headers.get('X-Admin-Key')
    if not auth_key or auth_key != ADMIN_KEY:
        return jsonify({'error': 'Acesso não autorizado'}), 401
    
    try:
        with engine.connect() as conn:
            # Verificar colunas existentes
            result = conn.execute(text("PRAGMA table_info(instagram_credentials)"))
            existing_columns = [row[1] for row in result.fetchall()]
            
            # Lista de todas as colunas necessárias e seus tipos
            required_columns = {
                'username': 'TEXT NOT NULL',
                'password': 'TEXT NOT NULL',
                'session_id': 'TEXT',
                'proxy': 'TEXT',
                'is_active': 'INTEGER DEFAULT 1',
                'last_used': 'TIMESTAMP',
                'usage_count': 'INTEGER DEFAULT 0',
                'rotation_interval': 'INTEGER DEFAULT 10'
            }
            
            # Adicionar colunas que faltam
            added_columns = []
            for col_name, col_type in required_columns.items():
                if col_name not in existing_columns:
                    conn.execute(text(f"ALTER TABLE instagram_credentials ADD COLUMN {col_name} {col_type}"))
                    added_columns.append(col_name)
                    logger.info(f"Coluna {col_name} adicionada")
            
            return jsonify({
                'message': 'Colunas adicionadas com sucesso!',
                'added_columns': added_columns
            })
            
    except Exception as e:
        logger.error(f"Erro ao adicionar colunas: {str(e)}")
        return jsonify({'error': str(e)}), 500

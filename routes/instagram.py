from flask import Blueprint, request, jsonify
from sqlalchemy.exc import IntegrityError
from models.base import InstagramCredentials  # Importando do models.base
from database import Session
import logging

instagram_bp = Blueprint('instagram', __name__)
logger = logging.getLogger(__name__)

@instagram_bp.route('/accounts', methods=['POST'])
def add_account():
    data = request.json
    session = Session()
    
    try:
        if not data.get('username') or not data.get('password'):
            return jsonify({'error': 'Username e password são obrigatórios'}), 400

        new_acc = InstagramCredentials(
            username=data['username'],
            password=data['password']
        )
        
        session.add(new_acc)
        session.commit()
        
        return jsonify({
            'id': new_acc.id,
            'username': new_acc.username
        }), 201
        
    except IntegrityError:
        session.rollback()
        return jsonify({'error': 'Username já existe'}), 409
    except Exception as e:
        session.rollback()
        logger.error(f"Erro: {str(e)}", exc_info=True)
        return jsonify({'error': 'Erro interno'}), 500
    finally:
        session.close()

@instagram_bp.route('/accounts/<string:username>', methods=['PUT'])
def update_instagram_credentials(username):
    data = request.get_json()
    session = Session()
    try:
        credentials = session.query(InstagramCredentials)\
                             .filter_by(username=username)\
                             .first()
        if not credentials:
            return jsonify({'error': 'Credenciais não encontradas'}), 404

        # Atualização segura dos campos
        updatable_fields = ['password', 'proxy', 'session_id', 'is_active', 'rotation_interval']
        for field in updatable_fields:
            if field in data:
                if field == 'proxy' and data[field] and not data[field].startswith(('http://', 'socks5://')):
                    return jsonify({'error': 'Formato de proxy inválido'}), 400
                setattr(credentials, field, data[field])

        session.commit()
        return jsonify({
            'message': 'Credenciais atualizadas com sucesso',
            'changes': data
        }), 200
    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()

@instagram_bp.route('/accounts/<username>', methods=['DELETE'])
def delete_instagram_credentials(username):
    session = Session()
    try:
        credentials = session.query(InstagramCredentials).filter_by(username=username).first()
        if not credentials:
            return jsonify({'error': 'Credenciais não encontradas'}), 404
            
        session.delete(credentials)
        session.commit()
        return jsonify({
            'message': 'Credenciais apagadas com sucesso',
            'username': username
        }), 200
    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()

@instagram_bp.route('/accounts', methods=['GET'])
def list_accounts():
    session = Session()
    try:
        accounts = session.query(InstagramCredentials).all()
        result = [{
            'id': acc.id,
            'username': acc.username,
            'is_active': acc.is_active,
            'usage_count': acc.usage_count,
            'last_used': acc.last_used.isoformat() if acc.last_used else None,
            'rotation_interval': acc.rotation_interval
        } for acc in accounts]
        
        return jsonify(result), 200
    except Exception as e:
        logger.error(f"Erro ao listar contas: {str(e)}")
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()

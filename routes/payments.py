from flask import Blueprint, jsonify, request
from database import Session
from models.base import Payments, ProductServices

payments_bp = Blueprint('payments', __name__)


@payments_bp.route('/payments', methods=['GET'])
def get_payments():
    # Criar uma sessão para interagir com o banco de dados
    session = Session()
    try:
        # Consultar todos os registros da tabela payments
        payments = session.query(Payments).all()

        # Converter os registros para uma lista de dicionarios
        payments_list = []
        for payment in payments:
            payments_list.append({
            'id': payment.id,
            'order_id': payment.order_id,
            'status_alias': payment.status_alias,
            'customer_name': payment.customer_name,
            'email': payment.email,
            'phone_full_number': payment.phone_full_number, 
            'item_sku': payment.item_sku,
            'item_quantity': payment.item_quantity,
            'customization': payment.customization,
            'finished': payment.finished,
            'profile_status': payment.profile_status

        })
    # Retornar os dados como JSON com status 200 (ok)
        return jsonify(payments_list), 200
    except Exception as e:
        # Em caso de erro, retornar uma mensagem com status 500
        return jsonify({'error': 'Erro interno no servidor'}), 500
    finally:
        # Fechar a sessão
        session.close()


@payments_bp.route('/payments/<id>', methods=['PUT'])
def update_payment(id):
    session = Session()  # Inicia uma sessão com o banco de dados
    try:
        # Busca o pagamento pelo ID
        payment = session.query(Payments).filter_by(id=id).first()
        if not payment:
            return jsonify({'error': 'Pagamento não encontrado'}), 404

        # Obtém os dados enviados no corpo da requisição (JSON)
        data = request.get_json()

        # Atualiza os campos fornecidos no JSON
        if 'order_id' in data:
            payment.order_id = data['order_id']
        if 'status_alias' in data:
            payment.status_alias = data['status_alias']
        if 'customer_name' in data:
            payment.customer_name = data['customer_name']
        if 'email' in data:
            payment.email = data['email']
        if 'phone_full_number' in data:
            payment.phone_full_number = data['phone_full_number']
        if 'item_sku' in data:
            payment.item_sku = data['item_sku']
        if 'item_quantity' in data:
            payment.item_quantity = data['item_quantity']
        if 'customization' in data:
            payment.customization = data['customization']
        if 'finished' in data:
            payment.finished = data['finished']
        if 'profile_status' in data:
            payment.profile_status = data['profile_status']

        # Salva as alterações no banco de dados
        session.commit()
        return jsonify({'message': 'Pagamento atualizado com sucesso'}), 200

    except Exception as e:
        session.rollback()  # Desfaz alterações em caso de erro
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()  # Fecha a sessão       



@payments_bp.route('/payments/<id>', methods=['DELETE'])
def delete_payment(id):
    session = Session()
    try:
        payment = session.query(Payments).filter_by(id=id).first()
        if not payment:
            return jsonify({'error': 'Pagamento não encontrado'}), 404
        session.delete(payment)
        session.commit()
        return jsonify({'message': 'Pagamento apagado com sucesso'}), 200
    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()       


@payments_bp.route('/products/<sku>', methods=['DELETE'])
def delete_product(sku):
    session = Session()
    try:
        product = session.query(ProductServices).filter_by(sku=sku).first()
        if not product:
            return jsonify({'error': 'Produto não encontrado'}), 404
        session.delete(product)
        session.commit()
        return jsonify({'message': 'Produto apagado com sucesso'}), 200
    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()        

@payments_bp.route('/products', methods=['POST'])
def add_products():
    session = Session()  # Criar a sessão fora do try
    try:
        data = request.get_json()  # Tenta obter o JSON da requisição
        required_fields = ['sku', 'service_id', 'api', 'base_quantity', 'type']
        
        # Verifica se todos os campos obrigatórios estão presentes
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Campo {field} é obrigatório'}), 400

        # Verifica se o SKU já existe
        if session.query(ProductServices).filter_by(sku=data['sku']).first():
            return jsonify({'error': 'Produto com este SKU já existe'}), 409

        # Cria o novo produto
        new_product = ProductServices(
            sku=data['sku'],
            service_id=data['service_id'],
            api=data['api'],
            base_quantity=data['base_quantity'],
            type=data['type']
        )
        session.add(new_product)
        session.commit()
        return jsonify({'message': 'Produto adicionado com sucesso'}), 201

    except Exception as e:
        session.rollback()  # Agora session está acessível
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()  # Fecha a sessão corretamente


@payments_bp.route('/products', methods={'GET'})
def get_products():
    session = Session()
    try:
        # Consultar todos os produtos da tabela
        products = session.query(ProductServices).all()
        # Converter os produtos para uma lista de dicionarios
        products_list = []
        for product in products:
            products_list.append({
                'sku': product.sku,
                'service_id': product.service_id,
                'api': product.api,
                'base_quantity': product.base_quantity,
                'type': product.type
            })
        # Retornar a lista como JSON com status 200
        return jsonify(products_list), 200
    except Exception as e:
        return jsonify({'error': 'Erro interno no servidor'}), 500
    finally:
        session.close()

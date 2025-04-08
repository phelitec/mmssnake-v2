from flask import Blueprint, request, jsonify  
from database import Session
from services.yampi_client import YampiClient
from models.base import Payments, ProductServices
from utils import sanitize_customization
import logging
from utils import check_profile_privacy

webhook_bp = Blueprint('webhook', __name__)

@webhook_bp.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()
    logging.info(f"Received webhook: {data}")
    
    if data.get('event') == 'order.paid':
        resource = data.get('resource', {})
        status_data = resource.get('status', {}).get('data', {})
        
        if status_data.get('alias') == 'paid':
            session = Session()
            try:
                order_id = str(resource.get('id'))
                status_alias = check_profile_privacy(customization_sanitized)
                logger.info(f"Profile status for {customization_sanitized}: {profile_status}")
                customer_data = resource.get('customer', {}).get('data', {})
                customer_name = customer_data.get('name')
                email = customer_data.get('email')
                phone_full_number = customer_data.get('phone', {}).get('full_number')
                items = resource.get('items', {}).get('data', [])
                
                if not items:
                    logging.info(f"No items found in order {order_id}. Skipping.")
                    session.close()
                    return 'OK', 200
                
                # Primeiro, coletar todas as customizações disponíveis no pedido
                available_customizations = {}
                for index, item in enumerate(items):
                    customizations = item.get('customizations', [])
                    if customizations:
                        customization = customizations[0].get('value')
                        sanitized = sanitize_customization(customization)
                        if sanitized:
                            available_customizations[index] = sanitized
                
                # Iterar sobre todos os itens
                for index, item in enumerate(items):
                    item_sku = item.get('item_sku')
                    item_quantity = item.get('quantity')
                    customizations = item.get('customizations', [])
                    customization = customizations[0].get('value') if customizations else None
                    customization_sanitized = sanitize_customization(customization) if customization else None
                    
                    # Se o item não tiver customização, tentar pegar de outro item no pedido
                    if not customization_sanitized and available_customizations:
                        # Pegar a primeira customização disponível que não seja do próprio item (se houver mais de uma)
                        for other_index, other_customization in available_customizations.items():
                            if other_index != index:  # Evitar usar a própria customização (se existir)
                                customization_sanitized = other_customization
                                logging.info(f"Item {index} (SKU: {item_sku}) sem customização, usando customização '{customization_sanitized}' do item {other_index}")
                                break
                    
                    # Se ainda assim não houver customização, logar e pular
                    if not customization_sanitized:
                        logging.info(f"No valid customization found for item {index} (SKU: {item_sku}) in order {order_id}. Skipping.")
                        continue
                    
                    # Criar um ID único para cada item
                    unique_id = f"{order_id}_{index}"
                    
                    # Verificar se o item já foi registrado
                    existing_payment = session.query(Payments).filter_by(id=unique_id).first()
                    if existing_payment:
                        logging.info(f"Payment with id {unique_id} already exists. Skipping.")
                        continue
                    
                    # Salvar o item no banco de dados
                    payment = Payments(
                        id=unique_id,
                        order_id=order_id,
                        status_alias=status_alias,
                        customer_name=customer_name,
                        email=email,
                        phone_full_number=phone_full_number,
                        item_sku=item_sku,
                        item_quantity=item_quantity,
                        customization=customization_sanitized
                    )
                    session.add(payment)
                    session.commit()
                    logging.info(f"Payment {unique_id} saved successfully")
                    
                    # Verificar o perfil do Instagram
                    
                    profile_status = check_profile_privacy(customization_sanitized)
                    payment.profile_status = profile_status
                    session.commit()
                    logging.info(f"Profile status for {customization_sanitized}: {profile_status}")
                
            except Exception as e:
                logging.error(f"Error saving payment: {str(e)}")
                session.rollback()
                return 'Error', 500
            finally:
                session.close()
    
    return 'OK', 200


@webhook_bp.route('/webhook/order-created', methods=['POST'])
def webhook_order_created():
    data = request.get_json()
    logging.info(f"Received order.created webhook: {data}")
    
    if data.get('event') == 'order.created':
        resource = data.get('resource', {})
        items = resource.get('items', {}).get('data', [])
        
        if not items:
            logging.info(f"No items found in order {resource.get('id')}. Skipping.")
            return 'OK', 200
            
        try:
            order_id = str(resource.get('id'))
            cl = get_instagram_clients()  # Obtém o cliente Instagrapi
            
            for index, item in enumerate(items):
                customizations = item.get('customizations', [])
                if not customizations:
                    logging.info(f"No customization found for item {index} in order {order_id}")
                    continue
                    
                customization = customizations[0].get('value')
                username = sanitize_customization(customization)
                
                if not username:
                    logging.info(f"Could not extract username from customization: {customization}")
                    continue
                
                # Verificar se o perfil existe e seguir
                try:
                    user_info = cl.user_info_by_username(username)
                    user_id = user_info.pk
                    
                    # Seguir o usuário
                    follow_result = cl.user_follow(user_id)
                    logging.info(f"Follow request sent to {username} (user_id: {user_id})")
                    
                except Exception as e:
                    logging.error(f"Error processing username {username}: {str(e)}")
                    continue
                    
        except Exception as e:
            logging.error(f"Error processing webhook: {str(e)}")
            return 'Error', 500
    
    return 'OK', 200


@webhook_bp.route('/webhook/order-updated', methods=['POST'])
def webhook_order_updated():
    """
    Endpoint para processar o webhook 'order.updated' e enviar uma mensagem direta fixa no Instagram
    quando o pedido for marcado como entregue (delivered: true).
    A mensagem fixa será: "Seu pedido foi entregue com sucesso! Obrigado por sua compra."
    """
    data = request.get_json()
    logging.info(f"Received order.updated webhook: {data}")
    
    # Verificar se é o evento correto
    if data.get('event') != 'order.updated':
        logging.info("Evento não é 'order.updated'. Ignorando.")
        return 'OK', 200
    
    resource = data.get('resource', {})
    
    # Verificar se delivered é true
    if not resource.get('delivered', False):
        logging.info(f"Pedido {resource.get('id')} não está entregue (delivered: false). Ignorando.")
        return 'OK', 200
    
    # Extrair os itens do pedido
    items = resource.get('items', {}).get('data', [])
    if not items:
        logging.info(f"Nenhum item encontrado no pedido {resource.get('id')}. Ignorando.")
        return 'OK', 200
    
    # Processar o primeiro item (assumindo que há apenas um item com customization)
    item = items[0]
    customizations = item.get('customizations', [])
    if not customizations:
        logging.info(f"Nenhuma customização encontrada no pedido {resource.get('id')}. Ignorando.")
        return 'OK', 200
    
    # Extrair e sanitizar o username do Instagram
    customization_value = customizations[0].get('value')
    username = sanitize_customization(customization_value)
    if not username:
        logging.info(f"Não foi possível extrair username de {customization_value} no pedido {resource.get('id')}. Ignorando.")
        return 'OK', 200
    
    # Mensagem fixa definida no código
    fixed_message = os.getenv("MENSAGEM_ENTREGUE")
    
    try:
        # Obter o cliente Instagrapi configurado
        cl = get_instagram_clients()
        
        # Obter o ID do usuário a partir do username
        user_id = cl.user_id_from_username(username)
        
        # Enviar a mensagem direta fixa
        cl.direct_send(fixed_message, [user_id])
        logging.info(f"Mensagem direta enviada com sucesso para {username} no pedido {resource.get('id')}: {fixed_message}")
        
        return jsonify({'message': f'Mensagem enviada com sucesso para {username}'}), 200
    
    except Exception as e:
        logging.error(f"Erro ao enviar mensagem direta para {username} no pedido {resource.get('id')}: {str(e)}")
        return jsonify({'error': f'Erro ao enviar mensagem: {str(e)}'}), 500              
    


@webhook_bp.route('/update-order-status', methods=['POST'])
def update_order_status():
    data = request.get_json()
    session = Session()
    
    try:
        if not data or 'order_id' not in data or 'status_alias' not in data:
            return jsonify({"error": "Campos obrigatórios: order_id e status_alias"}), 400

        yampi_client = YampiClient()  # Nome correto da variável
        
        success = yampi_client.update_status(
            session=session,
            order_id=data['order_id'],
            status_alias=data['status_alias']
        )

        return jsonify({"success": success}), 200 if success else 400

    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        session.rollback()
        return jsonify({"error": "Erro interno no servidor"}), 500
    finally:
        session.close()

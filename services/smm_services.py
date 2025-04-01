import requests
from utils import sanitize_customization
from utils import logger 
import logging

# Configuração da API SMM
SMM_CONFIG = {
    'machinesmm': {'base_url': 'https://machinesmm.com/api/v2', 'api_key': '7933dcebc18d85d7486c1666a1ae3d4d'},
    'worldsmm': {'base_url': 'https://worldsmm.com.br/api/v2', 'api_key': '1287cfd6baf5e432500591201bc121e3'},
    'smmclouduk': {'base_url': 'https://smmcloud.uk/api/v2', 'api_key': '1c900607f193909296d6c8a5573fa4c1'}
}




# Função para processar pagamentos pendentes
def process_pending_payments():
    session = Session()
    try:
        pending_payments = session.query(Payments).filter_by(finished=0, profile_status='public').all()
        if pending_payments:
            
            for payment in pending_payments:
                product = session.query(ProductServices).filter_by(sku=payment.item_sku).first()
                if not product:
                    logging.error(f"Product with SKU {payment.item_sku} not found for payment {payment.id}")
                    continue

                api_config = SMM_CONFIG.get(product.api)
                if not api_config:
                    logging.error(f"SMM configuration for api {product.api} not found for payment {payment.id}")
                    continue

                # Verificar se o tipo é 'likes' para processamento especial
                if product.type == 'likes':
                    try:
                        # Obter as últimas 4 publicações do perfil
                        username = payment.customization
                        user_id = cl.user_id_from_username(username)
                        media_list = cl.user_medias(user_id, amount=4)  # Pegar até 4 posts
                        
                        if not media_list:
                            logging.error(f"No media found for username {username} in payment {payment.id}")
                            continue

                        # Calcular a quantidade por post (dividido por 4)
                        total_quantity = product.base_quantity * payment.item_quantity
                        quantity_per_post = total_quantity // 4
                        if quantity_per_post == 0:
                            logging.error(f"Quantity per post too low ({quantity_per_post}) for payment {payment.id}")
                            continue

                        # Processar cada um dos 4 links
                        all_orders_successful = True
                        for media in media_list[:4]:  # Garantir no máximo 4
                            post_url = f"https://www.instagram.com/p/{media.code}/"
                            url = f"{api_config['base_url']}"
                            params = {
                                'key': api_config['api_key'],
                                'action': 'add',
                                'service': product.service_id,
                                'link': post_url,
                                'quantity': quantity_per_post
                            }
                            response = requests.post(url, data=params)
                            if response.status_code == 200:
                                try:
                                    response_data = response.json()
                                    if response_data.get('order'):
                                        logging.info(f"Order placed for {post_url} with {quantity_per_post} likes in payment {payment.id}")
                                    else:
                                        logging.error(f"API response missing order ID for {post_url} in payment {payment.id}: {response.text}")
                                        all_orders_successful = False
                                except ValueError:
                                    logging.error(f"Invalid JSON response for {post_url} in payment {payment.id}: {response.text}")
                                    all_orders_successful = False
                            else:
                                logging.error(f"API call failed for {post_url} in payment {payment.id}: {response.status_code} - {response.text}")
                                all_orders_successful = False

                        # Marcar como concluído apenas se todos os pedidos foram bem-sucedidos
                        if all_orders_successful:
                            payment.finished = 1
                            session.commit()
                            logging.info(f"All likes orders placed successfully for payment {payment.id}")

                            # Enviar mensagem no Direct
                            try:
                                message = f"Olá! 😊 Tudo certo? Passando para avisar que sua compra na Pede Pra Seguir já foi processada! 🚀 Suas curtidas vão começar a chegar em alguns minutos nas suas últimas 4 publicações. Qualquer coisa, estou por aqui para te ajudar! 💙 Obrigada por confiar na gente! 😉📲"
                                cl.direct_send(message, [user_id])
                                logging.info(f"Direct message sent to {username} for payment {payment.id}")
                            except Exception as dm_error:
                                logging.error(f"Failed to send Direct message to {username}: {str(dm_error)}")

                    except Exception as e:
                        logging.error(f"Error processing likes for payment {payment.id}: {str(e)}")
                        continue

                # Processamento padrão para outros tipos (ex.: seguidores)
                else:
                    url = f"{api_config['base_url']}"
                    params = {
                        'key': api_config['api_key'],
                        'action': 'add',
                        'service': product.service_id,
                        'link': f"https://www.instagram.com/{payment.customization}/",
                        'quantity': product.base_quantity * payment.item_quantity
                    }
                    response = requests.post(url, data=params)
                    if response.status_code == 200:
                        try:
                            response_data = response.json()
                            if response_data.get('order'):
                                payment.finished = 1
                                session.commit()
                                logging.info(f"Order placed successfully for payment {payment.id}: {response.text}")

                                # Enviar mensagem no Direct
                                try:
                                    user_id = cl.user_id_from_username(payment.customization)
                                    message = f"Olá! 😊 Tudo certo? Passando para avisar que sua compra na Pede Pra Seguir já foi processada! 🚀 Seus seguidores vão começar a chegar em alguns minutos. Qualquer coisa, estou por aqui para te ajudar! 💙 Obrigada por confiar na gente! 😉📲"
                                    cl.direct_send(message, [user_id])
                                    logging.info(f"Direct message sent to {payment.customization} for payment {payment.id}")
                                except Exception as dm_error:
                                    logging.error(f"Failed to send Direct message to {payment.customization}: {str(dm_error)}")
                            else:
                                logging.error(f"API response missing order ID for payment {payment.id}: {response.text}")
                        except ValueError:
                            logging.error(f"Invalid JSON response for payment {payment.id}: {response.text}")
                    else:
                        logging.error(f"API call failed for payment {payment.id}: {response.status_code} - {response.text}")

        else:
            logging.info("No pending payments found with finished=0 and profile_status='public'")
    except Exception as e:
        logging.error(f"Error in process_pending_payments: {str(e)}")
        session.rollback()
    finally:
        session.close()       

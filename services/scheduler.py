import logging
import schedule
import time
import threading
import requests
from database import Session
from models.base import Payments, ProductServices
from utils import check_profile_privacy, SMM_CONFIG


# Configuração da API da Yampi
YAMPI_CONFIG = {
    'api_key': 'WpBOPsu6eNio5U0OFyYHoaPLAwsqCrADFk2oOSXH',  # Substitua por sua chave real da Yampi
    'secret_key': 'sk_Fxsjv9craEK3YgYGoQ6kWEfSHERFErbY7MZUX',
    'base_url': 'https://api.dooki.com.br/v2/pede-pra-seguir/orders'
}

# Função para verificar perfis pendentes periodicamente
def check_pending_profiles():
    session = Session()
    try:
        pending_payments = session.query(Payments).filter_by(profile_status='private').all()
        if pending_payments:
           
            for payments in pending_payments:
                profile_status = check_profile_privacy(payments.customization)
                payments.profile_status = profile_status
                session.commit()
                logging.info(f"Updated profile status for {payments.customization}: {profile_status}")
    except Exception as e:
        logging.error(f"Error in scheduled task: {str(e)}")        
    finally:
        session.close()  

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


# Função para atualizar pedidos como entregues no banco e na Yampi
def update_delivered_orders():
    session = Session()
    try:
        # Consultar todos os pedidos com finished = 1
        finished_payments = session.query(Payments).filter_by(finished=1).all()
        if not finished_payments:
            logging.info("Nenhum pedido com finished=1 encontrado para atualizar.")
            return
        
        headers = {
            "User-Token": f"{YAMPI_CONFIG['api_key']}",
            "User-Secret-Key": f"{YAMPI_CONFIG['secret_key']}",
            "Content-Type": "application/json"
        }
        data = {
                "status_id": "7",
                "desire_status": "delivered"
}
        
        for payment in finished_payments:
            order_id = payment.order_id
            url = f"{YAMPI_CONFIG['base_url']}/{order_id}"
            
            try:
                # Fazer a requisição PUT para a Yampi
                response = requests.put(url, headers=headers, json=data)
                
                if response.status_code == 200 or response.status_code == 204:
                    logging.info(f"Pedido {order_id} atualizado para 'delivered' na Yampi com sucesso.")
                    # Opcional: Atualizar algum campo no banco, se desejar rastrear a sincronização
                    # payment.profile_status = 'delivered'  # Exemplo
                    # session.commit()
                else:
                    logging.error(f"Falha ao atualizar pedido {order_id} na Yampi: {response.status_code} - {response.text}")
            
            except requests.RequestException as e:
                logging.error(f"Erro na requisição para o pedido {order_id}: {str(e)}")
        
        logging.info(f"Processamento de atualização de {len(finished_payments)} pedidos concluído.")
    
    except Exception as e:
        logging.error(f"Erro ao processar atualização de pedidos: {str(e)}")
        session.rollback()
    finally:
        session.close()


def run_scheduled_task():
    schedule.every(2).minutes.do(check_pending_profiles)
    schedule.every(1).minutes.do(process_pending_payments)
    schedule.every().day.at("22:56").do(update_delivered_orders)  # Nova tarefa às 18:00
    logging.info("Agendador configurado para rodar tarefas periódicas.")
    while True:
        try:
            schedule.run_pending()
            logging.info("Agendador rodando...")
            time.sleep(30)
        except Exception as e:
            logging.error(f"Erro no loop do agendador: {str(e)}")
            time.sleep(60)

def start_scheduler():
    scheduler_thread = threading.Thread(target=run_scheduled_task)
    scheduler_thread.daemon = True
    scheduler_thread.start()
    logging.info("Thread do agendador iniciada com sucesso.")

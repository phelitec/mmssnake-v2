# Sistema de Automação de Serviços Instagram

## Visão Geral

Este projeto é um sistema de automação para processar pedidos da plataforma e-commerce Yampi e fornecer serviços de Instagram, como adição de seguidores e likes a perfis. O sistema funciona como um intermediário que recebe webhooks da Yampi quando pedidos são pagos, processa os pedidos e executa os serviços solicitados através de APIs de terceiros de SMM (Social Media Marketing).

## Funcionalidades Principais

- **Processamento de Webhooks**: Recebe notificações da Yampi quando um pedido é pago
- **Validação de Perfis**: Verifica se o perfil do Instagram fornecido é válido e público
- **Serviços Automatizados**: Fornece serviços de seguidores e likes para contas do Instagram
- **Execução Programada**: Verifica periodicamente pedidos pendentes e atualiza status
- **Gestão de Produtos**: Armazena e gerencia configurações de produtos/serviços

## Tecnologias Utilizadas

- **Framework Web**: Flask
- **ORM**: SQLAlchemy
- **Banco de Dados**: PostgreSQL
- **Tarefas Agendadas**: Biblioteca `schedule`
- **Processamento de Requisições**: Requests
- **Deployment**: Railway

## Estrutura do Projeto

```
├── .env                  # Variáveis de ambiente (NÃO DEVE SER COMMITADO)
├── app.py                # Ponto de entrada da aplicação
├── database.py           # Configuração do banco de dados
├── models/               # Modelos de dados
│   └── base.py           # Definições das tabelas SQLAlchemy
├── routes/               # Rotas da API
│   ├── __init__.py       # Inicialização de blueprints
│   ├── payments.py       # Endpoints para gerenciamento de pagamentos
│   └── webhooks.py       # Endpoints para receber webhooks da Yampi
├── services/             # Serviços para lógica de negócio
│   ├── __init__.py
│   ├── instagram_service.py  # Interação com APIs do Instagram
│   ├── scheduler.py      # Agendador de tarefas periódicas
│   └── yampi_client.py   # Cliente para API da Yampi
├── utils.py              # Funções utilitárias
├── Procfile              # Configuração para deployment
├── railway.json          # Configuração do Railway
├── requirements.txt      # Dependências do projeto
└── runtime.txt           # Versão do Python para deployment
```

## Modelos de Dados

### ProductServices
Armazena informações sobre os serviços/produtos disponíveis:
- `sku`: Código único do produto (chave primária)
- `service_id`: ID do serviço na API do SMM
- `api`: Nome da API a ser usada (ex: 'machinesmm', 'worldsmm')
- `base_quantity`: Quantidade base por unidade do produto
- `type`: Tipo de serviço (ex: 'followers', 'likes')

### Payments
Armazena informações sobre pagamentos e pedidos:
- `id`: ID único do pagamento (chave primária)
- `order_id`: ID do pedido na Yampi
- `status_alias`: Status do pagamento (ex: 'paid', 'delivered')
- `customer_name`: Nome do cliente
- `email`: Email do cliente
- `phone_full_number`: Número de telefone
- `item_sku`: SKU do item comprado
- `item_quantity`: Quantidade comprada
- `customization`: Nome de usuário do Instagram fornecido
- `finished`: Flag indicando se o pedido foi processado (0/1)
- `profile_status`: Status do perfil ('public', 'private', 'error')

## Serviços

### YampiClient
Responsável pela comunicação com a API da Yampi:
- Atualização de status de pedidos
- Gerenciamento de credenciais da API

### InstagramService
Gerencia a interação com o Instagram via APIs de terceiros:
- Verificação de privacidade de perfis
- Obtenção de informações de mídia do usuário

### Scheduler
Gerencia as tarefas periódicas:
- Verificação de perfis pendentes a cada 10 minutos
- Processamento de pagamentos pendentes a cada 10 minutos
- Atualização de pedidos entregues diariamente às 19h

## Fluxo de Processamento de Pedidos

1. Webhook da Yampi é recebido quando um pedido é pago
2. O sistema verifica e valida a assinatura do webhook
3. O perfil do Instagram é verificado (público/privado)
4. Se o perfil for privado, o status do pedido é atualizado para `shipment_exception`
5. Se o perfil for público, o pedido é salvo com `profile_status='public'` e `finished=0`
6. O agendador verifica periodicamente pedidos com `finished=0` e `profile_status='public'`
7. O serviço é executado através da API de SMM correspondente
8. Após execução bem-sucedida, o pedido é marcado como `finished=1`
9. Diariamente, os pedidos com `finished=1` são atualizados para `delivered` na Yampi

## Configuração e Instalação

### Pré-requisitos
- Python 3.10+
- PostgreSQL
- Credenciais da Yampi (API Key e Secret Key)
- Chaves de API para serviços de Instagram

### Variáveis de Ambiente
Crie um arquivo `.env` com as seguintes variáveis:

```
YAMPI_API_KEY="sua_api_key"
YAMPI_SECRET_KEY="sua_secret_key"
YAMPI_BASE_URL="https://api.dooki.com.br/v2/seu-alias/orders"
DATABASE_URL="postgresql://usuario:senha@host:porta/database"
LOOTER_API="sua_api_key"
INTAGRAM230_API="sua_api_key"
YAMPI_WEBHOOK_SECRET="seu_webhook_secret"
```

**IMPORTANTE:** Nunca comite o arquivo `.env` no repositório. Adicione-o ao `.gitignore`.

### Instalação Local

1. Clone o repositório:
   ```
   git clone [URL_DO_REPOSITORIO]
   cd [NOME_DO_REPOSITORIO]
   ```

2. Crie e ative um ambiente virtual:
   ```
   python -m venv venv
   source venv/bin/activate  # No Windows: venv\Scripts\activate
   ```

3. Instale as dependências:
   ```
   pip install -r requirements.txt
   ```

4. Configure as variáveis de ambiente conforme descrito acima

5. Execute a aplicação:
   ```
   python app.py
   ```

### Deployment no Railway

1. Conecte seu repositório GitHub ao Railway
2. Configure as variáveis de ambiente na plataforma Railway
3. O deployment será feito automaticamente a partir do arquivo `railway.json`

## Endpoints da API

### Webhooks
- `POST /api/webhook`: Recebe webhooks da Yampi
- `POST /api/update-order-status`: Atualiza status de um pedido na Yampi

### Pagamentos
- `GET /api/payments`: Lista todos os pagamentos
- `PUT /api/payments/<id>`: Atualiza um pagamento
- `DELETE /api/payments/<id>`: Deleta um pagamento

### Produtos
- `GET /api/products`: Lista todos os produtos
- `POST /api/products`: Adiciona um novo produto
- `DELETE /api/products/<sku>`: Deleta um produto

## Manutenção e Troubleshooting

### Logs
A aplicação utiliza o módulo `logging` do Python para registrar eventos importantes. Os logs incluem:
- Erros de processamento de webhook
- Status de verificação de perfis
- Resultados de chamadas de API para serviços SMM
- Execução de tarefas agendadas

### Problemas Comuns

#### Perfil do Instagram não é verificado
- Verifique se as chaves de API para os serviços de Instagram estão válidas
- Verifique se o username foi extraído corretamente da personalização

#### Pedidos não são processados
- Verifique se o agendador está em execução
- Verifique se os produtos têm configurações corretas no banco de dados
- Verifique se as APIs de SMM estão respondendo corretamente

#### Webhook não é recebido
- Verifique se o webhook está configurado corretamente na Yampi
- Verifique se a assinatura do webhook está correta

### Backup do Banco de Dados
Recomenda-se fazer backup regular do banco de dados, especialmente antes de atualizações significativas.

## Considerações de Segurança

- Nunca compartilhe suas chaves de API ou credenciais de banco de dados
- Mantenha o arquivo `.env` fora do controle de versão
- A validação de assinatura HMAC para webhooks deve ser sempre mantida
- Implemente medidas de rate limiting para evitar sobrecarga de API

## Contribuindo

1. Faça um fork do repositório
2. Crie um branch para sua feature (`git checkout -b feature/nome-da-feature`)
3. Commit suas alterações (`git commit -m 'Adiciona nova feature'`)
4. Push para o branch (`git push origin feature/nome-da-feature`)
5. Abra um Pull Request


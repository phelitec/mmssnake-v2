from flask import Flask
from database import engine
from models.base import Base
from services.scheduler import start_scheduler
from routes import webhook_bp, payments_bp  # Importe todos os blueprints
from routes.instagram import instagram_bp
from routes.admin_routes import admin_bp


app = Flask(__name__)



# Registrar blueprints
app.register_blueprint(webhook_bp, url_prefix='/api')
app.register_blueprint(payments_bp, url_prefix='/api')
app.register_blueprint(instagram_bp)
app.register_blueprint(admin_bp, url_prefix='/admin')  # Registrar com prefixo /admin
# Registre outros blueprints conforme necessário

# Iniciar agendador
start_scheduler()

if __name__ == '__main__':
    app.run(debug=True)

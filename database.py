from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

def initialize_database():
    try:
        Base.metadata.create_all(bind=engine)
    except Exception as e:
        print(f"Erro ao criar tabelas: {str(e)}")

db_path = os.path.join(os.path.dirname(__file__), 'app.db')
engine = create_engine(f'sqlite:///{db_path}', echo=True)
Session = sessionmaker(bind=engine)
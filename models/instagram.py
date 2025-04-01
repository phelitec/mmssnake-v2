from sqlalchemy import Column, Integer, String, Boolean, DateTime
from database import Base  # Importar Base do database.py

class InstagramCredentials(Base):
    __tablename__ = 'instagram_credentials'

    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    password = Column(String(100), nullable=False)
    session_id = Column(String(200))
    is_active = Column(Boolean, default=True)
    usage_count = Column(Integer, default=0)
    last_used = Column(DateTime)
    rotation_interval = Column(Integer, default=20)
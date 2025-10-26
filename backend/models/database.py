from sqlalchemy import create_engine, Column, Integer, String, DateTime, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import datetime

# Подключение к PostgreSQL
DATABASE_URL = "postgresql://app_user:app_pass@postgres:5432/postgres_db"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class ContainerHistory(Base):
    __tablename__ = "containers_history"
    
    id = Column(Integer, primary_key=True, index=True)
    container_name = Column(String, index=True)
    status = Column(String)
    image = Column(String)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

class SystemMetrics(Base):
    __tablename__ = "system_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    cpu_percent = Column(Float)
    memory_percent = Column(Float)
    disk_usage = Column(Float)

# Создание таблиц
def create_tables():
    Base.metadata.create_all(bind=engine)

# Dependency для получения сессии БД
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
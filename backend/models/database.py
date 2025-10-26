from sqlalchemy import create_engine, Column, Integer, String, DateTime, Float
from sqlalchemy.ext.declarative import declarative_base
import datetime

# SQLite для тестирования
#DATABASE_URL = "sqlite:///./test.db"
# postgres
DATABASE_URL = "postgresql://app_user:app_pass@postgres:5432/postgres_db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
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

def create_tables():
    Base.metadata.create_all(bind=engine)

def get_db():
    from sqlalchemy.orm import sessionmaker
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
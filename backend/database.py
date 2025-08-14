# database.py - Versão melhorada
import os
from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError
from models import Base, ItemDB, ProcessesDB
from typing import Generator

class DatabaseManager:
    def __init__(self, database_dir: str = "./data"):
        self.database_dir = database_dir
        self.engine = None
        self.SessionLocal = None
        
    def initialize_database(self) -> bool:
        """Inicializa a conexão com o banco de dados"""
        try:
            db_file = self._find_sqlite_file()
            database_url = f'sqlite:///{os.path.join(self.database_dir, db_file)}'
            
            self.engine = create_engine(
                database_url,
                echo=True,  # Para debug - pode ser False em produção
                pool_pre_ping=True,  # Verifica conexão antes de usar
                connect_args={"check_same_thread": False}  # Para SQLite
            )
            
            self.SessionLocal = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.engine
            )
            
            # Cria as tabelas se não existirem
            Base.metadata.create_all(bind=self.engine)
            return True
            
        except Exception as e:
            print(f"Erro ao inicializar banco de dados: {e}")
            return False
    
    def _find_sqlite_file(self) -> str:
        """Encontra o primeiro arquivo .sqlite na pasta"""
        try:
            if not os.path.exists(self.database_dir):
                raise RuntimeError(f"O diretório '{self.database_dir}' não foi encontrado.")
                
            sqlite_files = [f for f in os.listdir(self.database_dir) if f.endswith(".sqlite")]
            
            if not sqlite_files:
                raise RuntimeError(f"Nenhum arquivo .sqlite encontrado na pasta '{self.database_dir}'")
            
            return sqlite_files[0]  # Retorna o primeiro encontrado
            
        except FileNotFoundError:
            raise RuntimeError(f"O diretório '{self.database_dir}' não foi encontrado.")
    
    def get_session(self) -> Generator[Session, None, None]:
        """Generator que retorna uma sessão do banco de dados"""
        if not self.SessionLocal:
            if not self.initialize_database():
                raise RuntimeError("Falha ao inicializar banco de dados")
        
        db = self.SessionLocal()
        try:
            yield db
        except SQLAlchemyError as e:
            db.rollback()
            raise e
        finally:
            db.close()
    
    def test_connection(self) -> bool:
        """Testa se a conexão com o banco está funcionando"""
        try:
            with self.get_session() as db:
                db.execute("SELECT 1")
            return True
        except Exception as e:
            print(f"Erro ao testar conexão: {e}")
            return False

# Instância global do gerenciador de banco
db_manager = DatabaseManager()

# Função para compatibilidade com FastAPI Depends
def get_db() -> Generator[Session, None, None]:
    """Função para usar com FastAPI Depends"""
    yield from db_manager.get_session()

# Funções utilitárias para operações comuns
def create_item(db: Session, item_data: dict) -> ItemDB:
    """Cria um novo item no banco"""
    db_item = ItemDB(**item_data)
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

def create_process(db: Session, process_data: dict) -> ProcessesDB:
    """Cria um novo processo no banco"""
    db_process = ProcessesDB(**process_data)
    db.add(db_process)
    db.commit()
    db.refresh(db_process)
    return db_process

def get_all_processes(db: Session, skip: int = 0, limit: int = 100):
    """Busca todos os processos com paginação"""
    return db.query(ProcessesDB).offset(skip).limit(limit).all()

def get_process_by_package_name(db: Session, package_name: str):
    """Busca processo por nome do pacote"""
    return db.query(ProcessesDB).filter(ProcessesDB.package_name == package_name).first()

def get_all_items(db: Session, skip: int = 0, limit: int = 100):
    """Busca todos os items com paginação"""
    return db.query(ItemDB).offset(skip).limit(limit).all()
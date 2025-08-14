# models.py - Versão melhorada
from pydantic import BaseModel, Field, validator
from sqlalchemy import Column, Integer, String, Float, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from typing import Optional, List, Dict

# SQLAlchemy Base
Base = declarative_base()

# SQLAlchemy Models (para o banco de dados)
class ItemDB(Base):
    __tablename__ = "items"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(String, index=True)
    uid = Column(Integer)
    package_name = Column(String, index=True)
    usagetime = Column(Integer)
    delta_cpu_time = Column(Integer)
    cpu_usage = Column(Float)
    rx_data = Column(Integer)
    tx_data = Column(Integer)

class ProcessesDB(Base):
    __tablename__ = "processes"
    
    id = Column(Integer, primary_key=True, index=True)
    package_name = Column(String, index=True)
    uid = Column(Integer)
    pids = Column(Text)  # Usando Text para dados longos
    metrics = Column(Text)
    byte_size = Column(Integer)

# Pydantic Models (para validação de dados da API)
class ItemBase(BaseModel):
    timestamp: str
    uid: int
    package_name: str
    usagetime: int = Field(ge=0, description="Tempo de uso deve ser não negativo")
    delta_cpu_time: int = Field(ge=0, description="Delta CPU deve ser não negativo")
    cpu_usage: float = Field(ge=0.0, le=100.0, description="CPU usage entre 0 e 100%")
    rx_data: int = Field(ge=0, description="RX data deve ser não negativo")
    tx_data: int = Field(ge=0, description="TX data deve ser não negativo")
    
    @validator('timestamp')
    def validate_timestamp(cls, v):
        try:
            # Tenta fazer parse da data para validar formato
            datetime.fromisoformat(v.replace('Z', '+00:00'))
            return v
        except ValueError:
            raise ValueError('Timestamp deve estar em formato ISO válido')

class ItemCreate(ItemBase):
    pass

class ItemResponse(ItemBase):
    id: Optional[int] = None
    
    class Config:
        from_attributes = True

class ProcessesBase(BaseModel):
    package_name: str = Field(..., min_length=1, description="Nome do pacote não pode ser vazio")
    uid: int = Field(..., ge=0, description="UID deve ser não negativo")
    pids: str = Field(..., description="PIDs no formato 'pid1:val1;pid2:val2'")
    metrics: str = Field(..., description="Métricas no formato 'val1:val2:val3:val4:val5:val6'")
    byte_size: int = Field(..., ge=0, description="Byte size deve ser não negativo")
    
    @validator('pids')
    def validate_pids(cls, v):
        if not v:
            return v
        
        try:
            for pair in v.split(';'):
                if pair:
                    pid, val = pair.split(':')
                    int(pid)  # Valida se é número
                    int(val)  # Valida se é número
            return v
        except ValueError:
            raise ValueError('PIDs devem estar no formato "pid1:val1;pid2:val2"')
    
    @validator('metrics')
    def validate_metrics(cls, v):
        if not v:
            return v
            
        try:
            valores = v.strip(';').split(':')
            if len(valores) != 6:
                raise ValueError('Métricas devem conter exatamente 6 valores')
            
            # Valida tipos: 3 int, 1 float, 2 int
            int(valores[0])
            int(valores[1])
            int(valores[2])
            float(valores[3])
            int(valores[4])
            int(valores[5])
            return v
        except (ValueError, IndexError):
            raise ValueError('Métricas devem estar no formato "int:int:int:float:int:int"')

class ProcessesCreate(ProcessesBase):
    pass

class ProcessesResponse(ProcessesBase):
    id: Optional[int] = None
    
    class Config:
        from_attributes = True

class MetricsBase(BaseModel):
    metric1: int = Field(..., description="Primeira métrica")
    metric2: int = Field(..., description="Segunda métrica")
    metric3: float = Field(..., description="Terceira métrica")
    metric4: int = Field(..., description="Quarta métrica")
    metric5: int = Field(..., description="Quinta métrica")

class MetricsResponse(MetricsBase):
    pass

# Modelos para respostas processadas
class ProcessedPids(BaseModel):
    pids_dict: Dict[int, int] = Field(..., description="Dicionário de PIDs processados")

class ProcessedMetrics(BaseModel):
    metrics_list: List[float] = Field(..., description="Lista de métricas processadas")

class ProcessedProcessResponse(BaseModel):
    package_name: str
    uid: int
    pids_info: Dict[int, int]
    metrics_info: List[float]
    byte_size: int
#importar o arquivo enviado via post no main e tratar ele pra salvar no database
from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class Item(BaseModel):
    timestamp: str
    uid: int
    package_name: str
    usagetime: int
    delta_cpu_time: int
    cpu_usage: float
    rx_data: int
    tx_data: int
# main.py - Versão melhorada
from typing import List, Optional
from fastapi import FastAPI, File, UploadFile, Depends, HTTPException, Query
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import os
import shutil
import sqlite3
import pandas as pd

# Importando os modelos e database
from database import get_db, db_manager, create_item, create_process, get_all_processes, get_all_items
from models import (
    ItemCreate, ItemResponse, 
    ProcessesCreate, ProcessesResponse, 
    ProcessedProcessResponse,
    ItemDB, ProcessesDB
)

app = FastAPI(
    title="Database API",
    description="API para upload e consulta de dados SQLite",
    version="1.0.0"
)

# Configuração CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, especifique os domínios permitidos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATABASE_DIR = "./data"

@app.on_event("startup")
async def startup():
    """Inicializa a aplicação"""
    if not os.path.exists(DATABASE_DIR):
        os.makedirs(DATABASE_DIR)
    print(" API iniciada com sucesso!")

@app.on_event("shutdown")
async def shutdown():
    """Finaliza a aplicação"""
    print(" API finalizada")

# Rota para upload de arquivos SQLite
@app.post("/upload-db/", summary="Upload de arquivos de banco de dados")
async def upload_database_files(files: List[UploadFile] = File(...)):

    if not files:
        raise HTTPException(status_code=400, detail="Nenhum arquivo foi enviado.")
    
    saved_files = []
    errors = []
    
    for file in files:
        try:
            if not file.filename.endswith(('.sqlite', '.db', '.sqlite3')):
                errors.append(f"Arquivo {file.filename} não é um arquivo SQLite válido")
                continue
            
            file_path = os.path.join(DATABASE_DIR, file.filename)
            
            # Salva o arquivo
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            # Valida se o arquivo é um SQLite válido
            try:
                conn = sqlite3.connect(file_path)
                conn.execute("SELECT 1")
                conn.close()
                saved_files.append(file.filename)
            except sqlite3.DatabaseError:
                os.remove(file_path)  # Remove arquivo inválido
                errors.append(f"Arquivo {file.filename} não é um banco SQLite válido")
                
        except Exception as e:
            errors.append(f"Erro ao processar {file.filename}: {str(e)}")
    
    if not saved_files and errors:
        raise HTTPException(status_code=400, detail={"errors": errors})
    

    db_manager.initialize_database()
    
    return {
        "message": f"{len(saved_files)} arquivo(s) enviado(s) com sucesso",
        "saved_files": saved_files,
        "errors": errors if errors else None
    }


@app.get("/health", summary="Status da aplicação")
async def health_check():

    try:
        db_status = db_manager.test_connection()
        return {
            "status": "healthy" if db_status else "unhealthy",
            "database": "connected" if db_status else "disconnected",
            "message": "API funcionando normalmente" if db_status else "Problemas com banco de dados"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "database": "error",
            "message": f"Erro: {str(e)}"
        }

@app.get("/processes/", response_model=List[ProcessesResponse], summary="Listar todos os processos")
async def read_processes(
    skip: int = Query(0, ge=0, description="Número de registros para pular"),
    limit: int = Query(100, ge=1, le=1000, description="Número máximo de registros a retornar"),
    db: Session = Depends(get_db)
):

    try:
        processes = get_all_processes(db, skip=skip, limit=limit)
        return [
            ProcessesResponse(
                id=process.id,
                package_name=process.package_name,
                uid=process.uid,
                pids=process.pids,
                metrics=process.metrics,
                byte_size=process.byte_size
            )
            for process in processes
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao consultar processos: {str(e)}")

@app.get("/processes/first-item", response_model=ProcessedProcessResponse, summary="Primeiro processo processado")
def read_first_process_processed(db: Session = Depends(get_db)):

    try:
        first_process = db.query(ProcessesDB).first()
        if not first_process:
            raise HTTPException(status_code=404, detail="Nenhum processo encontrado na tabela.")
        

        pids_dict = {}
        if first_process.pids:
            for pair in first_process.pids.split(';'):
                if pair:
                    try:
                        pid, val = pair.split(':')
                        pids_dict[int(pid)] = int(val)
                    except ValueError:
                        continue
        
        # Processa Métricas
        metrics_list = []
        if first_process.metrics:
            metrics_string = first_process.metrics.strip(';')
            valores = metrics_string.split(':')
            if len(valores) == 6:
                try:
                    metrics_list = [
                        int(valores[0]),    # metric1: int
                        int(valores[1]),    # metric2: int
                        int(valores[2]),    # metric3: int
                        float(valores[3]),  # metric4: float
                        int(valores[4]),    # metric5: int
                        int(valores[5])     # metric6: int
                    ]
                except ValueError as e:
                    raise HTTPException(status_code=500, detail=f"Erro ao processar métricas: {str(e)}")
        
        return ProcessedProcessResponse(
            package_name=first_process.package_name,
            uid=first_process.uid,
            pids_info=pids_dict,
            metrics_info=metrics_list,
            byte_size=first_process.byte_size
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

@app.get("/items/", response_model=List[ItemResponse], summary="Listar todos os items")
async def read_items(
    skip: int = Query(0, ge=0, description="Número de registros para pular"),
    limit: int = Query(100, ge=1, le=1000, description="Número máximo de registros a retornar"),
    db: Session = Depends(get_db)
):

    try:
        items = get_all_items(db, skip=skip, limit=limit)
        return [
            ItemResponse(
                id=item.id,
                timestamp=item.timestamp,
                uid=item.uid,
                package_name=item.package_name,
                usagetime=item.usagetime,
                delta_cpu_time=item.delta_cpu_time,
                cpu_usage=item.cpu_usage,
                rx_data=item.rx_data,
                tx_data=item.tx_data
            )
            for item in items
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao consultar items: {str(e)}")

@app.post("/processes/", response_model=ProcessesResponse, summary="Criar novo processo")
async def create_new_process(process: ProcessesCreate, db: Session = Depends(get_db)):

    try:
        process_data = {
            "package_name": process.package_name,
            "uid": process.uid,
            "pids": process.pids,
            "metrics": process.metrics,
            "byte_size": process.byte_size
        }
        db_process = create_process(db, process_data)
        return ProcessesResponse.from_orm(db_process)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao criar processo: {str(e)}")

@app.post("/items/", response_model=ItemResponse, summary="Criar novo item")
async def create_new_item(item: ItemCreate, db: Session = Depends(get_db)):
    try:
        item_data = {
            "timestamp": item.timestamp,
            "uid": item.uid,
            "package_name": item.package_name,
            "usagetime": item.usagetime,
            "delta_cpu_time": item.delta_cpu_time,
            "cpu_usage": item.cpu_usage,
            "rx_data": item.rx_data,
            "tx_data": item.tx_data
        }
        db_item = create_item(db, item_data)
        return ItemResponse.from_orm(db_item)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao criar item: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app", 
        host="0.0.0.0", 
        port=8000, 
        reload=True, 
        log_level="info"
    )
import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from supabase import create_client
from dotenv import load_dotenv
import subprocess

# Cargar variables de entorno
load_dotenv()

app = FastAPI()

# Configuración CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inicializar Supabase
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

# Modelos de datos
class Agencia(BaseModel):
    nombre: str
    whatsapp: str
    zona: str

class Interes(BaseModel):
    agencia_id: str
    marca: str
    modelo: str
    km_maximo: int
    combustible: str
    precio_minimo: float = None
    precio_maximo: float = None

# ENDPOINTS
@app.get("/agencias")
async def get_agencias():
    response = supabase.table("agencias").select("*").execute()
    return response.data

@app.post("/agencias")
async def crear_agencia(agencia: Agencia):
    response = supabase.table("agencias").insert(agencia.dict()).execute()
    return response.data

@app.get("/mapeo-radar")
async def get_mapeo_radar():
    response = supabase.table("filtros_slots").select("*").execute()
    return response.data

@app.post("/intereses")
async def crear_interes(interes: Interes):
    response = supabase.table("filtros_slots").insert(interes.dict()).execute()
    return response.data

@app.delete("/intereses/{interes_id}")
async def eliminar_interes(interes_id: str):
    supabase.table("filtros_slots").delete().eq("id", interes_id).execute()
    return {"status": "ok"}

@app.delete("/agencias/{agencia_id}")
async def eliminar_agencia(agencia_id: str):
    # Borrar filtros asociados primero para evitar conflictos
    supabase.table("filtros_slots").delete().eq("agencia_id", agencia_id).execute()
    supabase.table("agencias").delete().eq("id", agencia_id).execute()
    return {"status": "ok"}

@app.post("/trigger-radar")
async def trigger_radar():
    try:
        # Lanza el scraper en segundo plano
        subprocess.Popen(["python", "run_radar.py"])
        return {"status": "success", "message": "Radar patrullando..."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
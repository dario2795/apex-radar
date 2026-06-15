import os
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from supabase import create_client, Client
from dotenv import load_dotenv

# =========================================================
# 1. CARGA DE VARIABLES DE ENTORNO (CORREGIDO CON RUTA)
# =========================================================
# Esto le dice a Python que busque el archivo exactamente dentro de backend/
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")

# 2. FUNCIÓN DE PRUEBA ORIGINAL (Se ejecuta al iniciar el servidor)
def probar_conexion_inicial():
    try:
        print(f"\n📡 Intentando conectar a Supabase: {url}")
        client = create_client(url, key)
        response = client.table("vehiculos_detectados").select("*").limit(1).execute()
        print("¡CONEXIÓN EXITOSA CON SUPABASE! ✅")
        print("Muestra de datos:", response.data, "\n")
        return client
    except Exception as e:
        print("\n❌ --- ERROR DE CONEXIÓN CRÍTICO ---")
        print(f"Detalle: {e}\n")
        # Igualmente creamos el cliente para que no explote el script, 
        # pero te avisa en la terminal.
        return create_client(url, key)

# Inicializamos el cliente global de Supabase
supabase: Client = probar_conexion_inicial()

# 3. CONFIGURACIÓN DE FASTAPI
app = FastAPI(title="Apex Radar API - Mendoza")

# 🚨 REGLA ORO DE CORS: Permite que tu Live Server (puerto 5500) le hable a FastAPI (puerto 8000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================================================
# 4. MODELOS DE PYDANTIC (Corregidos y Flexibles)
# =========================================================

class AgenciaCreate(BaseModel):
    nombre: str
    whatsapp: str
    # Al hacerlos opcionales con '| None = None', Pydantic no explota si el JS manda uno u otro
    zona: str | None = None  
    region: str | None = None  

class InteresCreate(BaseModel):
    agencia_id: str
    marca: str
    modelo: str
    km_maximo: int
    combustible: str
    precio_minimo: int | None = None  # Recibe el precio mínimo
    precio_maximo: int | None = None  # Recibe el precio máximo

# =========================================================
# 5. ENDPOINTS REQUERIDOS BY APP.JS (Mesa de Entradas)
# =========================================================

@app.get("/agencias")
def obtener_agencias():
    """Trae las agencias respetando tus columnas reales en minúsculas"""
    try:
        print("\n🔄 [GET] Cargando agencias desde Supabase...")
        res = supabase.table("agencias").select("*").execute()
        
        agencias_limpias = []
        if res.data:
            for fila in res.data:
                agencias_limpias.append({
                    "id": fila.get("id"),
                    "nombre": fila.get("nombre"),
                    "whatsapp": fila.get("whatsapp"),
                    "zona": fila.get("region") or "Este",
                    "activo": fila.get("activo") or False
                })
        
        return agencias_limpias
    except Exception as e:
        print(f"❌ Error en GET /agencias: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error al leer base de datos: {str(e)}")


@app.post("/agencias", status_code=status.HTTP_201_CREATED)
def guardar_agencia(agencia: AgenciaCreate):
    """Guarda la agencia mandando las claves en minúsculas idénticas a Supabase"""
    try:
        print("\n📥 [POST] Recibiendo nueva agencia del frontend...")
        
        valor_region = agencia.region or agencia.zona or "Este"
        if valor_region.lower() == "este":
            valor_region = "Este"

        # payload adaptado 100% a tus columnas reales de la base de datos
        payload = {
            "nombre": agencia.nombre,
            "whatsapp": agencia.whatsapp,  
            "region": valor_region,        
            "activo": True                
        }
        
        print(f"📡 Insertando en Supabase: {payload}")
        res = supabase.table("agencias").insert(payload).execute()
        
        if res.data and len(res.data) > 0:
            fila = res.data[0]
            return [{
                "id": fila.get("id"),
                "nombre": fila.get("nombre"),
                "whatsapp": fila.get("whatsapp"),
                "zona": fila.get("region") or "Este"
            }]
            
        return []

    except Exception as e:
        error_str = str(e)
        print(f"❌ Error en POST /agencias: {error_str}")
        
        if "23505" in error_str or "already exists" in error_str.lower():
            raise HTTPException(
                status_code=400,
                detail="Ese número de WhatsApp ya pertenece a otra agencia registrada."
            )
            
        raise HTTPException(status_code=500, detail=f"Error interno en Supabase: {error_str}")

@app.get("/mapeo-radar")
async def get_mapeo_radar():
    try:
        res = supabase.table("filtros_slots").select("*").execute()
        return {"status": "success", "data": res.data if res.data else []}
    except Exception as e:
        return {"status": "error", "message": str(e)}
                    
@app.post("/intereses", status_code=status.HTTP_201_CREATED)
def guardar_interes(interes: InteresCreate):
    """Vincula un vehículo de interés (slot) a una agencia específica con rangos de precio"""
    try:
        payload = {
            "agencia_id": interes.agencia_id,
            "marca": interes.marca,
            "modelo": interes.modelo,
            "precio_minimo": interes.precio_minimo,  # Guarda directo en la columna SQL
            "precio_maximo": interes.precio_maximo   # Guarda directo en la columna SQL
        }
        
        print(f"📡 Intentando insertar interés en Supabase: {payload}")
        res = supabase.table("filtros_slots").insert(payload).execute()
        print("¡Interés enlazado con éxito! ⚡")
        return res.data
    except Exception as e:
        print(f"❌ Error crítico en POST /intereses: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    
@app.delete("/agencias/{id}")
def eliminar_agencia(id: str):
    """Borra una agencia completa (y limpia sus slots en cascada por regla SQL)"""
    try:
        res = supabase.table("agencias").delete().eq("id", id).execute()
        return {"status": "ok", "message": f"Agencia {id} eliminada."}
    except Exception as e:
        print(f"❌ Error en DELETE /agencias: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/intereses/{id}")
def eliminar_interes(id: str):
    """Remueve un vehículo del radar de una agencia desde la cruz (×)"""
    try:
        res = supabase.table("filtros_slots").delete().eq("id", id).execute()
        return {"status": "ok", "message": f"Slot {id} eliminado."}
    except Exception as e:
        print(f"❌ Error en DELETE /intereses: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# 6. DISPARADOR DE ARRANCADO LOCAL
if __name__ == "__main__":
    import uvicorn
    # Corre en localhost (127.0.0.1) en el puerto 8000 que trackea tu frontend
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)

    # ... (todo tu código anterior) ...

# 7. RUTA PARA DISPARAR EL RADAR (La que faltaba)
@app.get("/trigger-match")
async def trigger_match():
    try:
        print("🚀 ¡Radar activado desde el botón!")
        # ACA PODRÍAS LLAMAR A TU SCRAPER:
        # desde_scraper import ejecutar_radar
        # resultado = ejecutar_radar()
        return {"status": "success", "message": "Radar ejecutado correctamente"}
    except Exception as e:
        print(f"❌ Error al disparar el radar: {e}")
        return {"status": "error", "message": str(e)}

# 8. DISPARADOR DE ARRANCADO LOCAL
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
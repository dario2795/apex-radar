import os
from supabase import create_client
from dotenv import load_dotenv

# Carga las variables desde el archivo .env
load_dotenv()

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase = create_client(url, key)

def guardar_vehiculo(auto_info: dict):
    """
    Guarda el auto en Supabase con precio limpio y control de errores.
    """
    try:
        # Limpieza estricta del precio
        precio_crudo = str(auto_info["precio"])
        precio_limpio = precio_crudo.replace("$", "").replace(".", "").replace(",", "").strip()
        precio_entero = int(precio_limpio) if precio_limpio.isdigit() else 0

        # ESCUDO ANTIBUG 1: Limpieza y validación del año por si viene con texto o vacío
        anio_crudo = str(auto_info["anio"]).strip()
        anio_limpio = "".join(filter(str.isdigit, anio_crudo))
        anio_entero = int(anio_limpio) if anio_limpio.isdigit() else 0

        response = supabase.table("vehiculos_detectados").insert({
            "origen": auto_info["origen"],
            "titulo": auto_info["titulo"],
            "url_publicacion": auto_info["link"],   
            "precio_publicado": precio_entero,
            "marca": auto_info["marca"].strip(),
            "modelo": auto_info["modelo"].strip(),
            "anio": anio_entero,
            "localidad": auto_info["localidad"]
        }).execute()
        
        return True
        
    except Exception as e:
        # ESCUDO ANTIBUG 2: Capturar de forma limpia si el auto ya fue procesado antes (Duplicado)
        error_msg = str(e)
        if "duplicate key value" in error_msg or "violates unique constraint" in error_msg:
            print(f"ℹ️ [RADAR] El vehículo ya existe en la base de datos (URL duplicada).")
        else:
            print(f"⚠️ [AVISO DB] No se insertó vehículo por otro error: {e}")
        return False

def obtener_agencias_interesadas(region_auto: str, marca: str, modelo: str):
    """
    Busca agencias activas usando normalización estricta de minúsculas.
    """
    try:
        # Buscamos en la base usando ilike (que es case-insensitive)
        response = supabase.table("filtros_slots") \
            .select("agencias(nombre, whatsapp, region, activo)") \
            .ilike("marca", marca.strip()) \
            .ilike("modelo", modelo.strip()) \
            .execute()
        
        agencias = []
        
        # NORMALIZACIÓN AQUÍ: pasamos todo a minúsculas para comparar la región
        region_buscada = region_auto.lower().strip()
        
        for fila in response.data:
            agencia_info = fila.get("agencias")
            if agencia_info:
                # Comparamos región en minúsculas y verificamos estado activo
                region_agencia = agencia_info.get("region", "").lower().strip()
                
                if region_agencia == region_buscada and agencia_info.get("activo") is True:
                    agencias.append({
                        "nombre": agencia_info["nombre"],
                        "whatsapp": agencia_info["whatsapp"]
                    })
                    
        return agencias
    except Exception as e:
        print(f"❌ Error al consultar agencias interesadas: {e}")
        return []
import os
import time
import pandas as pd
import streamlit as st
from supabase import create_client
from dotenv import load_dotenv

# Configuración de la página
st.set_page_config(page_title="Apex Radar - Panel 15 Agencias", page_icon="🏎️", layout="wide")

# Inicialización de Base de Datos
load_dotenv()
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase = create_client(url, key)

st.title("🏎️ Apex Radar - Panel de Control Mendoza")
st.subheader("Gestión de Cupos (Máximo 15 Agencias / 3 por Región)")

# Dividimos la pantalla en dos columnas principales
col1, col2 = st.columns([1, 2])

# ==========================================
# COLUMNA 1: REGISTRO DE AGENCIAS
# ==========================================
with col1:
    st.markdown("### ➕ Registrar Nueva Agencia")
    nombre = st.text_input("Nombre de la Agencia", placeholder="Ej: San Martín Automotores")
    whatsapp = st.text_input("WhatsApp (Con código de país)", placeholder="Ej: 549261XXXXXXX")
    region = st.selectbox("Región Asignada", ["este", "gm_norte", "gm_sur", "valle_uco", "sur"])
    
    if st.button("Guardar Agencia", type="primary"):
        if nombre and whatsapp:
            try:
                # Chequeo de cupos estricto por región (Máximo 3)
                chequeo_cupo = supabase.table("agencias").select("id").eq("region", region).execute()
                if len(chequeo_cupo.data) >= 3:
                    st.error(f"❌ ¡Cupo lleno! Ya hay 3 agencias en la región {region.upper()}.")
                else:
                    supabase.table("agencias").insert({
                        "nombre": nombre, "whatsapp": whatsapp, "region": region
                    }).execute()
                    st.success(f"🔥 ¡{nombre} agregada con éxito!")
                    time.sleep(1)
                    st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")
        else:
            st.warning("Por favor completa los campos principales.")

# ==========================================
# COLUMNA 2: MONITOR DE SLOTS ACTIVOS
# ==========================================
with col2:
    st.markdown("### 📊 Tus 15 Agencias Activas")
    try:
        agencias_res = supabase.table("agencias").select("*").execute()
        if agencias_res.data:
            for ag in agencias_res.data:
                # Traer los slots asociados a esta agencia específica
                slots_res = supabase.table("filtros_slots").select("marca, modelo").eq("agencia_id", ag["id"]).execute()
                slots_texto = ", ".join([f"{s['marca']} {s['modelo']}" for s in slots_res.data]) if slots_res.data else "Sin slots configurados"
                
                # Desplegable estético por agencia
                with st.expander(f"🏢 {ag['nombre'].upper()} - 📍 Región: {ag['region'].upper()} ({ag['whatsapp']})"):
                    st.write(f"**Slots activos:** {slots_texto}")
                    st.markdown("---")
                    st.write("🔹 **Agregar Slot (Análisis de Match - Máx 5)**")
                    
                    c1, c2, c3 = st.columns(3)
                    with c1: 
                        marca_in = st.text_input("Marca", key=f"marca_{ag['id']}", placeholder="Volkswagen")
                    with c2: 
                        modelo_in = st.text_input("Modelo", key=f"mod_{ag['id']}", placeholder="Gol")
                    with c3:
                        st.write(" ")  # Espaciador visual para alinear el botón
                        if st.button("Sumar Slot", key=f"btn_{ag['id']}"):
                            if len(slots_res.data) >= 5:
                                st.error("Ya tiene los 5 slots ocupados, pa.")
                            elif marca_in and modelo_in:
                                supabase.table("filtros_slots").insert({
                                    "agencia_id": ag["id"], 
                                    "marca": marca_in.strip(), 
                                    "modelo": modelo_in.strip()
                                }).execute()
                                st.success("¡Slot asignado!")
                                time.sleep(1)
                                st.rerun()
        else:
            st.info("Todavía no cargaste ninguna agencia.")
    except Exception as e:
        st.error(f"Error al leer datos de agencias: {e}")


# ==========================================
# SECCIÓN TIEMPO REAL (FRAGMENTADA)
# ==========================================
st.markdown("---")
st.markdown("## 🚨 Últimos Vehículos Detectados por el Radar")

# Usamos el decorador fragment con un tiempo de ejecución aislado para simular streaming real
@st.fragment(run_every=5)
def renderizar_tabla_tiempo_real():
    try:
        autos_res = supabase.table("vehiculos_detectados").select("*").order("created_at", desc=True).limit(10).execute()
        
        if autos_res.data:
            df = pd.DataFrame(autos_res.data)
            
            # Limpieza estética de columnas para el operador del panel
            if "anio" in df.columns:
                df = df.rename(columns={"anio": "Año"})
            
            # Mostrar tabla estilizada que ocupa todo el ancho
            st.dataframe(df, use_container_width=True)
            st.caption(f"🔄 Última sincronización automática del radar: {time.strftime('%H:%M:%S')}")
        else:
            st.info("Patrullando DeRuedas... esperando el próximo match.")
            
    except Exception as e:
        st.error(f"Error en el flujo del radar: {e}")

# Ejecutamos el componente de tiempo real aislado
renderizar_tabla_tiempo_real()


# ... todo tu código anterior ...

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Esto permite que tu frontend (JS) hable con el backend
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

@app.get("/mapeo-radar")
async def get_mapeo_radar():
    return {
        "status": "patrullando", 
        "data": [],
        "mensaje": "El radar está observando..."
    }
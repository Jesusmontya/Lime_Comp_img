from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image
import io
import os

# Inicializamos FastAPI con nombre profesional
app = FastAPI(title="LessImage API - Dev Group Studio")

# Configuramos CORS (Corregido para producción)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permite conexiones de tu dominio
    allow_credentials=False, # ¡AQUÍ ESTABA EL ERROR! Debe ser False si usas "*"
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- NUEVA RUTA: EL PUENTE HACIA TU FRONTEND ---
@app.get("/")
async def read_index():
    # Esta ruta le dice a FastAPI: "Si alguien entra a la raíz, dales el index.html"
    if os.path.exists('index.html'):
        return FileResponse('index.html')
    return {"mensaje": "El servidor de Dev Group Studio está activo, pero falta el archivo index.html"}

# --- RUTA DE COMPRESIÓN ORIGINAL ---
@app.post("/api/compress")
async def compress_image(
    file: UploadFile = File(...),
    quality: int = 60
):
    # 1. Validación de seguridad básica
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="El archivo no es una imagen válida.")

    try:
        # 2. Leemos la imagen cruda que manda el frontend a la memoria (RAM)
        image_data = await file.read()
        img = Image.open(io.BytesIO(image_data))

        # 3. Mantenemos la transparencia (RGBA). 
        # Convertimos solo si es una paleta rara para evitar errores, pero respetando el canal Alpha.
        if img.mode not in ("RGB", "RGBA"):
            img = img.convert("RGBA")

        # 4. Preparamos un buffer de memoria para guardar el resultado optimizado
        output_buffer = io.BytesIO()

        # 5. Magia de optimización: Convertimos a WebP
        img.save(output_buffer, format="WEBP", optimize=True, quality=quality)
        
        # Regresamos el "cursor" del buffer al inicio para poder leerlo y enviarlo
        output_buffer.seek(0)

        # 6. Enviamos la imagen procesada de vuelta al usuario para que se descargue
        return StreamingResponse(
            output_buffer, 
            media_type="image/webp",
            headers={"Content-Disposition": f"attachment; filename=lessimage_optimized.webp"}
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error procesando la imagen: {str(e)}")
    
    
# Código para correr el servidor si ejecutas este archivo directamente
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)

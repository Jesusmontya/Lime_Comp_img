from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
# IMPORTACIÓN AÑADIDA: ImageOps para manejar la rotación de los celulares
from PIL import Image, ImageOps 
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

# --- NUEVA RUTA: AUTORIZACIÓN PARA GOOGLE ADSENSE ---
@app.get("/ads.txt")
async def get_ads_txt():
    # Si Google busca tu archivo de autorización, se lo entregamos
    if os.path.exists("ads.txt"):
        return FileResponse("ads.txt")
    return {"error": "Archivo ads.txt no encontrado en el servidor"}

# --- RUTA: EL PUENTE HACIA TU FRONTEND ---
@app.get("/")
async def read_index():
    # Esta ruta le dice a FastAPI: "Si alguien entra a la raíz, dales el index.html"
    if os.path.exists('index.html'):
        return FileResponse('index.html')
    return {"mensaje": "El servidor de Dev Group Studio está activo, pero falta el archivo index.html"}

# --- RUTA DE COMPRESIÓN CORREGIDA Y MEJORADA ---
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

        # 3. CORRECCIÓN EXIF (MÓVILES):
        # Lee el sensor de orientación del celular y voltea la foto si es necesario
        img = ImageOps.exif_transpose(img)

        # 4. Mantenemos la transparencia (RGBA). 
        # Convertimos solo si es una paleta rara para evitar errores, pero respetando el canal Alpha.
        if img.mode not in ("RGB", "RGBA"):
            img = img.convert("RGBA")

        # 5. Preparamos un buffer de memoria para guardar el resultado optimizado
        output_buffer = io.BytesIO()

        # 6. Magia de optimización: Convertimos a WebP
        img.save(output_buffer, format="WEBP", optimize=True, quality=quality)
        
        # Regresamos el "cursor" del buffer al inicio para poder leerlo y enviarlo
        output_buffer.seek(0)

        # Extraemos el nombre original del archivo para que la descarga se vea más limpia
        filename_base = file.filename.split('.')[0] if file.filename else "optimizada"

        # 7. Enviamos la imagen procesada de vuelta al usuario para que se descargue
        return StreamingResponse(
            output_buffer, 
            media_type="image/webp",
            headers={"Content-Disposition": f"attachment; filename=lessimage_{filename_base}.webp"}
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error procesando la imagen: {str(e)}")
    
    
# Código para correr el servidor si ejecutas este archivo directamente
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)

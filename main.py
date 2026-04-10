from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image
import io

# Inicializamos FastAPI con nombre profesional
app = FastAPI(title="LessImage API - Dev Group Studio")

# Configuramos CORS (Crucial para que tu Frontend pueda hablar con el Backend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción pon aquí la URL de tu página
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/api/compress")
async def compress_image(
    file: UploadFile = File(...),
    # Aquí podríamos recibir el % de compresión que elija el usuario, por ahora lo fijamos en 60
    quality: int = 60
):
    # 1. Validación de seguridad básica
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="El archivo no es una imagen válida.")

    try:
        # 2. Leemos la imagen cruda que manda el frontend a la memoria (RAM)
        image_data = await file.read()
        img = Image.open(io.BytesIO(image_data))

        # Opcional: Convertir imágenes RGBA (con transparencia como los PNG) a RGB
        # porque los formatos más ligeros como JPEG no soportan transparencia
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")

        # 3. Preparamos un buffer de memoria para guardar el resultado optimizado
        output_buffer = io.BytesIO()

        # 4. Magia de optimización: 
        # Convertimos a WebP, que es el mejor formato para reducir peso manteniendo calidad
        img.save(output_buffer, format="WEBP", optimize=True, quality=quality)
        
        # Regresamos el "cursor" del buffer al inicio para poder leerlo y enviarlo
        output_buffer.seek(0)

        # 5. Enviamos la imagen procesada de vuelta al usuario para que se descargue
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
from fastapi import FastAPI, UploadFile, File, HTTPException, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import os
from typing import List
import shutil
from datetime import datetime
import json
from services import MediaProcessor
from database import get_db, MediaFile
from sqlalchemy.orm import Session
from fastapi import Depends

app = FastAPI(title="Media Search API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create upload directory if it doesn't exist
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

class MediaItem(BaseModel):
    id: int
    filename: str
    file_type: str
    transcription: str
    created_at: datetime

class ProcessingLog(BaseModel):
    stage: str
    message: str
    timestamp: datetime

@app.post("/upload")
async def upload_file(file: UploadFile = File(...), db: Session = Depends(get_db)):
    try:
        # Save the file
        file_path = os.path.join(UPLOAD_DIR, file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Initialize processor and process file
        processor = MediaProcessor()
        logs = []
        
        # Stage 1: File upload
        logs.append(ProcessingLog(
            stage="upload",
            message=f"Файл {file.filename} успешно загружен",
            timestamp=datetime.utcnow()
        ).dict())
        
        # Stage 2: Convert to MP3
        mp3_path = processor.convert_to_mp3(file_path, os.path.splitext(file_path)[0] + '.mp3')
        logs.append(ProcessingLog(
            stage="conversion",
            message="Аудио успешно конвертировано в MP3",
            timestamp=datetime.utcnow()
        ).dict())
        
        # Stage 3: Transcribe
        transcription = processor.transcribe_audio(mp3_path)
        logs.append(ProcessingLog(
            stage="transcription",
            message="Транскрипция успешно создана",
            timestamp=datetime.utcnow()
        ).dict())
        
        # Stage 4: Generate embeddings
        embeddings = processor.generate_embeddings(transcription)
        logs.append(ProcessingLog(
            stage="embeddings",
            message="Эмбеддинги успешно сгенерированы",
            timestamp=datetime.utcnow()
        ).dict())
        
        # Save to database
        media_file = MediaFile(
            filename=file.filename,
            file_type=file.content_type.split('/')[0],
            transcription=transcription,
            embeddings=embeddings
        )
        db.add(media_file)
        db.commit()
        
        logs.append(ProcessingLog(
            stage="database",
            message="Данные успешно сохранены в базу данных",
            timestamp=datetime.utcnow()
        ).dict())
        
        return JSONResponse(
            status_code=200,
            content={
                "message": f"File {file.filename} uploaded successfully",
                "logs": logs
            }
        )
    except Exception as e:
        logs.append(ProcessingLog(
            stage="error",
            message=f"Ошибка: {str(e)}",
            timestamp=datetime.utcnow()
        ).dict())
        raise HTTPException(status_code=500, detail={"error": str(e), "logs": logs})

@app.get("/search")
async def search(query: str, db: Session = Depends(get_db)):
    try:
        processor = MediaProcessor()
        media_files = db.query(MediaFile).all()
        embeddings_list = [file.embeddings for file in media_files]
        results_indices = processor.search_similar(query, embeddings_list)
        
        results = []
        for idx in results_indices:
            file = media_files[idx]
            results.append({
                "filename": file.filename,
                "transcription": file.transcription,
                "created_at": file.created_at
            })
            
        return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/media")
async def get_media(db: Session = Depends(get_db)):
    try:
        media_files = db.query(MediaFile).all()
        return {
            "media": [{
                "id": file.id,
                "filename": file.filename,
                "file_type": file.file_type,
                "transcription": file.transcription,
                "created_at": file.created_at
            } for file in media_files]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 
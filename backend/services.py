import os
from pydub import AudioSegment
import torch
from transformers import pipeline
from sentence_transformers import SentenceTransformer
import json
import numpy as np

class MediaProcessor:
    def __init__(self):
        # Initialize the transcription pipeline
        self.transcriber = pipeline(
            "automatic-speech-recognition",
            model="openai/whisper-base",
            device="cuda" if torch.cuda.is_available() else "cpu"
        )
        
        # Initialize the embeddings model
        self.embeddings_model = SentenceTransformer('all-MiniLM-L6-v2')

    def convert_to_mp3(self, input_path: str, output_path: str) -> str:
        """Convert audio/video file to MP3 format"""
        audio = AudioSegment.from_file(input_path)
        audio.export(output_path, format="mp3")
        return output_path

    def transcribe_audio(self, audio_path: str) -> str:
        """Transcribe audio file to text"""
        result = self.transcriber(audio_path)
        return result["text"]

    def generate_embeddings(self, text: str) -> str:
        """Generate embeddings for the given text"""
        embeddings = self.embeddings_model.encode(text)
        return json.dumps(embeddings.tolist())

    def process_media_file(self, file_path: str) -> tuple[str, str]:
        """Process media file: convert to MP3, transcribe, and generate embeddings"""
        # Convert to MP3 if needed
        if not file_path.endswith('.mp3'):
            mp3_path = os.path.splitext(file_path)[0] + '.mp3'
            self.convert_to_mp3(file_path, mp3_path)
        else:
            mp3_path = file_path

        # Transcribe audio
        transcription = self.transcribe_audio(mp3_path)

        # Generate embeddings
        embeddings = self.generate_embeddings(transcription)

        return transcription, embeddings

    def search_similar(self, query: str, embeddings_list: list[str], threshold: float = 0.7) -> list[int]:
        """Search for similar content using embeddings"""
        query_embedding = self.embeddings_model.encode(query)
        results = []
        
        for idx, emb_str in enumerate(embeddings_list):
            emb = np.array(json.loads(emb_str))
            similarity = np.dot(query_embedding, emb) / (np.linalg.norm(query_embedding) * np.linalg.norm(emb))
            if similarity > threshold:
                results.append(idx)
        
        return results 
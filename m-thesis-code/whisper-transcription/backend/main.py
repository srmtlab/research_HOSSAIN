from fastapi import FastAPI, File, UploadFile, HTTPException
from pydantic import BaseModel
from contextlib import asynccontextmanager
from faster_whisper import WhisperModel
import tempfile
import openai
from pathlib import Path
from typing import List, Dict
from fastapi.responses import JSONResponse
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)

# Set OpenAI API Key
client = openai.OpenAI(api_key="sk-proj-##################961FgJ")

class AudioRequest(BaseModel):
    audio_path: str

class TextRequest(BaseModel):
    text: str

@asynccontextmanager
async def lifespan(app: FastAPI):
    global model
    model_size = "large-v3"  # Adjust model size as needed
    model = WhisperModel(model_size, device="cpu", compute_type="int8")
    yield

app = FastAPI(lifespan=lifespan)

@app.post("/transcript")
async def transcribe_file(file: UploadFile):
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as temp_audio:
            temp_audio.write(await file.read())
            temp_audio_path = temp_audio.name
        
        segments, _ = model.transcribe(temp_audio_path)
        transcript_text = " ".join(segment.text for segment in segments)
        
        return JSONResponse(content={"transcription": transcript_text})
    except Exception as e:
        logging.error(f"Transcription failed: {e}")
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")

@app.post("/generate-response")
async def generate_openai_response(request: TextRequest):
    try:
        messages: List[Dict[str, str]] = [
            {"role": "system", "content": "You are an assistant that provides helpful responses."},
            {"role": "user", "content": request.text}
        ]
        
        logging.info(f"Sending messages to OpenAI API: {messages}")
        
        response = client.chat.completions.create(
            model="gpt-4",
            messages=messages,
            temperature=0.7
        )
        
        logging.info(f"OpenAI API response: {response}")
        
        return response.choices[0].message.content
    except openai.APIError as e:
        logging.error(f"OpenAI API error: {e}")
        raise HTTPException(status_code=500, detail=f"OpenAI API error: {str(e)}")
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

@app.post("/meeting_summary")
async def summarize_text(request: TextRequest):
    try:
        messages = [
            {"role": "system", "content": "You are an AI that summarizes meeting transcripts and also provides an emotional analysis. Your summaries should include any detected signs of stress, urgency, or emotional intensity in the conversation."},
            {"role": "user", "content": f"Summarize this meeting transcript and analyze the emotional tone, especially if there are signs of stress or urgency: {request.text}"}
        ]
        
        logging.info(f"Sending summary request to OpenAI API: {messages}")
        
        response = client.chat.completions.create(
            model="gpt-4",
            messages=messages,
            temperature=0.5
        )
        
        logging.info(f"OpenAI API summary response: {response}")
        
        return response.choices[0].message.content  # Returning plain text instead of JSON
    except openai.APIError as e:
        logging.error(f"OpenAI API error: {e}")
        raise HTTPException(status_code=500, detail=f"OpenAI API error: {str(e)}")
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

@app.get("/")
def home():
    return {"message": "API is running"}

import os
import base64
import json
import re
import google.generativeai as genai
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

app = FastAPI(title="Cosmetica API", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=[
                   "*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

frontend_path = os.path.join(os.path.dirname(__file__), "..", "frontend")
app.mount("/static", StaticFiles(directory=os.path.join(frontend_path,
          "static")), name="static")
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))


def clean_json(text):
    text = text.strip()
    text = re.sub(r'^```(?:json)?\s*', '', text)
    text = re.sub(r'\s*```$', '', text)
    return text.strip()


@app.get("/")
async def serve_frontend():
    return FileResponse(os.path.join(frontend_path, "index.html"))


@app.post("/api/analyze-product")
async def analyze_product(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        content_type = file.content_type or "image/jpeg"
        if content_type not in ["image/jpeg", "image/png", "image/gif", "image/webp"]:
            content_type = "image/jpeg"
        image_part = {"mime_type": content_type, "data": contents}
        prompt = """You are an expert cosmetic chemist and safety analyst. Analyze this cosmetic product image carefully. Respond ONLY with a valid JSON object (no markdown, no code blocks, just raw JSON):
{"product_name":"Full product name and brand","safety_score":85,"safety_rating":"Good","is_vegan":true,"is_cruelty_free":true,"ingredients":[{"name":"ingredient name","purpose":"what it does","safety":"Safe","concern":"","is_toxic":false}],"concerns":["concern 1"],"benefits":["benefit 1"],"skin_types":["All skin types"],"summary":"2-3 sentence overall analysis.","recommendation":"Clear recommendation for users"}
Safety score: 90-100=Excellent, 70-89=Good, 50-69=Fair, 30-49=Poor, 0-29=Dangerous. Be thorough and analyze all visible ingredients."""
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content([prompt, image_part])
        return json.loads(clean_json(response.text))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/shade-match")
async def shade_match(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        content_type = file.content_type or "image/jpeg"
        if content_type not in ["image/jpeg", "image/png", "image/gif", "image/webp"]:
            content_type = "image/jpeg"
        image_part = {"mime_type": content_type, "data": contents}
        prompt = """You are an expert makeup artist. Analyze this person's skin tone. Respond ONLY with valid JSON (no markdown):
{"undertone":"Warm","skin_tone":"Medium","recommended_shades":[{"brand":"MAC","product":"Studio Fix Fluid","shade":"NC35","match_quality":"Perfect"}],"foundation_range":"Look for NC/NW shades in the 30-40 range","tips":["Tip 1","Tip 2","Tip 3"],"summary":"Personalized skin tone analysis"}
Include 5-6 shades from MAC, Fenty Beauty, NARS, Maybelline, L'Oreal."""
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content([prompt, image_part])
        return json.loads(clean_json(response.text))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/health")
async def health():
    return {"status": "ok", "service": "Cosmetica API"}

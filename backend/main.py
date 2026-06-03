import os
import base64
import json
import re
import google.generativeai as genai
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from google.generativeai.types import HarmCategory, HarmBlockThreshold

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=[
                   "*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
frontend_path = os.path.join(os.path.dirname(__file__), "..", "frontend")
app.mount("/static", StaticFiles(directory=os.path.join(frontend_path,
          "static")), name="static")

api_key = os.environ.get("GEMINI_API_KEY")
print(f"GEMINI_API_KEY present: {bool(api_key)}")
genai.configure(api_key=api_key)


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
        b64 = base64.b64encode(contents).decode("utf-8")
        prompt = """You are an expert cosmetic chemist. Analyze this cosmetic product image.
Respond ONLY with raw JSON, no markdown, no code blocks:
{"product_name":"Brand Product Name","safety_score":75,"safety_rating":"Good","is_vegan":true,"is_cruelty_free":true,"ingredients":[{"name":"Water","purpose":"Solvent","safety":"Safe","concern":"","is_toxic":false}],"concerns":["example concern"],"benefits":["example benefit"],"skin_types":["All skin types"],"summary":"Brief analysis here.","recommendation":"Recommendation here."}
Safety score guide: 90-100=Excellent, 70-89=Good, 50-69=Fair, 30-49=Poor, 0-29=Dangerous. Analyze ALL visible ingredients thoroughly."""
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content([
            prompt,
            {"mime_type": content_type, "data": b64}
        ])
        print("Gemini response:", response.text[:200])
        return json.loads(clean_json(response.text))
    except Exception as e:
        import traceback
        print("ERROR:", traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/shade-match")
async def shade_match(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        content_type = file.content_type or "image/jpeg"
        if content_type not in ["image/jpeg", "image/png", "image/gif", "image/webp"]:
            content_type = "image/jpeg"
        b64 = base64.b64encode(contents).decode("utf-8")
        prompt = """You are an expert makeup artist. Analyze this person's skin tone.
Respond ONLY with raw JSON, no markdown, no code blocks:
{"undertone":"Warm","skin_tone":"Medium","recommended_shades":[{"brand":"MAC","product":"Studio Fix Fluid","shade":"NC35","match_quality":"Perfect"},{"brand":"Fenty Beauty","product":"Pro Filt'r","shade":"240W","match_quality":"Perfect"},{"brand":"NARS","product":"Natural Radiant Longwear","shade":"Syracuse","match_quality":"Great"},{"brand":"Maybelline","product":"Fit Me Matte","shade":"220 Natural Beige","match_quality":"Great"},{"brand":"L'Oreal","product":"True Match","shade":"W3 Warm Beige","match_quality":"Good"}],"foundation_range":"Look for medium shades with warm undertones","tips":["Tip 1","Tip 2","Tip 3"],"summary":"Your skin tone analysis here."}"""
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content([
            prompt,
            {"mime_type": content_type, "data": b64}
        ])
        print("Gemini response:", response.text[:200])
        return json.loads(clean_json(response.text))
    except Exception as e:
        import traceback
        print("ERROR:", traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/health")
async def health():
    return {"status": "ok"}

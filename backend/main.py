import os
import base64
import json
import re
import requests
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=[
                   "*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
frontend_path = os.path.join(os.path.dirname(__file__), "..", "frontend")
app.mount("/static", StaticFiles(directory=os.path.join(frontend_path,
          "static")), name="static")


def clean_json(text):
    text = text.strip()
    text = re.sub(r'^```(?:json)?\s*', '', text)
    text = re.sub(r'\s*```$', '', text)
    return text.strip()


def call_openrouter(prompt, b64_image, content_type):
    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {os.environ.get('OPENROUTER_API_KEY')}",
            "Content-Type": "application/json"
        },
        json={
            "model": "google/gemma-4-31b-it:free",
            "messages": [{
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {
                        "url": f"data:{content_type};base64,{b64_image}"}}
                ]
            }],
            "max_tokens": 2000
        },
        timeout=60
    )
    data = response.json()
    print("OpenRouter full response:", json.dumps(data)[:500])
    if "error" in data:
        raise Exception(f"OpenRouter error: {data['error']}")
    if "choices" not in data:
        raise Exception(f"Unexpected response: {json.dumps(data)[:200]}")
    return data["choices"][0]["message"]["content"]


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
        prompt = """You are an expert cosmetic chemist and safety analyst. Analyze this cosmetic product image carefully.
Respond ONLY with raw JSON, no markdown, no code blocks:
{"product_name":"Brand Product Name","safety_score":75,"safety_rating":"Good","is_vegan":true,"is_cruelty_free":true,"ingredients":[{"name":"Water","purpose":"Solvent base","safety":"Safe","concern":"","is_toxic":false},{"name":"Glycerin","purpose":"Moisturizer","safety":"Safe","concern":"","is_toxic":false}],"concerns":["example concern"],"benefits":["example benefit"],"skin_types":["All skin types"],"summary":"Brief 2-3 sentence analysis.","recommendation":"Clear recommendation for users."}
Safety score: 90-100=Excellent, 70-89=Good, 50-69=Fair, 30-49=Poor, 0-29=Dangerous. Analyze ALL visible ingredients."""
        text = call_openrouter(prompt, b64, content_type)
        return json.loads(clean_json(text))
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
        prompt = """You are an expert makeup artist. Analyze this person's skin tone from the image.
Respond ONLY with raw JSON, no markdown, no code blocks:
{"undertone":"Warm","skin_tone":"Medium","recommended_shades":[{"brand":"MAC","product":"Studio Fix Fluid","shade":"NC35","match_quality":"Perfect"},{"brand":"Fenty Beauty","product":"Pro Filt'r Soft Matte","shade":"240W","match_quality":"Perfect"},{"brand":"NARS","product":"Natural Radiant Longwear","shade":"Syracuse","match_quality":"Great"},{"brand":"Maybelline","product":"Fit Me Matte","shade":"220 Natural Beige","match_quality":"Great"},{"brand":"L'Oreal","product":"True Match","shade":"W3 Warm Beige","match_quality":"Good"}],"foundation_range":"Medium shades with warm undertones","tips":["Tip 1","Tip 2","Tip 3"],"summary":"Personalized skin tone analysis."}
Include 5-6 shades from popular brands."""
        text = call_openrouter(prompt, b64, content_type)
        return json.loads(clean_json(text))
    except Exception as e:
        import traceback
        print("ERROR:", traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/health")
async def health():
    return {"status": "ok"}

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
            "model": "openrouter/free",
            "messages": [{
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {
                        "url": f"data:{content_type};base64,{b64_image}"}}
                ]
            }],
            "max_tokens": 2500
        },
        timeout=60
    )
    data = response.json()
    print("OpenRouter response:", json.dumps(data)[:300])
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
        prompt = """You are an expert professional makeup artist. Analyze this person's skin tone, undertone, and features from the image.
Respond ONLY with raw JSON, no markdown, no code blocks:
{
  "undertone": "Warm",
  "skin_tone": "Medium",
  "summary": "Personalized skin tone analysis in 2 sentences.",
  "foundation": [
    {"brand":"MAC","product":"Studio Fix Fluid","shade":"NC35","match_quality":"Perfect"},
    {"brand":"Fenty Beauty","product":"Pro Filt'r Soft Matte","shade":"240W","match_quality":"Perfect"},
    {"brand":"Maybelline","product":"Fit Me Matte","shade":"220 Natural Beige","match_quality":"Great"},
    {"brand":"L'Oreal","product":"True Match","shade":"W3 Warm Beige","match_quality":"Good"}
  ],
  "concealer": [
    {"brand":"NARS","product":"Radiant Creamy Concealer","shade":"Caramel","match_quality":"Perfect"},
    {"brand":"Maybelline","product":"Fit Me Concealer","shade":"25 Medium","match_quality":"Great"}
  ],
  "blush": [
    {"brand":"NARS","product":"Blush","shade":"Orgasm","match_quality":"Perfect"},
    {"brand":"Rare Beauty","product":"Soft Pinch Liquid Blush","shade":"Joy","match_quality":"Great"}
  ],
  "bronzer": [
    {"brand":"Too Faced","product":"Chocolate Soleil","shade":"Medium Deep","match_quality":"Perfect"},
    {"brand":"Fenty Beauty","product":"Sun Stalkr Bronzer","shade":"Caramel Honeysnap","match_quality":"Great"}
  ],
  "eyeshadow": [
    {"brand":"Urban Decay","product":"Naked3 Palette","shade":"Rose tones","match_quality":"Perfect"},
    {"brand":"Charlotte Tilbury","product":"Luxury Palette","shade":"The Dolce Vita","match_quality":"Great"}
  ],
  "lipcolour": [
    {"brand":"MAC","product":"Matte Lipstick","shade":"Velvet Teddy","match_quality":"Perfect"},
    {"brand":"Charlotte Tilbury","product":"Matte Revolution","shade":"Pillow Talk","match_quality":"Perfect"},
    {"brand":"NYX","product":"Soft Matte Lip Cream","shade":"Rome","match_quality":"Great"}
  ],
  "highlighter": [
    {"brand":"Fenty Beauty","product":"Killawatt Highlighter","shade":"Mean Money","match_quality":"Perfect"},
    {"brand":"Becca","product":"Shimmering Skin Perfector","shade":"Champagne Pop","match_quality":"Great"}
  ],
  "tips": [
    "Tip 1 specific to this skin tone",
    "Tip 2 specific to this skin tone",
    "Tip 3 specific to this skin tone",
    "Tip 4 specific to this skin tone"
  ]
}
Be accurate and specific to the person's actual skin tone in the image."""
        text = call_openrouter(prompt, b64, content_type)
        return json.loads(clean_json(text))
    except Exception as e:
        import traceback
        print("ERROR:", traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/alternatives")
async def find_alternatives(
    product_name: str = Form(...),
    safety_rating: str = Form(...),
    min_price: str = Form(...),
    max_price: str = Form(...)
):
    try:
        prompt = f"""You are a cosmetic product expert. The user has a product called "{product_name}" with safety rating "{safety_rating}".
Suggest 4-5 safer alternative products within price range ₹{min_price} to ₹{max_price}.
Respond ONLY with raw JSON, no markdown:
{{"alternatives":[{{"name":"Product Name","brand":"Brand","price":"₹299","safety_rating":"Excellent","why_better":"reason it is safer","where_to_buy":"Nykaa / Amazon / Flipkart"}}]}}
Be specific with real Indian market products. Only suggest products genuinely available in India in that price range."""

        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {os.environ.get('OPENROUTER_API_KEY')}",
                "Content-Type": "application/json"
            },
            json={
                "model": "openrouter/free",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 1000
            },
            timeout=60
        )
        data = response.json()
        if "error" in data:
            raise Exception(f"OpenRouter error: {data['error']}")
        text = data["choices"][0]["message"]["content"]
        return json.loads(clean_json(text))
    except Exception as e:
        import traceback
        print("ERROR:", traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/health")
async def health():
    return {"status": "ok"}

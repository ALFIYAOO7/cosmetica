import os
import base64
import json
import re
from openai import OpenAI
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


def get_client():
    return OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=os.environ.get("OPENROUTER_API_KEY"),
    )


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
        data_url = f"data:{content_type};base64,{b64}"

        prompt = """You are an expert cosmetic chemist and safety analyst. Analyze this cosmetic product image carefully.
Respond ONLY with raw JSON, no markdown, no code blocks, exactly this structure:
{"product_name":"Brand Product Name","safety_score":75,"safety_rating":"Good","is_vegan":true,"is_cruelty_free":true,"ingredients":[{"name":"Water","purpose":"Solvent base","safety":"Safe","concern":"","is_toxic":false},{"name":"Glycerin","purpose":"Moisturizer","safety":"Safe","concern":"","is_toxic":false}],"concerns":["example concern"],"benefits":["example benefit"],"skin_types":["All skin types"],"summary":"Brief 2-3 sentence analysis here.","recommendation":"Clear recommendation for users."}
Safety score: 90-100=Excellent, 70-89=Good, 50-69=Fair, 30-49=Poor, 0-29=Dangerous. Analyze ALL visible ingredients."""

        client = get_client()
        response = client.chat.completions.create(
            model="google/gemini-2.0-flash-exp:free",
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": data_url}}
                ]
            }],
            max_tokens=2000
        )
        text = response.choices[0].message.content
        print("Response:", text[:200])
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
        data_url = f"data:{content_type};base64,{b64}"

        prompt = """You are an expert makeup artist and color analyst. Analyze this person's skin tone from the image.
Respond ONLY with raw JSON, no markdown, no code blocks, exactly this structure:
{"undertone":"Warm","skin_tone":"Medium","recommended_shades":[{"brand":"MAC","product":"Studio Fix Fluid","shade":"NC35","match_quality":"Perfect"},{"brand":"Fenty Beauty","product":"Pro Filt'r Soft Matte","shade":"240W","match_quality":"Perfect"},{"brand":"NARS","product":"Natural Radiant Longwear","shade":"Syracuse","match_quality":"Great"},{"brand":"Maybelline","product":"Fit Me Matte + Poreless","shade":"220 Natural Beige","match_quality":"Great"},{"brand":"L'Oreal","product":"True Match","shade":"W3 Warm Beige","match_quality":"Good"}],"foundation_range":"Look for medium shades with warm undertones in the NC30-40 range","tips":["Use a peach-toned concealer to brighten under eyes","Warm bronzers complement your undertone beautifully","Avoid foundations with pink undertones as they can look ashy"],"summary":"Your personalized skin tone analysis here."}
Include 5-6 shades from popular brands. Be specific and accurate."""

        client = get_client()
        response = client.chat.completions.create(
            model="google/gemini-2.0-flash-exp:free",
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": data_url}}
                ]
            }],
            max_tokens=1500
        )
        text = response.choices[0].message.content
        print("Response:", text[:200])
        return json.loads(clean_json(text))
    except Exception as e:
        import traceback
        print("ERROR:", traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/health")
async def health():
    return {"status": "ok"}

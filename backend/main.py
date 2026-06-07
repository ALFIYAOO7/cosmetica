import os
import base64
import json
import re
import requests
from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=[
                   "*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
frontend_path = os.path.join(os.path.dirname(
    os.path.abspath(__file__)), "..", "frontend")
static_path = os.path.join(os.path.dirname(
    os.path.abspath(__file__)), "..", "frontend", "static")
app.mount("/static", StaticFiles(directory=static_path), name="static")


def clean_json(text):
    text = text.strip()
    text = re.sub(r'^```(?:json)?\s*', '', text)
    text = re.sub(r'\s*```$', '', text)
    return text.strip()


def call_groq(prompt):
    response = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {os.environ.get('GROQ_API_KEY')}", "Content-Type": "application/json"},
        json={"model": "llama-3.3-70b-versatile", "messages": [
            {"role": "user", "content": prompt}], "max_tokens": 2000, "temperature": 0.3},
        timeout=60
    )
    data = response.json()
    print("Groq response:", json.dumps(data)[:300])
    if "error" in data:
        raise Exception(f"Groq error: {data['error']}")
    return data["choices"][0]["message"]["content"]


def call_hf_vision(b64_image):
    image_bytes = base64.b64decode(b64_image)
    response = requests.post(
        "https://api-inference.huggingface.co/models/Salesforce/blip-image-captioning-large",
        headers={"Authorization": f"Bearer {os.environ.get('HF_API_KEY')}"},
        data=image_bytes,
        timeout=60
    )
    result = response.json()
    print("HF response:", str(result)[:300])
    if isinstance(result, list) and len(result) > 0:
        return result[0].get("generated_text", "a person with medium skin tone")
    return "a person with medium skin tone"


@app.get("/")
async def serve_frontend():
    return FileResponse(os.path.join(frontend_path, "index.html"))


@app.post("/api/analyze-product")
async def analyze_product(product_name: str = Form(...)):
    try:
        prompt = f"""You are an expert cosmetic chemist and safety analyst. Analyze the cosmetic product: "{product_name}"
Respond ONLY with raw JSON, no markdown, no code blocks:
{{"product_name":"{product_name}","safety_score":75,"safety_rating":"Good","is_vegan":true,"is_cruelty_free":true,"ingredients":[{{"name":"Water","purpose":"Solvent base","safety":"Safe","concern":"","is_toxic":false}},{{"name":"Glycerin","purpose":"Moisturizer","safety":"Safe","concern":"","is_toxic":false}}],"concerns":["example concern"],"benefits":["example benefit"],"skin_types":["All skin types"],"summary":"Brief 2-3 sentence analysis.","recommendation":"Clear recommendation for users."}}
Safety score: 90-100=Excellent, 70-89=Good, 50-69=Fair, 30-49=Poor, 0-29=Dangerous. Be thorough and accurate."""
        text = call_groq(prompt)
        return json.loads(clean_json(text))
    except Exception as e:
        import traceback
        print("ERROR:", traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/shade-match")
async def shade_match(file: UploadFile = File(...), category: str = Form("full")):
    try:
        contents = await file.read()
        content_type = file.content_type or "image/jpeg"
        if content_type not in ["image/jpeg", "image/png", "image/gif", "image/webp"]:
            content_type = "image/jpeg"
        b64 = base64.b64encode(contents).decode("utf-8")
        image_description = "a person's face for skin tone analysis"
        category_prompts = {
            "foundation": "ONLY recommend foundation shades. Only include 'foundation' array.",
            "lipcolour": "ONLY recommend lip colours. Only include 'lipcolour' array.",
            "eyeshadow": "ONLY recommend eyeshadow. Only include 'eyeshadow' array.",
            "blush": "ONLY recommend blush and bronzer. Only include 'blush' and 'bronzer' arrays.",
            "concealer": "ONLY recommend concealer. Only include 'concealer' array.",
            "full": "Recommend ALL categories."
        }
        cat_instruction = category_prompts.get(
            category, category_prompts["full"])
        prompt = f"""You are an expert professional makeup artist. Based on this image description: "{image_description}"
Analyze the person's skin tone and undertone. {cat_instruction}
Respond ONLY with raw JSON, no markdown:
{{"undertone":"Warm","skin_tone":"Medium","summary":"2 sentence personalized analysis.","foundation":[{{"brand":"MAC","product":"Studio Fix","shade":"NC35","match_quality":"Perfect"}}],"concealer":[{{"brand":"NARS","product":"Radiant Creamy","shade":"Caramel","match_quality":"Perfect"}}],"blush":[{{"brand":"NARS","product":"Blush","shade":"Orgasm","match_quality":"Perfect"}}],"bronzer":[{{"brand":"Too Faced","product":"Chocolate Soleil","shade":"Medium","match_quality":"Perfect"}}],"eyeshadow":[{{"brand":"Urban Decay","product":"Naked3","shade":"Rose tones","match_quality":"Perfect"}}],"lipcolour":[{{"brand":"MAC","product":"Matte Lipstick","shade":"Velvet Teddy","match_quality":"Perfect"}}],"highlighter":[{{"brand":"Fenty Beauty","product":"Killawatt","shade":"Mean Money","match_quality":"Perfect"}}],"tips":["Tip 1","Tip 2","Tip 3"]}}
Only populate arrays for the requested category. Give 4-5 real product recommendations."""
        text = call_groq(prompt)
        return json.loads(clean_json(text))
    except Exception as e:
        import traceback
        print("ERROR:", traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/alternatives")
async def find_alternatives(product_name: str = Form(...), safety_rating: str = Form(...), min_price: str = Form(...), max_price: str = Form(...)):
    try:
        prompt = f"""You are a cosmetic product expert. The user has "{product_name}" with safety rating "{safety_rating}".
Suggest 4-5 safer alternatives within ₹{min_price} to ₹{max_price} available in India.
Respond ONLY with raw JSON, no markdown:
{{"alternatives":[{{"name":"Product Name","brand":"Brand","price":"₹299","safety_rating":"Excellent","why_better":"reason","where_to_buy":"Nykaa / Amazon"}}]}}"""
        text = call_groq(prompt)
        return json.loads(clean_json(text))
    except Exception as e:
        import traceback
        print("ERROR:", traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/health")
async def health():
    return {"status": "ok"}

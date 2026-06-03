import os
import base64
import json
import re
import anthropic
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional

app = FastAPI(title="Cosmetica API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve frontend static files
frontend_path = os.path.join(os.path.dirname(__file__), "..", "frontend")
app.mount("/static", StaticFiles(directory=os.path.join(frontend_path, "static")), name="static")

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

class AnalysisResult(BaseModel):
    product_name: str
    safety_score: int
    safety_rating: str
    is_vegan: bool
    is_cruelty_free: bool
    ingredients: list
    concerns: list
    benefits: list
    skin_types: list
    summary: str
    recommendation: str

class ShadeResult(BaseModel):
    undertone: str
    skin_tone: str
    recommended_shades: list
    foundation_range: str
    tips: list
    summary: str


@app.get("/")
async def serve_frontend():
    return FileResponse(os.path.join(frontend_path, "index.html"))


@app.post("/api/analyze-product")
async def analyze_product(file: UploadFile = File(...)):
    """Analyze a cosmetic product image for safety, ingredients, toxicity, etc."""
    try:
        contents = await file.read()
        base64_image = base64.standard_b64encode(contents).decode("utf-8")

        # Determine media type
        content_type = file.content_type or "image/jpeg"
        if content_type not in ["image/jpeg", "image/png", "image/gif", "image/webp"]:
            content_type = "image/jpeg"

        prompt = """You are an expert cosmetic chemist and safety analyst. Analyze this cosmetic product image carefully.

Look at the ingredients list, product name, brand, and any visible information on the packaging.

Respond ONLY with a valid JSON object (no markdown, no code blocks, just raw JSON) with exactly this structure:
{
  "product_name": "Full product name and brand",
  "safety_score": <integer 0-100>,
  "safety_rating": "<one of: Excellent, Good, Fair, Poor, Dangerous>",
  "is_vegan": <true/false>,
  "is_cruelty_free": <true/false>,
  "ingredients": [
    {
      "name": "ingredient name",
      "purpose": "what it does",
      "safety": "<Safe/Caution/Avoid>",
      "concern": "any concern or empty string",
      "is_toxic": <true/false>
    }
  ],
  "concerns": ["concern 1", "concern 2"],
  "benefits": ["benefit 1", "benefit 2"],
  "skin_types": ["suitable skin type 1", "suitable skin type 2"],
  "summary": "2-3 sentence overall analysis",
  "recommendation": "Clear recommendation for users"
}

Be thorough. If you can see an ingredient list, analyze each ingredient. If no ingredients are visible, analyze based on product type and brand reputation. Safety score: 90-100=Excellent, 70-89=Good, 50-69=Fair, 30-49=Poor, 0-29=Dangerous."""

        message = client.messages.create(
            model="claude-opus-4-5",
            max_tokens=2000,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": content_type,
                                "data": base64_image,
                            },
                        },
                        {"type": "text", "text": prompt},
                    ],
                }
            ],
        )

        response_text = message.content[0].text.strip()

        # Clean up response - remove any markdown if present
        response_text = re.sub(r'^```(?:json)?\s*', '', response_text)
        response_text = re.sub(r'\s*```$', '', response_text)
        response_text = response_text.strip()

        result = json.loads(response_text)
        return result

    except json.JSONDecodeError as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse AI response: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/shade-match")
async def shade_match(file: UploadFile = File(...)):
    """Analyze a person's skin tone for shade matching recommendations."""
    try:
        contents = await file.read()
        base64_image = base64.standard_b64encode(contents).decode("utf-8")

        content_type = file.content_type or "image/jpeg"
        if content_type not in ["image/jpeg", "image/png", "image/gif", "image/webp"]:
            content_type = "image/jpeg"

        prompt = """You are an expert makeup artist and color analyst. Analyze this person's skin tone from the image.

Provide personalized shade matching recommendations.

Respond ONLY with a valid JSON object (no markdown, no code blocks, just raw JSON) with exactly this structure:
{
  "undertone": "<Warm/Cool/Neutral/Olive>",
  "skin_tone": "<Fair/Light/Light-Medium/Medium/Medium-Tan/Tan/Deep/Rich>",
  "recommended_shades": [
    {
      "brand": "Brand name",
      "product": "Product name",
      "shade": "Shade name/number",
      "match_quality": "<Perfect/Great/Good>"
    }
  ],
  "foundation_range": "Description of the foundation undertone range that works",
  "tips": [
    "Tip 1 for this skin tone",
    "Tip 2 for this skin tone",
    "Tip 3 for this skin tone"
  ],
  "summary": "Personalized analysis of this person's skin tone and what works best"
}

Include 5-6 recommended shades from popular brands like MAC, Fenty Beauty, NARS, Maybelline, L'Oreal. Be specific and helpful."""

        message = client.messages.create(
            model="claude-opus-4-5",
            max_tokens=1500,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": content_type,
                                "data": base64_image,
                            },
                        },
                        {"type": "text", "text": prompt},
                    ],
                }
            ],
        )

        response_text = message.content[0].text.strip()
        response_text = re.sub(r'^```(?:json)?\s*', '', response_text)
        response_text = re.sub(r'\s*```$', '', response_text)
        response_text = response_text.strip()

        result = json.loads(response_text)
        return result

    except json.JSONDecodeError as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse AI response: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/health")
async def health():
    return {"status": "ok", "service": "Cosmetica API"}

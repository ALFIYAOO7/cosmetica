# ✦ Cosmetica

> AI-powered cosmetic safety checker & shade matching — built with FastAPI + Claude AI

---

## What It Does

- **Product Safety Scan** — Upload or photograph any cosmetic product. Cosmetica decodes every ingredient, flags toxins, checks vegan/cruelty-free status, and assigns a safety score (0–100).
- **Shade Match** — Upload a selfie or take one live. The AI reads your skin tone and undertone, then recommends exact shades from MAC, Fenty Beauty, NARS, Maybelline, L'Oreal, and more.

---

## Tech Stack

| Layer     | Tech                          |
|-----------|-------------------------------|
| Frontend  | HTML, CSS, Vanilla JS         |
| Backend   | Python 3.11 + FastAPI         |
| AI        | Anthropic Claude (vision API) |
| Deploy    | Railway (recommended)         |

---

## Local Setup

### 1. Clone and enter the project

```bash
git clone <your-repo-url>
cd cosmetica
```

### 2. Create a virtual environment

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r backend/requirements.txt
```

### 4. Set your API key

```bash
cp .env.example .env
# Edit .env and add your Anthropic API key
```

Get your API key at: https://console.anthropic.com

### 5. Run the server

```bash
uvicorn backend.main:app --reload --port 8000
```

Open http://localhost:8000 — done!

---

## Deploy to Railway (Recommended — Free Tier Available)

Railway is the easiest one-click deploy for this stack.

### Steps

1. **Push to GitHub**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin https://github.com/YOUR_USERNAME/cosmetica.git
   git push -u origin main
   ```

2. **Create a Railway project**
   - Go to https://railway.app
   - Click **New Project → Deploy from GitHub repo**
   - Select your repository

3. **Add environment variable**
   - In your Railway project → **Variables** tab
   - Add: `ANTHROPIC_API_KEY` = your key

4. **Deploy** — Railway auto-detects Python and deploys. Your site is live in ~2 minutes.

---

## Deploy to Render (Alternative — Also Free)

1. Go to https://render.com → New Web Service
2. Connect your GitHub repo
3. Set:
   - **Build command**: `pip install -r backend/requirements.txt`
   - **Start command**: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
4. Add environment variable: `ANTHROPIC_API_KEY`

---

## Project Structure

```
cosmetica/
├── backend/
│   ├── main.py              # FastAPI app + API routes
│   └── requirements.txt     # Python dependencies
├── frontend/
│   ├── index.html           # Main HTML
│   └── static/
│       ├── css/style.css    # All styles
│       └── js/app.js        # All frontend logic
├── .env.example             # Environment variable template
├── .gitignore
├── Procfile                 # Heroku/Railway process file
├── railway.json             # Railway config
├── runtime.txt              # Python version
└── README.md
```

---

## API Endpoints

| Method | Path                  | Description                          |
|--------|-----------------------|--------------------------------------|
| GET    | `/`                   | Serves the frontend                  |
| POST   | `/api/analyze-product`| Analyse cosmetic product image       |
| POST   | `/api/shade-match`    | Analyse skin tone from selfie        |
| GET    | `/api/health`         | Health check                         |

---

## Notes

- Images are processed in memory — nothing is stored or logged
- Analysis accuracy depends on image clarity and visible ingredient list
- For best shade matching, use a photo in natural daylight without heavy makeup
- Results are informational only — consult a dermatologist for medical advice

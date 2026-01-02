# 🚀 Deployment Guide - Indonesische Recepten

Deze gids helpt je bij het deployen van de Indonesische Recepten app naar Vercel (frontend) en Render (backend).

## 📋 Vereisten

- GitHub repository
- Neo4j Aura database (al draaiend)
- Vercel account (gratis)
- Render account (gratis)

## 🔧 Stap 1: Repository Setup

1. Push alle bestanden naar GitHub:
```bash
git add .
git commit -m "Add deployment configuration"
git push origin main
```

## 🌐 Stap 2: Backend Deployment (Render)

1. Ga naar [Render Dashboard](https://dashboard.render.com)
2. Klik "New" → "Web Service"
3. Connect je GitHub repository
4. Configureer:
   - **Name**: `indonesische-recepten-backend`
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r backend/requirements.txt`
   - **Start Command**: `uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT`

5. **Environment Variables** toevoegen:
   ```
   NEO4J_URI=neo4j+s://jouw-instance.databases.neo4j.io
   NEO4J_USERNAME=neo4j
   NEO4J_PASSWORD=jouw-wachtwoord
   NEO4J_DATABASE=neo4j
   ```

6. Klik "Create Web Service"
7. Kopieer de **service URL** (bijv. `https://indonesische-recepten-backend.onrender.com`)

## 🎨 Stap 3: Frontend Deployment (Vercel)

1. Ga naar [Vercel Dashboard](https://vercel.com/dashboard)
2. Klik "Add New..." → "Project"
3. Import je GitHub repository
4. Configureer:
   - **Framework Preset**: `Next.js`
   - **Root Directory**: `frontend/`

5. **Environment Variables** toevoegen:
   ```
   NEXT_PUBLIC_API_URL=https://jouw-render-backend-url.onrender.com
   ```

6. Klik "Deploy"
7. Vercel geeft je een URL (bijv. `https://indonesische-recepten.vercel.app`)

## 🔗 Stap 4: CORS Configuratie

Update de backend CORS instellingen voor productie:

```python
# backend/app/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://world-recipes-eight.vercel.app/"], # Vervang met je Vercel URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## ✅ Stap 5: Testing

1. Open je Vercel URL
2. Controleer of recepten laden
3. Test filtering en zoeken
4. Controleer browser console voor errors

## 🐛 Troubleshooting

### Backend Issues:
- Controleer environment variables in Render
- Check Neo4j Aura connection string
- Bekijk Render logs voor errors

### Frontend Issues:
- Controleer `NEXT_PUBLIC_API_URL` in Vercel
- Zorg dat backend CORS de Vercel URL accepteert
- Check browser network tab voor API calls

## 💰 Kosten

- **Vercel**: Gratis tier (100GB bandwidth/maand)
- **Render**: Gratis tier (750 uur/maand)
- **Neo4j Aura**: Gratis tier (200k nodes/relationships)

## 🔄 Updates Deployen

Nieuwe commits naar `main` branch worden automatisch gedeployed door beide platforms.

---

**Veel succes met je deployment! 🎉**

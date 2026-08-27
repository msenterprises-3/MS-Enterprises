# Production Deployment Guide — MS Furniture Gallery

This guide details how to deploy the **MS Furniture Gallery** web application to **Vercel**, **Render**, **Railway**, or container platforms using **Supabase** as the database.

---

## 1. Quick Deploy on Vercel (Recommended)

Vercel provides zero-configuration serverless hosting for Python WSGI applications with automatic global CDN caching for static assets.

### Step 1: Push to GitHub
1. Push this project repository to a **GitHub** repository.

### Step 2: Import into Vercel
1. Log into your [Vercel Dashboard](https://vercel.com).
2. Click **Add New...** → **Project**.
3. Select and import your GitHub repository.
4. If your project files are inside the `MS_Enterprises_Project` subdirectory, set **Root Directory** to `MS_Enterprises_Project` (or leave as `./` if your repo root contains `wsgi.py`).

### Step 3: Configure Environment Variables
Under **Environment Variables**, add the following 4 variables:

| Variable | Required | Example / Value |
| :--- | :---: | :--- |
| `FLASK_SECRET_KEY` | **Yes** | A long random secret string (e.g. `prod_secret_ms_gallery_2026`) |
| `FLASK_ENV` | **Yes** | `production` |
| `SUPABASE_URL` | **Yes** | `https://your-project-id.supabase.co` |
| `SUPABASE_KEY` | **Yes** | Your Supabase service role or anon API key |

### Step 4: Deploy
1. Click **Deploy**.
2. Vercel builds the project using `@vercel/python` and provisions the serverless endpoints.
3. Your application is live at `https://your-project.vercel.app`!

---

## 2. Deploy on Render

1. Log into [Render Dashboard](https://dashboard.render.com).
2. Click **New +** → **Web Service**.
3. Connect your GitHub repository.
4. Configure:
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn wsgi:app --workers 4 --threads 2 --bind 0.0.0.0:$PORT --timeout 120`
5. Under **Environment Variables**, add:
   - `FLASK_SECRET_KEY`
   - `FLASK_ENV=production`
   - `SUPABASE_URL`
   - `SUPABASE_KEY`
6. Click **Create Web Service**.

---

## 3. Deploy on Railway

1. Log into [Railway.app](https://railway.app).
2. Click **New Project** → **Deploy from GitHub repo**.
3. Select your repository.
4. Under **Variables**, add:
   - `FLASK_SECRET_KEY`
   - `FLASK_ENV=production`
   - `SUPABASE_URL`
   - `SUPABASE_KEY`
5. Railway provisions a domain automatically under **Settings** → **Networking**.

---

## 4. Deploy with Docker

```bash
docker-compose up -d --build
```
The site will run on `http://localhost:5000`.

---

## 5. Health & Verification Check

Once deployed, you can verify your service status at:
* **Health Check URL**: `https://your-domain.com/health`
* **Response**: `{"status": "healthy", "timestamp": "...", "app": "MS Furniture Gallery"}`

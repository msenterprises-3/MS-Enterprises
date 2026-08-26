# Production Deployment Guide — MS Furniture Gallery

This guide details how to deploy the **MS Furniture Gallery** web application to popular hosting platforms, cloud container providers, or self-hosted virtual private servers (VPS).

---

## 1. Quick Deploy on Render (Recommended)

Render offers free/affordable hosting with automatic SSL, custom domains, and zero maintenance.

### Option A: 1-Click Render Blueprint
1. Push this repository to **GitHub** or **GitLab**.
2. Log into [Render Dashboard](https://dashboard.render.com).
3. Click **New +** → **Blueprint**.
4. Connect your repository. Render will automatically read `render.yaml` and configure:
   - **Runtime**: Python 3.11.9
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn wsgi:app --workers 4 --threads 2 --bind 0.0.0.0:$PORT --timeout 120`
   - **Health Check Path**: `/health`
5. Set any secret environment variables (e.g. `SUPABASE_URL`, `SUPABASE_KEY` if using Supabase).
6. Click **Apply**. Your app is live!

### Option B: Manual Web Service on Render
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `gunicorn wsgi:app --workers 4 --threads 2 --bind 0.0.0.0:$PORT --timeout 120`

---

## 2. Quick Deploy on Railway

1. Log into [Railway.app](https://railway.app).
2. Click **New Project** → **Deploy from GitHub repo**.
3. Select your repository. Railway will detect `railway.toml` and build automatically with Nixpacks.
4. Under **Variables**, add:
   - `PORT=5000` (or let Railway set `$PORT`)
   - `FLASK_SECRET_KEY=your_generated_secret_key`
5. Railway provides a free live HTTPS domain automatically under **Settings** → **Networking**.

---

## 3. Deploy with Docker (Cloud Run / AWS / DigitalOcean / Fly.io)

This repository includes a production-grade `Dockerfile` and `docker-compose.yml`.

### Build & Run with Docker Compose Locally:
```bash
docker-compose up -d --build
```
The site will be available on `http://localhost:5000`.

### Deploy to Google Cloud Run:
```bash
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/ms-furniture-gallery
gcloud run deploy ms-furniture-gallery \
  --image gcr.io/YOUR_PROJECT_ID/ms-furniture-gallery \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --port 5000
```

### Deploy to Fly.io:
```bash
fly launch
fly deploy
```

---

## 4. Deploy on Ubuntu VPS (Nginx + Gunicorn + Systemd)

### 1. Clone & Setup Python Environment:
```bash
sudo apt update && sudo apt install -y python3-pip python3-venv nginx git
git clone https://github.com/your-username/ms-furniture-gallery.git /var/www/ms_furniture
cd /var/www/ms_furniture
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 2. Configure Systemd Service:
Create `/etc/systemd/system/msfurniture.service`:
```ini
[Unit]
Description=MS Furniture Gallery Gunicorn Application
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/ms_furniture
Environment="PATH=/var/www/ms_furniture/venv/bin"
Environment="FLASK_ENV=production"
Environment="FLASK_SECRET_KEY=your_production_secret_key"
ExecStart=/var/www/ms_furniture/venv/bin/gunicorn wsgi:app --workers 4 --threads 2 --bind 127.0.0.1:5000 --timeout 120

[Install]
WantedBy=multi-user.target
```
Enable and start the service:
```bash
sudo systemctl daemon-reload
sudo systemctl start msfurniture
sudo systemctl enable msfurniture
```

### 3. Configure Nginx Reverse Proxy:
Create `/etc/nginx/sites-available/msfurniture`:
```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;

    client_max_body_size 10M;

    location /static/ {
        alias /var/www/ms_furniture/static/;
        expires 30d;
        add_header Cache-Control "public, no-transform";
    }

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```
Enable site and install free SSL certificate:
```bash
sudo ln -s /etc/nginx/sites-available/msfurniture /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

---

## 5. Environment Variables Reference

| Variable | Required | Default | Description |
| :--- | :---: | :---: | :--- |
| `FLASK_SECRET_KEY` | Optional | Auto-generated | Secret key for session security & CSRF protection |
| `PORT` | Optional | `5000` | Port for the HTTP server |
| `HOST` | Optional | `0.0.0.0` | Bind host IP address |
| `SUPABASE_URL` | Optional | None | Supabase PostgreSQL project URL |
| `SUPABASE_KEY` | Optional | None | Supabase API key (anon or service role) |
| `FIREBASE_CREDENTIALS_JSON` | Optional | None | JSON string of Firebase service account |

---

## 6. Health & Verification Check

Once deployed, you can verify your service status at:
* **Health Check URL**: `https://your-domain.com/health`
* **Response**: `{"status": "healthy", "timestamp": "...", "app": "MS Furniture Gallery"}`

import os
import sys

# Ensure current directory is in python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    
    # Try using waitress production WSGI server
    try:
        from waitress import serve
        print(f"[WSGI] Starting production server using Waitress on http://0.0.0.0:{port}...")
        serve(app, host="0.0.0.0", port=port)
    except ImportError:
        print("[WSGI] Waitress not found. Falling back to Flask built-in development server...")
        app.run(host="0.0.0.0", port=port, debug=False)

# MS Enterprises - Furniture Store & Portal

A full-stack web application built with Python (Flask) and Supabase. Features a customer portal, dealer portal (B2B wholesale pricing), and an admin dashboard.

## Prerequisites
- Python 3.9+
- Supabase project with database and storage buckets

## Getting Started

1. **Install dependencies**
   Create a virtual environment (optional but recommended) and install required Python packages:
   ```bash
   pip install -r requirements.txt
   ```
   *(If requirements.txt is missing, ensure you have `flask`, `supabase`, `python-dotenv`, `requests`, `pillow` installed)*

2. **Configure Environment Variables**
   Copy `.env.example` to `.env` and fill in your Supabase credentials:
   ```bash
   cp .env.example .env
   ```

3. **Supabase Setup**
   You need to have the following tables set up in your Supabase project:
   - `products`: Product catalog
   - `categories`: Category listings
   - `dealers`: B2B dealer registrations and credentials
   - `settings`: Admin credentials and global settings
   - `orders` (if applicable)

   You also need the following Storage buckets (public):
   - `products`: For product and category images

4. **Run the Development Server**
   Start the Flask application:
   ```bash
   python app.py
   ```
   The application will run locally on `http://127.0.0.1:5000`.

## Features
- **Retail & Wholesale Pricing**: Seamless toggle based on authentication.
- **Portals**: Dedicated portals for customers (`/profile`), dealers (`/dealer`), and admins (`/admin`).
- **Cart & Wishlist**: Session-based cart handling.
- **Admin Management**: Full CRUD for products, categories, dealer approvals, and images.

import os
import re
import uuid
import json
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Import Database & Cache Layer
from firebase_db import db, get_cache, get_settings, touch_catalogue_update, get_last_update_time, Increment

app = Flask(__name__)
from werkzeug.middleware.proxy_fix import ProxyFix
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1, x_prefix=1)

app.secret_key = os.environ.get("FLASK_SECRET_KEY") or os.environ.get("SECRET_KEY") or "prod_secret_key_ms_furniture_gallery_2026_secure"
from datetime import timedelta
app.permanent_session_lifetime = timedelta(days=365)
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5MB Max upload size
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp', 'gif'}

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Helper function to check allowed file extensions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Helper function to generate clean URL slugs
def slugify(text):
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    text = re.sub(r'[\s-]+', '-', text)
    return text.strip('-')

# Login required decorator
def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

# Role-based validation decorator
def role_required(roles):
    if isinstance(roles, str):
        roles = [roles]
    def decorator(f):
        from functools import wraps
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user_role = session.get('user_role')
            if not user_role or user_role not in roles:
                if 'dealer' in roles:
                    return redirect(url_for('dealer_login'))
                return redirect(url_for('index'))
            
            # Approved dealer session validation
            if user_role == 'dealer' and not session.get('dealer_logged_in'):
                return redirect(url_for('dealer_login'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# Dealer activity log helper
def log_dealer_activity(action, details=""):
    if not session.get('dealer_logged_in'):
        return
    
    dealer_id = session.get('dealer_id')
    dealer_name = session.get('dealer_name')
    business_name = session.get('dealer_business')
    mobile = session.get('dealer_mobile')
    email = session.get('dealer_email')
    
    ua_str = request.headers.get('User-Agent', '')
    device = "Desktop"
    if any(m in ua_str.lower() for m in ['mobile', 'android', 'iphone', 'ipad']):
        device = "Mobile"
        
    ip_addr = request.headers.get('X-Forwarded-For', request.remote_addr or "")
    if ',' in ip_addr:
        ip_addr = ip_addr.split(',')[0].strip()
        
    try:
        db.collection('dealer_activities').document().set({
            'dealer_id': str(dealer_id),
            'dealer_name': dealer_name,
            'business_name': business_name,
            'mobile_number': mobile,
            'email': email,
            'browser': ua_str[:120],
            'device': device,
            'ip_address': ip_addr,
            'action': action,
            'details': details,
            'created_at': datetime.utcnow()
        })
    except Exception as e:
        print(f"Error logging dealer activity: {e}")

# Helper to sanitize pricing information based on active session role
def sanitize_products_by_role(prods):
    if not isinstance(prods, list):
        # Handle single product dictionary
        is_single = True
        prods = [prods]
    else:
        is_single = False
        
    sanitized = []
    is_dealer = session.get('dealer_logged_in')
    tier = session.get('dealer_tier', 'default')
    
    for p in prods:
        p_copy = dict(p)
        if is_dealer:
            prices_map = p_copy.get('dealer_prices', {})
            p_copy['wholesale_price'] = prices_map.get(tier, prices_map.get('default', 0.0))
        else:
            if 'dealer_prices' in p_copy:
                del p_copy['dealer_prices']
        sanitized.append(p_copy)
        
    return sanitized[0] if is_single else sanitized

# Context processor to inject global settings on all templates
@app.context_processor
def inject_settings():
    settings = get_settings()
    categories_raw = get_cache('categories')
    subcategories_raw = get_cache('subcategories')
    
    categories = []
    for c in categories_raw:
        if c.get('status') == 'active':
            c_dict = dict(c)
            c_dict['subcategories'] = [
                s for s in subcategories_raw
                if s.get('category_id') == c['id'] and s.get('status') == 'active'
            ]
            categories.append(c_dict)
            
    return {
        'settings': settings,
        'global_categories': categories,
        'current_year': datetime.now().year
    }

# Memory filtering and sorting engine for database collections
def get_filtered_products(q=None, category_slug=None, subcat_slug=None, price_max=None, sort_by='newest',
                          featured=None, new_arrival=None, best_seller=None, premium=None, status='active'):
    products = get_cache('products')
    
    # Secure role-based catalog filtering
    user_role = session.get('user_role')
    if user_role == 'dealer':
        products = [p for p in products if p.get('dealer_status', 'visible') != 'hidden']
    else:
        products = [p for p in products if p.get('dealer_status', 'visible') != 'dealer_only']
        
    # 1. Status filter
    if status:
        products = [p for p in products if p.get('status') == status]
        
    # 2. Category filter
    if category_slug:
        categories = get_cache('categories')
        cat_id = None
        for c in categories:
            if c.get('slug', '').lower() == category_slug.lower() or str(c.get('id', '')) == str(category_slug):
                cat_id = c['id']
                break
        if cat_id is not None:
            products = [p for p in products if str(p.get('category_id')) == str(cat_id)]
        else:
            return []
            
    # 3. Subcategory filter
    if subcat_slug:
        subcategories = get_cache('subcategories')
        subcat_id = None
        for s in subcategories:
            if s.get('slug', '').lower() == subcat_slug.lower() or str(s.get('id', '')) == str(subcat_slug):
                subcat_id = s['id']
                break
        if subcat_id is not None:
            products = [p for p in products if str(p.get('subcategory_id')) == str(subcat_id)]
        else:
            return []
            
    # 4. Search query (Category-aware & precise search)
    if q:
        q_clean = q.strip().lower()
        q_tokens = [t for t in re.split(r'\s+', q_clean) if t]
        
        categories_cache = get_cache('categories')
        subcategories_cache = get_cache('subcategories')
        
        # Identify matching category & subcategory IDs
        matching_cat_ids = set()
        for c in categories_cache:
            c_name = c.get('name', '').lower()
            c_slug = c.get('slug', '').lower()
            if q_clean in c_name or c_name in q_clean or q_clean in c_slug:
                matching_cat_ids.add(str(c['id']))
            elif any(t in c_name or (len(t) > 3 and t.rstrip('s') in c_name) for t in q_tokens):
                matching_cat_ids.add(str(c['id']))
                
        matching_subcat_ids = set()
        for s in subcategories_cache:
            s_name = s.get('name', '').lower()
            s_slug = s.get('slug', '').lower()
            if q_clean in s_name or s_name in q_clean or q_clean in s_slug:
                matching_subcat_ids.add(str(s['id']))
            elif any(t in s_name or (len(t) > 3 and t.rstrip('s') in s_name) for t in q_tokens):
                matching_subcat_ids.add(str(s['id']))

        filtered = []
        for p in products:
            p_cat_id = str(p.get('category_id', ''))
            p_subcat_id = str(p.get('subcategory_id', ''))
            name = p.get('name', '').lower()
            s_desc = p.get('short_description', '').lower()
            sku = p.get('sku', '').lower()
            
            # Category / Subcategory direct match
            if p_cat_id in matching_cat_ids or p_subcat_id in matching_subcat_ids:
                filtered.append(p)
                continue
                
            # Direct name or SKU match
            if q_clean in name or q_clean in sku or (len(q_clean) >= 3 and q_clean in s_desc):
                filtered.append(p)
                continue
                
            # Token match across name and sku
            if q_tokens and all(t in name or t in sku or t in s_desc for t in q_tokens):
                filtered.append(p)
                
        products = filtered
        
    # 5. Price Max filter
    if price_max:
        try:
            p_max = float(price_max)
            def safe_get_price(p):
                try:
                    return float(p.get('offer_price') or p.get('price') or 0.0)
                except (ValueError, TypeError):
                    return 0.0
            products = [p for p in products if safe_get_price(p) <= p_max]
        except (ValueError, TypeError):
            pass
            
    # 6. Flag filters
    def is_flag_set(val):
        return val is True or val == 1 or val == '1' or str(val).lower() in ('true', '1', 'yes')

    if featured == '1' or featured == 'best-seller':
        products = [p for p in products if is_flag_set(p.get('is_featured'))]
    if new_arrival == '1':
        products = [p for p in products if is_flag_set(p.get('is_new_arrival'))]
    if best_seller == '1':
        products = [p for p in products if is_flag_set(p.get('is_best_seller'))]
    if premium == '1':
        products = [p for p in products if is_flag_set(p.get('is_premium'))]
        
    # 7. Sorting
    def get_sort_price(p):
        try:
            return float(p.get('offer_price') or p.get('price') or 0.0)
        except (ValueError, TypeError):
            return 0.0

    if sort_by == 'price_low':
        products.sort(key=get_sort_price)
    elif sort_by == 'price_high':
        products.sort(key=get_sort_price, reverse=True)
    elif sort_by == 'name_asc':
        products.sort(key=lambda x: str(x.get('name', '')).lower())
    elif sort_by == 'name_desc':
        products.sort(key=lambda x: str(x.get('name', '')).lower(), reverse=True)
    elif sort_by == 'oldest':
        products.sort(key=lambda x: str(x.get('created_at', '')))
    else:  # newest / featured (default)
        products.sort(key=lambda x: str(x.get('created_at', '')), reverse=True)
        
    return products

# --- CUSTOMER VIEWS ---

@app.route('/')
def index():
    if 'user_role' not in session:
        session['user_role'] = 'customer'
    hero_banners = get_cache('hero_banners')
    offer_banners = get_cache('offer_banners')
    trust_badges = get_cache('trust_badges')
    videos = get_cache('video_testimonials')
    
    # 1. Curated base testimonials from cache
    base_testimonials = list(get_cache('testimonials'))
    
    # 2. Approved customer reviews from Supabase database
    approved_reviews = []
    try:
        reviews_ref = db.collection('reviews').where('status', '==', 'approved').stream()
        for doc in reviews_ref:
            r = doc.to_dict()
            r['id'] = doc.id
            approved_reviews.append(r)
    except Exception as e:
        print(f"Error fetching approved reviews for homepage: {e}")
        
    approved_reviews.sort(key=lambda x: str(x.get('created_at', '')), reverse=True)
    
    # Combine & deduplicate testimonials
    seen_keys = set()
    combined_testimonials = []
    
    for t in base_testimonials:
        t_dict = dict(t)
        name = (t_dict.get('customer_name') or '').strip()
        rev_text = (t_dict.get('review') or '').strip()
        key = (name.lower(), rev_text.lower())
        if key not in seen_keys and name and rev_text:
            seen_keys.add(key)
            combined_testimonials.append(t_dict)
            
    for r in approved_reviews:
        name_raw = (r.get('reviewer_name') or '').strip()
        name = name_raw
        city = ''
        if '(' in name_raw and name_raw.endswith(')'):
            parts = name_raw.rsplit('(', 1)
            name = parts[0].strip()
            city = parts[1].rstrip(')').strip()
            
        rev_text = (r.get('review_text') or r.get('review') or '').strip()
        key = (name.lower(), rev_text.lower())
        if key not in seen_keys and name and rev_text:
            seen_keys.add(key)
            combined_testimonials.append({
                'id': r.get('id', uuid.uuid4().hex),
                'customer_name': name,
                'city': city or 'Verified Customer',
                'customer_photo': r.get('customer_photo', '') or '',
                'rating': int(r.get('rating') or 5),
                'review': rev_text,
                'status': 'active'
            })
    
    # Popular Categories with dynamic product count
    categories = []
    all_products = get_cache('products')
    for c in get_cache('categories'):
        if c.get('status') == 'active':
            c_dict = dict(c)
            c_dict['product_count'] = sum(1 for p in all_products if str(p.get('category_id')) == str(c['id']) and p.get('status') == 'active')
            categories.append(c_dict)
    categories = categories[:20]
    
    # Active collections mapping
    user_role = session.get('user_role')
    if user_role == 'dealer':
        active_products = [p for p in all_products if p.get('status') == 'active' and p.get('dealer_status', 'visible') != 'hidden']
    else:
        active_products = [p for p in all_products if p.get('status') == 'active' and p.get('dealer_status', 'visible') != 'dealer_only']
    
    def is_truthy(val):
        return val is True or val == 1 or val == '1' or str(val).lower() in ('true', '1', 'yes')

    def enrich_home_products(prods):
        enriched = []
        categories_cache = get_cache('categories')
        for p in prods:
            p_dict = dict(p)
            p_dict['image_url'] = p_dict['images'][0] if p_dict.get('images') else '/static/uploads/products/prod_generic_1.webp'
            cat = next((c for c in categories_cache if str(c['id']) == str(p_dict.get('category_id'))), None)
            p_dict['category_name'] = cat['name'] if cat else 'Furniture'
            enriched.append(p_dict)
        return sanitize_products_by_role(enriched)
        
    # Strictly filter homepage collections based on admin flags (no random fallbacks)
    all_home_products = enrich_home_products(active_products)
    best_sellers = enrich_home_products([p for p in active_products if is_truthy(p.get('is_best_seller'))][:8])
    new_arrivals = enrich_home_products([p for p in active_products if is_truthy(p.get('is_new_arrival'))][:8])
    trending = enrich_home_products([p for p in active_products if is_truthy(p.get('is_featured'))][:8])
    premium_collection = enrich_home_products([p for p in active_products if is_truthy(p.get('is_premium'))][:8])
    
    active_offer = dict(offer_banners[0]) if offer_banners else None
    
    return render_template('index.html',
                           hero_banners=hero_banners,
                           active_offer=active_offer,
                           trust_badges=trust_badges,
                           categories=categories,
                           products=all_home_products,
                           featured=trending,
                           trending=trending,
                           new_arrivals=new_arrivals,
                           best_sellers=best_sellers,
                           premium=premium_collection,
                           testimonials=combined_testimonials,
                           videos=videos)

@app.route('/products')
def products():
    try:
        q = request.args.get('q', '').strip()
        category_slug = request.args.get('category', '').strip()
        subcat_slug = request.args.get('subcategory', '').strip()
        price_max = request.args.get('price_max', '').strip()
        sort_by = request.args.get('sort', 'newest').strip()
        
        featured = request.args.get('featured', '').strip()
        new_arrival = request.args.get('new_arrival', '').strip()
        best_seller = request.args.get('best_seller', '').strip()
        premium = request.args.get('premium', '').strip()
        
        page = int(request.args.get('page', 1))
        per_page = 24
        
        filtered_list = get_filtered_products(
            q=q, category_slug=category_slug, subcat_slug=subcat_slug, price_max=price_max, sort_by=sort_by,
            featured=featured, new_arrival=new_arrival, best_seller=best_seller, premium=premium, status='active'
        )
        
        total_count = len(filtered_list)
        offset = (page - 1) * per_page
        paginated_list = filtered_list[offset:offset+per_page]
        
        # Enrich image_url and category details
        enriched_products = []
        categories_cache = get_cache('categories')
        for p in paginated_list:
            p_dict = dict(p)
            p_dict['image_url'] = p_dict['images'][0] if p_dict.get('images') else '/static/uploads/products/prod_generic_1.webp'
            
            # Get category details
            cat = next((c for c in categories_cache if str(c['id']) == str(p_dict['category_id'])), None)
            p_dict['category_name'] = cat['name'] if cat else 'Uncategorized'
            p_dict['category_slug'] = cat['slug'] if cat else ''
            
            enriched_products.append(p_dict)
            
        all_categories = [c for c in categories_cache if c.get('status') == 'active']
        subcategories = []
        current_category = None
        if category_slug:
            current_category = next((c for c in all_categories if c['slug'].lower() == category_slug.lower() or str(c['id']) == str(category_slug)), None)
            if current_category:
                subcategories = [s for s in get_cache('subcategories') if s['category_id'] == current_category['id'] and s['status'] == 'active']
                
        sanitized_products = sanitize_products_by_role(enriched_products)

        # Group products by category
        from collections import OrderedDict
        grouped_products = OrderedDict()

        if current_category:
            cat_name = current_category['name']
            if sanitized_products:
                grouped_products[cat_name] = sanitized_products
        else:
            # Group products maintaining category order from cache
            for cat in all_categories:
                cat_prods = [p for p in sanitized_products if str(p.get('category_id')) == str(cat['id'])]
                if cat_prods:
                    grouped_products[cat['name']] = cat_prods
            # Any uncategorized or remaining products
            uncategorized = [p for p in sanitized_products if not any(str(p.get('category_id')) == str(cat['id']) for cat in all_categories)]
            if uncategorized:
                grouped_products['Other Collections'] = uncategorized

        # Max price ceiling
        max_db_price = max([p.get('price', 0) for p in get_cache('products')] or [100000])
        total_pages = (total_count + per_page - 1) // per_page
        
        return render_template('products.html',
                               products=sanitized_products,
                               grouped_products=grouped_products,
                               categories=all_categories,
                               subcategories=subcategories,
                               current_category=current_category,
                               total_count=total_count,
                               page=page,
                               total_pages=total_pages,
                               q=q,
                               category_slug=category_slug,
                               subcat_slug=subcat_slug,
                               price_max=price_max,
                               max_db_price=int(max_db_price),
                               sort_by=sort_by,
                               featured=featured,
                               new_arrival=new_arrival,
                               best_seller=best_seller,
                               premium=premium)
    except Exception as e:
        print(f"CRITICAL ERROR IN PRODUCTS ROUTE: {e}")
        import traceback
        traceback.print_exc()
        return render_template('error.html', 
                               error_title="Unable to load products", 
                               error_message="Unable to load products. Please try again later."), 500

@app.route('/product/<slug>')
def product_details(slug):
    all_products = get_cache('products')
    product = next((p for p in all_products if p['slug'] == slug and p.get('status') == 'active'), None)
    if not product:
        return redirect(url_for('products'))
        
    product = dict(product)
    
    # Secure role visibility checks
    user_role = session.get('user_role')
    dealer_status = product.get('dealer_status', 'visible')
    if user_role != 'dealer' and dealer_status == 'dealer_only':
        flash("This product is reserved for authorized dealers.", "warning")
        return redirect(url_for('products'))
    if user_role == 'dealer' and dealer_status == 'hidden':
        flash("This product is not available for wholesale dealers.", "warning")
        return redirect(url_for('products'))
        
    # Log activity for dealers
    if session.get('dealer_logged_in'):
        log_dealer_activity('view_product', f"Product: {product['name']} (SKU: {product['sku']})")
        
    categories_cache = get_cache('categories')
    
    # Fetch Category Details
    category_row = next((c for c in categories_cache if c['id'] == product['category_id']), None)
    product['category_name'] = category_row['name'] if category_row else 'Uncategorized'
    product['category_slug'] = category_row['slug'] if category_row else ''
    
    # Specifications & features dictionaries are already parsed/maps in NoSQL document
    product['specs_dict'] = product.get('specifications') or {}
    product['features_list'] = product.get('features') or []
    
    if not product.get('images'):
        product['images'] = ['/static/uploads/products/prod_generic_1.webp']
        
    # Format variants dictionary as template expects
    variants_dict = {}
    for v in product.get('variants', []):
        v_name = v['name']
        if v_name not in variants_dict:
            variants_dict[v_name] = []
        variants_dict[v_name].append({
            'value': v['value'],
            'price_adjustment': v['price_adjustment']
        })
    product['variants'] = variants_dict
    
    # Related Products (Same category, limited to 4)
    related = []
    for r in all_products:
        if r.get('category_id') == product['category_id'] and r['id'] != product['id'] and r.get('status') == 'active':
            r_dict = dict(r)
            r_dict['image_url'] = r_dict['images'][0] if r_dict.get('images') else '/static/uploads/products/prod_generic_1.webp'
            related.append(r_dict)
            if len(related) >= 4:
                break
                
    # Reviews (Streamed live from database)
    reviews_ref = db.collection('reviews')\
                    .where('product_id', '==', str(product['id']))\
                    .where('status', '==', 'approved')\
                    .stream()
    reviews = []
    for doc in reviews_ref:
        r = doc.to_dict()
        r['id'] = doc.id
        reviews.append(r)
    reviews.sort(key=lambda x: x.get('created_at', ''), reverse=True)
    
    avg_rating = 0
    if reviews:
        avg_rating = sum(r['rating'] for r in reviews) / len(reviews)
    product['avg_rating'] = round(avg_rating, 1)
    product['reviews_count'] = len(reviews)
    
    seo_data = {
        'title': f"{product['name']} | MS Furniture Gallery",
        'description': product['short_description'] or product['name'],
        'image': product['images'][0]
    }
    
    return render_template('product.html', product=sanitize_products_by_role(product), related=sanitize_products_by_role(related), reviews=reviews, seo=seo_data)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        flash("Thank you for contacting MS Furniture Gallery! Our executive will get in touch with you shortly.", "success")
        return redirect(url_for('contact'))
    return render_template('contact.html')

# --- ADMIN GATEWAYS ---

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if session.get('admin_logged_in'):
        return redirect(url_for('admin_dashboard'))
        
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        
        settings = get_settings()
        if settings and username == 'admin' and check_password_hash(settings.get('admin_password_hash'), password):
            session['admin_logged_in'] = True
            session.permanent = True
            flash("Welcome to MS Furniture Gallery Admin Panel!", "success")
            return redirect(url_for('admin_dashboard'))
        else:
            flash("Invalid Admin username or password.", "danger")
            
    return render_template('admin_login.html')

@app.route('/admin')
@login_required
def admin_dashboard():
    # Fetch pending reviews count
    pending_reviews_ref = db.collection('reviews').where('status', '==', 'pending').stream()
    pending_reviews_count = sum(1 for _ in pending_reviews_ref)
    
    stats = {
        'products': len(get_cache('products')),
        'categories': len(get_cache('categories')),
        'testimonials': len(get_cache('testimonials')),
        'reviews': pending_reviews_count
    }
    
    # Products list with nested category name
    products = []
    categories_cache = get_cache('categories')
    for p in get_cache('products'):
        p_dict = dict(p)
        p_dict['wishlist_count'] = p_dict.get('wishlist_count', 0)
        p_dict['cart_count'] = p_dict.get('cart_count', 0)
        cat = next((c for c in categories_cache if str(c['id']) == str(p_dict['category_id'])), None)
        p_dict['category_name'] = cat['name'] if cat else 'Uncategorized'
        products.append(p_dict)
        
    # Subcategories list with nested category name
    subcategories = []
    for s in get_cache('subcategories'):
        s_dict = dict(s)
        cat = next((c for c in categories_cache if str(c['id']) == str(s_dict['category_id'])), None)
        s_dict['category_name'] = cat['name'] if cat else 'Uncategorized'
        subcategories.append(s_dict)
        
    # Banners and testimonials
    hero_banners = get_cache('hero_banners')
    offer_banners = get_cache('offer_banners')
    testimonials = get_cache('testimonials')
    videos = get_cache('video_testimonials')
    trust_badges = get_cache('trust_badges')
    
    # Reviews
    reviews_ref = db.collection('reviews').stream()
    reviews = []
    products_cache = get_cache('products')
    for doc in reviews_ref:
        r = doc.to_dict()
        r['id'] = doc.id
        prod = next((p for p in products_cache if str(p['id']) == str(r['product_id'])), None)
        r['product_name'] = prod['name'] if prod else ('General Store Review' if r.get('product_id') == 'general' else 'Unknown Product')
        reviews.append(r)
    reviews.sort(key=lambda x: (x.get('status', 'pending') != 'pending', x.get('created_at', '')), reverse=True)
    
    # Stock Notifications
    stock_notifications = []
    try:
        from supabase_db import supabase_client
        if supabase_client:
            res = supabase_client.table('stock_notifications').select('*').order('id', desc=True).execute()
            sn_rows = res.data or []
        else:
            sn_rows = [doc.to_dict() for doc in db.collection('stock_notifications').stream()]
            sn_rows.sort(key=lambda x: str(x.get('created_at', '')), reverse=True)

        for sn in sn_rows:
            sn_dict = dict(sn)
            prod = next((p for p in products_cache if str(p.get('id')) == str(sn_dict.get('product_id'))), None)
            sn_dict['product_name'] = prod['name'] if prod else f"Product #{sn_dict.get('product_id')}"
            created_at_raw = sn_dict.get('created_at')
            if created_at_raw:
                try:
                    dt = datetime.fromisoformat(str(created_at_raw).replace('Z', '+00:00'))
                    sn_dict['formatted_date'] = dt.strftime('%d-%b-%Y %I:%M %p')
                except Exception:
                    sn_dict['formatted_date'] = str(created_at_raw)[:19].replace('T', ' ')
            else:
                sn_dict['formatted_date'] = 'N/A'
            stock_notifications.append(sn_dict)
    except Exception as e:
        print(f"Error loading stock notifications for admin: {e}")

    return render_template('admin.html',
                           stats=stats,
                           products=products,
                           categories=categories_cache,
                           subcategories=subcategories,
                           hero_banners=hero_banners,
                           offer_banners=offer_banners,
                           testimonials=testimonials,
                           videos=videos,
                           reviews=reviews,
                           trust_badges=trust_badges,
                           stock_notifications=stock_notifications)

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    flash("You have logged out successfully.", "info")
    return redirect(url_for('admin_login'))

# --- INTERACTIVE API ENDPOINTS ---

@app.route('/api/search')
def api_search():
    q = request.args.get('q', '').strip()
    if len(q) < 2:
        return jsonify([])
        
    q_lower = q.lower()
    results = []
    products_cache = get_cache('products')
    categories_cache = get_cache('categories')
    
    for p in products_cache:
        if p.get('status') == 'active':
            name = p.get('name', '').lower()
            s_desc = p.get('short_description', '').lower()
            if q_lower in name or q_lower in s_desc:
                cat = next((c for c in categories_cache if str(c['id']) == str(p.get('category_id'))), None)
                results.append({
                    'id': p['id'],
                    'name': p['name'],
                    'slug': p['slug'],
                    'price': p['price'],
                    'offer_price': p.get('offer_price'),
                    'category_name': cat['name'] if cat else 'Uncategorized',
                    'image_url': p['images'][0] if p.get('images') and p['images'][0] else '/static/uploads/products/prod_generic_1.webp'
                })
                if len(results) >= 8:
                    break
                    
    return jsonify(results)

@app.route('/api/reviews', methods=['POST'])
def api_submit_review():
    data = request.json or request.form or {}
    product_id = str(data.get('product_id', '')).strip()
    reviewer_name = str(data.get('reviewer_name', '')).strip()
    try:
        rating = int(data.get('rating', 5))
    except (ValueError, TypeError):
        rating = 5
    review_text = str(data.get('review_text', '')).strip()
    
    if not (product_id and reviewer_name and review_text):
        return jsonify({'success': False, 'message': 'All review fields are required.'}), 400
        
    doc_ref = db.collection('reviews').document()
    doc_ref.set({
        'product_id': product_id,
        'reviewer_name': reviewer_name,
        'rating': max(1, min(5, rating)),
        'review_text': review_text,
        'status': 'pending',
        'created_at': datetime.utcnow().isoformat()
    })
    return jsonify({'success': True, 'message': 'Review submitted successfully! It will appear on the site once approved by the administrator.'})

# ----------------- DEALER / B2B PORTAL ROUTES -----------------

@app.route('/api/set-role', methods=['POST'])
def api_set_role():
    data = request.json or {}
    role = data.get('role')
    if role not in ['customer', 'dealer']:
        return jsonify({'success': False, 'message': 'Invalid role choice.'}), 400
    
    session['user_role'] = role
    session.permanent = True
    return jsonify({'success': True, 'message': f'Role set to {role}'})


@app.route('/dealer/register', methods=['GET', 'POST'])
def dealer_register():
    if request.method == 'POST':
        # Retrieve form data
        business_name = request.form.get('business_name', '').strip()
        dealer_name = request.form.get('dealer_name', '').strip()
        gst_number = request.form.get('gst_number', '').strip()
        mobile_number = request.form.get('mobile_number', '').strip()
        email = request.form.get('email', '').strip().lower()
        address = request.form.get('address', '').strip()
        city = request.form.get('city', '').strip()
        state = request.form.get('state', '').strip()
        pincode = request.form.get('pincode', '').strip()
        password = request.form.get('password', '')
        
        if not (business_name and dealer_name and mobile_number and email and password):
            flash("Please fill in all required fields.", "error")
            return render_template('dealer_register.html')
            
        # Check if email exists
        existing = db.collection('dealers').where('email', '==', email).get()
        if len(existing) > 0:
            flash("This email address is already registered.", "error")
            return render_template('dealer_register.html')
            
        # Create pending dealer document
        new_dealer_doc = {
            'business_name': business_name,
            'dealer_name': dealer_name,
            'gst_number': gst_number,
            'mobile_number': mobile_number,
            'email': email,
            'business_address': address,
            'city': city,
            'state': state,
            'pincode': pincode,
            'password_hash': generate_password_hash(password),
            'status': 'pending',
            'tier': 'default',
            'created_at': datetime.utcnow()
        }
        
        db.collection('dealers').add(new_dealer_doc)
        flash("Registration submitted successfully! Your account is currently under review by the administrator.", "success")
        return redirect(url_for('dealer_login'))
        
    return render_template('dealer_register.html')


@app.route('/dealer/login', methods=['GET', 'POST'])
def dealer_login():
    session['user_role'] = 'dealer'
    if session.get('dealer_logged_in'):
        return redirect(url_for('dealer_portal'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        
        if not (email and password):
            flash("Please enter both email and password.", "error")
            return render_template('dealer_login.html')
            
        dealers = db.collection('dealers').where('email', '==', email).get()
        if len(dealers) == 0:
            flash("Invalid email or password.", "error")
            return render_template('dealer_login.html')
            
        dealer_doc = dealers[0]
        dealer_data = dealer_doc.to_dict()
        
        if not check_password_hash(dealer_data.get('password_hash', ''), password):
            flash("Invalid email or password.", "error")
            return render_template('dealer_login.html')
            
        status = dealer_data.get('status', 'pending')
        if status != 'approved':
            if status == 'pending':
                flash("Your dealer account is currently under review by the administrator. You will be notified once it has been approved.", "warning")
            elif status == 'suspended':
                flash("Your dealer account has been suspended. Please contact customer support.", "error")
            else:
                flash("Your dealer registration has been rejected.", "error")
            return render_template('dealer_login.html')
            
        # Log success and populate session
        session['user_role'] = 'dealer'
        session['dealer_logged_in'] = True
        session['dealer_id'] = dealer_doc.id
        session['dealer_name'] = dealer_data.get('dealer_name')
        session['dealer_business'] = dealer_data.get('business_name')
        session['dealer_mobile'] = dealer_data.get('mobile_number')
        session['dealer_email'] = dealer_data.get('email')
        session['dealer_tier'] = dealer_data.get('tier', 'default')
        session.permanent = True
        
        # Merge guest cart into dealer cart on successful login
        guest_sess_id = session.get('session_id')
        if guest_sess_id:
            merge_guest_cart_to_dealer(guest_sess_id, dealer_doc.id)
        
        log_dealer_activity('login', "Dealer logged in successfully")
        flash(f"Welcome back, {session['dealer_name']}!", "success")
        return redirect(url_for('dealer_portal'))
        
    return render_template('dealer_login.html')


@app.route('/dealer/logout')
def dealer_logout():
    if session.get('dealer_logged_in'):
        log_dealer_activity('logout', "Dealer logged out")
        
    session.pop('dealer_logged_in', None)
    session.pop('dealer_id', None)
    session.pop('dealer_name', None)
    session.pop('dealer_business', None)
    session.pop('dealer_mobile', None)
    session.pop('dealer_email', None)
    session.pop('dealer_tier', None)
    
    flash("You have logged out of the Dealer Portal.", "info")
    return redirect(url_for('dealer_login'))


@app.route('/dealer')
@app.route('/dealer/portal')
@role_required('dealer')
def dealer_portal():
    stats = {
        'business': session.get('dealer_business'),
        'name': session.get('dealer_name'),
        'tier': session.get('dealer_tier')
    }
    
    categories = get_cache('categories')
    activities = []
    activities_error = False
    
    try:
        recent_activities = db.collection('dealer_activities')\
                              .where('dealer_id', '==', str(session.get('dealer_id')))\
                              .order_by('created_at', direction='DESCENDING')\
                              .limit(5).get()
    except Exception as e:
        print(f"Index notice (dealer_activities): {e}. Falling back to in-memory sorting.")
        try:
            raw_activities = db.collection('dealer_activities')\
                               .where('dealer_id', '==', str(session.get('dealer_id')))\
                               .get()
            
            def get_created_at(doc):
                d = doc.to_dict()
                val = d.get('created_at')
                if isinstance(val, str):
                    return val
                if val:
                    return val
                return datetime.min
                
            recent_activities = sorted(raw_activities, key=get_created_at, reverse=True)[:5]
        except Exception as fallback_err:
            print(f"Fallback query failed: {fallback_err}")
            recent_activities = []
            activities_error = True
            
    for doc in recent_activities:
        act = doc.to_dict()
        if 'created_at' in act:
            if hasattr(act['created_at'], 'strftime'):
                act['created_at'] = act['created_at'].strftime('%Y-%m-%d %H:%M:%S')
            elif isinstance(act['created_at'], str):
                act['created_at'] = act['created_at'][:19].replace('T', ' ')
        activities.append(act)
        
    return render_template('dealer_portal.html', stats=stats, categories=categories, activities=activities, activities_error=activities_error)


@app.route('/api/dealer/products', methods=['GET'])
@role_required('dealer')
def api_dealer_products():
    tier = session.get('dealer_tier', 'default')
    products = get_cache('products')
    
    dealer_products = [p for p in products if p.get('dealer_status', 'visible') != 'hidden']
    
    results = []
    for p in dealer_products:
        p_dict = dict(p)
        prices_map = p_dict.get('dealer_prices', {})
        wholesale_price = prices_map.get(tier, prices_map.get('default', 0.0))
        
        p_dict['wholesale_price'] = wholesale_price
        
        if 'dealer_prices' in p_dict:
            del p_dict['dealer_prices']
            
        results.append(p_dict)
        
    log_dealer_activity('view_wholesale_catalog', f"Fetched {len(results)} products for tier {tier}")
    return jsonify(results)


@app.route('/api/dealer/log-activity', methods=['POST'])
@role_required('dealer')
def api_dealer_log_activity():
    data = request.json or {}
    action = data.get('action')
    details = data.get('details', '')
    if not action:
        return jsonify({'success': False, 'message': 'Missing action parameter.'}), 400
        
    log_dealer_activity(action, details)
    return jsonify({'success': True})


@app.route('/api/dealer/orders', methods=['POST'])
@role_required('dealer')
def api_dealer_submit_order():
    data = request.json or {}
    items = data.get('items', [])
    if not items:
        return jsonify({'success': False, 'message': 'No items in order.'}), 400
        
    tier = session.get('dealer_tier', 'default')
    products_cache = get_cache('products')
    
    ordered_products = []
    total_val = 0.0
    
    for item in items:
        prod_id = item.get('product_id')
        qty = int(item.get('quantity', 1))
        
        prod = next((p for p in products_cache if str(p['id']) == str(prod_id)), None)
        if not prod:
            continue
            
        prices_map = prod.get('dealer_prices', {})
        wholesale_price = float(prices_map.get(tier, prices_map.get('default', 0.0)))
        item_total = wholesale_price * qty
        total_val += item_total
        
        ordered_products.append({
            'product_id': str(prod_id),
            'name': prod['name'],
            'sku': prod.get('sku', ''),
            'quantity': qty,
            'price': wholesale_price,
            'total': item_total
        })
        
    if not ordered_products:
        return jsonify({'success': False, 'message': 'Failed to process any products in order.'}), 400
        
    order_doc = {
        'dealer_id': str(session.get('dealer_id')),
        'dealer_name': session.get('dealer_name'),
        'business_name': session.get('dealer_business'),
        'mobile_number': session.get('dealer_mobile'),
        'email': session.get('dealer_email'),
        'products': ordered_products,
        'total_value': total_val,
        'order_status': 'Pending',
        'payment_status': 'unpaid',
        'created_at': datetime.utcnow()
    }
    
    doc_ref = db.collection('dealer_orders').document()
    doc_ref.set(order_doc)
    
    log_dealer_activity('order_placed', f"Placed wholesale order {doc_ref.id} for value: INR {total_val}")
    
    return jsonify({
        'success': True,
        'message': 'Order placed successfully!',
        'order_id': doc_ref.id
    })


@app.route('/api/admin/dealers', methods=['GET', 'POST', 'PUT', 'DELETE'])
@login_required
def api_admin_dealers():
    if request.method == 'GET':
        dealers_ref = db.collection('dealers').order_by('created_at', direction='DESCENDING').stream()
        dealers = []
        for doc in dealers_ref:
            d = doc.to_dict()
            d['id'] = doc.id
            if 'created_at' in d and hasattr(d['created_at'], 'strftime'):
                d['created_at'] = d['created_at'].strftime('%Y-%m-%d %H:%M:%S')
            dealers.append(d)
        return jsonify(dealers)
        
    elif request.method == 'PUT':
        data = request.json or {}
        dealer_id = data.get('id')
        if not dealer_id:
            return jsonify({'success': False, 'message': 'Missing dealer ID.'}), 400
            
        doc_ref = db.collection('dealers').document(dealer_id)
        
        update_data = {}
        for field in ['status', 'tier', 'dealer_name', 'business_name', 'mobile_number', 'email', 'business_address', 'city', 'state', 'pincode']:
            if field in data:
                update_data[field] = data[field]
                
        doc_ref.update(update_data)
        return jsonify({'success': True, 'message': 'Dealer information updated.'})
        
    elif request.method == 'DELETE':
        dealer_id = request.args.get('id')
        if not dealer_id:
            return jsonify({'success': False, 'message': 'Missing dealer ID.'}), 400
            
        db.collection('dealers').document(dealer_id).delete()
        return jsonify({'success': True, 'message': 'Dealer deleted successfully.'})


@app.route('/api/admin/dealer-activities', methods=['GET'])
@login_required
def api_admin_dealer_activities():
    q = request.args.get('q', '').strip().lower()
    action_filter = request.args.get('action', '').strip()
    
    logs_ref = db.collection('dealer_activities').order_by('created_at', direction='DESCENDING').limit(1000).stream()
    logs = []
    for doc in logs_ref:
        log = doc.to_dict()
        log['id'] = doc.id
        if 'created_at' in log and hasattr(log['created_at'], 'strftime'):
            log['created_at'] = log['created_at'].strftime('%Y-%m-%d %H:%M:%S')
            
        match = True
        if q:
            name = log.get('dealer_name', '').lower()
            biz = log.get('business_name', '').lower()
            details = log.get('details', '').lower()
            if q not in name and q not in biz and q not in details:
                match = False
        if action_filter and log.get('action') != action_filter:
            match = False
            
        if match:
            logs.append(log)
            
    return jsonify(logs)


@app.route('/api/admin/dealer-orders', methods=['GET', 'PUT'])
@login_required
def api_admin_dealer_orders():
    if request.method == 'GET':
        orders_ref = db.collection('dealer_orders').order_by('created_at', direction='DESCENDING').stream()
        orders = []
        for doc in orders_ref:
            o = doc.to_dict()
            o['id'] = doc.id
            if 'created_at' in o and hasattr(o['created_at'], 'strftime'):
                o['created_at'] = o['created_at'].strftime('%Y-%m-%d %H:%M:%S')
            orders.append(o)
        return jsonify(orders)
        
    elif request.method == 'PUT':
        data = request.json or {}
        order_id = data.get('id')
        if not order_id:
            return jsonify({'success': False, 'message': 'Missing order ID.'}), 400
            
        doc_ref = db.collection('dealer_orders').document(order_id)
        
        update_data = {}
        for field in ['order_status', 'payment_status']:
            if field in data:
                update_data[field] = data[field]
                
        doc_ref.update(update_data)
        return jsonify({'success': True, 'message': 'Order updated.'})

# --- ADMIN API CRUD ENDPOINTS ---

@app.route('/api/admin/upload', methods=['POST'])
@login_required
def api_admin_upload():
    if 'image' not in request.files:
        return jsonify({'success': False, 'message': 'No image file found.'}), 400
        
    file = request.files['image']
    if file.filename == '':
        return jsonify({'success': False, 'message': 'Empty file selected.'}), 400
        
    if file and allowed_file(file.filename):
        filename = f"{uuid.uuid4().hex}_{secure_filename(file.filename)}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        return jsonify({'success': True, 'url': f'/static/uploads/{filename}'})
        
    return jsonify({'success': False, 'message': 'Invalid file format. Allowed extensions are JPG, PNG, WEBP, and GIF.'}), 400

# SETTINGS API
@app.route('/api/admin/settings', methods=['PUT'])
@login_required
def api_admin_settings():
    data = request.json
    
    update_data = {}
    
    # Text fields
    text_fields = [
        'whatsapp_number', 'contact_email', 'contact_phone', 'contact_address', 
        'working_hours', 'google_map_link', 'instagram_url', 'facebook_url', 
        'youtube_url', 'about_story', 'about_mission', 'about_vision', 
        'seo_meta_title', 'seo_meta_description', 'whatsapp_cart_prefix', 
        'whatsapp_wishlist_prefix', 'countdown_end_date', 'upi_id'
    ]
    for field in text_fields:
        if field in data:
            update_data[field] = data.get(field, '').strip()
            
    # Booleans / toggles
    for field in ['wishlist_enabled', 'cart_enabled', 'show_facebook', 'show_instagram', 'show_youtube', 'countdown_enabled']:
        if field in data:
            val = data.get(field)
            if isinstance(val, str):
                update_data[field] = 1 if val.lower() in ('true', '1', 'yes', 'on') else 0
            else:
                update_data[field] = 1 if bool(val) else 0
            
    if 'cart_min_value' in data:
        try:
            update_data['cart_min_value'] = float(data.get('cart_min_value') or 0.0)
        except ValueError:
            pass

    if 'standard_delivery_days' in data:
        try:
            update_data['standard_delivery_days'] = int(data.get('standard_delivery_days') or 5)
        except (ValueError, TypeError):
            pass

    if 'preorder_delivery_days' in data:
        try:
            update_data['preorder_delivery_days'] = int(data.get('preorder_delivery_days') or 15)
        except (ValueError, TypeError):
            pass
            
    new_password = data.get('new_password', '').strip()
    if new_password:
        update_data['admin_password_hash'] = generate_password_hash(new_password)
        
    if update_data:
        db.collection('settings').document('global').update(update_data)
        touch_catalogue_update()
    
    return jsonify({'success': True, 'message': 'Settings saved successfully!'})

# PRODUCTS API
@app.route('/api/admin/products', methods=['GET', 'POST', 'PUT', 'DELETE'])
@login_required
def api_admin_products():
    if request.method == 'GET':
        p_id = request.args.get('id')
        if p_id:
            doc = db.collection('products').document(p_id).get()
            if not doc.exists:
                return jsonify({'success': False, 'message': 'Product not found'}), 404
            p_data = doc.to_dict()
            p_data['id'] = doc.id
            return jsonify(p_data)
        else:
            products = []
            categories_cache = get_cache('categories')
            for p in get_cache('products'):
                p_dict = dict(p)
                cat = next((c for c in categories_cache if str(c['id']) == str(p_dict['category_id'])), None)
                p_dict['category_name'] = cat['name'] if cat else 'Uncategorized'
                products.append(p_dict)
            return jsonify(products)
            
    elif request.method == 'POST':
        data = request.json or {}
        name = str(data.get('name') or '').strip()
        category_id = str(data.get('category_id') or '').strip()
        price_val = data.get('price')
        
        # Validation of required fields
        if not name:
            return jsonify({'success': False, 'message': 'Product name is required.'}), 400
        if not category_id:
            return jsonify({'success': False, 'message': 'Category is required.'}), 400
        try:
            price = float(price_val or 0.0)
            if price <= 0:
                return jsonify({'success': False, 'message': 'Price must be a positive number.'}), 400
        except (ValueError, TypeError):
            return jsonify({'success': False, 'message': 'Price must be a valid number.'}), 400
            
        slug = slugify(name)
        
        # Check slug uniqueness
        all_prods = get_cache('products')
        exist = any(p['slug'] == slug for p in all_prods)
        if exist:
            slug = f"{slug}-{uuid.uuid4().hex[:6]}"
            
        p_id = str(int(max([float(p['id']) for p in all_prods] or [0])) + 1)
        
        # Extract B2B attributes
        dealer_status = data.get('dealer_status', 'visible')
        dealer_prices = data.get('dealer_prices', {})
        if not dealer_prices:
            default_wholesale = float(data.get('wholesale_price') or 0.0)
            dealer_prices = {'default': default_wholesale}

        specs = data.get('specifications', {})
        if not isinstance(specs, dict):
            specs = {}
        if dealer_prices and 'default' in dealer_prices:
            specs['_wholesale_price'] = float(dealer_prices['default'])

        try:
            cat_id_int = int(category_id)
        except ValueError:
            return jsonify({'success': False, 'message': 'Category must be a valid selection.'}), 400

        try:
            subcat_val = data.get('subcategory_id')
            subcat_id_int = int(subcat_val) if subcat_val else None
        except ValueError:
            subcat_id_int = None

        # Extract Inventory attributes
        stock_status = data.get('stock_status', 'in_stock') or 'in_stock'
        try:
            stock_quantity = int(data.get('stock_quantity') if data.get('stock_quantity') is not None and str(data.get('stock_quantity')).strip() != '' else 10)
        except (ValueError, TypeError):
            stock_quantity = 10
        allow_preorder = bool(data.get('allow_preorder', False))

        now = datetime.utcnow()
        doc_ref = db.collection('products').document(p_id)
        try:
            doc_ref.set({
                'category_id': cat_id_int,
                'subcategory_id': subcat_id_int,
                'name': name,
                'slug': slug,
                'sku': str(data.get('sku') or '').strip() or f"MSE-{uuid.uuid4().hex[:8].upper()}",
            'short_description': str(data.get('short_description') or '').strip(),
            'description': str(data.get('description') or '').strip(),
            'price': price,
            'offer_price': float(data.get('offer_price')) if data.get('offer_price') else None,
            'offer_badge': str(data.get('offer_badge') or '').strip() or None,
            'status': data.get('status', 'active'),
            'is_featured': 1 if data.get('is_featured') else 0,
            'is_new_arrival': 1 if data.get('is_new_arrival') else 0,
            'is_best_seller': 1 if data.get('is_best_seller') else 0,
            'is_premium': 1 if data.get('is_premium') else 0,
            'specifications': specs,
            'features': data.get('features', []),
            'images': data.get('images', []),
            'variants': data.get('variants', []),
            'display_order': int(data.get('display_order') or 0),
            'created_at': now,
            'updated_at': now,
            'createdAt': now.isoformat(),
            'updatedAt': now.isoformat(),
            'wishlist_count': 0,
            'cart_count': 0,
            'dealer_prices': dealer_prices,
            'dealer_status': dealer_status,
            'stock_status': stock_status,
            'stock_quantity': stock_quantity,
            'allow_preorder': allow_preorder
            })
        except Exception as e:
            return jsonify({'success': False, 'message': f'Database Error: {str(e)}'}), 500
            
        try:
            from supabase_db import supabase_client
            for idx, img in enumerate(data.get('images', [])):
                if img and str(img).strip():
                    img_id = str(uuid.uuid4().int)[:8]
                    supabase_client.table('product_images').insert({
                        'id': int(img_id),
                        'product_id': int(p_id),
                        'image_url': str(img).strip(),
                        'display_order': idx
                    }).execute()
            for idx, var in enumerate(data.get('variants', [])):
                var_name = var.get('name', f'Variant {idx}')
                var_val = var.get('value', '')
                if var_name or var_val:
                    var_id = str(uuid.uuid4().int)[:8]
                    supabase_client.table('product_variants').insert({
                        'id': int(var_id),
                        'product_id': int(p_id),
                        'name': str(var_name),
                        'value': str(var_val),
                        'price_adjustment': float(var.get('price_adjustment', 0))
                    }).execute()
        except Exception as e:
            print(f"Failed to add images/variants natively: {e}")
            
        touch_catalogue_update()
        return jsonify({'success': True, 'message': 'Product created successfully!', 'id': p_id})
        
    elif request.method == 'PUT':
        data = request.json or {}
        p_id = data.get('id')
        if not p_id:
            return jsonify({'success': False, 'message': 'Product ID missing.'}), 400
            
        name = str(data.get('name') or '').strip()
        category_id = str(data.get('category_id') or '').strip()
        price_val = data.get('price')
        
        # Validation of required fields
        if not name:
            return jsonify({'success': False, 'message': 'Product name is required.'}), 400
        if not category_id:
            return jsonify({'success': False, 'message': 'Category is required.'}), 400
        try:
            price = float(price_val or 0.0)
            if price <= 0:
                return jsonify({'success': False, 'message': 'Price must be a positive number.'}), 400
        except (ValueError, TypeError):
            return jsonify({'success': False, 'message': 'Price must be a valid number.'}), 400
            
        slug = slugify(name)
        
        # Check slug uniqueness excluding self
        all_prods = get_cache('products')
        exist = any(p['slug'] == slug and p['id'] != p_id for p in all_prods)
        if exist:
            slug = f"{slug}-{uuid.uuid4().hex[:6]}"
            
        # Extract B2B attributes
        dealer_status = data.get('dealer_status', 'visible')
        dealer_prices = data.get('dealer_prices', {})
        if not dealer_prices:
            default_wholesale = float(data.get('wholesale_price') or 0.0)
            dealer_prices = {'default': default_wholesale}

        specs = data.get('specifications', {})
        if not isinstance(specs, dict):
            specs = {}
        if dealer_prices and 'default' in dealer_prices:
            specs['_wholesale_price'] = float(dealer_prices['default'])

        try:
            cat_id_int = int(category_id)
        except ValueError:
            return jsonify({'success': False, 'message': 'Category must be a valid selection.'}), 400

        try:
            subcat_val = data.get('subcategory_id')
            subcat_id_int = int(subcat_val) if subcat_val else None
        except ValueError:
            subcat_id_int = None

        # Extract Inventory attributes
        stock_status = data.get('stock_status', 'in_stock') or 'in_stock'
        try:
            stock_quantity = int(data.get('stock_quantity') if data.get('stock_quantity') is not None and str(data.get('stock_quantity')).strip() != '' else 10)
        except (ValueError, TypeError):
            stock_quantity = 10
        allow_preorder = bool(data.get('allow_preorder', False))

        now = datetime.utcnow()
        try:
            db.collection('products').document(p_id).update({
                'category_id': cat_id_int,
                'subcategory_id': subcat_id_int,
            'name': name,
            'slug': slug,
            'sku': str(data.get('sku') or '').strip(),
            'short_description': str(data.get('short_description') or '').strip(),
            'description': str(data.get('description') or '').strip(),
            'price': price,
            'offer_price': float(data.get('offer_price')) if data.get('offer_price') else None,
            'offer_badge': str(data.get('offer_badge') or '').strip() or None,
            'status': data.get('status', 'active'),
            'is_featured': 1 if data.get('is_featured') else 0,
            'is_new_arrival': 1 if data.get('is_new_arrival') else 0,
            'is_best_seller': 1 if data.get('is_best_seller') else 0,
            'is_premium': 1 if data.get('is_premium') else 0,
            'specifications': specs,
            'features': data.get('features', []),
            'images': data.get('images', []),
            'variants': data.get('variants', []),
            'display_order': int(data.get('display_order') or 0),
            'updated_at': now,
            'updatedAt': now.isoformat(),
            'dealer_prices': dealer_prices,
            'dealer_status': dealer_status,
            'stock_status': stock_status,
            'stock_quantity': stock_quantity,
            'allow_preorder': allow_preorder
            })
        except Exception as e:
            return jsonify({'success': False, 'message': f'Database Error: {str(e)}'}), 500
            
        try:
            from supabase_db import supabase_client
            supabase_client.table('product_images').delete().eq('product_id', int(p_id)).execute()
            supabase_client.table('product_variants').delete().eq('product_id', int(p_id)).execute()
            for idx, img in enumerate(data.get('images', [])):
                if img and str(img).strip():
                    img_id = str(uuid.uuid4().int)[:8]
                    supabase_client.table('product_images').insert({
                        'id': int(img_id),
                        'product_id': int(p_id),
                        'image_url': str(img).strip(),
                        'display_order': idx
                    }).execute()
            for idx, var in enumerate(data.get('variants', [])):
                var_name = var.get('name', f'Variant {idx}')
                var_val = var.get('value', '')
                if var_name or var_val:
                    var_id = str(uuid.uuid4().int)[:8]
                    supabase_client.table('product_variants').insert({
                        'id': int(var_id),
                        'product_id': int(p_id),
                        'name': str(var_name),
                        'value': str(var_val),
                        'price_adjustment': float(var.get('price_adjustment', 0))
                    }).execute()
        except Exception as e:
            print(f"Failed to update images/variants natively: {e}")
            
        touch_catalogue_update()
        return jsonify({'success': True, 'message': 'Product updated successfully!'})
        
    elif request.method == 'DELETE':
        p_id = request.args.get('id')
        if not p_id:
            return jsonify({'success': False, 'message': 'Product ID missing.'}), 400
            
        try:
            db.collection('products').document(p_id).delete()
        except Exception as e:
            return jsonify({'success': False, 'message': f'Database Error: {str(e)}'}), 500
            
        touch_catalogue_update()
        return jsonify({'success': True, 'message': 'Product deleted successfully!'})

# DUPLICATE PRODUCT API
@app.route('/api/admin/products/duplicate', methods=['POST'])
@login_required
def api_admin_duplicate_product():
    p_id = request.json.get('id')
    if not p_id:
        return jsonify({'success': False, 'message': 'Product ID missing.'}), 400
        
    doc = db.collection('products').document(p_id).get()
    if not doc.exists:
        return jsonify({'success': False, 'message': 'Product not found'}), 404
        
    p_dict = doc.to_dict()
    
    new_name = f"{p_dict['name']} (Copy)"
    new_slug = f"{p_dict['slug']}-copy-{uuid.uuid4().hex[:4]}"
    new_sku = f"COPY-{p_dict['sku']}-{uuid.uuid4().hex[:4].upper()}"
    
    all_prods = get_cache('products')
    new_id = str(int(max([float(p['id']) for p in all_prods] or [0])) + 1)
    
    try:
        db.collection('products').document(new_id).set({
            'category_id': int(p_dict['category_id']) if str(p_dict.get('category_id')).isdigit() else p_dict.get('category_id'),
            'subcategory_id': int(p_dict['subcategory_id']) if str(p_dict.get('subcategory_id')).isdigit() else p_dict.get('subcategory_id'),
            'name': new_name,
            'slug': new_slug,
            'sku': new_sku,
            'short_description': p_dict.get('short_description'),
            'description': p_dict.get('description'),
            'price': p_dict.get('price'),
            'offer_price': p_dict.get('offer_price'),
            'offer_badge': p_dict.get('offer_badge'),
            'status': 'draft',
            'is_featured': p_dict.get('is_featured', 0),
            'is_new_arrival': p_dict.get('is_new_arrival', 0),
            'is_best_seller': p_dict.get('is_best_seller', 0),
            'is_premium': p_dict.get('is_premium', 0),
            'specifications': p_dict.get('specifications', {}),
            'features': p_dict.get('features', []),
            'images': p_dict.get('images', []),
            'variants': p_dict.get('variants', []),
            'display_order': p_dict.get('display_order', 0),
            'created_at': datetime.utcnow(),
            'wishlist_count': 0,
            'cart_count': 0,
            'stock_status': p_dict.get('stock_status', 'in_stock'),
            'stock_quantity': p_dict.get('stock_quantity', 10),
            'allow_preorder': p_dict.get('allow_preorder', False)
        })
    except Exception as e:
        return jsonify({'success': False, 'message': f'Database Error: {str(e)}'}), 500
        
    touch_catalogue_update()
    return jsonify({'success': True, 'message': 'Product duplicated as draft successfully!'})

# CATEGORY CRUD API
@app.route('/api/admin/categories', methods=['GET', 'POST', 'PUT', 'DELETE'])
@login_required
def api_admin_categories():
    if request.method == 'GET':
        c_id = request.args.get('id')
        if c_id:
            doc = db.collection('categories').document(c_id).get()
            if doc.exists:
                c_data = doc.to_dict()
                c_data['id'] = doc.id
                return jsonify(c_data)
            return jsonify({})
            
    elif request.method == 'POST':
        data = request.json
        name = data.get('name', '').strip()
        slug = slugify(name)
        
        all_cats = get_cache('categories')
        exist = any(c['slug'] == slug for c in all_cats)
        if exist:
            slug = f"{slug}-{uuid.uuid4().hex[:4]}"
            
        c_id = str(int(max([float(c['id']) for c in all_cats] or [0])) + 1)
        
        db.collection('categories').document(c_id).set({
            'name': name,
            'slug': slug,
            'image_url': data.get('image_url', '').strip(),
            'description': data.get('description', '').strip(),
            'display_order': int(data.get('display_order') or 0),
            'status': data.get('status', 'active')
        })
        touch_catalogue_update()
        return jsonify({'success': True, 'message': 'Category created successfully!'})
        
    elif request.method == 'PUT':
        data = request.json
        c_id = data.get('id')
        name = data.get('name', '').strip()
        slug = slugify(name)
        
        all_cats = get_cache('categories')
        exist = any(c['slug'] == slug and c['id'] != c_id for c in all_cats)
        if exist:
            slug = f"{slug}-{uuid.uuid4().hex[:4]}"
            
        db.collection('categories').document(c_id).update({
            'name': name,
            'slug': slug,
            'image_url': data.get('image_url', '').strip(),
            'description': data.get('description', '').strip(),
            'display_order': int(data.get('display_order') or 0),
            'status': data.get('status', 'active')
        })
        touch_catalogue_update()
        return jsonify({'success': True, 'message': 'Category updated successfully!'})
        
    elif request.method == 'DELETE':
        c_id = request.args.get('id')
        db.collection('categories').document(c_id).delete()
        touch_catalogue_update()
        return jsonify({'success': True, 'message': 'Category deleted successfully!'})

# SUBCATEGORY CRUD API
@app.route('/api/admin/subcategories', methods=['GET', 'POST', 'PUT', 'DELETE'])
@login_required
def api_admin_subcategories():
    if request.method == 'GET':
        s_id = request.args.get('id')
        if s_id:
            doc = db.collection('subcategories').document(s_id).get()
            if doc.exists:
                s_data = doc.to_dict()
                s_data['id'] = doc.id
                return jsonify(s_data)
            return jsonify({})
            
    elif request.method == 'POST':
        data = request.json
        name = data.get('name', '').strip()
        slug = slugify(name)
        
        all_subs = get_cache('subcategories')
        exist = any(s['slug'] == slug for s in all_subs)
        if exist:
            slug = f"{slug}-{uuid.uuid4().hex[:4]}"
            
        s_id = str(int(max([float(s['id']) for s in all_subs] or [0])) + 1)
        
        db.collection('subcategories').document(s_id).set({
            'category_id': str(data.get('category_id')),
            'name': name,
            'slug': slug,
            'display_order': int(data.get('display_order') or 0),
            'status': data.get('status', 'active')
        })
        touch_catalogue_update()
        return jsonify({'success': True, 'message': 'Subcategory created successfully!'})
        
    elif request.method == 'PUT':
        data = request.json
        s_id = data.get('id')
        name = data.get('name', '').strip()
        slug = slugify(name)
        
        all_subs = get_cache('subcategories')
        exist = any(s['slug'] == slug and s['id'] != s_id for s in all_subs)
        if exist:
            slug = f"{slug}-{uuid.uuid4().hex[:4]}"
            
        db.collection('subcategories').document(s_id).update({
            'category_id': str(data.get('category_id')),
            'name': name,
            'slug': slug,
            'display_order': int(data.get('display_order') or 0),
            'status': data.get('status', 'active')
        })
        touch_catalogue_update()
        return jsonify({'success': True, 'message': 'Subcategory updated successfully!'})
        
    elif request.method == 'DELETE':
        s_id = request.args.get('id')
        db.collection('subcategories').document(s_id).delete()
        touch_catalogue_update()
        return jsonify({'success': True, 'message': 'Subcategory deleted successfully!'})

# HERO BANNER API
@app.route('/api/admin/hero_banners', methods=['GET', 'POST', 'PUT', 'DELETE'])
@login_required
def api_admin_hero_banners():
    if request.method == 'GET':
        b_id = request.args.get('id')
        if b_id:
            doc = db.collection('hero_banners').document(b_id).get()
            if doc.exists:
                b_data = doc.to_dict()
                b_data['id'] = doc.id
                return jsonify(b_data)
            return jsonify({})
            
    elif request.method == 'POST':
        data = request.json
        all_banners = get_cache('hero_banners')
        b_id = str(int(max([float(b['id']) for b in all_banners] or [0])) + 1)
        
        db.collection('hero_banners').document(b_id).set({
            'image_url': data.get('image_url', '').strip(),
            'title': data.get('title', '').strip(),
            'subtitle': data.get('subtitle', '').strip(),
            'link_text': data.get('link_text', '').strip(),
            'link_url': data.get('link_url', '').strip(),
            'display_order': int(data.get('display_order') or 0),
            'status': data.get('status', 'active')
        })
        touch_catalogue_update()
        return jsonify({'success': True, 'message': 'Hero banner created successfully!'})
        
    elif request.method == 'PUT':
        data = request.json
        b_id = data.get('id')
        db.collection('hero_banners').document(b_id).update({
            'image_url': data.get('image_url', '').strip(),
            'title': data.get('title', '').strip(),
            'subtitle': data.get('subtitle', '').strip(),
            'link_text': data.get('link_text', '').strip(),
            'link_url': data.get('link_url', '').strip(),
            'display_order': int(data.get('display_order') or 0),
            'status': data.get('status', 'active')
        })
        touch_catalogue_update()
        return jsonify({'success': True, 'message': 'Hero banner updated successfully!'})
        
    elif request.method == 'DELETE':
        b_id = request.args.get('id')
        db.collection('hero_banners').document(b_id).delete()
        touch_catalogue_update()
        return jsonify({'success': True, 'message': 'Hero banner deleted successfully!'})

# OFFER BANNER API
@app.route('/api/admin/offer_banners', methods=['GET', 'POST', 'PUT', 'DELETE'])
@login_required
def api_admin_offer_banners():
    if request.method == 'GET':
        b_id = request.args.get('id')
        if b_id:
            doc = db.collection('offer_banners').document(b_id).get()
            if doc.exists:
                b_data = doc.to_dict()
                b_data['id'] = doc.id
                return jsonify(b_data)
            return jsonify({})
            
    elif request.method == 'POST':
        data = request.json
        all_banners = get_cache('offer_banners')
        b_id = str(int(max([float(b['id']) for b in all_banners] or [0])) + 1)
        
        db.collection('offer_banners').document(b_id).set({
            'image_url': data.get('image_url', '').strip(),
            'title': data.get('title', '').strip(),
            'subtitle': data.get('subtitle', '').strip(),
            'ending_date': data.get('ending_date', '').strip(),
            'button_text': data.get('button_text', '').strip(),
            'button_link': data.get('button_link', '').strip(),
            'display_order': int(data.get('display_order') or 0),
            'status': data.get('status', 'active')
        })
        touch_catalogue_update()
        return jsonify({'success': True, 'message': 'Offer banner created successfully!'})
        
    elif request.method == 'PUT':
        data = request.json
        b_id = data.get('id')
        db.collection('offer_banners').document(b_id).update({
            'image_url': data.get('image_url', '').strip(),
            'title': data.get('title', '').strip(),
            'subtitle': data.get('subtitle', '').strip(),
            'ending_date': data.get('ending_date', '').strip(),
            'button_text': data.get('button_text', '').strip(),
            'button_link': data.get('button_link', '').strip(),
            'display_order': int(data.get('display_order') or 0),
            'status': data.get('status', 'active')
        })
        touch_catalogue_update()
        return jsonify({'success': True, 'message': 'Offer banner updated successfully!'})
        
    elif request.method == 'DELETE':
        b_id = request.args.get('id')
        db.collection('offer_banners').document(b_id).delete()
        touch_catalogue_update()
        return jsonify({'success': True, 'message': 'Offer banner deleted successfully!'})

# TESTIMONIALS API
@app.route('/api/admin/testimonials', methods=['GET', 'POST', 'PUT', 'DELETE'])
@login_required
def api_admin_testimonials():
    if request.method == 'GET':
        t_id = request.args.get('id')
        if t_id:
            doc = db.collection('testimonials').document(t_id).get()
            if doc.exists:
                t_data = doc.to_dict()
                t_data['id'] = doc.id
                return jsonify(t_data)
            return jsonify({})
            
    elif request.method == 'POST':
        data = request.json
        all_t = get_cache('testimonials')
        t_id = str(int(max([float(t['id']) for t in all_t] or [0])) + 1)
        
        db.collection('testimonials').document(t_id).set({
            'customer_name': data.get('customer_name', '').strip(),
            'customer_photo': data.get('customer_photo', '').strip(),
            'city': data.get('city', '').strip(),
            'rating': int(data.get('rating') or 5),
            'review': data.get('review', '').strip(),
            'status': data.get('status', 'active'),
            'display_order': int(data.get('display_order') or 0)
        })
        touch_catalogue_update()
        return jsonify({'success': True, 'message': 'Testimonial created successfully!'})
        
    elif request.method == 'PUT':
        data = request.json
        t_id = data.get('id')
        db.collection('testimonials').document(t_id).update({
            'customer_name': data.get('customer_name', '').strip(),
            'customer_photo': data.get('customer_photo', '').strip(),
            'city': data.get('city', '').strip(),
            'rating': int(data.get('rating') or 5),
            'review': data.get('review', '').strip(),
            'status': data.get('status', 'active'),
            'display_order': int(data.get('display_order') or 0)
        })
        touch_catalogue_update()
        return jsonify({'success': True, 'message': 'Testimonial updated successfully!'})
        
    elif request.method == 'DELETE':
        t_id = request.args.get('id')
        db.collection('testimonials').document(t_id).delete()
        touch_catalogue_update()
        return jsonify({'success': True, 'message': 'Testimonial deleted successfully!'})

# VIDEO TESTIMONIALS API
@app.route('/api/admin/videos', methods=['GET', 'POST', 'PUT', 'DELETE'])
@login_required
def api_admin_videos():
    if request.method == 'GET':
        v_id = request.args.get('id')
        if v_id:
            doc = db.collection('video_testimonials').document(v_id).get()
            if doc.exists:
                v_data = doc.to_dict()
                v_data['id'] = doc.id
                return jsonify(v_data)
            return jsonify({})
            
    elif request.method == 'POST':
        data = request.json
        all_v = get_cache('video_testimonials')
        v_id = str(int(max([float(v['id']) for v in all_v] or [0])) + 1)
        
        db.collection('video_testimonials').document(v_id).set({
            'customer_name': data.get('customer_name', '').strip(),
            'video_url': data.get('video_url', '').strip(),
            'thumbnail_url': data.get('thumbnail_url', '').strip(),
            'review_text': data.get('review_text', '').strip(),
            'status': data.get('status', 'active'),
            'display_order': int(data.get('display_order') or 0)
        })
        touch_catalogue_update()
        return jsonify({'success': True, 'message': 'Video testimonial created successfully!'})
        
    elif request.method == 'PUT':
        data = request.json
        v_id = data.get('id')
        db.collection('video_testimonials').document(v_id).update({
            'customer_name': data.get('customer_name', '').strip(),
            'video_url': data.get('video_url', '').strip(),
            'thumbnail_url': data.get('thumbnail_url', '').strip(),
            'review_text': data.get('review_text', '').strip(),
            'status': data.get('status', 'active'),
            'display_order': int(data.get('display_order') or 0)
        })
        touch_catalogue_update()
        return jsonify({'success': True, 'message': 'Video testimonial updated successfully!'})
        
    elif request.method == 'DELETE':
        v_id = request.args.get('id')
        db.collection('video_testimonials').document(v_id).delete()
        touch_catalogue_update()
        return jsonify({'success': True, 'message': 'Video testimonial deleted successfully!'})

# REVIEWS APPROVAL/DELETE API
@app.route('/api/admin/reviews', methods=['PUT', 'DELETE'])
@login_required
def api_admin_reviews():
    if request.method == 'PUT':
        r_id = request.json.get('id')
        status = request.json.get('status', 'approved')
        db.collection('reviews').document(r_id).update({'status': status})
        touch_catalogue_update()
        return jsonify({'success': True, 'message': f'Review status updated to {status}!'})
        
    elif request.method == 'DELETE':
        r_id = request.args.get('id')
        db.collection('reviews').document(r_id).delete()
        touch_catalogue_update()
        return jsonify({'success': True, 'message': 'Review deleted successfully!'})

# --- GUEST SESSION MIDDLEWARE & DB-BACKED CART / WISHLIST / UPDATE LOG APIS ---

def get_user_cart_id():
    # First, try to get from the custom persistent cookie
    from flask import request
    cookie_id = request.cookies.get('mse_cart_id')
    if cookie_id:
        return cookie_id
    
    if session.get('dealer_logged_in') and session.get('dealer_id'):
        return f"dealer_{session['dealer_id']}"
    if session.get('b2c_mobile'):
        return f"mobile_{session['b2c_mobile']}"
    
    if 'session_id' not in session:
        session['session_id'] = uuid.uuid4().hex
    return session['session_id']

@app.after_request
def apply_cart_cookie(response):
    from flask import request, session
    if 'session_id' in session and not request.cookies.get('mse_cart_id'):
        # Set persistent cart cookie (1 year duration)
        response.set_cookie('mse_cart_id', session['session_id'], max_age=31536000)
    return response

def merge_guest_cart_to_dealer(guest_session_id, dealer_id):
    dealer_cart_id = f"dealer_{dealer_id}"
    try:
        # Fetch guest items
        guest_items = db.collection('cart_items').where('session_id', '==', guest_session_id).stream()
        for doc in guest_items:
            g_item = doc.to_dict()
            product_id = g_item['product_id']
            variant_id = g_item.get('variant_id') or ''
            qty = g_item['quantity']
            
            d_doc_id = f"{dealer_cart_id}_{product_id}"
            d_doc_ref = db.collection('cart_items').document(d_doc_id)
            d_doc = d_doc_ref.get()
            
            if d_doc.exists:
                new_qty = d_doc.to_dict().get('quantity', 0) + qty
                d_doc_ref.update({'quantity': new_qty})
            else:
                d_doc_ref.set({
                    'session_id': dealer_cart_id,
                    'product_id': product_id,
                    'quantity': qty,
                    'variant_id': variant_id
                })
            doc.reference.delete()
            
        guest_wish = db.collection('wishlist_items').where('session_id', '==', guest_session_id).stream()
        for doc in guest_wish:
            g_wish = doc.to_dict()
            product_id = g_wish['product_id']
            d_wish_id = f"{dealer_cart_id}_{product_id}"
            d_wish_ref = db.collection('wishlist_items').document(d_wish_id)
            if not d_wish_ref.get().exists:
                d_wish_ref.set({
                    'session_id': dealer_cart_id,
                    'product_id': product_id
                })
            doc.reference.delete()
    except Exception as e:
        print(f"Error merging guest cart to dealer: {e}")

def merge_guest_cart_to_mobile(guest_session_id, mobile):
    mobile_cart_id = f"mobile_{mobile}"
    try:
        guest_items = db.collection('cart_items').where('session_id', '==', guest_session_id).stream()
        for doc in guest_items:
            g_item = doc.to_dict()
            product_id = g_item['product_id']
            variant_id = g_item.get('variant_id') or ''
            qty = g_item['quantity']
            
            m_doc_id = f"{mobile_cart_id}_{product_id}"
            m_doc_ref = db.collection('cart_items').document(m_doc_id)
            m_doc = m_doc_ref.get()
            
            if m_doc.exists:
                new_qty = m_doc.to_dict().get('quantity', 0) + qty
                m_doc_ref.update({'quantity': new_qty})
            else:
                m_doc_ref.set({
                    'session_id': mobile_cart_id,
                    'product_id': product_id,
                    'quantity': qty,
                    'variant_id': variant_id
                })
            doc.reference.delete()
            
        guest_wish = db.collection('wishlist_items').where('session_id', '==', guest_session_id).stream()
        for doc in guest_wish:
            g_wish = doc.to_dict()
            product_id = g_wish['product_id']
            m_wish_id = f"{mobile_cart_id}_{product_id}"
            m_wish_ref = db.collection('wishlist_items').document(m_wish_id)
            if not m_wish_ref.get().exists:
                m_wish_ref.set({
                    'session_id': mobile_cart_id,
                    'product_id': product_id
                })
            doc.reference.delete()
    except Exception as e:
        print(f"Error merging guest cart to mobile: {e}")

@app.before_request
def ensure_session_id():
    session.permanent = True
    if 'session_id' not in session:
        session['session_id'] = uuid.uuid4().hex
    if 'user_role' not in session:
        session['user_role'] = 'customer'

@app.route('/api/updates/check')
def api_updates_check():
    last_updated = get_last_update_time()
    return jsonify({'success': True, 'last_updated': last_updated})

@app.route('/api/cart', methods=['GET'])
def api_get_cart():
    session_id = get_user_cart_id()
    rows = db.collection('cart_items').where('session_id', '==', session_id).stream()
    items = []
    products_cache = get_cache('products')
    for doc in rows:
        c = doc.to_dict()
        prod = next((p for p in products_cache if str(p['id']) == str(c['product_id'])), None)
        if prod:
            items.append({
                'product_id': c['product_id'],
                'quantity': c['quantity'],
                'variant_id': c.get('variant_id'),
                'name': prod['name'],
                'slug': prod['slug'],
                'sku': prod.get('sku'),
                'price': prod['price'],
                'offer_price': prod.get('offer_price'),
                'offer_badge': prod.get('offer_badge'),
                'image_url': prod['images'][0] if prod.get('images') else '/static/uploads/products/prod_generic_1.webp'
            })
    total_amount = sum((item['offer_price'] or item['price']) * item['quantity'] for item in items)
    return jsonify({'success': True, 'items': items, 'total_amount': total_amount, 'count': sum(item['quantity'] for item in items)})

@app.route('/api/cart/add', methods=['POST'])
def api_cart_add():
    session_id = get_user_cart_id()
    data = request.json or {}
    product_id = str(data.get('product_id'))
    quantity = int(data.get('quantity', 1))
    variant_id = data.get('variant_id')
    
    if not product_id:
        return jsonify({'success': False, 'message': 'Product ID is required.'}), 400
        
    doc_id = f"{session_id}_{product_id}"
    doc_ref = db.collection('cart_items').document(doc_id)
    doc = doc_ref.get()
    if doc.exists:
        new_qty = doc.to_dict().get('quantity', 0) + quantity
        doc_ref.update({'quantity': new_qty})
    else:
        doc_ref.set({
            'session_id': session_id,
            'product_id': product_id,
            'quantity': quantity,
            'variant_id': variant_id,
            'created_at': datetime.utcnow()
        })
        
    cart_count = 0
    cart_docs = db.collection('cart_items').where('session_id', '==', session_id).stream()
    for c_doc in cart_docs:
        cart_count += c_doc.to_dict().get('quantity', 0)
        
    return jsonify({'success': True, 'cart_count': cart_count, 'message': 'Item added to cart.'})

@app.route('/api/cart/update', methods=['POST'])
def api_cart_update():
    session_id = get_user_cart_id()
    data = request.json or {}
    product_id = str(data.get('product_id'))
    quantity = int(data.get('quantity', 1))
    
    if not product_id:
        return jsonify({'success': False, 'message': 'Product ID is required.'}), 400
        
    doc_id = f"{session_id}_{product_id}"
    doc_ref = db.collection('cart_items').document(doc_id)
    if quantity <= 0:
        doc_ref.delete()
    else:
        doc_ref.update({'quantity': quantity})
        
    cart_count = 0
    total_amount = 0.0
    products_cache = get_cache('products')
    cart_docs = db.collection('cart_items').where('session_id', '==', session_id).stream()
    for c_doc in cart_docs:
        c = c_doc.to_dict()
        qty = c.get('quantity', 0)
        cart_count += qty
        prod = next((p for p in products_cache if str(p['id']) == str(c['product_id'])), None)
        if prod:
            total_amount += (prod.get('offer_price') or prod['price']) * qty
            
    return jsonify({'success': True, 'cart_count': cart_count, 'total_amount': total_amount, 'message': 'Cart updated.'})

@app.route('/api/cart/remove', methods=['POST'])
def api_cart_remove():
    session_id = get_user_cart_id()
    data = request.json or {}
    product_id = str(data.get('product_id'))
    
    if not product_id:
        return jsonify({'success': False, 'message': 'Product ID is required.'}), 400
        
    doc_id = f"{session_id}_{product_id}"
    db.collection('cart_items').document(doc_id).delete()
    
    cart_count = 0
    total_amount = 0.0
    products_cache = get_cache('products')
    cart_docs = db.collection('cart_items').where('session_id', '==', session_id).stream()
    for c_doc in cart_docs:
        c = c_doc.to_dict()
        qty = c.get('quantity', 0)
        cart_count += qty
        prod = next((p for p in products_cache if str(p['id']) == str(c['product_id'])), None)
        if prod:
            total_amount += (prod.get('offer_price') or prod['price']) * qty
            
    return jsonify({'success': True, 'cart_count': cart_count, 'total_amount': total_amount, 'message': 'Item removed.'})

@app.route('/api/cart/clear', methods=['POST'])
def api_cart_clear():
    session_id = get_user_cart_id()
    cart_docs = db.collection('cart_items').where('session_id', '==', session_id).stream()
    batch = db.batch()
    for c_doc in cart_docs:
        batch.delete(c_doc.reference)
    batch.commit()
    return jsonify({'success': True, 'cart_count': 0, 'total_amount': 0, 'message': 'Cart cleared.'})

@app.route('/checkout', methods=['GET'])
def checkout():
    session_id = get_user_cart_id()
    settings = get_settings()
    
    # Check if cart has items
    cart_docs = db.collection('cart_items').where('session_id', '==', session_id).get()
    if len(cart_docs) == 0:
        return redirect('/')
        
    return render_template('checkout.html', settings=settings)

@app.route('/api/order/place', methods=['POST'])
def api_order_place():
    session_id = get_user_cart_id()
    data = request.json or {}
    
    name = str(data.get('fullName') or '').strip()
    mobile = str(data.get('mobileNumber') or '').strip()
    email = str(data.get('email') or '').strip()
    address = str(data.get('deliveryAddress') or '').strip()
    pincode = str(data.get('pincode') or '').strip()
    notes = str(data.get('orderNotes') or '').strip()
    
    # Validate required fields
    if not name or not mobile or not address or not pincode:
        return jsonify({'success': False, 'message': 'All required fields must be filled.'}), 400
        
    # Get cart items
    cart_docs = db.collection('cart_items').where('session_id', '==', session_id).get()
    if len(cart_docs) == 0:
        return jsonify({'success': False, 'message': 'Your cart is empty.'}), 400
        
    items = []
    total_val = 0.0
    products_cache = get_cache('products')
    
    for doc in cart_docs:
        c = doc.to_dict()
        prod = next((p for p in products_cache if str(p['id']) == str(c['product_id'])), None)
        if prod:
            price = prod.get('offer_price') or prod['price']
            subtotal = price * c['quantity']
            image_url = prod['images'][0] if prod.get('images') else '/static/uploads/products/prod_generic_1.webp'
            items.append({
                'product_id': c['product_id'],
                'product_name': prod['name'],
                'product_image': image_url,
                'sku': prod.get('sku', ''),
                'quantity': c['quantity'],
                'variant': c.get('variant_id') or '',
                'unit_price': price,
                'subtotal': subtotal
            })
            total_val += subtotal
            
    # Generate unique order id
    import uuid
    order_id = "MSE-" + datetime.utcnow().strftime('%y%m%d') + "-" + uuid.uuid4().hex[:6].upper()
    
    # Create order doc with the full required database schema
    order_doc = {
        'order_id': order_id,
        'session_id': session_id,
        'customer_name': name,
        'email': email,
        'mobile_number': mobile,
        'delivery_address': address,
        'pincode': pincode,
        'order_notes': notes,
        'items': items,
        'total_value': total_val,
        'payment_method': 'UPI / Offline',
        'payment_status': 'Pending',
        'order_status': 'Pending',
        'created_at': datetime.utcnow(),
        'last_updated': datetime.utcnow()
    }
    
    # Upsert Customer Record
    try:
        db.collection('customers').document(mobile).set({
            'mobile_number': mobile,
            'name': name,
            'email': email,
            'address': address,
            'pincode': pincode,
            'last_active': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }, merge=True)
    except Exception as e:
        print(f"Failed to upsert customer record: {e}")
    
    # Save order in database
    db.collection('orders').document(order_id).set(order_doc)
    
    # Clear cart_items for session
    batch = db.batch()
    for doc in cart_docs:
        batch.delete(doc.reference)
    batch.commit()
    
    # Merge guest cart to the mobile-linked cart identifier
    guest_sess_id = session.get('session_id')
    session['b2c_mobile'] = mobile
    if guest_sess_id:
        merge_guest_cart_to_mobile(guest_sess_id, mobile)
        
    return jsonify({
        'success': True,
        'order_id': order_id,
        'message': 'Order placed successfully!'
    })

@app.route('/order-confirmation', methods=['GET'])
def order_confirmation():
    order_id = request.args.get('id', '')
    settings = get_settings()
    
    order_doc = db.collection('orders').document(order_id).get()
    order_data = order_doc.to_dict() if order_doc.exists else {}
    
    return render_template('order_confirmation.html', order_id=order_id, order=order_data, settings=settings)

@app.route('/api/admin/orders', methods=['GET', 'PUT', 'DELETE'])
@login_required
def api_admin_orders():
    if request.method == 'GET':
        o_id = request.args.get('id')
        if o_id:
            doc = db.collection('orders').document(o_id).get()
            if not doc.exists:
                return jsonify({'success': False, 'message': 'Order not found.'}), 404
            order_data = doc.to_dict()
            if 'created_at' in order_data and hasattr(order_data['created_at'], 'strftime'):
                order_data['created_at'] = order_data['created_at'].strftime('%Y-%m-%d %H:%M:%S')
            return jsonify(order_data)
            
        orders_ref = db.collection('orders').order_by('created_at', direction='DESCENDING').stream()
        orders_list = []
        for doc in orders_ref:
            o = doc.to_dict()
            if 'created_at' in o and hasattr(o['created_at'], 'strftime'):
                o['created_at'] = o['created_at'].strftime('%Y-%m-%d %H:%M:%S')
            orders_list.append(o)
        return jsonify(orders_list)
        
    elif request.method == 'PUT':
        data = request.json or {}
        o_id = data.get('order_id')
        status = data.get('order_status')
        pay_status = data.get('payment_status')
        
        if not o_id:
            return jsonify({'success': False, 'message': 'Missing Order ID.'}), 400
            
        doc_ref = db.collection('orders').document(o_id)
        if not doc_ref.get().exists:
            return jsonify({'success': False, 'message': 'Order not found.'}), 404
            
        update_data = {'last_updated': datetime.utcnow()}
        if status is not None:
            update_data['order_status'] = status
        if pay_status is not None:
            update_data['payment_status'] = pay_status
            
        doc_ref.update(update_data)
        return jsonify({'success': True, 'message': 'Order updated successfully!'})
        
    elif request.method == 'DELETE':
        o_id = request.args.get('id')
        if not o_id:
            return jsonify({'success': False, 'message': 'Order ID missing.'}), 400
            
        db.collection('orders').document(o_id).delete()
        return jsonify({'success': True, 'message': 'Order deleted successfully!'})

@app.route('/api/wishlist', methods=['GET'])
def api_get_wishlist():
    session_id = get_user_cart_id()
    rows = db.collection('wishlist_items').where('session_id', '==', session_id).stream()
    items = []
    products_cache = get_cache('products')
    for doc in rows:
        w = doc.to_dict()
        prod = next((p for p in products_cache if str(p['id']) == str(w['product_id'])), None)
        if prod:
            items.append({
                'product_id': w['product_id'],
                'name': prod['name'],
                'slug': prod['slug'],
                'sku': prod.get('sku'),
                'price': prod['price'],
                'offer_price': prod.get('offer_price'),
                'offer_badge': prod.get('offer_badge'),
                'image_url': prod['images'][0] if prod.get('images') else '/static/uploads/products/prod_generic_1.webp',
                'avg_rating': prod.get('avg_rating', 4.5),
                'reviews_count': prod.get('reviews_count', 12)
            })
    return jsonify({'success': True, 'items': items, 'count': len(items)})

@app.route('/api/wishlist/toggle', methods=['POST'])
def api_wishlist_toggle():
    session_id = get_user_cart_id()
    data = request.json or {}
    product_id = str(data.get('product_id'))
    
    if not product_id:
        return jsonify({'success': False, 'message': 'Product ID is required.'}), 400
        
    doc_id = f"{session_id}_{product_id}"
    doc_ref = db.collection('wishlist_items').document(doc_id)
    doc = doc_ref.get()
    if doc.exists:
        doc_ref.delete()
        is_in = False
        msg = "Item removed from wishlist."
    else:
        doc_ref.set({
            'session_id': session_id,
            'product_id': product_id,
            'created_at': datetime.utcnow()
        })
        is_in = True
        msg = "Item added to wishlist."
        
    wishlist_count = sum(1 for _ in db.collection('wishlist_items').where('session_id', '==', session_id).stream())
    return jsonify({'success': True, 'is_in_wishlist': is_in, 'wishlist_count': wishlist_count, 'message': msg})

@app.route('/api/recently_viewed', methods=['GET'])
def api_get_recently_viewed():
    session_id = get_user_cart_id()
    try:
        rows = db.collection('recently_viewed_items')\
                  .where('session_id', '==', session_id)\
                  .order_by('viewed_at', direction='DESCENDING')\
                  .limit(6)\
                  .get()
    except Exception as e:
        print(f"Index notice (recently_viewed_items): {e}. Falling back to in-memory sorting.")
        try:
            raw_rows = db.collection('recently_viewed_items')\
                          .where('session_id', '==', session_id)\
                          .get()
            
            def get_viewed_at(doc):
                d = doc.to_dict()
                val = d.get('viewed_at')
                if isinstance(val, str):
                    return val
                if val:
                    return val
                return datetime.min
                
            rows = sorted(raw_rows, key=get_viewed_at, reverse=True)[:6]
        except Exception as fallback_err:
            print(f"Fallback query failed: {fallback_err}")
            rows = []
    items = []
    products_cache = get_cache('products')
    for doc in rows:
        r = doc.to_dict()
        prod = next((p for p in products_cache if str(p['id']) == str(r['product_id'])), None)
        if prod:
            items.append({
                'product_id': r['product_id'],
                'name': prod['name'],
                'slug': prod['slug'],
                'sku': prod.get('sku'),
                'price': prod['price'],
                'offer_price': prod.get('offer_price'),
                'offer_badge': prod.get('offer_badge'),
                'image_url': prod['images'][0] if prod.get('images') else '/static/uploads/products/prod_generic_1.webp',
                'avg_rating': prod.get('avg_rating', 4.5),
                'reviews_count': prod.get('reviews_count', 12)
            })
    return jsonify({'success': True, 'items': items})

@app.route('/api/recently_viewed/add', methods=['POST'])
def api_recently_viewed_add():
    session_id = get_user_cart_id()
    data = request.json or {}
    product_id = str(data.get('product_id'))
    
    if not product_id:
        return jsonify({'success': False, 'message': 'Product ID is required.'}), 400
        
    doc_id = f"{session_id}_{product_id}"
    db.collection('recently_viewed_items').document(doc_id).set({
        'session_id': session_id,
        'product_id': product_id,
        'viewed_at': datetime.utcnow()
    })
    return jsonify({'success': True})

@app.route('/wishlist')
def wishlist():
    return render_template('wishlist.html')

@app.route('/cart')
def cart():
    return render_template('cart.html')

@app.route('/category/<slug>')
def category_page(slug):
    categories_cache = get_cache('categories')
    category = next((c for c in categories_cache if c['slug'] == slug and c.get('status') == 'active'), None)
    if not category:
        return redirect(url_for('products'))
        
    category = dict(category)
    
    # Fetch category hero & offer banners from cache
    hero_banner = next((b for b in get_cache('category_hero_banners') if b['category_id'] == category['id'] and b['status'] == 'active'), None)
    offer_banner = next((b for b in get_cache('category_offer_banners') if b['category_id'] == category['id'] and b['status'] == 'active'), None)
    
    subcategories = [s for s in get_cache('subcategories') if s['category_id'] == category['id'] and s['status'] == 'active']
    
    q = request.args.get('q', '').strip()
    subcat_slug = request.args.get('subcategory', '').strip()
    price_max = request.args.get('price_max', '').strip()
    sort_by = request.args.get('sort', 'newest').strip()
    
    featured = request.args.get('featured', '').strip()
    new_arrival = request.args.get('new_arrival', '').strip()
    best_seller = request.args.get('best_seller', '').strip()
    premium = request.args.get('premium', '').strip()
    
    page = int(request.args.get('page', 1))
    per_page = 24
    
    # Filter products locked to category
    filtered_list = get_filtered_products(
        q=q, category_slug=slug, subcat_slug=subcat_slug, price_max=price_max, sort_by=sort_by,
        featured=featured, new_arrival=new_arrival, best_seller=best_seller, premium=premium, status='active'
    )
    
    total_count = len(filtered_list)
    offset = (page - 1) * per_page
    paginated_list = filtered_list[offset:offset+per_page]
    
    enriched_products = []
    for p in paginated_list:
        p_dict = dict(p)
        p_dict['image_url'] = p_dict['images'][0] if p_dict.get('images') else '/static/uploads/products/prod_generic_1.webp'
        p_dict['category_name'] = category['name']
        p_dict['category_slug'] = category['slug']
        enriched_products.append(p_dict)
        
    all_categories = [c for c in categories_cache if c.get('status') == 'active']
    max_db_price = max([p.get('price', 0) for p in get_cache('products')] or [100000])
    total_pages = (total_count + per_page - 1) // per_page
    
    return render_template('category.html',
                           category=category,
                           hero=hero_banner,
                           offer=offer_banner,
                           products=enriched_products,
                           categories=all_categories,
                           subcategories=subcategories,
                           total_count=total_count,
                           page=page,
                           total_pages=total_pages,
                           q=q,
                           subcat_slug=subcat_slug,
                           price_max=price_max,
                           max_db_price=int(max_db_price),
                           sort_by=sort_by,
                           featured=featured,
                           new_arrival=new_arrival,
                           best_seller=best_seller,
                           premium=premium)

@app.route('/api/products/batch', methods=['POST'])
def api_products_batch():
    ids = request.json.get('ids', [])
    if not ids:
        return jsonify([])
        
    # Convert list of IDs to string for matching in cached IDs
    id_strings = [str(i) for i in ids]
    
    results = []
    products_cache = get_cache('products')
    categories_cache = get_cache('categories')
    for p in products_cache:
        if str(p['id']) in id_strings:
            p_dict = dict(p)
            p_dict['image_url'] = p_dict['images'][0] if p_dict.get('images') else '/static/uploads/products/prod_generic_1.webp'
            cat = next((c for c in categories_cache if str(c['id']) == str(p_dict.get('category_id'))), None)
            p_dict['category_name'] = cat['name'] if cat else 'Furniture'
            results.append(p_dict)
            
    # Retain the exact order requested in parameters
    ordered_results = []
    for req_id in id_strings:
        match = next((item for item in results if str(item['id']) == req_id), None)
        if match:
            ordered_results.append(match)
            
    return jsonify(ordered_results)

@app.route('/api/stats/wishlist', methods=['POST'])
def api_stats_wishlist():
    data = request.json or {}
    p_id = data.get('id')
    if p_id:
        db.collection('products').document(str(p_id)).update({
            'wishlist_count': Increment(1)
        })
        return jsonify({'success': True})
    return jsonify({'success': False}), 400

@app.route('/api/stats/cart', methods=['POST'])
def api_stats_cart():
    data = request.json or {}
    p_id = data.get('id')
    if p_id:
        db.collection('products').document(str(p_id)).update({
            'cart_count': Increment(1)
        })
        return jsonify({'success': True})
    return jsonify({'success': False}), 400

# CATEGORY HERO BANNERS CRUD API
@app.route('/api/admin/category_hero_banners', methods=['GET', 'POST', 'PUT', 'DELETE'])
@login_required
def api_admin_category_hero_banners():
    if request.method == 'GET':
        c_id = request.args.get('category_id')
        if c_id:
            banner = next((b for b in get_cache('category_hero_banners') if b['category_id'] == str(c_id)), None)
            return jsonify(banner or {})
            
    elif request.method == 'POST':
        data = request.json
        category_id = str(data.get('category_id'))
        image_url = data.get('image_url', '').strip()
        title = data.get('title', '').strip()
        button_text = data.get('button_text', '').strip() or 'Explore Collection'
        offer_text = data.get('offer_text', '').strip()
        status = data.get('status', 'active')
        
        # Check if already exists in cache/db
        all_banners = get_cache('category_hero_banners')
        exist = next((b for b in all_banners if b['category_id'] == category_id), None)
        if exist:
            db.collection('category_hero_banners').document(exist['id']).update({
                'image_url': image_url,
                'title': title,
                'button_text': button_text,
                'offer_text': offer_text,
                'status': status
            })
        else:
            b_id = str(int(max([float(b['id']) for b in all_banners] or [0])) + 1)
            db.collection('category_hero_banners').document(b_id).set({
                'category_id': category_id,
                'image_url': image_url,
                'title': title,
                'button_text': button_text,
                'offer_text': offer_text,
                'status': status
            })
            
        touch_catalogue_update()
        return jsonify({'success': True, 'message': 'Category hero banner saved successfully!'})
        
    elif request.method == 'DELETE':
        b_id = request.args.get('id')
        db.collection('category_hero_banners').document(b_id).delete()
        touch_catalogue_update()
        return jsonify({'success': True, 'message': 'Category hero banner deleted successfully!'})

# CATEGORY OFFER BANNERS CRUD API
@app.route('/api/admin/category_offer_banners', methods=['GET', 'POST', 'PUT', 'DELETE'])
@login_required
def api_admin_category_offer_banners():
    if request.method == 'GET':
        c_id = request.args.get('category_id')
        if c_id:
            banner = next((b for b in get_cache('category_offer_banners') if b['category_id'] == str(c_id)), None)
            return jsonify(banner or {})
            
    elif request.method == 'POST':
        data = request.json
        category_id = str(data.get('category_id'))
        image_url = data.get('image_url', '').strip()
        title = data.get('title', '').strip()
        product_image_url = data.get('product_image_url', '').strip()
        product_price = float(data.get('product_price') or 0.0)
        discount = data.get('discount', '').strip()
        status = data.get('status', 'active')
        
        all_banners = get_cache('category_offer_banners')
        exist = next((b for b in all_banners if b['category_id'] == category_id), None)
        if exist:
            db.collection('category_offer_banners').document(exist['id']).update({
                'image_url': image_url,
                'title': title,
                'product_image_url': product_image_url,
                'product_price': product_price,
                'discount': discount,
                'status': status
            })
        else:
            b_id = str(int(max([float(b['id']) for b in all_banners] or [0])) + 1)
            db.collection('category_offer_banners').document(b_id).set({
                'category_id': category_id,
                'image_url': image_url,
                'title': title,
                'product_image_url': product_image_url,
                'product_price': product_price,
                'discount': discount,
                'status': status
            })
            
        touch_catalogue_update()
        return jsonify({'success': True, 'message': 'Category offer banner saved successfully!'})
        
    elif request.method == 'DELETE':
        b_id = request.args.get('id')
        db.collection('category_offer_banners').document(b_id).delete()
        touch_catalogue_update()
        return jsonify({'success': True, 'message': 'Category offer banner deleted successfully!'})

# --- HELP & POLICY PAGES ---

@app.route('/bulk-enquiry', methods=['GET', 'POST'])
def bulk_enquiry():
    if request.method == 'POST':
        data = request.json or request.form or {}
        name = data.get('name', '').strip()
        email = data.get('email', '').strip()
        phone = data.get('phone', '').strip()
        company = data.get('company', '').strip()
        details = data.get('details', '').strip()
        message_text = details
        if company:
            message_text = f"[{company}] {details}"
        db.collection('bulk_enquiries').document().set({
            'name': name,
            'email': email,
            'phone': phone,
            'company': company,
            'details': details,
            'message': message_text,
            'created_at': datetime.utcnow().isoformat()
        })
        return jsonify({'success': True, 'message': 'Bulk enquiry submitted successfully! We will contact you soon.'})
    return render_template('bulk_enquiry.html')

@app.route('/terms-and-conditions')
def terms_conditions():
    return render_template('terms_conditions.html')

@app.route('/privacy-policy')
def privacy_policy():
    return render_template('privacy_policy.html')

@app.route('/cancellation-policy')
def cancellation_policy():
    return render_template('cancellation_policy.html')

@app.route('/refund-policy')
def refund_policy():
    return render_template('refund_policy.html')

# --- PUBLIC TESTIMONIALS SUBMISSION ---

@app.route('/api/testimonials', methods=['POST'])
def api_submit_testimonial():
    data = request.json or request.form
    customer_name = data.get('customer_name', '').strip()
    city = data.get('city', '').strip()
    rating = int(data.get('rating') or 5)
    review = data.get('review', '').strip()
    
    if not (customer_name and rating and review):
        return jsonify({'success': False, 'message': 'Customer Name, Rating, and Review content are required.'}), 400
        
    reviewer_full = f"{customer_name} ({city})" if city else customer_name
    doc_ref = db.collection('reviews').document()
    doc_ref.set({
        'product_id': 'general',
        'reviewer_name': reviewer_full,
        'rating': rating,
        'review_text': review,
        'status': 'pending',
        'created_at': datetime.utcnow().isoformat()
    })
    return jsonify({'success': True, 'message': 'Thank you! Your review has been submitted and will appear on the website once approved.'})

# --- STOCK NOTIFICATIONS API ---

@app.route('/api/notify-stock', methods=['POST'])
def api_notify_stock():
    try:
        data = request.json or {}
        product_id = data.get('product_id')
        contact_info = str(data.get('contact_info') or '').strip()
        
        if not product_id:
            return jsonify({'success': False, 'message': 'Product ID is required.'}), 400
        if not contact_info:
            return jsonify({'success': False, 'message': 'Please enter a valid email or phone number.'}), 400
            
        try:
            prod_id_val = int(product_id)
        except (ValueError, TypeError):
            prod_id_val = product_id

        # Insert into Supabase stock_notifications table
        try:
            from supabase_db import supabase_client
            supabase_client.table('stock_notifications').insert({
                'product_id': prod_id_val,
                'contact_info': contact_info,
                'status': 'pending'
            }).execute()
        except Exception as e:
            print(f"Supabase direct insert error for stock notification, using db collection fallback: {e}")
            db.collection('stock_notifications').document().set({
                'product_id': prod_id_val,
                'contact_info': contact_info,
                'status': 'pending',
                'created_at': datetime.utcnow()
            })
            
        return jsonify({
            'success': True,
            'message': "We'll notify you when this is back in stock!"
        })
    except Exception as e:
        print(f"Error in api_notify_stock: {e}")
        return jsonify({'success': False, 'message': 'Failed to save notification request. Please try again.'}), 500

@app.route('/api/admin/stock-notifications', methods=['GET'])
@login_required
def api_admin_stock_notifications():
    try:
        from supabase_db import supabase_client
        products_cache = get_cache('products')
        notifications = []
        if supabase_client:
            res = supabase_client.table('stock_notifications').select('*').order('id', desc=True).execute()
            rows = res.data or []
        else:
            rows = [doc.to_dict() for doc in db.collection('stock_notifications').stream()]
            rows.sort(key=lambda x: str(x.get('created_at', '')), reverse=True)

        for r in rows:
            item = dict(r)
            prod = next((p for p in products_cache if str(p.get('id')) == str(item.get('product_id'))), None)
            item['product_name'] = prod['name'] if prod else f"Product #{item.get('product_id')}"
            item['product_slug'] = prod['slug'] if prod else ''
            created_at_raw = item.get('created_at')
            if created_at_raw:
                try:
                    dt = datetime.fromisoformat(str(created_at_raw).replace('Z', '+00:00'))
                    item['formatted_date'] = dt.strftime('%d-%b-%Y %I:%M %p')
                except Exception:
                    item['formatted_date'] = str(created_at_raw)[:19].replace('T', ' ')
            else:
                item['formatted_date'] = 'N/A'
            notifications.append(item)

        return jsonify({
            'success': True,
            'notifications': notifications
        })
    except Exception as e:
        print(f"Error fetching stock notifications: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/admin/stock-notifications/<int:notif_id>', methods=['DELETE', 'PUT'])
@login_required
def api_admin_stock_notification_detail(notif_id):
    try:
        from supabase_db import supabase_client
        if request.method == 'DELETE':
            if supabase_client:
                supabase_client.table('stock_notifications').delete().eq('id', notif_id).execute()
            else:
                db.collection('stock_notifications').document(str(notif_id)).delete()
            return jsonify({'success': True, 'message': 'Notification deleted successfully.'})
        elif request.method == 'PUT':
            data = request.json or {}
            new_status = data.get('status', 'notified')
            if supabase_client:
                supabase_client.table('stock_notifications').update({'status': new_status}).eq('id', notif_id).execute()
            else:
                db.collection('stock_notifications').document(str(notif_id)).update({'status': new_status})
            return jsonify({'success': True, 'message': f'Status updated to {new_status}.'})
    except Exception as e:
        print(f"Error managing stock notification: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

# --- ESTIMATED DELIVERY CHECKER API ---

@app.route('/api/check-delivery', methods=['POST'])
def api_check_delivery():
    try:
        data = request.json or {}
        pincode = str(data.get('pincode') or '').strip()
        product_id = data.get('product_id')

        # Validation: Check if the pincode is exactly 6 digits. If not, return error: "Please enter a valid 6-digit pincode."
        if not pincode.isdigit() or len(pincode) != 6:
            return jsonify({'success': False, 'message': 'Please enter a valid 6-digit pincode.'}), 400

        if not product_id:
            return jsonify({'success': False, 'message': 'Product ID is required.'}), 400

        # Fetch standard_delivery_days and preorder_delivery_days from settings table (safe fallbacks 5 and 15)
        settings = get_settings()
        try:
            standard_delivery_days = int(settings.get('standard_delivery_days') if settings.get('standard_delivery_days') is not None else 5)
        except (ValueError, TypeError):
            standard_delivery_days = 5

        try:
            preorder_delivery_days = int(settings.get('preorder_delivery_days') if settings.get('preorder_delivery_days') is not None else 15)
        except (ValueError, TypeError):
            preorder_delivery_days = 15

        # Fetch product's stock_status and allow_preorder
        all_products = get_cache('products')
        product = next((p for p in all_products if str(p.get('id')) == str(product_id)), None)
        if not product:
            doc = db.collection('products').document(str(product_id)).get()
            if doc.exists:
                product = doc.to_dict()
                product['id'] = doc.id

        if not product:
            return jsonify({'success': False, 'message': 'Product not found.'}), 404

        stock_status = product.get('stock_status', 'in_stock') or 'in_stock'
        allow_preorder = product.get('allow_preorder', False)
        if isinstance(allow_preorder, str):
            allow_preorder = allow_preorder.lower() in ('true', '1', 'yes')
        else:
            allow_preorder = bool(allow_preorder)

        current_date = datetime.now()

        if stock_status == 'out_of_stock':
            if allow_preorder:
                delivery_date = current_date + timedelta(days=preorder_delivery_days)
                formatted_date = delivery_date.strftime("%a %d-%b")
                return jsonify({
                    'success': True,
                    'delivery_date': formatted_date,
                    'message': f"Estimated delivery by {formatted_date} (Pre-order)"
                })
            else:
                return jsonify({
                    'success': False,
                    'message': 'This item is currently unavailable for delivery.'
                }), 400
        else:
            # in_stock
            delivery_date = current_date + timedelta(days=standard_delivery_days)
            formatted_date = delivery_date.strftime("%a %d-%b")
            return jsonify({
                'success': True,
                'delivery_date': formatted_date,
                'message': f"Estimated delivery by {formatted_date}"
            })

    except Exception as e:
        print(f"Error in api_check_delivery: {e}")
        return jsonify({'success': False, 'message': 'Internal error checking delivery date.'}), 500

# --- USER PROFILE & LOGOUT ---

@app.route('/profile')
def user_profile():
    session['user_role'] = 'customer'
    session_id = session.get('session_id')
    profile_data = {
        'role': session.get('user_role', 'customer'),
        'logged_in': session.get('dealer_logged_in', False),
        'session_id': session_id or 'Guest Session'
    }
    
    dealer_details = None
    dealer_activities = []
    dealer_orders = []
    customer_orders = []
    
    # 1. If Dealer: fetch details, activities, and dealer orders
    if profile_data['logged_in'] and session.get('dealer_id'):
        # Fetch dealer details
        try:
            dealer_doc = db.collection('dealers').document(session['dealer_id']).get()
            if dealer_doc.exists:
                dealer_details = dealer_doc.to_dict()
        except Exception as e:
            print(f"Error fetching dealer profile details: {e}")
            
        # Fetch dealer activities
        try:
            activities_ref = db.collection('dealer_activities')\
                               .where('dealer_id', '==', session['dealer_id'])\
                               .order_by('created_at', direction='DESCENDING')\
                               .limit(15)
            dealer_activities = [doc.to_dict() for doc in activities_ref.get()]
        except Exception as e:
            print(f"Failed to fetch dealer activities from index: {e}. Falling back to in-memory sorting.")
            try:
                fallback_ref = db.collection('dealer_activities')\
                                 .where('dealer_id', '==', session['dealer_id'])
                all_acts = [doc.to_dict() for doc in fallback_ref.stream()]
                
                def get_act_time(x):
                    val = x.get('created_at')
                    if isinstance(val, str):
                        return val
                    if val:
                        return val
                    return datetime.min
                    
                all_acts = sorted(all_acts, key=get_act_time, reverse=True)
                dealer_activities = all_acts[:15]
            except Exception as ex:
                print(f"Error in fallback fetching dealer activities: {ex}")
                
        # Fetch B2B dealer orders
        try:
            d_orders_ref = db.collection('dealer_orders')\
                             .where('dealer_id', '==', session['dealer_id'])\
                             .order_by('created_at', direction='DESCENDING')
            dealer_orders = [doc.to_dict() for doc in d_orders_ref.get()]
        except Exception as e:
            print(f"Failed to fetch dealer orders from index: {e}. Falling back to in-memory stream.")
            try:
                fallback_orders_ref = db.collection('dealer_orders')\
                                        .where('dealer_id', '==', session['dealer_id'])
                all_orders = [doc.to_dict() for doc in fallback_orders_ref.stream()]
                
                def get_ord_time(x):
                    val = x.get('created_at')
                    if isinstance(val, str):
                        return val
                    if val:
                        return val
                    return datetime.min
                all_orders = sorted(all_orders, key=get_ord_time, reverse=True)
                dealer_orders = all_orders
            except Exception as ex:
                print(f"Error in fallback fetching dealer orders: {ex}")

        # Format datetimes to strings for template compatibility
        formatted_activities = []
        for act in dealer_activities:
            if 'created_at' in act:
                if hasattr(act['created_at'], 'strftime'):
                    act['created_at'] = act['created_at'].strftime('%Y-%m-%d %H:%M:%S')
                elif isinstance(act['created_at'], str):
                    act['created_at'] = act['created_at'][:19].replace('T', ' ')
            formatted_activities.append(act)
        dealer_activities = formatted_activities
        
        for o in dealer_orders:
            if 'created_at' in o:
                if hasattr(o['created_at'], 'strftime'):
                    o['created_at'] = o['created_at'].strftime('%Y-%m-%d %H:%M')
                elif isinstance(o['created_at'], str):
                    o['created_at'] = o['created_at'][:16].replace('T', ' ')

    # 2. If Retail Customer (or even if guest/dealer, fetch B2C session/mobile orders):
    if session_id:
        try:
            # Query by session_id
            for doc in db.collection('orders').where('session_id', '==', session_id).stream():
                customer_orders.append(doc.to_dict())
                
            # Query by b2c_mobile if cached in session
            b2c_mobile = session.get('b2c_mobile')
            if b2c_mobile:
                for doc in db.collection('orders').where('mobile_number', '==', b2c_mobile).stream():
                    o = doc.to_dict()
                    if o.get('order_id', o.get('id')) not in [x.get('order_id', x.get('id')) for x in customer_orders]:
                        customer_orders.append(o)
                
                # Also check if it's an order ID directly
                doc = db.collection('orders').document(b2c_mobile).get()
                if doc.exists:
                    o = doc.to_dict()
                    if o.get('order_id', o.get('id')) not in [x.get('order_id', x.get('id')) for x in customer_orders]:
                        customer_orders.append(o)
        except Exception as e:
            print(f"Error fetching B2C customer orders: {e}")
            
        for o in customer_orders:
            if 'created_at' in o:
                if hasattr(o['created_at'], 'strftime'):
                    o['created_at'] = o['created_at'].strftime('%Y-%m-%d %H:%M')
                elif isinstance(o['created_at'], str):
                    o['created_at'] = o['created_at'][:16].replace('T', ' ')
                    
        def get_cust_ord_time(x):
            val = x.get('created_at', '')
            return val
        customer_orders = sorted(customer_orders, key=get_cust_ord_time, reverse=True)

    # 3. Retrieve Customer Cart and Wishlist from Database
    customer_cart = []
    customer_wishlist = []
    try:
        cart_owner_id = get_user_cart_id()
        products_cache = get_cache('products') or []
        
        # Cart Items
        cart_docs = db.collection('cart_items').where('session_id', '==', cart_owner_id).stream()
        for doc in cart_docs:
            c = doc.to_dict()
            prod = next((p for p in products_cache if str(p['id']) == str(c['product_id'])), None)
            if prod:
                customer_cart.append({
                    'product_id': c['product_id'],
                    'quantity': c['quantity'],
                    'variant_id': c.get('variant_id'),
                    'product_name': prod['name'],
                    'product_image': prod.get('image_url', '/static/uploads/products/prod_generic_1.webp'),
                    'unit_price': prod.get('offer_price') or prod.get('price'),
                    'subtotal': (prod.get('offer_price') or prod.get('price')) * c['quantity']
                })
                
        # Wishlist Items
        wishlist_docs = db.collection('wishlist').where('session_id', '==', cart_owner_id).stream()
        for doc in wishlist_docs:
            w = doc.to_dict()
            prod = next((p for p in products_cache if str(p['id']) == str(w['product_id'])), None)
            if prod:
                customer_wishlist.append({
                    'product_id': w['product_id'],
                    'product_name': prod['name'],
                    'product_image': prod.get('image_url', '/static/uploads/products/prod_generic_1.webp'),
                    'unit_price': prod.get('offer_price') or prod.get('price')
                })
    except Exception as e:
        print(f"Error fetching cart/wishlist for profile: {e}")

    return render_template('profile.html', 
                           profile=profile_data, 
                           dealer=dealer_details, 
                           activities=dealer_activities,
                           dealer_orders=dealer_orders,
                           customer_orders=customer_orders,
                           customer_cart=customer_cart,
                           customer_wishlist=customer_wishlist)

@app.route('/api/profile/sync-mobile', methods=['POST'])
def api_profile_sync_mobile():
    data = request.json or {}
    mobile = data.get('mobile', '').strip()
    if not mobile:
        return jsonify({'success': False, 'message': 'Mobile number is required.'}), 400
        
    guest_sess_id = session.get('session_id')
    session['b2c_mobile'] = mobile
    if guest_sess_id:
        merge_guest_cart_to_mobile(guest_sess_id, mobile)
        
    return jsonify({'success': True, 'message': 'Mobile number synced successfully and cart loaded!'})

@app.route('/logout')
def global_logout():
    if session.get('dealer_logged_in'):
        try:
            log_dealer_activity('logout', "Dealer logged out via profile page")
        except Exception as e:
            print(f"Error logging dealer logout activity: {e}")
            
    session.clear()
    flash("You have successfully logged out.", "success")
    return redirect(url_for('index'))

# --- ERROR HANDLERS ---

@app.errorhandler(404)
def page_not_found(e):
    return render_template('error.html', 
                           error_title="Page Not Found", 
                           error_message="The page you are looking for does not exist or has been moved."), 404

@app.errorhandler(500)
@app.errorhandler(Exception)
def internal_server_error(e):
    # Log details to terminal
    print(f"CRITICAL SERVER ERROR: {e}")
    import traceback
    traceback.print_exc()
    return render_template('error.html', 
                           error_title="Something Went Wrong", 
                           error_message="We experienced an unexpected error on our server. Please try again shortly or contact support if the issue persists."), 500

@app.route('/health')
@app.route('/healthz')
def health_check():
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "app": "MS Furniture Gallery"
    }), 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)

import os
import subprocess
import sys

# Ensure pillow is installed
try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("Pillow not found. Installing Pillow package...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "Pillow"])
    from PIL import Image, ImageDraw, ImageFont

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads')
os.makedirs(UPLOAD_DIR, exist_ok=True)

def create_gradient_image(filename, width, height, text, bg_color1, bg_color2, text_color):
    # Create base image
    base = Image.new('RGB', (width, height), bg_color1)
    draw = ImageDraw.Draw(base)
    
    # Draw simple diagonal gradient lines
    for y in range(height):
        # Interpolate color
        factor = y / height
        r = int(bg_color1[0] + factor * (bg_color2[0] - bg_color1[0]))
        g = int(bg_color1[1] + factor * (bg_color2[1] - bg_color1[1]))
        b = int(bg_color1[2] + factor * (bg_color2[2] - bg_color1[2]))
        draw.line([(0, y), (width, y)], fill=(r, g, b))
        
    # Draw nice border
    draw.rectangle([(0, 0), (width - 1, height - 1)], outline=(197, 160, 40), width=2)
    
    # Write text labels
    try:
        # Load standard default font or arial
        font = ImageFont.load_default()
    except Exception:
        font = None
        
    # Standard text draw in center
    draw.text((width // 2, height // 2), text, fill=text_color, anchor="mm", align="center")
    
    filepath = os.path.join(UPLOAD_DIR, filename)
    base.save(filepath, "WEBP", quality=85)
    print(f"Created placeholder: {filename}")

def main():
    # 1. Categories (Webp)
    categories = [
        ("cat_sofas.webp", "Living Sofas"),
        ("cat_beds.webp", "Bedroom Beds"),
        ("cat_dining.webp", "Luxury Dining"),
        ("cat_office.webp", "Office Ergonomics"),
        ("cat_wardrobes.webp", "Modular Wardrobes"),
        ("cat_tables.webp", "Stylised Tables"),
        ("cat_chairs.webp", "Accent Chairs"),
        ("cat_decor.webp", "Decor & Lighting"),
        ("cat_storage.webp", "Storage Cabinets"),
        ("cat_mattresses.webp", "Comfort Mattresses"),
        ("cat_outdoor.webp", "Outdoor Living"),
        ("cat_home_office.webp", "Home Office")
    ]
    for filename, text in categories:
        create_gradient_image(filename, 300, 300, text, (31, 31, 31), (60, 50, 40), (250, 249, 246))

    # 2. Spotlight Covers
    spotlights = [
        ("spot_sofa.webp", "Living Chesterfield Collection"),
        ("spot_dining.webp", "Italian Marble Dining Tops"),
        ("spot_bed.webp", "Hydraulic Bed Frames"),
        ("spot_office.webp", "Workspace Setups"),
        ("spot_decor.webp", "Design Accents")
    ]
    for filename, text in spotlights:
        create_gradient_image(filename, 600, 400, text, (20, 20, 20), (197, 160, 40), (255, 255, 255))

    # 3. Testimonials and Default Avatar
    avatars = [
        ("test_user1.webp", "Kunal S."),
        ("test_user2.webp", "Ananya R."),
        ("test_user3.webp", "Vikram M."),
        ("test_user4.webp", "Pooja S."),
        ("avatar_default.jpg", "User")
    ]
    for filename, text in avatars:
        create_gradient_image(filename, 150, 150, text, (197, 160, 40), (170, 130, 20), (17, 17, 17))

    # 4. Video test thumbs
    vids = [
        ("vid_thumb1.webp", "Walkthrough Video #1"),
        ("vid_thumb2.webp", "Review Showcase #2")
    ]
    for filename, text in vids:
        create_gradient_image(filename, 480, 270, text, (40, 40, 40), (20, 20, 20), (197, 160, 40))

    # 5. Product Generic Bulk Covers
    generics = [
        ("prod_generic_1.webp", "MS Furniture Item A"),
        ("prod_generic_2.webp", "MS Furniture Item B"),
        ("prod_generic_3.webp", "MS Furniture Item C"),
        ("prod_generic_4.webp", "MS Furniture Item D")
    ]
    for filename, text in generics:
        create_gradient_image(filename, 400, 300, text, (246, 245, 242), (220, 215, 210), (17, 17, 17))

    # 6. Hero Banners
    heros = [
        ("hero_banner1.webp", "MS ENTERPRISES\n\nElevate Your Living Room"),
        ("hero_banner2.webp", "MS ENTERPRISES\n\nModular Storage Hydraulic Beds"),
        ("hero_banner3.webp", "MS ENTERPRISES\n\nErgonomic Office Setups")
    ]
    for filename, text in heros:
        create_gradient_image(filename, 1400, 700, text, (17, 17, 17), (40, 35, 30), (250, 249, 246))

    # 7. Offer Banner
    create_gradient_image("offer_festive.webp", 800, 500, "FESTIVE HOME MAKE-OVER\n\nUp to 40% Off", (17, 17, 17), (197, 160, 40), (250, 249, 246))

    # 8. Real Product Gallery Images (8 products, 3 images each)
    slugs = [
        "ms-royal-oak-premium-3-seater-sofa",
        "ms-emperor-l-shape-leatherette-sofa",
        "ms-cloud-ergonomic-recliner-chair",
        "ms-grand-heritage-hydraulic-storage-bed",
        "ms-velvet-crown-tufted-queen-bed",
        "ms-majestic-italian-marble-6-seater-dining-set",
        "ms-ergopro-high-back-office-chair",
        "ms-senator-executive-mahogany-desk"
    ]
    
    for slug in slugs:
        for idx in range(1, 4):
            filename = f"prod_{slug}_{idx}.webp"
            text = f"{slug.replace('-', ' ').title()}\n\nShot #{idx}"
            create_gradient_image(filename, 600, 450, text, (250, 249, 246), (235, 230, 220), (17, 17, 17))

if __name__ == "__main__":
    main()

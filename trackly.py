import requests
from datetime import datetime, timezone
from PIL import Image
from io import BytesIO
import random
import os
import re
from dotenv import load_dotenv

# ========== LOAD ENV ==========
load_dotenv()

# ========== CONFIG ==========

GUMROAD_TOKEN = os.getenv("TRACKLY_GUMROAD_TOKEN")
APP_PASSWORD = os.getenv("TRACKLY_APP_PASSWORD")

BLUESKY_HANDLE = "trackly.bsky.social"
GUMROAD_HOME = "https://trackly.gumroad.com"
HISTORY_FILE = "posted_products.txt"
IMAGE_PATH = "image.jpg"
ALT_TEXT = "trackly.gumroad.com"

# Safety check (important)
if not GUMROAD_TOKEN or not APP_PASSWORD:
    raise RuntimeError("❌ Missing TRACKLY secrets. Check your .env file.")

# ========== HISTORY TRACKING ==========

def load_posted_ids():
    if not os.path.exists(HISTORY_FILE):
        return []
    with open(HISTORY_FILE, "r") as f:
        return f.read().splitlines()

def save_posted_id(product_id):
    with open(HISTORY_FILE, "a") as f:
        f.write(f"{product_id}\n")

# ========== GUMROAD FETCHING ==========

def fetch_gumroad_products():
    url = f"https://api.gumroad.com/v2/products?access_token={GUMROAD_TOKEN}"
    res = requests.get(url, timeout=15)
    res.raise_for_status()
    data = res.json()

    if not data.get("success"):
        raise Exception("❌ Gumroad API request failed.")

    all_products = [
        p for p in data["products"]
        if "Tracker" in p["name"] and p.get("thumbnail_url")
    ]

    posted_ids = load_posted_ids()
    available = [p for p in all_products if p["id"] not in posted_ids]

    if not available:
        print("🔁 All products posted, restarting list.")
        open(HISTORY_FILE, "w").close()
        available = all_products

    return random.choice(available)

def download_image(image_url):
    res = requests.get(image_url, timeout=15)
    img = Image.open(BytesIO(res.content))
    if img.mode != "RGB":
        img = img.convert("RGB")
    img.save(IMAGE_PATH, format="JPEG", quality=85, optimize=True)
    print("✅ Image downloaded.")

# ========== BLUESKY POSTING ==========

def create_session():
    res = requests.post(
        "https://bsky.social/xrpc/com.atproto.server.createSession",
        json={"identifier": BLUESKY_HANDLE, "password": APP_PASSWORD},
        timeout=10
    )
    res.raise_for_status()
    return res.json()

def upload_image(access_token):
    with open(IMAGE_PATH, "rb") as f:
        image_data = f.read()

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "image/jpeg"
    }

    res = requests.post(
        "https://bsky.social/xrpc/com.atproto.repo.uploadBlob",
        headers=headers,
        data=image_data,
        timeout=15
    )
    res.raise_for_status()
    return res.json()["blob"]

def create_post(access_token, did, image_blob, product):
    with Image.open(IMAGE_PATH) as img:
        width, height = img.size

    desc = re.sub("<.*?>", "", product.get("description", "")).strip()
    short_desc = desc.split(".")[0] + "." if "." in desc else desc

    caption = f"{short_desc}\n\nCheck out the full collection:\n{GUMROAD_HOME}"

    post = {
        "$type": "app.bsky.feed.post",
        "text": caption,
        "createdAt": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "embed": {
            "$type": "app.bsky.embed.images",
            "images": [{
                "alt": ALT_TEXT,
                "image": image_blob,
                "aspectRatio": {
                    "width": int(width),
                    "height": int(height)
                }
            }]
        }
    }

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    payload = {
        "repo": did,
        "collection": "app.bsky.feed.post",
        "record": post
    }

    res = requests.post(
        "https://bsky.social/xrpc/com.atproto.repo.createRecord",
        headers=headers,
        json=payload,
        timeout=15
    )

    if res.status_code == 200:
        print("📤 Trackly posted successfully!")
    else:
        print("❌ Posting failed:", res.status_code, res.text)

# ========== MAIN ==========

def main():
    try:
        product = fetch_gumroad_products()
        download_image(product["thumbnail_url"])

        session = create_session()
        access_token = session["accessJwt"]
        did = session["did"]

        image_blob = upload_image(access_token)
        create_post(access_token, did, image_blob, product)
        save_posted_id(product["id"])

    except Exception as e:
        print("❌ Trackly bot error:", e)

if __name__ == "__main__":
    main()

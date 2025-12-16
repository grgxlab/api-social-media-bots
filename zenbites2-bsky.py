from openai import OpenAI  # unused now, kept for future
import requests
import random
from datetime import datetime, timezone
from PIL import Image
from io import BytesIO
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# ========== ENV CONFIG ==========

PIXABAY_API_KEY = os.getenv("PIXABAY_API_KEY")
APP_PASSWORD = os.getenv("ZENBITES_APP_PASSWORD")

BLUESKY_HANDLE = "zenbites.bsky.social"
ALT_TEXT = ""
IMAGE_PATH = "zenbites-image.jpg"

# Safety check (important)
if not PIXABAY_API_KEY or not APP_PASSWORD:
    raise RuntimeError("Missing environment variables. Check your .env file.")

# ========== PROMPTS ==========

PROMPTS = [
    "nature landscape",
    "calm forest",
    "sunrise over mountains",
    "peaceful lake",
    "zen garden",
    "misty morning hills",
    "minimal nature",
    "a path in nature",
    "calm ocean waves",
]

# ========== ZEN QUOTE ==========

def get_zen_quote():
    try:
        res = requests.get("https://zenquotes.io/api/random", timeout=10)
        res.raise_for_status()
        data = res.json()[0]
        return f'"{data["q"]}" – {data["a"]}'
    except Exception as e:
        print("⚠️ Quote fetch failed:", e)
        return "Breathe. You’re doing just fine. 🌿"

# ========== PIXABAY IMAGE ==========

def get_pixabay_image():
    query = random.choice(PROMPTS)
    print(f"🌄 Querying Pixabay for: {query}")

    url = (
        "https://pixabay.com/api/"
        f"?key={PIXABAY_API_KEY}"
        f"&q={query.replace(' ', '+')}"
        "&image_type=photo"
        "&orientation=horizontal"
        "&safesearch=true"
        "&per_page=20"
    )

    response = requests.get(url, timeout=15)
    response.raise_for_status()
    data = response.json()

    if not data.get("hits"):
        raise RuntimeError("No images found on Pixabay.")

    image_url = random.choice(data["hits"])["largeImageURL"]
    print("✅ Image URL:", image_url)
    return image_url

# ========== DOWNLOAD IMAGE ==========

def download_image(image_url):
    img_data = requests.get(image_url, timeout=20).content
    img = Image.open(BytesIO(img_data))

    if img.mode != "RGB":
        img = img.convert("RGB")

    img.save(IMAGE_PATH, format="JPEG", quality=85, optimize=True)
    print("✅ Image saved.")

# ========== BLUESKY API ==========

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

def create_post(access_token, did, image_blob, caption):
    with Image.open(IMAGE_PATH) as img:
        width, height = img.size

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
                    "width": width,
                    "height": height
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
    res.raise_for_status()
    print("📿 Zenbite posted successfully.")

# ========== EXECUTION ==========

try:
    caption = get_zen_quote()
    image_url = get_pixabay_image()
    download_image(image_url)

    session = create_session()
    access_token = session["accessJwt"]
    did = session["did"]

    image_blob = upload_image(access_token)
    create_post(access_token, did, image_blob, caption)

except Exception as e:
    print("❌ Zenbite failed:", e)

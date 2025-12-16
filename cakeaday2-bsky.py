import requests
from datetime import datetime, timezone
from PIL import Image
from io import BytesIO
import random
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# ========== ENV CONFIG ==========

PIXABAY_API_KEY = os.getenv("PIXABAY_API_KEY")
APP_PASSWORD = os.getenv("CAKEADAY_APP_PASSWORD")
BLUESKY_HANDLE = "cakeaday.bsky.social"

ALT_TEXT = ""
IMAGE_PATH = "image.jpg"

# Safety check
if not PIXABAY_API_KEY or not APP_PASSWORD:
    raise RuntimeError("Missing environment variables. Check your .env file.")

# ========== CAKE SEARCH TAGS ==========

CAKE_TAGS = [
    "slice of cake",
    "fruit cake on plate",
    "birthday cake",
    "chocolate cake closeup",
    "strawberry cake",
]

# ========== PIXABAY IMAGE ==========

def get_pixabay_image():
    query = random.choice(CAKE_TAGS)
    print(f"🎂 Searching Pixabay for: {query}")

    url = (
        "https://pixabay.com/api/"
        f"?key={PIXABAY_API_KEY}"
        f"&q={query.replace(' ', '+')}"
        "&category=food"
        "&image_type=photo"
        "&orientation=horizontal"
        "&safesearch=true"
        "&per_page=20"
    )

    res = requests.get(url, timeout=15)
    res.raise_for_status()
    data = res.json()

    cake_images = [
        hit for hit in data["hits"]
        if "cake" in hit["tags"].lower()
    ]

    if not cake_images:
        raise RuntimeError("❌ No clearly cake-related images found!")

    selected = random.choice(cake_images)
    print("✅ Selected image:", selected["largeImageURL"])
    print("📝 Tags:", selected["tags"])
    return selected["largeImageURL"]

def download_image(image_url):
    res = requests.get(image_url, timeout=20)
    img = Image.open(BytesIO(res.content))

    if img.mode != "RGB":
        img = img.convert("RGB")

    img.save(IMAGE_PATH, format="JPEG", quality=85, optimize=True)
    print("✅ Image downloaded and saved.")

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

def create_post(access_token, did, image_blob):
    with Image.open(IMAGE_PATH) as img:
        width, height = img.size

    post = {
        "$type": "app.bsky.feed.post",
        "text": "",
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
    print("🍰 Cake posted successfully!")

# ========== MAIN ==========

def main():
    try:
        image_url = get_pixabay_image()
        download_image(image_url)

        session = create_session()
        access_token = session["accessJwt"]
        did = session["did"]

        image_blob = upload_image(access_token)
        create_post(access_token, did, image_blob)

    except Exception as e:
        print("🎂 Cake-A-Day error:", e)

if __name__ == "__main__":
    main()

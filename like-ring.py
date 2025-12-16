import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load env vars
load_dotenv()

# ========== BOT CONFIGURATION ==========

BOTS = [
    {
        "handle": os.getenv("ZENBITES_HANDLE"),
        "app_password": os.getenv("ZENBITES_APP_PASSWORD")
    },
    {
        "handle": os.getenv("CHICKENADAY_HANDLE"),
        "app_password": os.getenv("CHICKENADAY_APP_PASSWORD")
    },
    {
        "handle": os.getenv("CATSADAY_HANDLE"),
        "app_password": os.getenv("CATSADAY_APP_PASSWORD")
    },
    {
        "handle": os.getenv("CAKEADAY_HANDLE"),
        "app_password": os.getenv("CAKEADAY_APP_PASSWORD")
    },
    {
        "handle": os.getenv("SPACEADAY_HANDLE"),
        "app_password": os.getenv("SPACEADAY_APP_PASSWORD")
    },
    {
        "handle": os.getenv("TRACKLY_HANDLE"),
        "app_password": os.getenv("TRACKLY_APP_PASSWORD")
    },
]

# ========== BLUESKY INTERACTIONS ==========

def create_session(handle, password):
    res = requests.post(
        "https://bsky.social/xrpc/com.atproto.server.createSession",
        json={"identifier": handle, "password": password},
    )
    res.raise_for_status()
    return res.json()

def fetch_latest_post(handle, access_token):
    headers = {"Authorization": f"Bearer {access_token}"}
    res = requests.get(
        f"https://bsky.social/xrpc/app.bsky.feed.getAuthorFeed?actor={handle}&limit=1",
        headers=headers
    )
    res.raise_for_status()
    feed = res.json().get("feed", [])
    if feed:
        return {
            "uri": feed[0]["post"].get("uri"),
            "cid": feed[0]["post"].get("cid")
        }
    return None

def like_post(access_token, post):
    payload = {
        "$type": "app.bsky.feed.like",
        "subject": {
            "uri": post["uri"],
            "cid": post["cid"]
        },
        "createdAt": datetime.utcnow().isoformat() + "Z"
    }

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    res = requests.post(
        "https://bsky.social/xrpc/com.atproto.repo.createRecord",
        headers=headers,
        json={
            "repo": get_did(access_token),
            "collection": "app.bsky.feed.like",
            "record": payload
        }
    )

    if res.status_code == 200:
        print("👍 Liked:", post["uri"])
    else:
        print("❌ Failed to like:", post["uri"], res.status_code, res.text)

def get_did(access_token):
    headers = {"Authorization": f"Bearer {access_token}"}
    res = requests.get("https://bsky.social/xrpc/com.atproto.server.getSession", headers=headers)
    res.raise_for_status()
    return res.json()["did"]

# ========== MAIN ==========

def main():
    print("\n=== Starting Like-Ring Automation ===")
    for liker in BOTS:
        print(f"\n🔐 Logging in as: {liker['handle']}")
        liker_session = create_session(liker['handle'], liker['app_password'])
        liker_token = liker_session["accessJwt"]

        for target in BOTS:
            if target['handle'] == liker['handle']:
                continue  # Skip self-liking

            target_post = fetch_latest_post(target['handle'], liker_token)
            if target_post:
                like_post(liker_token, target_post)

    print("\n✅ Like-Ring Completed")

if __name__ == "__main__":
    main()

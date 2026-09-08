import feedparser
import requests
import time
import os

# --- CONFIGURATION ---
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

# Safety check to ensure environment variables are present
if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
    raise ValueError("Error: TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID is missing from environment variables!")

# Add the subreddits you want to monitor (without the 'r/')
SUBREDDITS = [
        "HungryArtists",
        "artcommissions",
        "gameDevClassifieds",
        "gameDevJobs",
        "hireanartist",
        "artcommissions",
        "fantasyartists",
        "INAT",
        "artstore"
        "BookCovers",
        "artistforhire",
        "ArtBuddy",
        "ComicBookCollabs",
        "dibujo",
        "arte",
        "Mercadoreddit",
        "empleos_AR",
        "vzla",
        "ColombiaEmpleo",
        "TrabajoMexico",
        "devsarg"
    ]

# --- MEMORY SETUP ---
# We use a text file to remember old posts so we don't spam you when the script restarts
MEMORY_FILE = "seen_posts.txt"

def load_seen_posts():
    if not os.path.exists(MEMORY_FILE):
        return set()
    with open(MEMORY_FILE, "r") as f:
        return set(f.read().splitlines())

def save_seen_post(post_id):
    with open(MEMORY_FILE, "a") as f:
        f.write(f"{post_id}\n")

# --- CORE LOGIC ---
def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "disable_web_page_preview": False
    }
    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            print("Successfully sent to Telegram!")
        else:
            print(f"Telegram error: {response.text}")
    except Exception as e:
        print(f"Failed to send message: {e}")

def check_subreddits():
    seen_posts = load_seen_posts()

    # Reddit blocks automated requests unless you pretend to be a normal web browser
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

    for sub in SUBREDDITS:
        print(f"Checking r/{sub}...")
        feed_url = f"https://www.reddit.com/r/{sub}/new.rss"

        try:
            response = requests.get(feed_url, headers=headers)
            feed = feedparser.parse(response.content)

            # Check the 10 newest posts
            for entry in feed.entries:
                post_id = entry.id
                title = entry.title
                title_lower = title.lower()
                link = entry.link

                if post_id not in seen_posts:
                    # 1. ENGLISH FILTER
                    is_hiring_en = any(word in title_lower for word in ['hiring', '[hiring]', 'paid'])
                    is_artist_en = any(word in title_lower for word in ['for hire', '[for hire]', 'hire me', 'portfolio', 'commissions open'])
                    match_en = is_hiring_en and not is_artist_en

                    # 2. SPANISH FILTER
                    # Words a buyer would use
                    is_hiring_es = any(word in title_lower for word in ['busco artista', 'busco dibujante', 'busco ilustrador', 'pago por', 'remunerado', 'encargo'])
                    # Words an artist would use to advertise themselves
                    is_artist_es = any(word in title_lower for word in ['comisiones abiertas', 'mi portafolio', 'mis dibujos', 'hago comisiones', 'precios'])
                    match_es = is_hiring_es and not is_artist_es

                    # 3. COMBINED CHECK
                    if match_en or match_es:
                        print(f"Found a match! {title}")

                        message = f"🚨 **New Hiring Post in r/{sub}**\n\n"
                        message += f"📌 {title}\n\n"
                        message += f"🔗 {link}"

                        send_telegram_message(message)

                    # Mark as seen so we never process it again
                    save_seen_post(post_id)
                    seen_posts.add(post_id)

        except Exception as e:
            print(f"Error checking {sub}: {e}")

# --- ENTRY POINT ---
if __name__ == "__main__":
    print("Running Reddit RSS Monitor...")
    check_subreddits()
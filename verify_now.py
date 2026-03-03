import requests, re, os, json
from datetime import datetime, timezone

VIDEO_ID = "6_9ZiuONXt0"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
}

def get_config():
    print(f"[SEARCH] Fetching config for {VIDEO_ID}...")
    try:
        r = requests.get(f"https://www.youtube.com/watch?v={VIDEO_ID}", headers=HEADERS, timeout=15)
        html = r.text
        key = (re.search(r'"INNERTUBE_API_KEY"\s*:\s*"([^"]+)"', html) or [None,None])[1]
        ver = (re.search(r'"clientVersion"\s*:\s*"([^"]+)"', html) or [None,"2.20240301"])[1]
        vis = (re.search(r'"visitorData"\s*:\s*"([^"]+)"', html) or [None,""])[1]
        
        patterns = [
            r'"invalidationContinuationData"\s*:\s*\{[^}]{0,300}?"continuation"\s*:\s*"([^"]+)"',
            r'"timedContinuationData"\s*:\s*\{[^}]{0,300}?"continuation"\s*:\s*"([^"]+)"',
            r'"continuation"\s*:\s*"([^"]{20,})"',
        ]
        cont = next((re.search(p, html).group(1) for p in patterns if re.search(p, html)), None)
        return key, ver, vis, cont
    except Exception as e:
        print(f"[ERROR] Config error: {e}")
        return None, None, None, None

def fetch_latest():
    key, ver, vis, cont = get_config()
    if not cont:
        print("[OFFLINE] Stream might be offline or blocked.")
        return

    print("[SYNC] Fetching live actions...")
    try:
        r = requests.post(f"https://www.youtube.com/youtubei/v1/live_chat/get_live_chat?key={key}", 
                          json={"context":{"client":{"clientName":"WEB","clientVersion":ver,"visitorData":vis}}, "continuation":cont},
                          headers={"Content-Type":"application/json"}, timeout=10)
        
        if r.status_code != 200:
            print(f"[ERROR] YouTube API Error: {r.status_code}")
            return

        data = r.json()
        actions = data.get("continuationContents",{}).get("liveChatContinuation",{}).get("actions",[])
        
        if not actions:
            print("[INFO] No new actions currently in the live feed.")
            return

        print(f"\n[OK] Found {len(actions)} actions. Recent messages:\n")
        msg_count = 0
        for a in actions:
            if "addChatItemAction" in a:
                rd = a["addChatItemAction"].get("item", {}).get("liveChatTextMessageRenderer", {})
                if not rd: continue
                author = rd.get("authorName",{}).get("simpleText","?")
                txt = "".join(r.get("text","") for r in rd.get("message",{}).get("runs",[]))
                
                # Sanitize for console display
                safe_author = author.encode('ascii', 'ignore').decode('ascii')
                safe_txt = txt.encode('ascii', 'ignore').decode('ascii')
                
                print(f"MSG | {safe_author or 'User'}: {safe_txt}")
                msg_count += 1
        
        if msg_count == 0:
            print("[INFO] No text messages found in current actions.")
            
    except Exception as e:
        print(f"[ERROR] Fetching error: {e}")

if __name__ == "__main__":
    fetch_latest()

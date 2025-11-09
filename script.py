import requests
import time
from config import cookie, universes

def get_csrf_token(session, universe):
    url = f"https://badges.roblox.com/v1/universes/{universe}/badges"
    delay = 2
    attempt = 0
    while True:
        attempt += 1
        response = session.post(url)
        token = response.headers.get("x-csrf-token")
        if token:
            return token
        print(f"CSRF token invalid or missing, retrying in {delay} seconds... (attempt {attempt})")
        time.sleep(delay)

def get_badge_quota(universe):
    url = f"https://badges.roblox.com/v1/universes/{universe}/free-badges-quota"
    delay = 2
    attempt = 0
    while True:
        attempt += 1
        resp = requests.get(url)
        if resp.status_code == 429:
            print(f"HTTP 429 on getting quota, retrying in {delay} seconds... (attempt {attempt})")
            time.sleep(delay)
            continue
        if resp.status_code == 200:
            return resp.json()
        print(f"Failed to get quota (status {resp.status_code}), retrying in {delay} seconds... (attempt {attempt})")
        time.sleep(delay)

def badgecreate(universe):
    print(f"\nStarting badge creation for universe {universe}")
    time.sleep(0.75)

    count = get_badge_quota(universe)
    if count is None:
        print(f"Failed to get quota for universe {universe} after retries.")
        return

    print(f"Free badge quota for universe {universe}: {count}")

    if count <= 0:
        print("No free badges available for creation.")
        return

    with requests.Session() as session:
        session.cookies[".ROBLOSECURITY"] = cookie

        csrf_token = get_csrf_token(session, universe)
        if not csrf_token:
            print("Failed to get CSRF token after retries, aborting.")
            return

        session.headers.update({
            "X-CSRF-TOKEN": csrf_token,
            "Origin": "https://www.roblox.com",
            "Referer": "https://www.roblox.com",
        })

        url = f"https://badges.roblox.com/v1/universes/{universe}/badges"

        for i in range(count):
            delay = 2  # initial delay for backoff
            while True:
                try:
                    with open("icon.png", "rb") as f:
                        files = {"upload_file": f}
                        data = {
                            "name": f"Badge Name", # edit Badge name here
                            "description": "Badge Description", # edit description of badge if you dont want description you can remove it.
                            "paymentSourceType": "User",
                            "expectedCost": 0
                        }
                        response = session.post(url, data=data, files=files)

                    if response.status_code == 429:
                        print(f"Too many requests (429) creating badge #{i+1}, retrying in {delay} seconds...")
                        time.sleep(delay)
                        continue  # retry request

                    if response.status_code == 403 and "x-csrf-token" in response.headers:
                        # Possibly invalid CSRF token, refresh and retry
                        print(f"CSRF token invalid during badge creation, refreshing token and retrying...")
                        csrf_token = get_csrf_token(session, universe)
                        if not csrf_token:
                            print("Failed to refresh CSRF token, aborting badge creation.")
                            return
                        session.headers.update({"X-CSRF-TOKEN": csrf_token})
                        continue  # retry request with new token

                    if response.status_code != 200:
                        print(f"Failed to create badge #{i+1} (status {response.status_code}): {response.text}")
                        break  # stop retrying for this badge

                    badge = response.json()
                    if 'id' in badge:
                        print(f"Badge #{i+1} created successfully with ID: {badge['id']}")
                        break  # badge created, move to next
                    else:
                        print(f"Unexpected response for badge #{i+1}: {badge}")
                        break

                except Exception as e:
                    print(f"Exception occurred while creating badge #{i+1}: {e}")
                    break  # stop retrying on exception

if __name__ == "__main__":
    for uni in universes:
        badgecreate(uni)

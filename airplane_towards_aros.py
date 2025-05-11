import requests
import math
import time
import json
from datetime import datetime, timedelta

# Configuration
AARHUS_LAT = 56.1629
AARHUS_LON = 10.2039
RADIUS_KM = 20
ALTITUDE_MAX = 30000  # feet
DATA_URL = "http://192.168.8.31:8080/data/aircraft.json"
LOG_FILE = "over_aarhus_log.json"

# Pushover setup
PUSHOVER_ENABLED = True
PUSHOVER_TOKEN = "token"
PUSHOVER_USER = "token"
PUSHOVER_COOLDOWN_MINUTES = 5
alerted_recently = {}

# Toggle debug output
DEBUG = False

def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * \
        math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

def calculate_bearing(lat1, lon1, lat2, lon2):
    dlon = math.radians(lon2 - lon1)
    y = math.sin(dlon) * math.cos(math.radians(lat2))
    x = math.cos(math.radians(lat1)) * math.sin(math.radians(lat2)) - \
        math.sin(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.cos(dlon)
    return (math.degrees(math.atan2(y, x)) + 360) % 360

def get_distance_and_bearing(ac):
    lat = ac.get("lat")
    lon = ac.get("lon")
    if lat is None or lon is None:
        return None, None
    distance = haversine(lat, lon, AARHUS_LAT, AARHUS_LON)
    bearing = calculate_bearing(lat, lon, AARHUS_LAT, AARHUS_LON)
    return distance, bearing

def is_heading_toward_aarhus(ac, bearing_to_aarhus):
    heading = ac.get("true_heading") or ac.get("track")
    if heading is None:
        return False
    diff = abs((bearing_to_aarhus - heading + 180) % 360 - 180)
    return diff <= 40  # Can loosen this if needed

def analyze_tags(ac):
    tags = []
    if ac.get("baro_rate", 0) < -256:
        tags.append("descending")
    if ac.get("alt_baro", 99999) < 3000 and ac.get("gs", 9999) < 150:
        tags.append("low_and_slow")
    return tags

def fetch_aircraft():
    try:
        response = requests.get(DATA_URL, timeout=5)
        response.raise_for_status()
        return response.json().get("aircraft", [])
    except Exception as e:
        if DEBUG:
            print(f"Error fetching data: {e}")
        return []

def log_aircraft(ac, distance, bearing, tags):
    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "flight": ac.get("flight", "").strip(),
        "type": ac.get("desc", "?"),
        "altitude_ft": ac.get("alt_baro"),
        "ground_speed": ac.get("gs"),
        "baro_rate": ac.get("baro_rate"),
        "tags": tags,
        "distance_km": round(distance, 2),
        "bearing_deg": round(bearing, 1),
        "lat": ac.get("lat"),
        "lon": ac.get("lon")
    }
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(log_entry) + "\n")

def send_pushover(title, message, key):
    now = datetime.utcnow()
    if key in alerted_recently and now - alerted_recently[key] < timedelta(minutes=PUSHOVER_COOLDOWN_MINUTES):
        return
    alerted_recently[key] = now
    try:
        requests.post("https://api.pushover.net/1/messages.json", data={
            "token": PUSHOVER_TOKEN,
            "user": PUSHOVER_USER,
            "title": title,
            "message": message,
            "priority": 1,
            "sound": "siren"
        })
        print(f"📲 Notification sent: {message}")
    except Exception as e:
        print(f"❌ Failed to send Pushover notification: {e}")

def main():
    print("✈️ Tracking aircraft heading toward Aarhus...\n")
    while True:
        aircraft = fetch_aircraft()
        count = 0
        for ac in aircraft:
            distance, bearing = get_distance_and_bearing(ac)
            altitude = ac.get("alt_baro")
            if distance is None or altitude is None:
                continue
            if (
                distance <= RADIUS_KM
                and altitude <= ALTITUDE_MAX
                and is_heading_toward_aarhus(ac, bearing)
            ):
                tags = analyze_tags(ac)
                count += 1
                print(
                    f"→ {ac.get('flight', '???').strip()} {ac.get('desc', '?')} "
                    f"at {altitude} ft | {distance:.2f} km away, bearing {bearing:.0f}°"
                    + (f" | Tags: {', '.join(tags)}" if tags else "")
                )
                log_aircraft(ac, distance, bearing, tags)

                if PUSHOVER_ENABLED and tags:
                    msg = (
                        f"{ac.get('flight', '???').strip()} {ac.get('desc', '?')} is "
                        f"{', '.join(tags)} at {altitude} ft, {distance:.1f} km away"
                    )
                    key = ac.get("hex", "") + "," + ",".join(tags)
                    send_pushover("Plane over Aarhus", msg, key)

        if count > 0:
            print("-" * 50)

        time.sleep(10)

if __name__ == "__main__":
    main()

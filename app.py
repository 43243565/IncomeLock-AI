import streamlit as st
import random
import pandas as pd
import pydeck as pdk
import requests
import os
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont

def create_incomelock_logo():
    w, h = 420, 140
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Shield
    shield = [(30, 20), (70, 10), (110, 20), (105, 80), (70, 120), (35, 80)]
    draw.polygon(shield, fill=(220, 38, 38, 255), outline=(15, 23, 42, 255))
    inner_shield = [(70, 10), (110, 20), (105, 80), (70, 120)]
    draw.polygon(inner_shield, fill=(226, 232, 240, 255), outline=(15, 23, 42, 255))

    # Lock body
    draw.rounded_rectangle((48, 48, 92, 88), radius=10, fill=(250, 204, 21, 255), outline=(146, 64, 14, 255), width=2)

    # Lock shackle
    draw.arc((54, 28, 86, 62), start=180, end=360, fill=(250, 204, 21, 255), width=6)

    # Keyhole
    draw.ellipse((66, 60, 74, 68), fill=(68, 64, 60, 255))
    draw.rectangle((69, 68, 71, 78), fill=(68, 64, 60, 255))

    # Text
    try:
        font_big = ImageFont.truetype("/System/Library/Fonts/Supplemental/Times New Roman Bold.ttf", 34)
        font_small = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 14)
    except:
        font_big = ImageFont.load_default()
        font_small = ImageFont.load_default()

    draw.text((135, 38), "IncomeLock AI", fill=(15, 23, 42, 255), font=font_big)
    draw.text((138, 80), "Smart income protection", fill=(71, 85, 105, 255), font=font_small)

    return img

logo = create_incomelock_logo()
# =========================================================
# PAGE CONFIG
# =========================================================
st.set_page_config(page_title="IncomeLock AI", layout="centered")

# =========================================================
# SAFE API KEY LOADING
# =========================================================
try:
    OPENWEATHER_API_KEY = st.secrets["OPENWEATHER_API_KEY"]
except Exception:
    OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY", "")

try:
    TOMTOM_API_KEY = st.secrets["TOMTOM_API_KEY"]
except Exception:
    TOMTOM_API_KEY = os.getenv("TOMTOM_API_KEY", "")

# =========================================================
# OPTIONAL LOCAL DATA FILES
# =========================================================
ACTUARIAL_DATA_FILE = "historical_actuarial_data.csv"
OFFICIAL_AQI_FILE = "official_aqi_recent.csv"

# =========================================================
# APP FLOW
# =========================================================
APP_ORDER = [
    "Splash",
    "Registration",
    "Policy Management",
    "Weekly Premium",
    "Actuarial Engine",
    "AI Risk Map",
    "Hyperlocal Risk",
    "Risk Dashboard",
    "Stress Testing",
    "Claim Triggered",
    "Bank Details",
    "Final Verification",
    "Payout Confirmation",
]

CITY_COORDS = {
    "Chennai": {"lat": 13.0827, "lon": 80.2707},
    "Delhi": {"lat": 28.6139, "lon": 77.2090},
    "Mumbai": {"lat": 19.0760, "lon": 72.8777},
    "Gurugram": {"lat": 28.4595, "lon": 77.0266},
    "Noida": {"lat": 28.5355, "lon": 77.3910},
}

# =========================================================
# SESSION STATE DEFAULTS
# =========================================================
defaults = {
    "page": "Splash",
    "name": "",
    "phone": "",
    "address": "",
    "age": 21,
    "gender": "Male",
    "platform": "Swiggy",
    "city": "Chennai",
    "vehicle": "Bike",
    "work_hours": 8,
    "shift_start": 10,
    "active_days_30": 8,
    "profile_photo": None,
    "selfie_photo": None,
    "activity": "Active",
    "location_valid": True,
    "verified": False,
    "face_verified": False,
    "premium": 30,
    "base_risk": "Medium",
    "rain": 52,
    "aqi": 210,
    "temperature": 39,
    "traffic": "High",
    "risk_score": 78,
    "live_risk": "High",
    "triggered": False,
    "fraud_score": 18,
    "approved": False,
    "payout": 0,
    "txn": "",
    "payout_reason": "",
    "claim_status": "Not Triggered",
    "bank_name": "",
    "account_holder": "",
    "account_number": "",
    "ifsc": "",
    "upi_id": "",
    "payment_mode": "UPI",
    "otp_sent": False,
    "otp_code": "",
    "entered_otp": "",
    "api_mode": "Demo Mode",
    "aqi_source": "Fallback Demo AQI",
    "policy_id": "",
    "policy_active": False,
    "eligibility_status": "Pending",
    "worker_tier": "Standard",
    "city_pool": "",
    "subscription_plan": "Basic Weekly Cover",
    "claim_history": [],
    "manual_trigger_mode": True,
    "bcr_value": 0.0,
    "hyperlocal_df": pd.DataFrame(),
}

for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# =========================================================
# HELPERS
# =========================================================
def set_page(name: str):
    st.session_state.page = name

def prev_page():
    i = APP_ORDER.index(st.session_state.page)
    if i > 0:
        st.session_state.page = APP_ORDER[i - 1]

def get_progress():
    progress_map = {
        "Splash": 5,
        "Registration": 12,
        "Policy Management": 20,
        "Weekly Premium": 28,
        "Actuarial Engine": 38,
        "AI Risk Map": 48,
        "Hyperlocal Risk": 58,
        "Risk Dashboard": 68,
        "Stress Testing": 76,
        "Claim Triggered": 84,
        "Bank Details": 90,
        "Final Verification": 96,
        "Payout Confirmation": 100,
    }
    return progress_map.get(st.session_state.page, 0)

def determine_city_pool():
    city = st.session_state.city
    if city == "Delhi":
        return "Delhi AQI Pool"
    if city == "Mumbai":
        return "Mumbai Rain Pool"
    if city == "Chennai":
        return "Chennai Multi-Peril Pool"
    if city == "Gurugram":
        return "Gurugram AQI Pool"
    if city == "Noida":
        return "Noida AQI Pool"
    return "General City Pool"

def determine_worker_tier():
    days = st.session_state.active_days_30
    if days < 5:
        return "Lower Tier"
    elif days < 10:
        return "Standard"
    return "Priority"

def evaluate_eligibility():
    days = st.session_state.active_days_30
    st.session_state.worker_tier = determine_worker_tier()
    st.session_state.city_pool = determine_city_pool()

    if days >= 7:
        st.session_state.eligibility_status = "Eligible"
        st.session_state.policy_active = True
    elif days >= 5:
        st.session_state.eligibility_status = "Limited Eligibility"
        st.session_state.policy_active = True
    else:
        st.session_state.eligibility_status = "Low Activity Tier"
        st.session_state.policy_active = True

    if not st.session_state.policy_id:
        st.session_state.policy_id = f"POL{random.randint(10000,99999)}"

def risk_badge_html(risk):
    if risk == "High":
        return '<span class="badge-high">High Risk</span>'
    if risk == "Medium":
        return '<span class="badge-medium">Medium Risk</span>'
    return '<span class="badge-low">Low Risk</span>'

def get_risk_color():
    if st.session_state.live_risk == "High":
        return [255, 59, 48, 180]
    elif st.session_state.live_risk == "Medium":
        return [255, 159, 10, 180]
    return [52, 199, 89, 180]

def current_active_hours_match():
    return True

# =========================================================
# 1) 10-YEAR ACTUARIAL DATA
# =========================================================
@st.cache_data
def load_actuarial_data():
    if os.path.exists(ACTUARIAL_DATA_FILE):
        try:
            df = pd.read_csv(ACTUARIAL_DATA_FILE)
            required = {
                "year", "city", "avg_aqi", "avg_rain_days", "avg_temp",
                "trigger_days", "claims_count", "total_payout", "total_premium_collected"
            }
            if required.issubset(set(df.columns)):
                return df
        except Exception:
            pass

    rows = []
    for year in range(2016, 2026):
        for city in CITY_COORDS.keys():
            seed = abs(hash(f"{year}-{city}")) % 100000
            rng = random.Random(seed)

            if city in ["Delhi", "Noida", "Gurugram"]:
                avg_aqi = rng.randint(240, 360)
                avg_rain_days = rng.randint(20, 40)
                avg_temp = rng.randint(32, 38)
            elif city == "Mumbai":
                avg_aqi = rng.randint(90, 180)
                avg_rain_days = rng.randint(55, 95)
                avg_temp = rng.randint(29, 34)
            else:
                avg_aqi = rng.randint(70, 160)
                avg_rain_days = rng.randint(35, 70)
                avg_temp = rng.randint(30, 36)

            trigger_days = rng.randint(10, 30)
            claims_count = rng.randint(80, 180)
            total_payout = rng.randint(50000, 120000)
            total_premium_collected = rng.randint(85000, 160000)

            rows.append({
                "year": year,
                "city": city,
                "avg_aqi": avg_aqi,
                "avg_rain_days": avg_rain_days,
                "avg_temp": avg_temp,
                "trigger_days": trigger_days,
                "claims_count": claims_count,
                "total_payout": total_payout,
                "total_premium_collected": total_premium_collected,
            })

    return pd.DataFrame(rows)

def get_10y_city_stats(city):
    df = load_actuarial_data()
    city_df = df[df["city"] == city].sort_values("year").tail(10)

    if city_df.empty:
        return {
            "avg_trigger_days": 15,
            "avg_claims": 100,
            "avg_payout": 70000,
            "avg_premium": 100000,
            "avg_aqi": 180,
            "avg_rain_days": 35,
            "avg_temp": 33,
        }

    return {
        "avg_trigger_days": round(city_df["trigger_days"].mean(), 2),
        "avg_claims": round(city_df["claims_count"].mean(), 2),
        "avg_payout": round(city_df["total_payout"].mean(), 2),
        "avg_premium": round(city_df["total_premium_collected"].mean(), 2),
        "avg_aqi": round(city_df["avg_aqi"].mean(), 2),
        "avg_rain_days": round(city_df["avg_rain_days"].mean(), 2),
        "avg_temp": round(city_df["avg_temp"].mean(), 2),
    }

# =========================================================
# 2) BCR
# =========================================================
def calculate_bcr(city):
    df = load_actuarial_data()
    city_df = df[df["city"] == city].sort_values("year").tail(10)

    if city_df.empty:
        return 0.65

    total_payout = city_df["total_payout"].sum()
    total_premium = city_df["total_premium_collected"].sum()

    if total_premium == 0:
        return 0.0

    return round(total_payout / total_premium, 2)

def compute_base_premium():
    city = st.session_state.city
    tier = determine_worker_tier()
    stats = get_10y_city_stats(city)
    bcr = calculate_bcr(city)
    st.session_state.bcr_value = bcr

    trigger_factor = stats["avg_trigger_days"] / 20
    base = 25 * trigger_factor

    if city in ["Delhi", "Noida", "Gurugram"]:
        base *= 1.15
        risk = "High"
    elif city == "Mumbai":
        base *= 1.08
        risk = "Medium"
    else:
        base *= 1.00
        risk = "Medium"

    if tier == "Lower Tier":
        base *= 0.90
    elif tier == "Priority":
        base *= 1.15

    if st.session_state.vehicle == "Cycle":
        base *= 0.90

    if st.session_state.work_hours >= 10:
        base += 8
    elif st.session_state.work_hours >= 8:
        base += 5

    if bcr > 0.80:
        base *= 1.20
    elif bcr > 0.65:
        base *= 1.10
    elif bcr < 0.40:
        base *= 0.95

    premium = int(round(base))
    premium = max(20, min(50, premium))

    st.session_state.base_risk = risk
    st.session_state.premium = premium

# =========================================================
# 3) AQI PIPELINE
# =========================================================
@st.cache_data
def load_official_aqi_data():
    if os.path.exists(OFFICIAL_AQI_FILE):
        try:
            df = pd.read_csv(OFFICIAL_AQI_FILE)
            required = {"date", "city", "aqi"}
            if required.issubset(set(df.columns)):
                df["date"] = pd.to_datetime(df["date"], errors="coerce")
                return df
        except Exception:
            pass
    return pd.DataFrame(columns=["date", "city", "aqi"])

def get_official_aqi_or_fallback(city: str):
    official_df = load_official_aqi_data()
    city_official = official_df[official_df["city"].astype(str).str.lower() == city.lower()].copy()

    if not city_official.empty:
        city_official = city_official.sort_values("date")
        row = city_official.iloc[-1]
        return {
            "aqi": int(row["aqi"]),
            "source": "Official AQI dataset",
        }

    coords = CITY_COORDS[city]
    lat, lon = coords["lat"], coords["lon"]

    if OPENWEATHER_API_KEY:
        try:
            air_url = (
                f"https://api.openweathermap.org/data/2.5/air_pollution"
                f"?lat={lat}&lon={lon}&appid={OPENWEATHER_API_KEY}"
            )
            res = requests.get(air_url, timeout=10)
            res.raise_for_status()
            air_json = res.json()

            owm_aqi = air_json["list"][0]["main"]["aqi"]
            components = air_json["list"][0]["components"]
            pm25 = components.get("pm2_5", 0)
            pm10 = components.get("pm10", 0)

            approx_aqi = int((pm25 * 2.2) + (pm10 * 0.8) + (owm_aqi * 20))
            approx_aqi = max(20, min(approx_aqi, 500))

            return {
                "aqi": approx_aqi,
                "source": "OpenWeather AQI fallback",
            }
        except Exception:
            pass

    return {
        "aqi": random.randint(250, 420),
        "source": "Fallback Demo AQI",
    }

# =========================================================
# WEATHER + TRAFFIC
# =========================================================
@st.cache_data(ttl=600)
def get_weather_data(city: str):
    coords = CITY_COORDS[city]
    lat, lon = coords["lat"], coords["lon"]

    if not OPENWEATHER_API_KEY:
        return {
            "rain": random.randint(55, 85),
            "temperature": random.randint(35, 45),
            "api_mode": "Demo Mode",
        }

    try:
        weather_url = (
            f"https://api.openweathermap.org/data/2.5/weather"
            f"?lat={lat}&lon={lon}&appid={OPENWEATHER_API_KEY}&units=metric"
        )
        weather_res = requests.get(weather_url, timeout=10)
        weather_res.raise_for_status()
        weather_json = weather_res.json()

        rain_1h = weather_json.get("rain", {}).get("1h", 0)
        temp = weather_json.get("main", {}).get("temp", 35)

        return {
            "rain": max(55, int(rain_1h * 20)) if rain_1h else random.randint(55, 85),
            "temperature": max(36, int(temp)),
            "api_mode": "Live Weather API",
        }
    except Exception:
        return {
            "rain": random.randint(55, 85),
            "temperature": random.randint(35, 45),
            "api_mode": "Demo Mode (Weather fallback)",
        }

@st.cache_data(ttl=600)
def get_traffic_data(city: str):
    coords = CITY_COORDS[city]
    lat, lon = coords["lat"], coords["lon"]

    if not TOMTOM_API_KEY:
        return {"traffic": random.choice(["Moderate", "High"])}

    try:
        url = (
            f"https://api.tomtom.com/traffic/services/4/flowSegmentData/absolute/10/json"
            f"?point={lat},{lon}&key={TOMTOM_API_KEY}"
        )
        res = requests.get(url, timeout=10)
        res.raise_for_status()
        data = res.json()

        current_speed = data.get("flowSegmentData", {}).get("currentSpeed", 0)
        free_speed = data.get("flowSegmentData", {}).get("freeFlowSpeed", 1)
        ratio = current_speed / free_speed if free_speed else 0.5

        if ratio < 0.45:
            return {"traffic": "High"}
        elif ratio < 0.75:
            return {"traffic": "Moderate"}
        return {"traffic": "Moderate"}
    except Exception:
        return {"traffic": random.choice(["Moderate", "High"])}

# =========================================================
# 4) HYPERLOCAL GRID
# =========================================================
def generate_hyperlocal_grid(city):
    base = CITY_COORDS[city]
    lat = base["lat"]
    lon = base["lon"]

    rows = []
    zone_num = 1

    for i in range(-2, 3):
        for j in range(-2, 3):
            local_rain = max(0, st.session_state.rain + random.randint(-10, 10))
            local_aqi = max(0, st.session_state.aqi + random.randint(-35, 35))
            local_temp = max(0, st.session_state.temperature + random.randint(-2, 2))

            local_score = int(local_rain * 0.70 + local_aqi * 0.12 + local_temp * 1.4)
            local_score = min(local_score, 100)

            if local_score >= 80:
                local_risk = "High"
                color = [255, 59, 48, 180]
            elif local_score >= 45:
                local_risk = "Medium"
                color = [255, 159, 10, 180]
            else:
                local_risk = "Low"
                color = [52, 199, 89, 180]

            rows.append({
                "zone": f"Ward {zone_num}",
                "lat": lat + i * 0.01,
                "lon": lon + j * 0.01,
                "rain": local_rain,
                "aqi": local_aqi,
                "temp": local_temp,
                "risk_score": local_score,
                "risk_label": local_risk,
                "color": color,
            })
            zone_num += 1

    return pd.DataFrame(rows)

# =========================================================
# 5) STRESS TESTING
# =========================================================
def run_stress_test(city):
    stats = get_10y_city_stats(city)

    scenarios = [
        {"name": "Severe AQI Shock", "aqi_multiplier": 1.35, "rain_multiplier": 1.00, "temp_add": 1},
        {"name": "Extreme Rain Event", "aqi_multiplier": 1.00, "rain_multiplier": 1.50, "temp_add": 0},
        {"name": "Combined Catastrophe Week", "aqi_multiplier": 1.25, "rain_multiplier": 1.40, "temp_add": 2},
    ]

    results = []
    base_claims = stats["avg_claims"]
    base_payout = stats["avg_payout"]
    base_trigger = stats["avg_trigger_days"]

    for s in scenarios:
        factor = ((s["aqi_multiplier"] + s["rain_multiplier"]) / 2)
        stressed_claims = int(base_claims * factor)
        stressed_payout = int(base_payout * (factor + 0.10))
        stressed_triggers = round(base_trigger * factor, 1)

        if stressed_payout > base_payout * 1.35:
            solvency = "Watch"
        else:
            solvency = "Stable"

        results.append({
            "Scenario": s["name"],
            "Projected Trigger Days": stressed_triggers,
            "Projected Claims": stressed_claims,
            "Projected Payout": stressed_payout,
            "Solvency Flag": solvency,
        })

    return pd.DataFrame(results)

# =========================================================
# OTHER BUSINESS LOGIC
# =========================================================
def compute_live_risk():
    rain = st.session_state.rain
    aqi = st.session_state.aqi
    temp = st.session_state.temperature

    score = int((rain * 0.75) + (aqi * 0.12) + (temp * 1.5))

    if st.session_state.traffic == "High":
        score += 8
    elif st.session_state.traffic == "Moderate":
        score += 4

    st.session_state.risk_score = min(score, 100)

    if st.session_state.risk_score >= 80:
        st.session_state.live_risk = "High"
    elif st.session_state.risk_score >= 45:
        st.session_state.live_risk = "Medium"
    else:
        st.session_state.live_risk = "Low"

def verification_model():
    score = 0
    if st.session_state.name.strip():
        score += 10
    if st.session_state.phone.strip():
        score += 15
    if st.session_state.address.strip():
        score += 10
    if st.session_state.age >= 18:
        score += 10
    if st.session_state.profile_photo is not None:
        score += 15
    if st.session_state.selfie_photo is not None:
        score += 20
    if st.session_state.activity == "Active":
        score += 10
    if st.session_state.location_valid:
        score += 10

    st.session_state.verified = score >= 60
    return score

def face_verification_demo():
    st.session_state.face_verified = st.session_state.selfie_photo is not None
    return st.session_state.face_verified

def fraud_model():
    score = random.randint(10, 25)

    if st.session_state.activity != "Active":
        score += 15
    if not st.session_state.location_valid:
        score += 15
    if st.session_state.work_hours < 4:
        score += 8
    if st.session_state.face_verified:
        score -= 8

    st.session_state.fraud_score = max(0, min(score, 100))
    return st.session_state.fraud_score

def bank_details_valid():
    if st.session_state.payment_mode == "UPI":
        return bool(st.session_state.upi_id.strip())
    return (
        bool(st.session_state.bank_name.strip())
        and bool(st.session_state.account_holder.strip())
        and bool(st.session_state.account_number.strip())
        and bool(st.session_state.ifsc.strip())
    )

def send_demo_otp():
    otp = str(random.randint(1000, 9999))
    st.session_state.otp_code = otp
    st.session_state.otp_sent = True
    return otp

def record_claim_history():
    st.session_state.claim_history.append({
        "Time": datetime.now().strftime("%d-%m-%Y %H:%M"),
        "Policy ID": st.session_state.policy_id,
        "City": st.session_state.city,
        "Trigger": st.session_state.claim_status,
        "Risk": st.session_state.live_risk,
        "Payout": f"₹{st.session_state.payout}",
        "Transaction ID": st.session_state.txn if st.session_state.txn else "Pending"
    })

def force_trigger_environment():
    official_aqi = get_official_aqi_or_fallback(st.session_state.city)
    st.session_state.rain = random.randint(70, 90)
    st.session_state.aqi = max(320, official_aqi["aqi"])
    st.session_state.temperature = random.randint(40, 45)
    st.session_state.traffic = random.choice(["Moderate", "High"])
    st.session_state.aqi_source = official_aqi["source"]
    st.session_state.api_mode = "Forced Demo Trigger"
    compute_live_risk()
    st.session_state.hyperlocal_df = generate_hyperlocal_grid(st.session_state.city)
    auto_claim_engine()

def auto_claim_engine():
    city_ok = st.session_state.city in CITY_COORDS
    active_hour_ok = current_active_hours_match()
    policy_ok = st.session_state.policy_active

    threshold_hit = (
        st.session_state.rain > 50
        or st.session_state.aqi > 300
        or st.session_state.temperature > 42
    )

    if st.session_state.manual_trigger_mode:
        threshold_hit = True

    st.session_state.triggered = threshold_hit and city_ok and active_hour_ok and policy_ok

    if st.session_state.triggered:
        st.session_state.claim_status = "Triggered Automatically"
    else:
        st.session_state.claim_status = "Not Triggered"
        st.session_state.approved = False
        st.session_state.payout = 0
        st.session_state.txn = ""
        st.session_state.payout_reason = ""

def final_claim_approval():
    fraud_score = fraud_model()
    verification_score = verification_model()

    st.session_state.approved = (
        st.session_state.triggered
        and fraud_score < 50
        and verification_score >= 60
        and st.session_state.activity == "Active"
        and st.session_state.location_valid
        and st.session_state.policy_active
        and bank_details_valid()
        and st.session_state.entered_otp == st.session_state.otp_code
    )

    if st.session_state.approved:
        if st.session_state.rain > 70 or st.session_state.aqi > 400:
            payout = 500
            reason = "Severe disruption payout"
        else:
            payout = 300
            reason = "Moderate disruption payout"

        if st.session_state.face_verified:
            payout += 5
            reason += " + ₹5 verified worker bonus"

        st.session_state.payout = payout
        st.session_state.payout_reason = reason
        st.session_state.txn = f"INS{random.randint(10000,99999)}"
        record_claim_history()
    else:
        st.session_state.payout = 0
        st.session_state.payout_reason = "Verification / fraud / payment validation failed"
        st.session_state.txn = ""

def simulate_live_environment():
    weather = get_weather_data(st.session_state.city)
    traffic = get_traffic_data(st.session_state.city)
    official_aqi = get_official_aqi_or_fallback(st.session_state.city)

    st.session_state.rain = weather["rain"]
    st.session_state.temperature = weather["temperature"]
    st.session_state.aqi = official_aqi["aqi"]
    st.session_state.traffic = traffic["traffic"]
    st.session_state.api_mode = weather["api_mode"]
    st.session_state.aqi_source = official_aqi["source"]

    compute_live_risk()
    st.session_state.hyperlocal_df = generate_hyperlocal_grid(st.session_state.city)
    auto_claim_engine()

# =========================================================
# INITIAL CALCULATIONS
# =========================================================
evaluate_eligibility()
compute_base_premium()
compute_live_risk()
if st.session_state.hyperlocal_df.empty:
    st.session_state.hyperlocal_df = generate_hyperlocal_grid(st.session_state.city)
auto_claim_engine()

# =========================================================
# CSS FIX
# =========================================================
st.markdown("""
<style>

/* ================= GLOBAL ================= */
html, body, [class*="css"] {
    font-family: Inter, sans-serif;
    color: #1e293b;
}

/* ================= BACKGROUND ================= */
body {
    background: #fffbea;
}

[data-testid="stAppViewContainer"] {
    background: linear-gradient(180deg, #fffbea 0%, #fff3c4 100%);
}

/* ================= MAIN CARD ================= */
.main .block-container {
    max-width: 460px !important;
    margin-top: 1.2rem !important;
    margin-bottom: 2rem !important;
    background: #ffffff;
    border: 1px solid #f3e8a1;
    border-radius: 32px;
    padding: 1rem 1rem 1.5rem 1rem !important;
    box-shadow: 0 18px 40px rgba(0,0,0,0.08);
    min-height: 850px;
    position: relative;
}

/* notch effect */
.main .block-container::before {
    content: "";
    display: block;
    width: 120px;
    height: 16px;
    background: #fef3c7;
    border-radius: 999px;
    margin: 0 auto 0.8rem auto;
}

/* ================= SIDEBAR ================= */
section[data-testid="stSidebar"] {
    background: #fffdf2;
    border-right: 1px solid #f3e8a1;
}

/* ================= TOPBAR ================= */
.topbar-title {
    font-size: 18px;
    font-weight: 800;
    color: #0f172a;
    text-align: center;
}

.icon-btn {
    background: #fff3c4;
    color: #0f172a;
    padding: 7px 10px;
    border-radius: 999px;
    font-size: 14px;
    font-weight: 700;
    text-align: center;
    border: 1px solid #f3e8a1;
}

/* ================= TEXT ================= */
.screen-title {
    font-size: 28px;
    font-weight: 800;
    color: #0f172a;
    margin-bottom: 4px;
    text-align: center;
}

.screen-subtitle {
    font-size: 14px;
    color: #475569;
    margin-bottom: 16px;
    text-align: center;
}

.input-label {
    font-size: 14px;
    font-weight: 700;
    color: #334155;
    margin-top: 8px;
    margin-bottom: 4px;
}

/* ================= CARDS ================= */
.card {
    background: #ffffff !important;
    border-radius: 18px;
    padding: 14px;
    box-shadow: 0 4px 14px rgba(0,0,0,0.05);
    border: 1px solid #f3e8a1;
    margin-bottom: 14px;
    color: #1e293b;
}

.card-soft {
    background: #fffdf2 !important;
    border-radius: 16px;
    padding: 14px;
    border: 1px solid #f3e8a1;
    margin-bottom: 14px;
    color: #1e293b;
}

/* ================= BADGES ================= */
.badge-high, .badge-medium, .badge-low {
    display: inline-block;
    padding: 6px 12px;
    border-radius: 999px;
    font-size: 13px;
    font-weight: 800;
}

.badge-high { background: #fee2e2; color: #b91c1c; }
.badge-medium { background: #fef3c7; color: #b45309; }
.badge-low { background: #dcfce7; color: #15803d; }

/* ================= ALERT BOXES ================= */
.info-box, .warn-box, .ok-box, .err-box {
    border-radius: 14px;
    padding: 14px;
    margin-bottom: 12px;
    font-size: 15px;
    line-height: 1.55;
}

.info-box {
    background: #fffbeb;
    border: 1px solid #fde68a;
    color: #92400e;
}

.warn-box {
    background: #fff7ed;
    border: 1px solid #fdba74;
    color: #9a3412;
    font-weight: 700;
}

.ok-box {
    background: #ecfdf5;
    border: 1px solid #86efac;
    color: #166534;
    font-weight: 700;
}

.err-box {
    background: #fef2f2;
    border: 1px solid #fca5a5;
    color: #b91c1c;
    font-weight: 700;
}

/* ================= PROGRESS ================= */
.progress-label {
    font-size: 12px;
    color: #64748b;
    margin-bottom: 6px;
    text-align: center;
    font-weight: 700;
}

/* ================= BUTTONS ================= */
.stButton > button {
    width: 100%;
    border-radius: 14px;
    padding: 0.82rem 1rem;
    border: none;
    font-weight: 800;
    font-size: 16px;
    background: linear-gradient(135deg, #facc15, #f59e0b);
    color: #1e293b;
}

/* hover */
.stButton > button:hover {
    background: linear-gradient(135deg, #fbbf24, #d97706);
    color: white;
}

/* ================= SPLASH ================= */
.splash {
    min-height: 600px;
    display: flex;
    flex-direction: column;
    justify-content: center;
    text-align: center;
    padding: 20px 8px;
}

.splash-logo {
    font-size: 56px;
    margin-bottom: 8px;
}

.splash-title {
    font-size: 34px;
    font-weight: 900;
    color: #0f172a;
    margin-bottom: 8px;
}

.splash-subtitle {
    font-size: 15px;
    color: #475569;
    margin-bottom: 20px;
}

</style>
""", unsafe_allow_html=True)

# =========================================================
# TOPBAR
# =========================================================
title_map = {
    "Splash": "IncomeLock AI",
    "Registration": "Registration",
    "Policy Management": "Policy Management",
    "Weekly Premium": "Weekly Premium",
    "Actuarial Engine": "Actuarial Engine",
    "AI Risk Map": "AI Risk App",
    "Hyperlocal Risk": "Hyperlocal Risk",
    "Risk Dashboard": "Risk Dashboard",
    "Stress Testing": "Stress Testing",
    "Claim Triggered": "Claim Triggered",
    "Bank Details": "Bank Details",
    "Final Verification": "Final Verification",
    "Payout Confirmation": "Payout Confirmation",
}

col_a, col_b, col_c = st.columns([1, 4, 1])

with col_a:
    with st.popover("👤"):
        st.markdown("### My Profile")
        if st.session_state.profile_photo is not None:
            st.image(st.session_state.profile_photo, width=120)
        st.write(f"**Name:** {st.session_state.name or 'Not filled'}")
        st.write(f"**Phone:** {st.session_state.phone or 'Not filled'}")
        st.write(f"**Address:** {st.session_state.address or 'Not filled'}")
        st.write(f"**Age:** {st.session_state.age}")
        st.write(f"**Gender:** {st.session_state.gender}")
        st.write(f"**Platform:** {st.session_state.platform}")
        st.write(f"**City:** {st.session_state.city}")
        st.write(f"**Vehicle:** {st.session_state.vehicle}")
        st.write(f"**Work Hours:** {st.session_state.work_hours}")
        st.write(f"**Policy ID:** {st.session_state.policy_id or 'Pending'}")

    if st.session_state.page != "Splash":
        if st.button("←", key="back_btn"):
            prev_page()
            st.rerun()

with col_b:
    st.markdown(f'<div class="topbar-title">{title_map[st.session_state.page]}</div>', unsafe_allow_html=True)

with col_c:
    with st.popover("⚙️"):
        st.markdown("### Settings")
        st.session_state.subscription_plan = st.selectbox(
            "Manage Subscription",
            ["Basic Weekly Cover", "Pro Weekly Cover", "Priority Cover"],
            index=["Basic Weekly Cover", "Pro Weekly Cover", "Priority Cover"].index(st.session_state.subscription_plan)
        )
        st.session_state.phone = st.text_input("Change Phone Number", value=st.session_state.phone)
        st.session_state.address = st.text_area("Change Address", value=st.session_state.address)
        st.session_state.bank_name = st.text_input("Change Bank Name", value=st.session_state.bank_name)
        st.session_state.account_number = st.text_input("Change Bank Account", value=st.session_state.account_number)
        st.session_state.ifsc = st.text_input("Change IFSC", value=st.session_state.ifsc)

        if st.button("Logout"):
            for k, v in defaults.items():
                st.session_state[k] = v
            st.rerun()

if st.session_state.page != "Splash":
    st.markdown('<div class="progress-label">Workflow Progress</div>', unsafe_allow_html=True)
    st.progress(get_progress() / 100)

# =========================================================
# PAGES
# =========================================================
if st.session_state.page == "Splash":
    st.markdown("""
    <div class="splash">
        <div class="splash-logo">🛡️</div>
        <div class="splash-title">IncomeLock AI</div>
        <div class="splash-subtitle">
            Parametric income protection for gig workers
        </div>
        <div class="card" style="text-align:left;">
            <b>What this app covers:</b><br><br>
            • Registration process<br>
            • Insurance policy management<br>
            • Dynamic premium calculation<br>
            • 10-year actuarial engine<br>
            • Hyperlocal risk mapping<br>
            • Stress testing<br>
            • Claims management<br>
            • Fraud verification<br>
            • Instant settlement simulation
        </div>
    </div>
    """, unsafe_allow_html=True)

    if st.button("Get Started"):
        set_page("Registration")
        st.rerun()

elif st.session_state.page == "Registration":
    st.markdown('<div class="screen-title">AI Gig Worker Insurance</div>', unsafe_allow_html=True)
    st.markdown('<div class="screen-subtitle">Protect your weekly delivery income</div>', unsafe_allow_html=True)

    with st.container(border=True):
        st.markdown('<div class="input-label">Name</div>', unsafe_allow_html=True)
        st.session_state.name = st.text_input("Name", value=st.session_state.name, label_visibility="collapsed")

        st.markdown('<div class="input-label">Phone Number</div>', unsafe_allow_html=True)
        st.session_state.phone = st.text_input("Phone", value=st.session_state.phone, label_visibility="collapsed")

        st.markdown('<div class="input-label">Address</div>', unsafe_allow_html=True)
        st.session_state.address = st.text_area("Address", value=st.session_state.address, label_visibility="collapsed")

        col1, col2 = st.columns(2)
        with col1:
            st.markdown('<div class="input-label">Age</div>', unsafe_allow_html=True)
            st.session_state.age = st.number_input("Age", min_value=18, max_value=70, value=st.session_state.age, label_visibility="collapsed")
        with col2:
            st.markdown('<div class="input-label">Gender</div>', unsafe_allow_html=True)
            st.session_state.gender = st.selectbox(
                "Gender",
                ["Male", "Female", "Other"],
                index=["Male", "Female", "Other"].index(st.session_state.gender),
                label_visibility="collapsed"
            )

        st.markdown('<div class="input-label">Delivery Platform</div>', unsafe_allow_html=True)
        platform_options = ["Swiggy", "Zomato", "Zepto", "Amazon"]
        current_platform = st.session_state.platform if st.session_state.platform in platform_options else "Swiggy"
        st.session_state.platform = st.selectbox(
            "Platform",
            platform_options,
            index=platform_options.index(current_platform),
            label_visibility="collapsed"
        )

        st.markdown('<div class="input-label">City</div>', unsafe_allow_html=True)
        city_options = list(CITY_COORDS.keys())
        st.session_state.city = st.selectbox(
            "City",
            city_options,
            index=city_options.index(st.session_state.city),
            label_visibility="collapsed"
        )

        st.markdown('<div class="input-label">Vehicle Type</div>', unsafe_allow_html=True)
        st.session_state.vehicle = st.selectbox(
            "Vehicle",
            ["Bike", "Scooter", "Cycle"],
            index=["Bike", "Scooter", "Cycle"].index(st.session_state.vehicle),
            label_visibility="collapsed"
        )

        st.markdown('<div class="input-label">Working Hours Per Day</div>', unsafe_allow_html=True)
        st.session_state.work_hours = st.selectbox(
            "Hours",
            [4, 6, 8, 10, 12],
            index=[4, 6, 8, 10, 12].index(st.session_state.work_hours),
            label_visibility="collapsed"
        )

        st.markdown('<div class="input-label">Shift Start Hour</div>', unsafe_allow_html=True)
        hour_options = list(range(0, 24))
        st.session_state.shift_start = st.selectbox(
            "Shift",
            hour_options,
            index=hour_options.index(st.session_state.shift_start),
            label_visibility="collapsed"
        )

        st.markdown('<div class="input-label">Active Delivery Days in Last 30 Days</div>', unsafe_allow_html=True)
        st.session_state.active_days_30 = st.slider(
            "Active Days",
            0,
            30,
            st.session_state.active_days_30,
            label_visibility="collapsed"
        )

        st.markdown('<div class="input-label">Upload Profile Photo</div>', unsafe_allow_html=True)
        st.session_state.profile_photo = st.file_uploader(
            "Upload Photo",
            type=["png", "jpg", "jpeg"],
            label_visibility="collapsed"
        )

    if st.button("Register"):
        evaluate_eligibility()
        verification_model()
        compute_base_premium()
        force_trigger_environment()
        set_page("Policy Management")
        st.rerun()

elif st.session_state.page == "Policy Management":
    evaluate_eligibility()
    compute_base_premium()

    st.markdown('<div class="screen-title">Insurance Policy Management</div>', unsafe_allow_html=True)
    st.markdown('<div class="screen-subtitle">Underwriting and worker eligibility</div>', unsafe_allow_html=True)

    st.markdown(f"""
    <div class="card-soft">
        <b>Policy ID:</b> {st.session_state.policy_id}<br>
        <b>Worker Tier:</b> {st.session_state.worker_tier}<br>
        <b>Eligibility:</b> {st.session_state.eligibility_status}<br>
        <b>City Pool:</b> {st.session_state.city_pool}<br>
        <b>Subscription:</b> {st.session_state.subscription_plan}<br>
        <b>Policy Status:</b> {'Active' if st.session_state.policy_active else 'Inactive'}
    </div>
    """, unsafe_allow_html=True)

    if st.button("Continue to Premium"):
        set_page("Weekly Premium")
        st.rerun()

elif st.session_state.page == "Weekly Premium":
    compute_base_premium()

    st.markdown('<div class="screen-title">Your Weekly Protection Plan</div>', unsafe_allow_html=True)

    st.markdown(f"""
    <div class="card">
        <div style="font-size:18px; margin-bottom:14px;">
            Base Risk: {risk_badge_html(st.session_state.base_risk)}
        </div>
        <div style="font-size:17px; margin-bottom:8px;">
            City: <b>{st.session_state.city}</b>
        </div>
        <div style="font-size:17px; margin-bottom:8px;">
            Tier: <b>{st.session_state.worker_tier}</b>
        </div>
        <div style="font-size:17px; margin-bottom:8px;">
            BCR: <b>{st.session_state.bcr_value}</b>
        </div>
        <div style="height:1px; background:#d1d5db; margin:10px 0 14px 0;"></div>
        <div style="font-size:30px; font-weight:800;">Weekly Premium ₹{st.session_state.premium}</div>
    </div>
    """, unsafe_allow_html=True)

    if st.button("Open Actuarial Engine"):
        set_page("Actuarial Engine")
        st.rerun()

elif st.session_state.page == "Actuarial Engine":
    st.markdown('<div class="screen-title">Actuarial Engine</div>', unsafe_allow_html=True)
    st.markdown('<div class="screen-subtitle">10-year pricing and burning cost analytics</div>', unsafe_allow_html=True)

    city_df = load_actuarial_data()
    city_df = city_df[city_df["city"] == st.session_state.city].sort_values("year")
    stats = get_10y_city_stats(st.session_state.city)
    bcr = calculate_bcr(st.session_state.city)

    st.markdown(f"""
    <div class="card-soft">
        <b>10Y Avg Trigger Days:</b> {stats['avg_trigger_days']}<br>
        <b>10Y Avg Claims:</b> {stats['avg_claims']}<br>
        <b>10Y Avg Payout:</b> ₹{stats['avg_payout']}<br>
        <b>10Y Avg Premium Collected:</b> ₹{stats['avg_premium']}<br>
        <b>Burning Cost Ratio:</b> {bcr}
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### 10-Year Trend")
    trend_df = city_df[["year", "total_payout", "total_premium_collected"]].rename(
        columns={"total_payout": "Payout", "total_premium_collected": "Premium"}
    ).set_index("year")
    st.line_chart(trend_df)

    if st.button("Continue to Risk Map"):
        st.session_state.policy_active = True
        simulate_live_environment()
        set_page("AI Risk Map")
        st.rerun()

elif st.session_state.page == "AI Risk Map":
    st.markdown('<div class="screen-title">AI Risk Map</div>', unsafe_allow_html=True)
    st.markdown('<div class="screen-subtitle">Live trigger data for covered workers</div>', unsafe_allow_html=True)

    colx, coly = st.columns(2)
    with colx:
        if st.button("Refresh Location"):
            simulate_live_environment()
            st.rerun()
    with coly:
        if st.button("Refresh Trigger"):
            force_trigger_environment()
            st.rerun()

    selected = CITY_COORDS[st.session_state.city]

    map_df = pd.DataFrame([{
        "city": st.session_state.city,
        "lat": selected["lat"],
        "lon": selected["lon"],
        "risk_score": st.session_state.risk_score,
        "rain": st.session_state.rain,
        "aqi": st.session_state.aqi,
        "temp": st.session_state.temperature,
        "traffic": st.session_state.traffic,
    }])

    layer = pdk.Layer(
        "ScatterplotLayer",
        data=map_df,
        get_position='[lon, lat]',
        get_fill_color=get_risk_color(),
        get_radius=12000,
        pickable=True,
    )

    view_state = pdk.ViewState(
        latitude=selected["lat"],
        longitude=selected["lon"],
        zoom=9,
        pitch=0,
    )

    tooltip = {
        "html": """
        <b>City:</b> {city}<br/>
        <b>Risk Score:</b> {risk_score}<br/>
        <b>Rain:</b> {rain}<br/>
        <b>AQI:</b> {aqi}<br/>
        <b>Temp:</b> {temp}°C<br/>
        <b>Traffic:</b> {traffic}
        """,
        "style": {"backgroundColor": "#111827", "color": "white"},
    }

    st.markdown(f"""
    <div class="info-box">
        <b>Weather Source:</b> {st.session_state.api_mode}<br>
        <b>AQI Source:</b> {st.session_state.aqi_source}<br>
        <b>Current Trigger Status:</b> {'Detected' if st.session_state.triggered else 'Not Yet'}
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"AI Risk Score: **{st.session_state.risk_score}/100** ({st.session_state.live_risk})")

    st.pydeck_chart(
        pdk.Deck(
            map_style="light",
            initial_view_state=view_state,
            layers=[layer],
            tooltip=tooltip,
        )
    )

    if st.button("Open Hyperlocal Risk View"):
        set_page("Hyperlocal Risk")
        st.rerun()

elif st.session_state.page == "Hyperlocal Risk":
    st.markdown('<div class="screen-title">Hyperlocal Risk</div>', unsafe_allow_html=True)
    st.markdown('<div class="screen-subtitle">Ward-style risk distribution across the city</div>', unsafe_allow_html=True)

    if st.button("Refresh Hyperlocal Grid"):
        st.session_state.hyperlocal_df = generate_hyperlocal_grid(st.session_state.city)
        st.rerun()

    grid_df = st.session_state.hyperlocal_df.copy()

    grid_layer = pdk.Layer(
        "ScatterplotLayer",
        data=grid_df,
        get_position='[lon, lat]',
        get_fill_color='color',
        get_radius=7000,
        pickable=True,
    )

    view_state = pdk.ViewState(
        latitude=CITY_COORDS[st.session_state.city]["lat"],
        longitude=CITY_COORDS[st.session_state.city]["lon"],
        zoom=10,
        pitch=0,
    )

    tooltip = {
        "html": """
        <b>Zone:</b> {zone}<br/>
        <b>Risk:</b> {risk_label}<br/>
        <b>Risk Score:</b> {risk_score}<br/>
        <b>Rain:</b> {rain}<br/>
        <b>AQI:</b> {aqi}<br/>
        <b>Temp:</b> {temp}°C
        """,
        "style": {"backgroundColor": "#111827", "color": "white"},
    }

    st.pydeck_chart(
        pdk.Deck(
            map_style="light",
            initial_view_state=view_state,
            layers=[grid_layer],
            tooltip=tooltip,
        )
    )

    st.markdown("### Hyperlocal Zone Table")
    st.dataframe(
        grid_df[["zone", "risk_label", "risk_score", "rain", "aqi", "temp"]],
        use_container_width=True
    )

    if st.button("Continue to Risk Dashboard"):
        set_page("Risk Dashboard")
        st.rerun()

elif st.session_state.page == "Risk Dashboard":
    auto_claim_engine()
    st.markdown('<div class="screen-title">Risk Dashboard</div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Refresh Location ", key="refresh_loc_dash"):
            simulate_live_environment()
            st.rerun()
    with col2:
        if st.button("Refresh Trigger ", key="refresh_trigger_dash"):
            force_trigger_environment()
            st.rerun()

    st.markdown(f"""
    <div class="card-soft">
        <b>City:</b> {st.session_state.city}<br>
        <b>Rain Level:</b> {st.session_state.rain}<br>
        <b>AQI:</b> {st.session_state.aqi}<br>
        <b>Temperature:</b> {st.session_state.temperature}°C<br>
        <b>Traffic:</b> {st.session_state.traffic}<br>
        <b>Live Risk:</b> {st.session_state.live_risk}<br>
        <b>Trigger:</b> {'Detected' if st.session_state.triggered else 'Not Detected'}<br>
        <b>BCR:</b> {st.session_state.bcr_value}
    </div>
    """, unsafe_allow_html=True)

    if st.button("Open Stress Testing"):
        set_page("Stress Testing")
        st.rerun()

elif st.session_state.page == "Stress Testing":
    st.markdown('<div class="screen-title">Stress Testing</div>', unsafe_allow_html=True)
    st.markdown('<div class="screen-subtitle">Scenario-based solvency and claim pressure checks</div>', unsafe_allow_html=True)

    stress_df = run_stress_test(st.session_state.city)

    st.markdown("### Scenario Results")
    st.dataframe(stress_df, use_container_width=True)

    st.markdown("""
    <div class="card-soft">
        <b>Scenarios Covered</b><br>
        • Severe AQI shock<br>
        • Extreme rain event<br>
        • Combined catastrophe week
    </div>
    """, unsafe_allow_html=True)

    if st.button("Continue to Claims"):
        set_page("Claim Triggered")
        st.rerun()

elif st.session_state.page == "Claim Triggered":
    auto_claim_engine()
    st.markdown('<div class="screen-title">Claim Structure</div>', unsafe_allow_html=True)

    if st.button("Force Trigger Again"):
        force_trigger_environment()
        st.rerun()

    if st.session_state.triggered:
        st.markdown("""
        <div class="err-box">
            1. Trigger fires<br>
            2. Policy checked<br>
            3. Fraud verification starts<br>
            4. Payout ready for release
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <div class="card-soft">
            <b>Policy Active:</b> {'Yes' if st.session_state.policy_active else 'No'}<br>
            <b>City Match:</b> {'Yes' if st.session_state.city in CITY_COORDS else 'No'}<br>
            <b>Active Hours Match:</b> Yes<br>
            <b>Claim Status:</b> {st.session_state.claim_status}
        </div>
        """, unsafe_allow_html=True)

        if st.button("Continue to Bank Details"):
            set_page("Bank Details")
            st.rerun()
    else:
        st.markdown("""
        <div class="ok-box">
            No trigger detected yet.
        </div>
        """, unsafe_allow_html=True)

elif st.session_state.page == "Bank Details":
    st.markdown('<div class="screen-title">Settlement & Payout Channel</div>', unsafe_allow_html=True)
    st.markdown('<div class="screen-subtitle">Choose transfer channel for payout</div>', unsafe_allow_html=True)

    st.session_state.payment_mode = st.radio(
        "Payment Mode",
        ["UPI", "IMPS", "Bank Transfer"],
        horizontal=True
    )

    if st.session_state.payment_mode == "UPI":
        st.session_state.upi_id = st.text_input(
            "UPI ID",
            value=st.session_state.upi_id,
            placeholder="name@upi"
        )
    else:
        st.session_state.bank_name = st.text_input("Bank Name", value=st.session_state.bank_name)
        st.session_state.account_holder = st.text_input("Account Holder Name", value=st.session_state.account_holder)
        st.session_state.account_number = st.text_input("Account Number", value=st.session_state.account_number)
        st.session_state.ifsc = st.text_input("IFSC Code", value=st.session_state.ifsc)

    if st.button("Save & Continue"):
        if bank_details_valid():
            set_page("Final Verification")
            st.rerun()
        else:
            st.error("Please fill valid payout details.")

elif st.session_state.page == "Final Verification":
    st.markdown('<div class="screen-title">Final Verification</div>', unsafe_allow_html=True)
    st.markdown('<div class="screen-subtitle">Selfie verification + OTP before settlement</div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="warn-box">
        Verified users receive ₹5 extra payout bonus.
    </div>
    """, unsafe_allow_html=True)

    st.markdown("**Step 1: Capture selfie**")
    selfie = st.camera_input("Open camera and take selfie")

    if selfie is not None:
        st.session_state.selfie_photo = selfie
        face_verification_demo()
        verification_model()
        st.success("Selfie captured successfully. User marked verified.")

    st.markdown("**Step 2: OTP verification**")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Send OTP"):
            otp = send_demo_otp()
            st.info(f"Demo OTP: {otp}")
    with c2:
        st.session_state.entered_otp = st.text_input("Enter OTP", value=st.session_state.entered_otp)

    st.markdown(f"""
    <div class="card-soft">
        <b>Identity Verified:</b> {'Yes' if st.session_state.verified else 'No'}<br>
        <b>Face Verified:</b> {'Yes' if st.session_state.face_verified else 'No'}<br>
        <b>Trigger Ready:</b> {'Yes' if st.session_state.triggered else 'No'}<br>
        <b>OTP Sent:</b> {'Yes' if st.session_state.otp_sent else 'No'}
    </div>
    """, unsafe_allow_html=True)

    if st.button("Complete Verification & Release Payout"):
        final_claim_approval()
        if st.session_state.approved:
            set_page("Payout Confirmation")
            st.rerun()
        else:
            st.error("Verification failed. Check selfie, OTP, activity, or bank details.")

elif st.session_state.page == "Payout Confirmation":
    st.markdown('<div class="screen-title">Payout Released ✅</div>', unsafe_allow_html=True)

    st.markdown(f"""
    <div class="card-soft">
        <b>Policy ID:</b> {st.session_state.policy_id}<br><br>
        <b>Amount Paid:</b> ₹{st.session_state.payout}<br><br>
        <b>Payment Channel:</b> {st.session_state.payment_mode}<br><br>
        <b>Transaction ID:</b> #{st.session_state.txn}<br><br>
        <b>Payout Reason:</b> {st.session_state.payout_reason}<br><br>
        <b>Record Updated:</b> Yes
    </div>
    """, unsafe_allow_html=True)

    if st.session_state.claim_history:
        st.markdown("### Claim History")
        df = pd.DataFrame(st.session_state.claim_history)
        st.dataframe(df, use_container_width=True)

    if st.button("Back to Home"):
        reset_keep_profile = {
            "page": "Registration",
            "triggered": False,
            "approved": False,
            "payout": 0,
            "txn": "",
            "payout_reason": "",
            "claim_status": "Not Triggered",
            "otp_sent": False,
            "otp_code": "",
            "entered_otp": "",
        }
        for key, value in reset_keep_profile.items():
            st.session_state[key] = value
        st.rerun()
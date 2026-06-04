import streamlit as st
import streamlit.components.v1 as components
st.markdown(
    """
    <style>
    /* 隱藏所有 Streamlit alert（包含 deprecation warning） */
    div[data-testid="stAlert"] {
        display: none;
    }
    </style>
    """,
    unsafe_allow_html=True
)

import requests
from predict_core import predict_flu_probability


st.title("Flu Radar")
# ⭐️ 預留一個「最上方」的 metric 位置
st.caption("Based on the 20 clinical inputs")
metric_placeholder = st.empty()

qp = st.experimental_get_query_params()

# 抽出參數
token_q = qp.get("token", [""])[0]
obs_q   = qp.get("obs", [""])[0]
# =========================================
# 1️⃣ 讀 FHIR Observation
# =========================================
def load_patient_data_from_fhir(token, obs_url):
    patient_data = {}
    try:
        r = requests.get(obs_url, headers={"Authorization": f"Bearer {token}"}, verify=False, timeout=10)
        o = r.json()
    except Exception:
        return None

    for c in o.get("component", []):
        text = c.get("code", {}).get("text", "").strip()
        # Numeric
        if text == "Temperature (°C)":
            patient_data["temp"] = c["valueQuantity"]["value"]
        elif text == "Height (CM)":
            patient_data["height"] = c["valueQuantity"]["value"]
        elif text == "Weight (KG)":
            patient_data["weight"] = c["valueQuantity"]["value"]
        elif text == "Pulse":
            patient_data["pulse"] = c["valueQuantity"]["value"]
        elif text == "Respiratory rate":
            patient_data["rr"] = c["valueQuantity"]["value"]
        elif text == "Systolic BP":
            patient_data["sbp"] = c["valueQuantity"]["value"]
        elif text == "Oxygen saturation (%)":
            patient_data["o2s"] = c["valueQuantity"]["value"]
        elif text == "Season (1–4)":
            patient_data["season"] = c.get("valueInteger")
        elif text == "Week of Year":
            patient_data["WOS"] = c.get("valueInteger")
        elif text == "Days of illness":
            patient_data["DOI"] = c.get("valueInteger")
        # Binary
        elif text == "Influenza vaccine this year?":
            patient_data["fluvaccine"] = "Yes" if c.get("valueInteger") == 1 else "No"
        elif text == "Exposure to confirmed influenza?":
            patient_data["exposehuman"] = "Yes" if c.get("valueInteger") == 1 else "No"
        elif text == "Recent travel?":
            patient_data["travel"] = "Yes" if c.get("valueInteger") == 1 else "No"
        elif text == "New or increased cough?":
            patient_data["cough"] = "Yes" if c.get("valueInteger") == 1 else "No"
        elif text == "Cough with sputum?":
            patient_data["coughsputum"] = "Yes" if c.get("valueInteger") == 1 else "No"
        elif text == "Sore throat?":
            patient_data["sorethroat"] = "Yes" if c.get("valueInteger") == 1 else "No"
        elif text == "Rhinorrhea / nasal congestion?":
            patient_data["rhinorrhea"] = "Yes" if c.get("valueInteger") == 1 else "No"
        elif text == "Sinus pain?":
            patient_data["sinuspain"] = "Yes" if c.get("valueInteger") == 1 else "No"
        elif text == "Influenza antivirals in past 30 days?":
            patient_data["medhistav"] = "Yes" if c.get("valueInteger") == 1 else "No"
        elif text == "Chronic lung disease?":
            patient_data["pastmedchronlundis"] = "Yes" if c.get("valueInteger") == 1 else "No"
    return patient_data

# =========================================
# 2️⃣ 接收 token / obs_url 等（你可從 URL 或手動填）
# =========================================
token = token_q
obs_url = obs_q

patient_data = {}
if token and obs_url:
    patient_data = load_patient_data_from_fhir(token, obs_url)

    # =========================================
    # 2a️⃣ 顯示 FHIR 原始資料 / patient_data (可收折)
    # =========================================
    with st.expander("Patient Data（Click to Expand）", expanded=False):
        st.json(patient_data)
        st.divider()

    # =========================================
    # 2b️⃣ 將抓到的值放入 session_state，強制更新 widget 預設值
    # =========================================
    for k, v in patient_data.items():
        if k not in st.session_state:
            st.session_state[k] = v

# =========================================
# 3️⃣ helper（改成讀 session_state）
# =========================================
def num_input(label, minv, maxv, default, step=1.0, key=None):
    value = st.session_state.get(key, default)
    if isinstance(minv, float):
        value = float(value)
    else:
        value = int(value)
    return st.number_input(label, minv, maxv, value, step=step, key=key)

def yn(label, key):
    options = ["No", "Yes"]
    idx = 0
    v = st.session_state.get(key, "No")
    if isinstance(v, int):
        idx = 1 if v == 1 else 0
    elif isinstance(v, str):
        idx = options.index(v)
    return st.selectbox(label, options, index=idx, key=key)

# =========================================
# 4️⃣ Streamlit UI
# =========================================

left_col, right_col = st.columns(2)

with left_col:
    

    st.subheader("Vitals & Timing")        
    temp = num_input("Temperature (°C)", 30.0, 42.0, 37.3, 1.0, "temp")
    height = num_input("HEIGHT (CM)", 1.0, 400.0, 160.0, 0.5, "height")
    weight = num_input("WEIGHT (KG)", 1.0, 400.0, 60.0, 0.5, "weight")
    DOI = num_input("Days of illness", 1, 14, 1, 1, "DOI")
    WOS = num_input("Week of year", 1, 53, 1, 1, "WOS")
    season = num_input("Season (1–4)", 1, 4, 1, 1, "season")
    rr = num_input("Respiratory rate", 10, 30, 12, 1, "rr")
    sbp = num_input("Systolic BP", 50, 250, 90, 1, "sbp")
    o2s = num_input("Oxygen saturation (%)", 1, 100, 100, 1, "o2s")
    pulse = num_input("Pulse", 50, 180, 100, 1, "pulse")

with right_col:

    st.subheader("Symptoms & History")

    fluvaccine = yn("Influenza vaccine this year?", "fluvaccine")
    cough = yn("New or increased cough?", "cough")
    coughsputum = yn("Cough with sputum?", "coughsputum")
    sorethroat = yn("Sore throat?", "sorethroat")
    rhinorrhea = yn("Rhinorrhea / nasal congestion?", "rhinorrhea")
    sinuspain = yn("Sinus pain?", "sinuspain")
    exposehuman = yn("Exposure to confirmed influenza?", "exposehuman")
    travel = yn("Recent travel?", "travel")
    medhistav = yn("Influenza antivirals in past 30 days?", "medhistav")
    pastmedchronlundis = yn("Chronic lung disease?", "pastmedchronlundis")


# =========================================
# 5️⃣ Prediction
# =========================================

required_fields = [
    temp, height, weight, DOI, WOS, season,
    rr, sbp, o2s, pulse,
    fluvaccine, cough, coughsputum, sorethroat,
    rhinorrhea, sinuspain, exposehuman, travel,
    medhistav, pastmedchronlundis
]

if all(v is not None for v in required_fields):
    prob = predict_flu_probability(
        temp, height, weight, DOI, WOS, season,
        rr, sbp, o2s, pulse,
        fluvaccine, cough, coughsputum, sorethroat,
        rhinorrhea, sinuspain, exposehuman, travel,
        medhistav, pastmedchronlundis
    )

    # ⭐️ 顯示在最上方
    risk_pct = round(prob, 1)
    
    if risk_pct < 20:
        risk_label = "LOW RISK"
        risk_color = "#2ecc71"
    elif risk_pct < 40:
        risk_label = "MODERATE RISK"
        risk_color = "#f39c12"
    else:
        risk_label = "HIGH RISK"
        risk_color = "#e74c3c"
    
    with metric_placeholder.container():
        pie_col, value_col = st.columns([1, 2], gap="large")
    
        # --------------------
        # 左：圓餅圖（只畫圖）
        # --------------------
        with pie_col:
            components.html(
                f"""
                <style>
                .pie {{
                    width: 120px;
                    height: 120px;
                    border-radius: 50%;
                    background: conic-gradient(
                        {risk_color} {risk_pct}%,
                        #2c2c2c {risk_pct}% 100%
                    );
                }}
                </style>
                <div style="display:flex; justify-content:center;">
                    <div class="pie"></div>
                </div>
                """,
                height=140,
            )

    
        # --------------------
        # 右：數值與風險（原生 Streamlit）
        # --------------------
        with value_col:
            st.markdown(
                f"""
                <div style="text-align:center; margin-top:16px;">
                    <div style="font-size:42px;font-weight:800;">
                        {risk_pct:.2f}%
                    </div>
                    <div style="font-size:20px;font-weight:700;color:{risk_color};">
                        {risk_label}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    
else:
    metric_placeholder.info(
        "請完成必要臨床欄位輸入，即可即時顯示預測結果。"
    )
    # =========================================
# 6️⃣ Token & Observation URL（放最下面）
# =========================================

st.divider()

token = st.text_input("Token", value=token)
obs_url = st.text_input("Observation URL", value=obs_url)

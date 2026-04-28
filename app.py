import streamlit as st
import pandas as pd
import requests
import datetime
import math
import io
import urllib.parse  # Crucial for fixing the WhatsApp button link
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

# ==========================================
# 1. PAGE CONFIG & STYLING
# ==========================================
st.set_page_config(page_title="Rubirizi Tax Pro", page_icon="⚖️", layout="wide")

# This CSS ensures the UI looks like a professional agency portal
st.markdown("""
<style>
    .main {background-color: #f8f9fa;}
    .header {background:#004b23; padding:25px; border-radius:15px; color:white; text-align:center; margin-bottom:20px}
    .card {background:white; padding:30px; border-radius:15px; box-shadow:0 4px 20px rgba(0,0,0,0.08); color:#333; border: 1px solid #eee;}
    .total-tax {color:#d90429; font-size:32px; font-weight:bold; margin:10px 0}
    .btn-wa {
        background-color: #25D366; 
        color: white !important; 
        padding: 16px; 
        border-radius: 10px; 
        text-align: center; 
        display: block; 
        text-decoration: none; 
        font-weight: bold; 
        font-size: 18px; 
        margin-top: 20px;
    }
    .btn-wa:hover {background-color: #128C7E; color: white !important;}
    .row-item {display:flex; justify-content:space-between; padding:12px 0; border-bottom:1px solid #eee; font-size:16px}
</style>
<div class="header">
    <h1>Rubirizi Tax Pro</h1>
    <p>Professional Customs & Tax Advisory | 2026 URA Standards</p>
</div>
""", unsafe_allow_html=True)

# ==========================================
# 2. VALUATION DATABASE (2026 ESTIMATES)
# ==========================================
car_db = {
    "Toyota Fielder (2015-2018)": 6500,
    "Toyota Premio (2014-2017)": 7200,
    "Toyota Harrier (2016-2019)": 14500,
    "Toyota Land Cruiser V8 (2016+)": 45000,
    "Subaru Forester (2015-2018)": 8500,
    "Other / Custom Value": 0
}

# ==========================================
# 3. SIDEBAR & LIVE RATES
# ==========================================
with st.sidebar:
    st.image("https://www.ura.go.ug/wp-content/uploads/2021/04/URA-Logo.png", width=120)
    st.title("Settings")
    def get_rate():
        try:
            r = requests.get("https://api.exchangerate-api.com/v4/latest/USD").json()
            return r["rates"]["UGX"]
        except: return 3880
    rate = st.number_input("Exchange Rate (UGX)", value=int(get_rate()))
    st.markdown("---")
    st.info("**Consultant:** Victor Tukesiga\n**Location:** Nakawa, Kampala")

# ==========================================
# 4. CALCULATOR INPUTS
# ==========================================
left, right = st.columns([1, 1], gap="large")

with left:
    st.subheader("📋 Shipment Details")
    category = st.selectbox("Category", ["Motor Vehicle", "General Goods", "Mivumba"])
    
    fob = 0.0
    if category == "Motor Vehicle":
        selected_car = st.selectbox("Model (URA Valuation Guide)", list(car_db.keys()))
        fob = car_db[selected_car] if selected_car != "Other / Custom Value" else st.number_input("Invoice FOB (USD)", 0.0)
        yom = st.number_input("Year of Manufacture", 2008, 2026, 2017)
        cc = st.number_input("Engine (cc)", 800, 6000, 1500)
    else:
        fob = st.number_input("Value of Goods", 0.0)
        curr = st.selectbox("Currency", ["USD", "UGX"])

    freight = st.number_input("Freight/Shipping", 0.0, value=1200.0 if category == "Motor Vehicle" else 0.0)
    wht_exempt = st.toggle("WHT Exempt?")

# ==========================================
# 5. TAX LOGIC (COMPLIANT 2026 STANDARDS)
# ==========================================
insurance = fob * 0.015
cif_ugx = (fob + freight + insurance) * rate if (category != "Motor Vehicle" or fob > 0) else 0

# Base Rates
duty_p, excise_p, env_p, reg_fees = 0.25, 0.10, 0.0, 0.0

if category == "Motor Vehicle":
    age = 2026 - yom
    if age >= 13: env_p = 0.50
    elif age >= 8: env_p = 0.35
    excise_p = 0.20 if cc > 2500 else 0.10
    reg_fees = 1500000 
elif category == "Mivumba":
    env_p, duty_p = 0.30, 0.35

# Core Calculations
i_duty = cif_ugx * duty_p
idf = cif_ugx * 0.015
infra = cif_ugx * 0.015
excise = cif_ugx * excise_p
env = cif_ugx * env_p
wht = 0 if wht_exempt else (cif_ug

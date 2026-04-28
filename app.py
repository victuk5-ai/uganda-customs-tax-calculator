import streamlit as st
import pandas as pd
import requests
import datetime
import math
import io
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

# =========================
# 1. PAGE CONFIG & STYLING
# =========================
st.set_page_config(page_title="Rubirizi Tax Pro", page_icon="⚖️", layout="wide")

st.markdown("""
<style>
    .header {background:#004b23; padding:25px; border-radius:15px; color:white; text-align:center; margin-bottom:20px}
    .card {background:white; padding:30px; border-radius:15px; box-shadow:0 4px 20px rgba(0,0,0,0.08); color:#333}
    .total-tax {color:#d90429; font-size:32px; font-weight:bold; margin:10px 0}
    .btn-wa {background:#25D366; color:white !important; padding:15px; border-radius:10px; text-align:center; 
             display:block; text-decoration:none; font-weight:bold; font-size:18px; margin-top:20px}
    .row-item {display:flex; justify-content:space-between; padding:12px 0; border-bottom:1px solid #eee; font-size:16px}
</style>
<div class="header">
    <h1>Rubirizi Tax Pro</h1>
    <p>2026 URA Valuation & Customs Advisory Portal</p>
</div>
""", unsafe_allow_html=True)

# =========================
# 2. VALUATION DATABASE (2026 ESTIMATES)
# =========================
# These are typical URA valuation guide averages for 2026
car_db = {
    "Toyota Fielder (2015-2018)": 6500,
    "Toyota Premio (2014-2017)": 7200,
    "Toyota Harrier (2016-2019)": 14500,
    "Toyota Land Cruiser V8 (2016+)": 45000,
    "Subaru Forester (2015-2018)": 8500,
    "Custom (Enter Manually)": 0
}

# =========================
# 3. SIDEBAR & TOOLS
# =========================
with st.sidebar:
    st.title("System Settings")
    def get_live_rate():
        try:
            r = requests.get("https://api.exchangerate-api.com/v4/latest/USD").json()
            return r["rates"]["UGX"]
        except: return 3880
    
    rate = st.number_input("Exchange Rate (UGX)", value=int(get_live_rate()))
    st.markdown("---")
    st.info("Agent: Victor Tukesiga\n\nLocation: Nakawa, Kampala")

# =========================
# 4. CALCULATOR INTERFACE
# =========================
left, right = st.columns([1, 1], gap="large")

with left:
    st.subheader("🔍 Valuation & Specs")
    
    cat = st.selectbox("Category", ["Motor Vehicle", "General Goods", "Mivumba"])
    
    # Dynamic Valuation Logic
    fob_input = 0.0
    if cat == "Motor Vehicle":
        selected_car = st.selectbox("Quick Valuation (URA Guide)", list(car_db.keys()))
        if selected_car != "Custom (Enter Manually)":
            fob_input = car_db[selected_car]
            st.success(f"URA Estimated FOB: ${fob_input:,.0f}")
        else:
            fob_input = st.number_input("Enter Invoice FOB (USD)", min_value=0.0)
        
        yom = st.number_input("Year of Manufacture", 2008, 2026, 2017)
        cc = st.number_input("Engine Size (cc)", 800, 6000, 1500)
    else:
        fob_input = st.number_input("Value of Goods", min_value=0.0)
        curr = st.selectbox("Currency", ["USD", "UGX"])

    shipping = st.number_input("Freight / Shipping", min_value=0.0, value=1200.0 if cat == "Motor Vehicle" else 0.0)
    wht_exempt = st.toggle("WHT Exempt (Tax Compliant?)")

# --- CALCULATION LOGIC ---
insurance = fob_input * 0.015
cif_ugx = (fob_input + shipping + insurance) * rate

# Tax Logic
duty_p, excise_p, env_p, reg_fees = 0.25, 0.10, 0.0, 0.0

if cat == "Motor Vehicle":
    age = 2026 - yom
    if age >= 13: env_p = 0.50
    elif age >= 8: env_p = 0.35
    excise_p = 0.20 if cc > 2500 else 0.10
    reg_fees = 1500000 

elif cat == "Mivumba":
    env_p, duty_p = 0.30, 0.35

# Taxes
i_duty = cif_ugx * duty_p
idf = cif_ugx * 0.015
infra = cif_ugx * 0.015
excise = cif_ugx * excise_p
env = cif_ugx * env_p
wht = 0 if wht_exempt else (cif_ugx * 0.06)

vat_base = cif_ugx + i_duty + excise + idf + infra + env
vat = vat_base * 0.18
total_ura = i_duty + idf + infra + excise + env + vat + wht

with right:
    st.subheader("⚖️ Final Quote")
    if fob_input > 0:
        st.markdown(f"""
        <div class="card">
            <p style="margin:0">Total Estimated URA Taxes:</p>
            <div class="total-tax">UGX {math.ceil(total_ura + reg_fees):,.0f}</div>
            <hr>
            <div class="row-item"><span>Import Duty (25%)</span><b>{i_duty:,.0f}</b></div>
            <div class="row-item"><span>VAT (18%)</span><b>{vat:,.0f}</b></div>
            <div class="row-item"><span>Env. Levy ({int(env_p*100)}%)</span><b>{env:,.0f}</b></div>
            <div class="row-item"><span>Excise ({int(excise_p*100)}%)</span><b>{excise:,.0f}</b></div>
            <div class="row-item"><span>WHT (6%)</span><b>{wht:,.0f}</b></div>
            <div class="row-item"><span>Registration</span><b>{reg_fees:,.0f}</b></div>
            <hr>
            <div class="row-item"><strong>TOTAL LANDING</strong><strong>UGX {math.ceil(cif_ugx + total_ura + reg_fees):,.0f}</strong></div>
            
            <a class="btn-wa" href="https://wa.me/256706631303?text=Hi Victor, I need clearing for {selected_car if cat=='Motor Vehicle' else 'Goods'}. Quote: UGX {total_ura+reg_fees:,.0f}">
            💬 Start Clearing Process
            </a>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.info("Select a vehicle or enter a value to generate the tax quote.")

st.markdown("---")
st.caption("© 2026 Rubirizi Clearing | Professional Tax Consultant | Nakawa, Kampala")

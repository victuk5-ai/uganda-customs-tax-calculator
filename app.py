import streamlit as st
import pandas as pd
import requests
import datetime
import math
import io
import urllib.parse
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

# ==========================================
# 1. PAGE CONFIG & STYLING
# ==========================================
st.set_page_config(page_title="Rubirizi Tax Pro", page_icon="⚖️", layout="wide")

st.markdown("""
<style>
    .header {background:#004b23; padding:25px; border-radius:15px; color:white; text-align:center; margin-bottom:20px}
    .card {background:white; padding:30px; border-radius:15px; box-shadow:0 4px 20px rgba(0,0,0,0.08); color:#333; border: 1px solid #eee;}
    .total-tax {color:#d90429; font-size:32px; font-weight:bold; margin:10px 0}
    .btn-wa {
        background-color: #25D366 !important; 
        color: white !important; 
        padding: 16px; 
        border-radius: 10px; 
        text-align: center; 
        display: block; 
        text-decoration: none !important; 
        font-weight: bold; 
        font-size: 18px; 
        margin-top: 20px;
    }
    .btn-wa:hover {background-color: #128C7E !important;}
    .row-item {display:flex; justify-content:space-between; padding:12px 0; border-bottom:1px solid #eee; font-size:16px}
</style>
<div class="header">
    <h1>Rubirizi Tax Pro</h1>
    <p>Professional Customs & Tax Advisory | 2026 URA Standards</p>
</div>
""", unsafe_allow_html=True)

# ==========================================
# 2. DATA & SIDEBAR
# ==========================================
car_db = {
    "Toyota Fielder (2015-2018)": 6500,
    "Toyota Premio (2014-2017)": 7200,
    "Toyota Harrier (2016-2019)": 14500,
    "Toyota Land Cruiser V8 (2016+)": 45000,
    "Subaru Forester (2015-2018)": 8500,
    "Other / Custom Value": 0
}

with st.sidebar:
    st.image("https://www.ura.go.ug/wp-content/uploads/2021/04/URA-Logo.png", width=120)
    st.title("Settings")
    def get_rate():
        try:
            r = requests.get("https://api.exchangerate-api.com/v4/latest/USD", timeout=5).json()
            return r["rates"]["UGX"]
        except: return 3880
    rate = st.number_input("Exchange Rate (UGX)", value=int(get_rate()))
    st.info("**Consultant:** Victor Tukesiga\n**Location:** Nakawa")

# ==========================================
# 3. INPUTS & LOGIC
# ==========================================
left, right = st.columns([1, 1], gap="large")

with left:
    st.subheader("📋 Shipment Details")
    category = st.selectbox("Category", ["Motor Vehicle", "General Goods", "Mivumba"])
    
    fob = 0.0
    item_label = ""
    if category == "Motor Vehicle":
        item_label = st.selectbox("Model (URA Guide)", list(car_db.keys()))
        fob = float(car_db[item_label]) if item_label != "Other / Custom Value" else st.number_input("Invoice FOB (USD)", 0.0)
        yom = st.number_input("Year of Manufacture", 2008, 2026, 2017)
        cc = st.number_input("Engine (cc)", 800, 6000, 1500)
    else:
        item_label = category
        fob = st.number_input("Value of Goods", 0.0)
        curr = st.selectbox("Currency", ["USD", "UGX"])

    freight = st.number_input("Freight/Shipping", 0.0, value=1200.0 if category == "Motor Vehicle" else 0.0)
    wht_exempt = st.toggle("WHT Exempt?")

# --- CALCULATIONS ---
insurance = fob * 0.015
cif_ugx = (fob + freight + insurance) * rate if (category != "Motor Vehicle" or fob > 0) else 0

duty_p, excise_p, env_p, reg_fees = 0.25, 0.10, 0.0, 0.0
if category == "Motor Vehicle":
    age = 2026 - yom
    env_p = 0.50 if age >= 13 else (0.35 if age >= 8 else 0.0)
    excise_p = 0.20 if cc > 2500 else 0.10
    reg_fees = 1500000 
elif category == "Mivumba":
    env_p, duty_p = 0.30, 0.35

i_duty = cif_ugx * duty_p
idf, infra = cif_ugx * 0.015, cif_ugx * 0.015
excise, env = cif_ugx * excise_p, cif_ugx * env_p
wht = 0 if wht_exempt else (cif_ugx * 0.06)
vat = (cif_ugx + i_duty + excise + idf + infra + env) * 0.18

total_taxes = i_duty + idf + infra + excise + env + vat + wht
grand_total = total_taxes + reg_fees
final_landing = cif_ugx + grand_total

# ==========================================
# 4. RESULTS & THE WHATSAPP BUTTON
# ==========================================
with right:
    st.subheader("⚖️ Final Assessment")
    if fob > 0:
        # 1. Clean URL encoding for the WhatsApp message
        message = f"Hi Victor, I need help clearing my {item_label}. Tax estimate: UGX {grand_total:,.0f}"
        encoded_msg = urllib.parse.quote(message)
        wa_url = f"https://wa.me/256706631303?text={encoded_msg}"
        
        # 2. Render the results card and button using HTML
        st.markdown(f"""
        <div class="card">
            <p style="margin:0">Total Estimated URA Taxes:</p>
            <div class="total-tax">UGX {math.ceil(grand_total):,.0f}</div>
            <hr>
            <div class="row-item"><span>Import Duty</span><b>{i_duty:,.0f}</b></div>
            <div class="row-item"><span>VAT (18%)</span><b>{vat:,.0f}</b></div>
            <div class="row-item"><span>Env. Levy</span><b>{env:,.0f}</b></div>
            <div class="row-item"><span>Excise & Others</span><b>{(excise + idf + infra):,.0f}</b></div>
            <div class="row-item"><span>Registration Fees</span><b>{reg_fees:,.0f}</b></div>
            <hr>
            <div class="row-item"><strong>TOTAL LANDING COST</strong><strong>UGX {math.ceil(final_landing):,.0f}</strong></div>
            
            <a href="{wa_url}" target="_blank" class="btn-wa">
                💬 Hire Rubirizi Clearing Expert
            </a>
        </div>
        """, unsafe_allow_html=True)
        
        st.write("")
        
        # PDF Generation
        try:
            buf = io.BytesIO()
            doc = SimpleDocTemplate(buf)
            s = getSampleStyleSheet()
            content = [
                Paragraph("Rubirizi Tax Pro Assessment", s["Title"]),
                Spacer(1, 12),
                Paragraph(f"Item: {item_label}", s["Normal"]),
                Paragraph(f"Total Taxes: UGX {grand_total:,.0f}", s["Heading2"]),
                Paragraph(f"Exchange Rate: {rate} UGX/USD", s["Normal"]),
                Spacer(1, 12),
                Paragraph("Disclaimer: This is an estimate based on 2026 URA standards.", s["Italic"])
            ]
            doc.build(content)
            st.download_button("📄 Download PDF Report", buf.getvalue(), "Rubirizi_Quote.pdf", "application/pdf")
        except Exception as e:
            st.error(f"Error generating PDF: {e}")
    else:
        st.info("Input item value to generate the report.")

st.markdown("---")
st.caption("© 2026 Rubirizi Clearing & Forwarding Agency | Nakawa, Kampala")

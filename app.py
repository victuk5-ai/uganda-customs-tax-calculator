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
# 1. PAGE CONFIG & UI THEME
# ==========================================
st.set_page_config(page_title="Rubirizi Tax Pro", page_icon="⚖️", layout="wide")

# We simplified the CSS to focus only on the button stability
st.markdown("""
<style>
    .report-card {
        background: #ffffff;
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #e0e0e0;
        margin-bottom: 20px;
    }
    .tax-val {
        color: #d90429;
        font-size: 28px;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. DATA & LIVE EXCHANGE
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
    st.title("Admin Settings")
    def get_rate():
        try:
            r = requests.get("https://api.exchangerate-api.com/v4/latest/USD", timeout=5).json()
            return r["rates"]["UGX"]
        except: return 3880
    rate = st.number_input("Exchange Rate (UGX)", value=int(get_rate()))
    st.info("**Consultant:** Victor Tukesiga\n**Location:** Nakawa")

# ==========================================
# 3. INPUT CALCULATOR
# ==========================================
col1, col2 = st.columns([1, 1], gap="large")

with col1:
    st.subheader("📋 Shipment Details")
    category = st.selectbox("Category", ["Motor Vehicle", "General Goods", "Mivumba"])
    
    fob = 0.0
    item_name = ""
    if category == "Motor Vehicle":
        item_name = st.selectbox("Select Model", list(car_db.keys()))
        fob = float(car_db[item_name]) if item_name != "Other / Custom Value" else st.number_input("Invoice FOB (USD)", 0.0)
        yom = st.number_input("Year of Manufacture", 2008, 2026, 2017)
        cc = st.number_input("Engine (cc)", 800, 6000, 1500)
    else:
        item_name = category
        fob = st.number_input("Value of Goods", 0.0)

    freight = st.number_input("Freight", 0.0, value=1200.0 if category == "Motor Vehicle" else 0.0)
    wht_exempt = st.toggle("Tax Compliant (WHT Exempt)")

# --- LOGIC ---
insurance = fob * 0.015
cif_ugx = (fob + freight + insurance) * rate if (fob > 0) else 0

# 2026 Tax Tiers
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

total_ura_taxes = i_duty + idf + infra + excise + env + vat + wht
grand_total = total_ura_taxes + reg_fees

# ==========================================
# 4. RESULTS & THE WHATSAPP FIX
# ==========================================
with col2:
    st.subheader("⚖️ Assessment Report")
    if fob > 0:
        # Displaying the Data in a clean way (Not HTML, to avoid errors)
        st.write("---")
        st.write(f"**Total Estimated Taxes:**")
        st.title(f"UGX {grand_total:,.0f}")
        
        st.write(f"Import Duty: {i_duty:,.0f}")
        st.write(f"VAT (18%): {vat:,.0f}")
        st.write(f"Environmental Levy: {env:,.0f}")
        st.write(f"Registration: {reg_fees:,.0f}")
        st.write("---")
        
        # THE WHATSAPP BUTTON FIX: 
        # Instead of a complex <a> tag, we use a simple button style inside st.markdown
        message_text = f"Hi Victor, I need help clearing my {item_name}. Estimate: UGX {grand_total:,.0f}"
        encoded_message = urllib.parse.quote(message_text)
        whatsapp_url = f"https://wa.me/256706631303?text={encoded_message}"
        
        # This is a much cleaner way to trigger the link as a button
        st.markdown(f'''
            <a href="{whatsapp_url}" target="_blank" style="text-decoration: none;">
                <div style="
                    background-color: #25D366;
                    color: white;
                    padding: 15px;
                    text-align: center;
                    border-radius: 10px;
                    font-weight: bold;
                    font-size: 20px;
                    cursor: pointer;
                    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                ">
                    💬 Chat with Victor on WhatsApp
                </div>
            </a>
        ''', unsafe_allow_html=True)
        
        st.write("")
        
        # PDF Option
        try:
            buf = io.BytesIO()
            doc = SimpleDocTemplate(buf)
            s = getSampleStyleSheet()
            content = [Paragraph("Rubirizi Quote", s["Title"]), Paragraph(f"Total: UGX {grand_total:,.0f}", s["Heading2"])]
            doc.build(content)
            st.download_button("📄 Download PDF Report", buf.getvalue(), "Quote.pdf", "application/pdf")
        except: pass
    else:
        st.info("Enter details on the left to generate the tax quote.")

st.markdown("---")
st.caption("© 2026 Rubirizi Clearing & Forwarding | Nakawa, Kampala")

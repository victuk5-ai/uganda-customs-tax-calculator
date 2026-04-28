import streamlit as st
import pandas as pd
import requests
import datetime
import math
import io
import urllib.parse
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4

# ==========================================
# 1. PAGE CONFIG & UI THEME (DARK MODE FIX)
# ==========================================
st.set_page_config(page_title="Rubirizi Tax Pro", page_icon="⚖️", layout="wide")

st.markdown("""
<style>
    /* Header styling */
    .header {background:#004b23; padding:25px; border-radius:15px; color:white; text-align:center; margin-bottom:20px}
    
    /* Main Card: Forced visibility for Dark Mode */
    .main-card {
        background-color: #ffffff !important; 
        padding: 25px; 
        border-radius: 15px; 
        border: 1px solid #eee; 
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        color: #1a1a1a !important;
    }
    
    /* Force text inside card to be dark */
    .main-card p, .main-card b, .main-card span {
        color: #1a1a1a !important;
    }
    
    .tax-amount {
        color: #d90429 !important; 
        margin-top: 0;
        font-weight: bold;
        font-size: 32px;
    }
    
    .tax-row {
        display: flex; 
        justify-content: space-between; 
        padding: 10px 0; 
        border-bottom: 1px solid #f0f0f0;
    }
</style>
<div class="header">
    <h1>Rubirizi Tax Pro</h1>
    <p>Professional Customs & Tax Advisory | Rubirizi Clearing Agency</p>
</div>
""", unsafe_allow_html=True)

# ==========================================
# 2. VALUATION & SIDEBAR
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
        except: return 3800
    rate = st.number_input("Exchange Rate (UGX)", value=int(get_rate()))
    st.info("**Agency:** Rubirizi Clearing & Forwarding\\n**Location:** Nakawa, Kampala")

# ==========================================
# 3. INPUTS & SAD-MATCHED LOGIC
# ==========================================
left, right = st.columns([1, 1], gap="large")

with left:
    st.subheader("📋 Shipment Details")
    category = st.selectbox("Category", ["General Goods", "Appliances (SAD Logic)", "Motor Vehicle", "Mivumba"])
    
    fob = 0.0
    item_label = ""
    if category == "Motor Vehicle":
        item_label = st.selectbox("Model (URA Guide)", list(car_db.keys()))
        fob = float(car_db[item_label]) if item_label != "Other / Custom Value" else st.number_input("Invoice FOB (USD)", 0.0)
        yom = st.number_input("Year of Manufacture", 2008, 2026, 2017)
        cc = st.number_input("Engine (cc)", 800, 6000, 1500)
    else:
        item_label = category
        fob = st.number_input("Value (USD)", 0.0)

    freight = st.number_input("Freight/Shipping", 0.0, value=1200.0 if category == "Motor Vehicle" else 0.0)
    wht_exempt = st.toggle("WHT Exempt?")

# --- CALCULATIONS (Based on URA SAD Document Logic) ---
insurance = fob * 0.015
stat_value_ugx = (fob + freight + insurance) * rate if (fob > 0) else 0

# SAD Rates
duty_p = 0.10 if category == "Appliances (SAD Logic)" else (0.35 if category == "Mivumba" else 0.25)
excise_p, env_p, reg_fees = 0.0, 0.0, 0.0

if category == "Motor Vehicle":
    age = 2026 - yom
    env_p = 0.50 if age >= 13 else (0.35 if age >= 8 else 0.0)
    excise_p = 0.20 if cc > 2500 else 0.10
    reg_fees = 1500000 

# Individual Taxes
i_duty = stat_value_ugx * duty_p
wht = 0 if wht_exempt else (stat_value_ugx * 0.06) 
idf_infra = stat_value_ugx * 0.03
env = stat_value_ugx * env_p
excise = stat_value_ugx * excise_p

# VAT Compounding Logic: (Stat Value + Duty + IDF + Infra + Env + Excise)
vat_base = stat_value_ugx + i_duty + idf_infra + env + excise
vat = vat_base * 0.18 

grand_total = i_duty + wht + vat + idf_infra + env + excise + reg_fees

# ==========================================
# 4. RESULTS & MOBILE-SAFE WHATSAPP
# ==========================================
with right:
    st.subheader("⚖️ Assessment Report")
    if fob > 0:
        st.markdown(f"""
        <div class="main-card">
            <p style="margin-bottom:5px;">Total Estimated URA Taxes</p>
            <div class="tax-amount">UGX {math.ceil(grand_total):,.0f}</div>
            <hr style="border: 0.5px solid #eee;">
            <div class="tax-row"><span>Import Duty (102)</span><b>{i_duty:,.0f}</b></div>
            <div class="tax-row"><span>VAT (401)</span><b>{vat:,.0f}</b></div>
            <div class="tax-row"><span>WHT (105)</span><b>{wht:,.0f}</b></div>
            <div class="tax-row" style="border-bottom:none;"><span>Registration Fees</span><b>{reg_fees:,.0f}</b></div>
        </div>
        """, unsafe_allow_html=True)
        
        st.write("")
        
        # Native link button prevents raw HTML code on mobile
        msg = f"Hi Victor, I need help clearing my {item_label}. Estimate: UGX {grand_total:,.0f}"
        wa_url = f"https://wa.me/256706631303?text={urllib.parse.quote(msg)}"
        st.link_button("💬 Hire Rubirizi Clearing Expert", wa_url, use_container_width=True)

        # ==========================================
        # 5. CLEAN PDF GENERATOR
        # ==========================================
        def generate_report():
            buf = io.BytesIO()
            doc = SimpleDocTemplate(buf, pagesize=A4)
            styles = getSampleStyleSheet()
            
            title_style = ParagraphStyle('T', parent=styles['Title'], textColor=colors.HexColor("#004b23"))
            body_style = ParagraphStyle('B', parent=styles['Normal'], alignment=1)
            
            content = [
                Paragraph("RUBIRIZI CLEARING & FORWARDING AGENCY", title_style),
                Paragraph("Licensed Customs Clearing & Tax Consultants", body_style),
                Paragraph("Nakawa, Kampala | Tel: +256 706 631303", body_style),
                Spacer(1, 25),
                Paragraph(f"Assessment for: {item_label}", styles["Heading2"]),
                Paragraph(f"Date: {datetime.datetime.now().strftime('%Y-%m-%d')}", styles["Normal"]),
                Spacer(1, 15)
            ]
            
            data = [
                ['Tax Component', 'Rate', 'Amount (UGX)'],
                ['Import Duty (102)', f'{int(duty_p*100)}%', f'{i_duty:,.0f}'],
                ['VAT (401)', '18%', f'{vat:,.0f}'],
                ['Withholding Tax (105)', '6%', f'{wht:,.0f}'],
                ['IDF & Infrastructure', '3%', f'{idf_infra:,.0f}'],
                ['Registration Fees', 'Fixed', f'{reg_fees:,.0f}'],
                ['GRAND TOTAL', '', f'{grand_total:,.0f}']
            ]
            
            table = Table(data, colWidths=[200, 100, 150])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#004b23")),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
                ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
                ('SIZE', (0, -1), (-1, -1), 12),
            ]))
            content.append(table)
            
            content.append(Spacer(1, 30))
            content.append(Paragraph("DISCLAIMER: This is a preliminary tax estimate based on 2026 URA standards. Final liability is determined by URA valuation.", styles["Italic"]))
            
            doc.build(content)
            return buf.getvalue()

        st.download_button("📄 Download Official Quote", generate_report(), "Rubirizi_Quote.pdf", "application/pdf")
    else:
        st.info("Enter details on the left to see assessment results.")

st.markdown("---")
st.caption("© 2026 Rubirizi Clearing & Forwarding Agency | Nakawa Branch | Expert: Victor Tukesiga")

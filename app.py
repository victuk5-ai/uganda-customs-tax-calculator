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
# 1. PAGE CONFIG & UI THEME
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
    <p>Official 2026 URA Customs Advisory Portal</p>
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
    st.title("Admin Tools")
    def get_rate():
        try:
            r = requests.get("https://api.exchangerate-api.com/v4/latest/USD", timeout=5).json()
            return r["rates"]["UGX"]
        except: return 3880
    rate = st.number_input("Exchange Rate (UGX)", value=int(get_rate()))
    st.info("**Agency:** Rubirizi Clearing & Forwarding\n**Location:** Nakawa, Kampala")

# ==========================================
# 3. INPUTS & UPDATED LOGIC (SAD-MATCHED)
# ==========================================
left, right = st.columns([1, 1], gap="large")

with left:
    st.subheader("📋 Shipment Details")
    category = st.selectbox("Category", ["Motor Vehicle", "Appliances (SAD Logic)", "General Goods", "Mivumba"])
    
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

# --- CALCULATIONS BASED ON YOUR SAD DOCUMENT ---
insurance = fob * 0.015
stat_value_ugx = (fob + freight + insurance) * rate if (fob > 0) else 0

# SAD Rates based on your image
duty_p = 0.10 if category == "Appliances (SAD Logic)" else (0.35 if category == "Mivumba" else 0.25)
excise_p, env_p, reg_fees = 0.0, 0.0, 0.0

if category == "Motor Vehicle":
    age = 2026 - yom
    env_p = 0.50 if age >= 13 else (0.35 if age >= 8 else 0.0)
    excise_p = 0.20 if cc > 2500 else 0.10
    reg_fees = 1500000 
elif category == "Mivumba":
    env_p = 0.30

# Individual Taxes
i_duty = stat_value_ugx * duty_p
wht = 0 if wht_exempt else (stat_value_ugx * 0.06) 
idf = stat_value_ugx * 0.015
infra = stat_value_ugx * 0.015
excise = stat_value_ugx * excise_p
env = stat_value_ugx * env_p

# VAT (Compounded logic: Stat Value + Duty + Excise + Levies)
vat_base = stat_value_ugx + i_duty + excise + idf + infra + env
vat = vat_base * 0.18 

grand_total = i_duty + wht + vat + idf + infra + excise + env + reg_fees

# ==========================================
# 4. RESULTS & WHATSAPP
# ==========================================
with right:
    st.subheader("⚖️ Final Assessment")
    if fob > 0:
        message = f"Hi Victor, I need help clearing my {item_label} via Rubirizi Clearing Agency. Tax estimate: UGX {grand_total:,.0f}"
        encoded_msg = urllib.parse.quote(message)
        wa_url = f"https://wa.me/256706631303?text={encoded_msg}"
        
        st.markdown(f"""
        <div class="card">
            <p style="margin:0">Total Estimated URA Taxes:</p>
            <div class="total-tax">UGX {math.ceil(grand_total):,.0f}</div>
            <hr>
            <div class="row-item"><span>Import Duty (102)</span><b>{i_duty:,.0f}</b></div>
            <div class="row-item"><span>VAT (401)</span><b>{vat:,.0f}</b></div>
            <div class="row-item"><span>WHT (105)</span><b>{wht:,.0f}</b></div>
            <div class="row-item"><span>IDF & Infrastructure</span><b>{(idf + infra):,.0f}</b></div>
            <div class="row-item"><span>Registration Fees</span><b>{reg_fees:,.0f}</b></div>
            <hr>
            <div class="row-item"><strong>GRAND TOTAL</strong><strong>UGX {math.ceil(grand_total):,.0f}</strong></div>
            
            <a href="{wa_url}" target="_blank" class="btn-wa">
                💬 Hire Rubirizi Clearing Expert
            </a>
        </div>
        """, unsafe_allow_html=True)
        
        st.write("")
        
        # ==========================================
        # 5. PDF DOWNLOAD WITH AGENCY & DISCLAIMER
        # ==========================================
        def generate_report():
            buf = io.BytesIO()
            doc = SimpleDocTemplate(buf, pagesize=A4)
            styles = getSampleStyleSheet()
            
            # Custom Styles
            title_style = ParagraphStyle('Title', parent=styles['Title'], textColor=colors.HexColor("#004b23"))
            agency_style = ParagraphStyle('Agency', parent=styles['Normal'], fontSize=12, alignment=1)
            disclaimer_style = ParagraphStyle('Disclaimer', parent=styles['Normal'], fontSize=8, textColor=colors.red, alignment=1)
            
            content = []
            content.append(Paragraph("RUBIRIZI CLEARING & FORWARDING AGENCY", title_style))
            content.append(Paragraph("Licensed Customs Clearing & Tax Consultants", agency_style))
            content.append(Paragraph("Nakawa, Kampala | Tel: +256 706 631303", agency_style))
            content.append(Spacer(1, 25))
            
            content.append(Paragraph(f"<b>Assessment Report:</b> {item_label}", styles["Normal"]))
            content.append(Paragraph(f"<b>Date:</b> {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}", styles["Normal"]))
            content.append(Spacer(1, 15))
            
            # Tax Table
            data = [
                ['Tax Component', 'Rate', 'Amount (UGX)'],
                ['Import Duty (Code 102)', f'{int(duty_p*100)}%', f'{i_duty:,.0f}'],
                ['VAT (Code 401)', '18%', f'{vat:,.0f}'],
                ['Withholding Tax (Code 105)', '6%', f'{wht:,.0f}'],
                ['IDF & Infrastructure', '3%', f'{(idf+infra):,.0f}'],
                ['Registration Fees', 'Fixed', f'{reg_fees:,.0f}'],
                ['GRAND TOTAL', '', f'<b>{grand_total:,.0f}</b>']
            ]
            
            table = Table(data, colWidths=[200, 100, 150])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#004b23")),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
            ]))
            content.append(table)
            
            content.append(Spacer(1, 30))
            content.append(Paragraph("<b>⚠️ DISCLAIMER:</b> This is a preliminary tax estimate issued by Rubirizi Clearing Agency for planning purposes. The final tax liability is determined by the Uganda Revenue Authority (URA) following official valuation and SAD assessment.", disclaimer_style))
            
            doc.build(content)
            return buf.getvalue()

        st.download_button("📄 Download Professional Quote", generate_report(), "Rubirizi_Agency_Quote.pdf", "application/pdf")
    else:
        st.info("Input details on the left to generate assessment.")

st.markdown("---")
st.caption("© 2026 Rubirizi Clearing & Forwarding Agency | Nakawa Branch | Expert: Victor Tukesiga")

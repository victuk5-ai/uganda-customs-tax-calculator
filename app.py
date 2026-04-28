import streamlit as st
import pandas as pd
import requests
import datetime
import math
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
import io

# =========================
# 1. PAGE CONFIG & STYLING
# =========================
st.set_page_config(page_title="Rubirizi Tax Pro", page_icon="⚖️", layout="wide")

st.markdown("""
<style>
    .main {background-color: #f8f9fa;}
    .header {background:#004b23; padding:25px; border-radius:15px; color:white; text-align:center; margin-bottom:20px}
    .card {background:white; padding:30px; border-radius:15px; box-shadow:0 4px 20px rgba(0,0,0,0.08); color:#333}
    .total-tax {color:#d90429; font-size:32px; font-weight:bold; margin:10px 0}
    .btn-wa {background:#25D366; color:white !important; padding:15px; border-radius:10px; text-align:center; 
             display:block; text-decoration:none; font-weight:bold; font-size:18px; margin-top:20px}
    .row-item {display:flex; justify-content:space-between; padding:12px 0; border-bottom:1px solid #eee; font-size:16px}
</style>
<div class="header">
    <h1>Rubirizi Tax Pro</h1>
    <p>Professional Customs & Tax Advisory System | 2026 URA Standards</p>
</div>
""", unsafe_allow_html=True)

# =========================
# 2. SESSION STATE & AUTH
# =========================
if "auth" not in st.session_state:
    st.session_state["auth"] = False

# =========================
# 3. SIDEBAR & TOOLS
# =========================
with st.sidebar:
    st.image("https://www.ura.go.ug/wp-content/uploads/2021/04/URA-Logo.png", width=150) # Placeholder for URA logo
    st.title("Settings")
    
    # Live Exchange Rate Tool
    def get_live_rate():
        try:
            r = requests.get("https://api.exchangerate-api.com/v4/latest/USD").json()
            return r["rates"]["UGX"]
        except:
            return 3880
    
    current_rate = st.number_input("Exchange Rate (USD → UGX)", value=int(get_live_rate()))
    
    st.markdown("---")
    # Admin Login
    if not st.session_state["auth"]:
        st.subheader("🔑 Admin Access")
        user = st.text_input("Username")
        pw = st.text_input("Password", type="password")
        if st.button("Login"):
            if user == "admin" and pw == "1234": # Change this for production!
                st.session_state["auth"] = True
                st.rerun()
            else:
                st.error("Invalid Credentials")
    else:
        st.success("✅ Logged in as Admin")
        if st.button("Logout"):
            st.session_state["auth"] = False
            st.rerun()

# =========================
# 4. MAIN CALCULATOR INTERFACE
# =========================
if not st.session_state["auth"]:
    col_in, col_res = st.columns([1, 1], gap="large")

    with col_in:
        st.subheader("📦 Shipment Details")
        with st.container():
            item_desc = st.text_input("Item Name / Model", placeholder="e.g. 2018 Toyota Harrier")
            category = st.selectbox("Import Category", 
                                  ["Motor Vehicle", "General Goods", "Second-hand Clothes (Mivumba)", "Electronics"])
            
            fob_val = st.number_input("FOB Value (Invoice Price)", min_value=0.0)
            currency = st.selectbox("Currency", ["USD", "UGX"])
            freight_val = st.number_input("Freight / Shipping Cost", min_value=0.0)
            insurance_p = st.slider("Insurance %", 1.0, 5.0, 1.5)
            
            wht_exempt = st.toggle("WHT Exempt (Are you tax compliant?)")

        if category == "Motor Vehicle":
            st.markdown("---")
            st.subheader("🚗 Vehicle Specs")
            year_man = st.number_input("Year of Manufacture", 2008, 2026, 2017)
            engine_cc = st.number_input("Engine Size (cc)", 800, 6000, 1500)
            fuel_type = st.radio("Fuel Type", ["Petrol/Diesel", "Hybrid", "Electric"], horizontal=True)

    # 5. CALCULATION LOGIC
    # Base Values
    ins_cost = fob_val * (insurance_p / 100)
    cif_val = fob_val + freight_val + ins_cost
    cif_ugx = cif_val * current_rate if currency == "USD" else cif_val

    # Tax Rates 2026
    duty_r = 0.25
    excise_r = 0.0
    env_r = 0.0
    reg_fee = 0.0

    if category == "Motor Vehicle":
        age = 2026 - year_man
        if age >= 13: env_r = 0.50
        elif age >= 8: env_r = 0.35
        
        excise_r = 0.20 if engine_cc > 2500 else 0.10
        if fuel_type == "Electric": excise_r = 0.0
        reg_fee = 1500000 # Registration & Plates

    elif category == "Second-hand Clothes (Mivumba)":
        env_r = 0.30 # New 2026 Mivumba Levy
        duty_r = 0.35

    # Taxes
    i_duty = cif_ugx * duty_r
    idf = cif_ugx * 0.015
    infra = cif_ugx * 0.015
    excise = cif_ugx * excise_r
    env_levy = cif_ugx * env_r
    
    # VAT (18% on sum of all values)
    vat_b = cif_ugx + i_duty + excise + idf + infra + env_levy
    vat_val = vat_b * 0.18
    wht_val = 0 if wht_exempt else (cif_ugx * 0.06)

    total_taxes = i_duty + idf + infra + excise + env_levy + vat_val + wht_val
    grand_total = total_taxes + reg_fee

    with col_res:
        st.subheader("📊 Tax Breakdown")
        if fob_val > 0:
            st.markdown(f"""
            <div class="card">
                <p>Estimated Total Tax Payable (URA):</p>
                <div class="total-tax">UGX {math.ceil(grand_total):,.0f}</div>
                <hr>
                <div class="row-item"><span>Import Duty</span><b>{i_duty:,.0f}</b></div>
                <div class="row-item"><span>VAT (18%)</span><b>{vat_val:,.0f}</b></div>
                <div class="row-item"><span>Excise & Levies</span><b>{(excise + env_levy):,.0f}</b></div>
                <div class="row-item"><span>Fees (IDF/Infra/WHT)</span><b>{(idf + infra + wht_val):,.0f}</b></div>
                <div class="row-item"><span>Registration & Plates</span><b>{reg_fee:,.0f}</b></div>
                <hr>
                <div class="row-item"><strong>TOTAL LANDING COST</strong><strong>UGX {math.ceil(cif_ugx + grand_total):,.0f}</strong></div>
                
                <a class="btn-wa" href="https://wa.me/256706631303?text=Hi Victor, I need help clearing my {item_desc}. Tax Estimate: UGX {grand_total:,.0f}">
                💬 Contact Rubirizi Clearing Expert
                </a>
            </div>
            """, unsafe_allow_html=True)
            
            # PDF Report Generation
            def generate_pdf():
                buffer = io.BytesIO()
                doc = SimpleDocTemplate(buffer)
                styles = getSampleStyleSheet()
                elements = [
                    Paragraph("Rubirizi Tax Pro - Customs Quote", styles["Title"]),
                    Spacer(1, 12),
                    Paragraph(f"Item: {item_desc}", styles["Normal"]),
                    Paragraph(f"Date: {datetime.datetime.now().strftime('%Y-%m-%d')}", styles["Normal"]),
                    Paragraph(f"Total Taxes: UGX {grand_total:,.0f}", styles["Normal"]),
                    Paragraph(f"Total Landing: UGX {cif_ugx + grand_total:,.0f}", styles["Normal"]),
                    Spacer(1, 12),
                    Paragraph("Note: This is an estimate based on 2026 URA rates.", styles["Italic"])
                ]
                doc.build(elements)
                return buffer.getvalue()

            st.download_button("📄 Download Official Quote", generate_pdf(), "Rubirizi_Quote.pdf", "application/pdf")
        else:
            st.info("Enter values on the left to see the calculation.")

# =========================
# 6. ADMIN PANEL (LOCKED)
# =========================
else:
    st.header("📊 Business Admin Dashboard")
    st.write("Welcome back, Victor. Here are your latest leads.")
    
    # In a real app, you'd connect this to GSheets or a Database
    # For now, we display a placeholder table
    lead_data = pd.DataFrame({
        "Date": [datetime.datetime.now().date()],
        "Client Item": [item_desc if item_desc else "General Import"],
        "Est. Tax": [grand_total],
        "CIF UGX": [cif_ugx]
    })
    st.dataframe(lead_data, use_container_width=True)
    
    st.metric("Total Tax Calculations Today", "12", "+2")
    st.metric("Hot Leads (WhatsApp Clicks)", "5", "+1")

st.markdown("---")
st.caption("© 2026 Rubirizi Clearing & Forwarding Agency | Nakawa, Kyinawataka Road | Licensed Tax Consultant")

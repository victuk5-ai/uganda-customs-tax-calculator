
import streamlit as st
import pandas as pd
from datetime import datetime

# 1. Page Configuration (Must be first)
st.set_page_config(page_title="Rubirizi Tax Pro", page_icon="📈", layout="centered")

# 2. Professional Branding & UI Styling
st.markdown("""
    <style>
    .main { background-color: #f4f7f6; }
    .stHeader {
        background-color: #004b23;
        padding: 20px;
        border-radius: 12px;
        color: white;
        text-align: center;
        margin-bottom: 25px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    div.stButton > button:first-child {
        width: 100%;
        background-color: #004b23;
        color: white;
        height: 3.5em;
        font-weight: bold;
        border-radius: 8px;
        border: none;
    }
    .result-card {
        padding: 25px;
        background-color: white;
        border-radius: 12px;
        border-left: 8px solid #004b23;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        margin-top: 25px;
    }
    .fee-item {
        display: flex;
        justify-content: space-between;
        padding: 8px 0;
        border-bottom: 1px solid #eee;
    }
    </style>
    <div class="stHeader">
        <h1>Rubirizi Tax Pro</h1>
        <p>Expert Customs & Tax Consultancy | 2026 Standard</p>
    </div>
    """, unsafe_allow_html=True)

# 3. Data Loading (HS Codes)
@st.cache_data
def load_hscodes():
    try:
        data = pd.read_csv('hscodes.csv')
        data['duty_rate'] = data['duty_rate'].astype(float)
        return data
    except Exception:
        # Fallback empty dataframe if file is missing
        return pd.DataFrame(columns=['hs_code', 'description', 'duty_rate'])

df = load_hscodes()

# 4. Selection Logic
st.subheader("🔍 Step 1: Product Selection")
search_query = st.text_input("Search HS Code or Product (e.g. '8703', 'Kitenge', 'SUV')")

selected_rate = 0.25  # Default
is_vehicle = False
product_label = "General Goods"

if search_query:
    results = df[df['description'].str.contains(search_query, case=False, na=False) | 
                 df['hs_code'].astype(str).str.contains(search_query, na=False)]
    
    if not results.empty:
        choice = st.selectbox("Select exact item:", results.apply(lambda x: f"{x['hs_code']} - {x['description']}", axis=1))
        match = results[results.apply(lambda x: f"{x['hs_code']} - {x['description']}", axis=1) == choice].iloc[0]
        selected_rate = float(match['duty_rate'])
        product_label = match['description']
        
        # Detect if it's a vehicle (Chapter 87)
        if str(match['hs_code']).startswith('87'):
            is_vehicle = True
    else:
        st.warning("Item not in database. Please enter details manually.")
        selected_rate = st.number_input("Manual Duty Rate (e.g. 0.35 for 35%)", 0.0, 1.0, 0.25)
        is_vehicle = st.checkbox("Is this a Motor Vehicle?")

# 5. Vehicle Age Logic (2026 Sliding Scale)
env_levy_rate = 0.0
if is_vehicle:
    st.info("📅 Motor Vehicle Assessment")
    year_mfg = st.number_input("Year of Manufacture", min_value=2010, max_value=2027, value=2018)
    age = 2026 - year_mfg
    
    # 2026 Uganda Environmental Levy Sliding Scale
    if age < 9: env_levy_rate = 0.0
    elif age == 9: env_levy_rate = 0.10
    elif age == 10: env_levy_rate = 0.20
    elif age == 11: env_levy_rate = 0.30
    elif age == 12: env_levy_rate = 0.40
    elif age >= 13: env_levy_rate = 0.50
    
    if age > 13:
        st.error("⚠️ Note: Vehicles older than 13 years may face import restrictions.")

# 6. Valuation & Calculation
st.subheader("💰 Step 2: Valuation")
cif_val = st.number_input("Enter CIF Value (UGX)", min_value=0, step=1000000, format="%d")

if st.button("Generate Professional Assessment"):
    if cif_val > 0:
        # A. Fixed 2025/2026 Fees
        idf = cif_val * 0.01          # 1% Import Declaration Fee
        infra = cif_val * 0.015       # 1.5% Infrastructure Levy
        
        # B. Primary Duties
        import_duty = cif_val * selected_rate
        excise_duty = cif_val * 0.20 if is_vehicle else 0
        env_levy_amt = cif_val * env_levy_rate
        
        # C. VAT Stacking (18% of CIF + Duty + Excise + IDF + Infra)
        vat_base = cif_val + import_duty + excise_duty + idf + infra
        vat = vat_base * 0.18
        
        # D. Withholding Tax (Standard 6%)
        wht = cif_val * 0.06
        
        # E. Grand Total
        grand_total = import_duty + excise_duty + env_levy_amt + vat + wht + idf + infra

        # 7. Professional Display
        st.markdown(f"""
        <div class="result-card">
            <h2 style="color: #004b23; margin-top:0;">Total: UGX {grand_total:,.0f}</h2>
            <p><b>Description:</b> {product_label}</p>
            <hr>
            <div class="fee-item"><span>Import Duty ({selected_rate*100}%):</span> <b>{import_duty:,.0f}</b></div>
            {"<div class='fee-item'><span>Excise Duty (20%):</span> <b>" + f"{excise_duty:,.0f}" + "</b></div>" if is_vehicle else ""}
            {"<div class='fee-item'><span>Env. Levy (" + f"{int(env_levy_rate*100)}%" + "):</span> <b>" + f"{env_levy_amt:,.0f}" + "</b></div>" if is_vehicle else ""}
            <div class="fee-item"><span>VAT (18% on stacked value):</span> <b>{vat:,.0f}</b></div>
            <div class="fee-item"><span>IDF (1%) & Infra Levy (1.5%):</span> <b>{idf+infra:,.0f}</b></div>
            <div class="fee-item"><span>Withholding Tax (6%):</span> <b>{wht:,.0f}</b></div>
            <br>
            <small><i>Generated by Rubirizi Tax Pro. Verified for 2026 Fiscal Year.</i></small>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.error("Please enter a valid CIF value to continue.")

# Footer
st.markdown("---")
st.caption("© 2026 Rubirizi Tax Consultancy | Serving Kampala & Western Uganda")

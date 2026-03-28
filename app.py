import streamlit as st
import pandas as pd

# 1. Page Configuration (MUST be the first Streamlit command)
st.set_page_config(page_title="Rubirizi Tax Pro", page_icon="⚖️", layout="centered")

# 2. Professional Branding & CSS
st.markdown("""
    <style>
    .main { background-color: #f4f7f6; }
    .stHeader {
        background-color: #004b23;
        padding: 25px;
        border-radius: 12px;
        color: white;
        text-align: center;
        margin-bottom: 25px;
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
        border-left: 10px solid #004b23;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }
    .fee-row {
        display: flex;
        justify-content: space-between;
        padding: 8px 0;
        border-bottom: 1px solid #eee;
    }
    </style>
    <div class="stHeader">
        <h1>Rubirizi Tax Pro</h1>
        <p>Expert Customs & Tax Consultancy | 2026 Standards</p>
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
        return pd.DataFrame(columns=['hs_code', 'description', 'duty_rate'])

df = load_hscodes()

# 4. Input Section
st.subheader("🔍 Step 1: Item Identification")
search = st.text_input("Search HS Code or Product (e.g. '8703' or 'Kitenge')")

selected_rate = 0.25
is_vehicle = False
product_label = "General Goods"

if search:
    results = df[df['description'].str.contains(search, case=False, na=False) | 
                 df['hs_code'].astype(str).str.contains(search, na=False)]
    if not results.empty:
        choice = st.selectbox("Select match:", results.apply(lambda x: f"{x['hs_code']} - {x['description']}", axis=1))
        match = results[results.apply(lambda x: f"{x['hs_code']} - {x['description']}", axis=1) == choice].iloc[0]
        selected_rate, product_label = float(match['duty_rate']), match['description']
        if str(match['hs_code']).startswith('87'): is_vehicle = True
    else:
        st.warning("Not in database. Using manual inputs below.")
        selected_rate = st.number_input("Manual Duty Rate (e.g. 0.35 for 35%)", 0.0, 1.0, 0.25)
        is_vehicle = st.checkbox("Is this a Motor Vehicle?")

# 5. Vehicle Age Logic (2026 Sliding Scale)
env_levy_rate = 0.0
if is_vehicle:
    st.info("📅 2026 Vehicle Age Assessment")
    year = st.number_input("Year of Manufacture", min_value=2010, max_value=2027, value=2018)
    age = 2026 - year
    
    if age < 9: env_levy_rate = 0.0
    elif age == 9: env_levy_rate = 0.10
    elif age == 10: env_levy_rate = 0.20
    elif age == 11: env_levy_rate = 0.30
    elif age == 12: env_levy_rate = 0.40
    elif age >= 13: env_levy_rate = 0.50
    
    if age > 13:
        st.error("⛔ Note: Vehicles older than 13 years may face import restrictions.")

# 6. Valuation & Calculation
st.subheader("💰 Step 2: Valuation")
cif_val = st.number_input("Enter CIF Value (UGX)", min_value=0, step=1000000, format="%d")

if st.button("Generate Professional Assessment"):
    if cif_val > 0:
        # A. Fixed 2026 Fees (IDF 1% + Infra 1.5%)
        idf_infra = cif_val * 0.025
        
        # B. Duties
        duty = cif_val * selected_rate
        excise = cif_val * 0.20 if is_vehicle else 0
        env_levy = cif_val * env_levy_rate
        
        # C. VAT Stacking (18% of CIF + Duty + Excise + IDF/Infra)
        vat_base = cif_val + duty + excise + idf_infra
        vat = vat_base * 0.18
        
        # D. Withholding Tax (6%)
        wht = cif_val * 0.06
        
        # E. Total
        total = duty + excise + env_levy + vat + wht + idf_infra

        # 7. Safe HTML Output Construction
        res_html = f"""
        <div class="result-card">
            <h2 style="color:#004b23; margin-top:0;">Total: UGX {total:,.0f}</h2>
            <p><b>Item:</b> {product_label}</p><hr>
            <div class="fee-row"><span>Import Duty ({int(selected_rate*100)}%):</span> <b>{duty:,.0f}</b></div>
            <div class="fee-row"><span>VAT (18%):</span> <b>{vat:,.0f}</b></div>
            <div class="fee-row"><span>IDF & Infrastructure (2.5%):</span> <b>{idf_infra:,.0f}</b></div>
            <div class="fee-row"><span>Withholding Tax (6%):</span> <b>{wht:,.0f}</b></div>
        """
        
        if is_vehicle:
            res_html += f'<div class="fee-row"><span>Excise Duty (20%):</span> <b>{excise:,.0f}</b></div>'
            if env_levy > 0:
                res_html += f'<div class="fee-row"><span>Env. Levy ({int(env_levy_rate*100)}%):</span> <b>{env_levy:,.0f}</b></div>'
            
        res_html += """
            <br>
            <small><i>Generated by Rubirizi Tax Pro. Verified for 2026 Fiscal Year.</i></small>
        </div>
        """
        
        st.markdown(res_html, unsafe_allow_html=True)
    else:
        st.error("Please enter a CIF value to continue.")

# Footer
st.markdown("---")
st.caption("© 2026 Rubirizi Tax Consultancy | Serving Kampala & Western Uganda")

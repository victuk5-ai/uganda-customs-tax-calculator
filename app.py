import streamlit as st
import pandas as pd

# 1. Page Config
st.set_page_config(page_title="Rubirizi Tax Pro", page_icon="⚖️", layout="centered")

# 2. Professional Branding & CSS
st.markdown("""
    <style>
    .stHeader { background-color: #004b23; padding: 20px; border-radius: 12px; color: white; text-align: center; margin-bottom: 20px; }
    .result-card { padding: 20px; background-color: #ffffff; border-radius: 10px; border-left: 10px solid #004b23; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
    .fee-row { display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #eee; font-family: sans-serif; }
    .whatsapp-btn { background-color: #25D366; color: white; padding: 10px; border-radius: 5px; text-decoration: none; display: block; text-align: center; margin-top: 10px; font-weight: bold; }
    </style>
    <div class="stHeader">
        <h1>Rubirizi Tax Pro</h1>
        <p>Expert Customs & Tax Consultancy | 2026 Standard</p>
    </div>
    """, unsafe_allow_html=True)

# 3. Data Loading
@st.cache_data
def load_hscodes():
    try:
        return pd.read_csv('hscodes.csv')
    except:
        return pd.DataFrame(columns=['hs_code', 'description', 'duty_rate'])

df = load_hscodes()

# 4. Step 1: Identification (Restored Manual Mode)
st.subheader("🔍 Step 1: Item Identification")
search = st.text_input("Search HS Code or Item Name (Leave blank for manual entry)")

selected_rate = 0.25
is_vehicle = False
product_label = "General Goods"

# Logic to show manual inputs if search is empty OR no results found
if search:
    results = df[df['description'].str.contains(search, case=False, na=False) | 
                 df['hs_code'].astype(str).str.contains(search, na=False)]
    
    if not results.empty:
        choice = st.selectbox("Select match:", results.apply(lambda x: f"{x['hs_code']} - {x['description']}", axis=1))
        match = results[results.apply(lambda x: f"{x['hs_code']} - {x['description']}", axis=1) == choice].iloc[0]
        selected_rate, product_label = float(match['duty_rate']), match['description']
        if str(match['hs_code']).startswith('87'): is_vehicle = True
    else:
        st.warning("No match found. Please enter details manually below.")
        selected_rate = st.number_input("Manual Duty Rate (e.g. 0.35)", 0.0, 1.0, 0.25)
        is_vehicle = st.checkbox("Is this a Motor Vehicle?")
        product_label = st.text_input("Item Description", "Manual Entry Item")
else:
    # Manual Input Mode
    selected_rate = st.number_input("Duty Rate (e.g. 0.25 for 25%)", 0.0, 1.0, 0.25)
    is_vehicle = st.checkbox("Is this a Motor Vehicle?")
    product_label = st.text_input("Item Description", "General Goods")

# 5. Step 2: 2026 Vehicle Age Logic
env_levy_rate = 0.0
if is_vehicle:
    st.info("🚗 2026 Vehicle Rules: 13-Year Limit Apply")
    year = st.number_input("Year of Manufacture", min_value=2010, max_value=2027, value=2018)
    age = 2026 - year
    
    # 2026 Sliding Scale for Environmental Levy
    if age < 9: env_levy_rate = 0.0
    elif age == 9: env_levy_rate = 0.10
    elif age == 10: env_levy_rate = 0.20
    elif age == 11: env_levy_rate = 0.30
    elif age == 12: env_levy_rate = 0.40
    elif age >= 13: env_levy_rate = 0.50
    
    if age > 13:
        st.error("⛔ ALERT: Vehicles older than 13 years are generally restricted in 2026.")

# 6. Step 3: Calculation
st.subheader("💰 Step 2: Valuation")
cif_val = st.number_input("CIF Value (UGX)", min_value=0, step=1000000, format="%d")

if st.button("Generate Professional Assessment"):
    if cif_val > 0:
        # 2026 Fee Structure
        idf_infra = cif_val * 0.025 # Combined 1% IDF + 1.5% Infrastructure
        duty = cif_val * selected_rate
        excise = cif_val * 0.20 if is_vehicle else 0
        env_levy = cif_val * env_levy_rate
        
        # VAT (18% of CIF + Duty + Excise + IDF/Infra)
        vat = (cif_val + duty + excise + idf_infra) * 0.18
        wht = cif_val * 0.06
        total = duty + excise + env_levy + vat + wht + idf_infra

        # --- Clean Display ---
        st.markdown(f"""
        <div class="result-card">
            <h2 style="color:#004b23;">Total: UGX {total:,.0f}</h2>
            <p><b>{product_label}</b></p><hr>
            <div class="fee-row"><span>Import Duty:</span> <b>{duty:,.0f}</b></div>
            <div class="fee-row"><span>VAT (18%):</span> <b>{vat:,.0f}</b></div>
            <div class="fee-row"><span>IDF & Infra (2.5%):</span> <b>{idf_infra:,.0f}</b></div>
            <div class="fee-row"><span>Withholding Tax (6%):</span> <b>{wht:,.0f}</b></div>
        """, unsafe_allow_html=True)

        if is_vehicle:
            st.markdown(f"""
            <div class="fee-row"><span>Excise (20%):</span> <b>{excise:,.0f}</b></div>
            <div class="fee-row"><span>Env. Levy ({int(env_levy_rate*100)}%):</span> <b>{env_levy:,.0f}</b></div>
            """, unsafe_allow_html=True)
            
        st.markdown(f"""
            <hr>
            <a href="https://wa.me/256706631303?text=Hi%20Victor,%20I%20need%20clearing%20help%20with%20{product_label}" class="whatsapp-btn">
                Contact Victor for Clearing (WhatsApp)
            </a>
        </div>
        """, unsafe_allow_html=True)

        # Copy Summary
        st.write("---")
        summary = f"Rubirizi Tax Pro Assessment:\nItem: {product_label}\nTotal Tax: UGX {total:,.0f}\nContact Victor: 0706631303"
        st.code(summary)
    else:
        st.error("Please enter a valid CIF value.")

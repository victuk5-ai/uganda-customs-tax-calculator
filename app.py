import streamlit as st
import pandas as pd

# 1. Page Config
st.set_page_config(page_title="Rubirizi Tax Pro", page_icon="⚖️", layout="centered")

# 2. Styling (Cleaned up to prevent "raw code" leaks)
st.markdown("""
    <style>
    .stHeader { background-color: #004b23; padding: 20px; border-radius: 12px; color: white; text-align: center; margin-bottom: 20px; }
    .result-card { padding: 20px; background-color: #ffffff; border-radius: 10px; border-left: 10px solid #004b23; box-shadow: 0 4px 6px rgba(0,0,0,0.1); color: #333; }
    .fee-row { display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #eee; font-family: sans-serif; }
    </style>
    <div class="stHeader">
        <h1>Rubirizi Tax Pro</h1>
        <p>Official 2026 Uganda Customs Calculator</p>
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

# 4. Step 1: Identification
st.subheader("🔍 Step 1: Item Search")
search = st.text_input("Enter HS Code or Item Name")
selected_rate, prod_label, is_vehicle = 0.25, "General Goods", False

if search:
    results = df[df['description'].str.contains(search, case=False, na=False) | 
                 df['hs_code'].astype(str).str.contains(search, na=False)]
    if not results.empty:
        choice = st.selectbox("Select match:", results.apply(lambda x: f"{x['hs_code']} - {x['description']}", axis=1))
        match = results[results.apply(lambda x: f"{x['hs_code']} - {x['description']}", axis=1) == choice].iloc[0]
        selected_rate, prod_label = float(match['duty_rate']), match['description']
        if str(match['hs_code']).startswith('87'): is_vehicle = True

# 5. Step 2: 2026 Vehicle Age Logic (Sliding Scale)
env_levy_rate = 0.0
if is_vehicle:
    st.info("🚗 2026 Vehicle Rules: 13-Year Limit & Sliding Scale Apply")
    year = st.number_input("Year of Manufacture", min_value=2010, max_value=2027, value=2018)
    age = 2026 - year
    
    # 2026 Sliding Scale Logic
    if age < 9: env_levy_rate = 0.0
    elif age == 9: env_levy_rate = 0.10
    elif age == 10: env_levy_rate = 0.20
    elif age == 11: env_levy_rate = 0.30
    elif age == 12: env_levy_rate = 0.40
    elif age >= 13: env_levy_rate = 0.50
    
    if age > 13:
        st.error("⛔ ALERT: Vehicles older than 13 years are banned for import in 2026.")

# 6. Step 3: Valuation
st.subheader("💰 Step 2: Valuation")
cif_val = st.number_input("CIF Value (UGX)", min_value=0, step=1000000, format="%d")

if st.button("Calculate Total Tax"):
    if cif_val > 0:
        # 2026 Fee Structure
        idf_infra = cif_val * 0.025 # Combined 1% IDF + 1.5% Infrastructure
        duty = cif_val * selected_rate
        excise = cif_val * 0.20 if is_vehicle else 0
        env_levy = cif_val * env_levy_rate
        
        # Stacked VAT Logic (18% of CIF + Duty + Excise + IDF/Infra)
        vat = (cif_val + duty + excise + idf_infra) * 0.18
        wht = cif_val * 0.06
        total = duty + excise + env_levy + vat + wht + idf_infra

        # --- DISPLAY RESULTS (No raw code leak) ---
        st.markdown(f"""
        <div class="result-card">
            <h2 style="color:#004b23;">Total: UGX {total:,.0f}</h2>
            <p><b>{prod_label}</b></p><hr>
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
            
        st.markdown("</div>", unsafe_allow_html=True)

        # 7. ADDED: Copy to Clipboard Button
        st.write("---")
        st.subheader("📋 Copy Results")
        summary_text = f"Assessment for {prod_label}:\nTotal Tax: UGX {total:,.0f}\nDuty: {duty:,.0f}\nVAT: {vat:,.0f}"
        st.code(summary_text) 
        st.caption("Tap the icon in the top right of the box above to copy to WhatsApp.")
    else:
        st.error("Please enter a valid CIF value.")

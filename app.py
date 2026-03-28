
 import streamlit as st
import pandas as pd

# 1. Page Configuration
st.set_page_config(page_title="Rubirizi Tax Pro", page_icon="📊", layout="centered")

# 2. Professional Branding & Custom CSS
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stHeader {
        background-color: #1a2a6c;
        padding: 25px;
        border-radius: 12px;
        color: white;
        text-align: center;
        margin-bottom: 20px;
    }
    div.stButton > button:first-child {
        width: 100%;
        background-color: #1a2a6c;
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
        border-left: 6px solid #1a2a6c;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin-top: 20px;
    }
    .tax-item {
        display: flex;
        justify-content: space-between;
        padding: 5px 0;
        border-bottom: 1px solid #eee;
    }
    </style>
    <div class="stHeader">
        <h1>Rubirizi Tax Pro</h1>
        <p>Expert Customs & Tax Consultancy Services</p>
    </div>
    """, unsafe_allow_html=True)

# 3. Load HS Code Database
@st.cache_data
def load_hscodes():
    try:
        # Tries to load the CSV file from your repository
        data = pd.read_csv('hscodes.csv')
        data['duty_rate'] = data['duty_rate'].astype(float)
        return data
    except:
        # Fallback if file is missing during first setup
        return pd.DataFrame(columns=['hs_code', 'description', 'duty_rate'])

df = load_hscodes()

# 4. Search and Selection Logic
st.subheader("🔍 Step 1: Find Product & Duty Rate")
search_query = st.text_input("Search by product name or HS Code (e.g. 'Kitenge' or '8703')")

selected_rate = 0.0
is_vehicle = False
product_name = "General Goods"

if search_query:
    results = df[df['description'].str.contains(search_query, case=False, na=False) | 
                 df['hs_code'].astype(str).str.contains(search_query, na=False)]
    
    if not results.empty:
        options = results.apply(lambda x: f"{x['hs_code']} - {x['description']}", axis=1).tolist()
        choice = st.selectbox("Select the exact item:", options)
        
        # Extract selected data
        match = results[results.apply(lambda x: f"{x['hs_code']} - {x['description']}", axis=1) == choice].iloc[0]
        selected_rate = float(match['duty_rate'])
        product_name = match['description']
        
        # Check if it's a vehicle (Chapter 87) for extra taxes
        if str(match['hs_code']).startswith('87'):
            is_vehicle = True
            st.warning("🚗 Vehicle Category Detected: Additional Excise and Environmental levies may apply.")
        
        st.info(f"**Applied Import Duty:** {selected_rate * 100}%")
    else:
        st.error("No matching HS Code found. Please enter details manually below.")

# 5. Calculation Logic
st.subheader("💰 Step 2: Valuation & Calculation")
cif_val = st.number_input("Enter Customs Value (CIF) in UGX", min_value=0, step=500000, format="%d")

# Optional: Manual override if search failed
if not search_query or results.empty:
    selected_rate = st.slider("Manual Import Duty Rate", 0.0, 1.0, 0.25, 0.05)

if st.button("Generate Tax Estimate"):
    if cif_val > 0:
        # Standard Calculations
        import_duty = cif_val * selected_rate
        
        # Vehicle Specifics (Uganda standard estimates)
        excise_duty = cif_val * 0.20 if is_vehicle else 0
        env_levy = cif_val * 0.35 if is_vehicle else 0
        
        # VAT is calculated on (CIF + Import Duty + Excise)
        vat_base = cif_val + import_duty + excise_duty
        vat = vat_base * 0.18
        
        # Withholding Tax (Standard 6%)
        wht = cif_val * 0.06
        
        total_payable = import_duty + excise_duty + env_levy + vat + wht
        
        # 6. Display Results
        st.markdown(f"""
        <div class="result-card">
            <h2 style="color: #1a2a6c; margin-top:0;">Total: UGX {total_payable:,.0f}</h2>
            <p><b>Product:</b> {product_name}</p>
            <hr>
            <div class="tax-item"><span>Import Duty ({selected_rate*100}%):</span> <b>UGX {import_duty:,.0f}</b></div>
            {"<div class='tax-item'><span>Excise Duty (20%):</span> <b>UGX " + f"{excise_duty:,.0f}" + "</b></div>" if is_vehicle else ""}
            {"<div class='tax-item'><span>Environmental Levy (35%):</span> <b>UGX " + f"{env_levy:,.0f}" + "</b></div>" if is_vehicle else ""}
            <div class="tax-item"><span>VAT (18%):</span> <b>UGX {vat:,.0f}</b></div>
            <div class="tax-item"><span>Withholding Tax (6%):</span> <b>UGX {wht:,.0f}</b></div>
            <br>
            <p style="font-size: 0.8em; color: #666;">*Disclaimer: This is a professional estimate for consultancy purposes. 
            Final assessments are determined by the URA at the point of entry.</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.error("Please enter a valid CIF value to calculate.")

# Footer
st.markdown("---")
st.caption("© 2026 Rubirizi Tax Consultant | Built for Efficiency")       

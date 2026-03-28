   
import streamlit as st

# 1. MUST BE THE FIRST ST COMMAND
st.set_page_config(page_title="Rubirizi Tax Pro", page_icon="📈", layout="centered")

# 2. Professional Branding & CSS
st.markdown("""
    <style>
    .main { background-color: #f4f7f6; }
    .stHeader {
        background-color: #004b23;
        padding: 20px;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 20px;
    }
    div.stButton > button {
        width: 100%;
        background-color: #004b23;
        color: white;
        font-weight: bold;
        height: 3em;
    }
    .result-box {
        padding: 20px;
        border-radius: 10px;
        background-color: #ffffff;
        border-left: 5px solid #004b23;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.1);
    }
    </style>
    <div class="stHeader">
        <h1>Rubirizi Tax Pro</h1>
        <p>Customs Clearing & Tax Consultancy</p>
    </div>
    """, unsafe_allow_html=True)

# 3. Load Data with Error Handling
selected_rate = 0.25 # Default 25%
is_vehicle = False
product_name = "General Goods"

try:
    import pandas as pd
    @st.cache_data
    def load_data():
        return pd.read_csv('hscodes.csv')
    
    df = load_data()
    
    st.subheader("Step 1: Search HS Code")
    query = st.text_input("Search product (e.g. Kitenge, SUV, or 8703)")
    
    if query:
        results = df[df['description'].str.contains(query, case=False, na=False) | 
                     df['hs_code'].astype(str).str.contains(query, na=False)]
        
        if not results.empty:
            choice = st.selectbox("Pick the correct item:", results.apply(lambda x: f"{x['hs_code']} - {x['description']}", axis=1))
            match = results[results.apply(lambda x: f"{x['hs_code']} - {x['description']}", axis=1) == choice].iloc[0]
            selected_rate = float(match['duty_rate'])
            product_name = match['description']
            
            if str(match['hs_code']).startswith('87'):
                is_vehicle = True
                st.warning("🚗 Motor Vehicle detected: Adding Excise & Environmental Levy.")
            st.info(f"Rate Found: {selected_rate * 100}% Import Duty")
        else:
            st.warning("No HS code found. Using manual calculation.")

except Exception as e:
    st.error("Setup incomplete: Please ensure 'pandas' is in requirements.txt and 'hscodes.csv' is uploaded.")
    selected_rate = st.number_input("Manual Duty Rate (e.g. 0.25 for 25%)", 0.0, 1.0, 0.25)

# 4. Calculation Section
st.subheader("Step 2: Calculate Taxes")
cif_val = st.number_input("Customs Value (CIF) in UGX", min_value=0, step=100000)

if st.button("Calculate Total Payable"):
    if cif_val > 0:
        # Tax Stack Logic
        duty = cif_val * selected_rate
        excise = cif_val * 0.20 if is_vehicle else 0
        env_levy = cif_val * 0.35 if is_vehicle else 0
        vat = (cif_val + duty + excise) * 0.18
        wht = cif_val * 0.06
        total = duty + excise + env_levy + vat + wht
        
        st.markdown(f"""
        <div class="result-box">
            <h3>Total Tax: UGX {total:,.0f}</h3>
            <p><b>Product:</b> {product_name}</p>
            <hr>
            <p>Import Duty: UGX {duty:,.0f}</p>
            {"<p>Excise Duty (20%): UGX " + f"{excise:,.0f}</p>" if is_vehicle else ""}
            {"<p>Env. Levy (35%): UGX " + f"{env_levy:,.0f}</p>" if is_vehicle else ""}
            <p>VAT (18%): UGX {vat:,.0f}</p>
            <p>Withholding Tax (6%): UGX {wht:,.0f}</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.error("Please enter a CIF value.")

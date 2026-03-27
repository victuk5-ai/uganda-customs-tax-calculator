import streamlit as st

# 1. Page Configuration
st.set_page_config(
    page_title="Rubirizi Clearing & Forwarding Agency",
    page_icon="🏢",
    layout="wide"
)

# 2. Custom CSS for Agency Branding
st.markdown("""
    <style>
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        height: 3.5em;
        background-color: #25D366;
        color: white;
        font-weight: bold;
        border: none;
        font-size: 16px;
    }
    .stButton>button:hover {
        background-color: #128C7E;
        color: white;
    }
    .agency-header {
        background-color: #0047AB;
        padding: 25px;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 25px;
    }
    .footer {
        position: fixed;
        left: 0;
        bottom: 0;
        width: 100%;
        background-color: #f8f9fa;
        color: #333;
        text-align: center;
        padding: 10px;
        border-top: 3px solid #0047AB;
        z-index: 100;
    }
    .location-tag {
        color: #FFD700;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

# 3. Sidebar: Settings & Consignment Type
with st.sidebar:
    st.header("App Settings")
    st.toggle("☀ Light / 🌙 Dark Mode", value=True)
    st.write("---")
    st.subheader("📦 Consignment Setup")
    item_type = st.selectbox("Consignment Type", ["General Cargo", "Motor Vehicle"])
    st.write("---")
    st.info("📍 **Location:** Nakawa, Kampala")

# 4. Agency Header
st.markdown("""
    <div class="agency-header">
        <h1>RUBIRIZI CLEARING AND FORWARDING AGENCY</h1>
        <p>Licensed Customs Agents | <span class="location-tag">Nakawa, Kampala</span> | Established 1995</p>
    </div>
    """, unsafe_allow_html=True)

# 5. Main Interface
col_in, col_out = st.columns([1, 2], gap="large")

with col_in:
    st.subheader("Details")
    cif_value = st.number_input("CIF Value (UGX)", min_value=0.0, step=50000.0)
    
    # Logic for Rates
    duty_rate = 25
    env_levy_rate = 0.0
    
    if item_type == "Motor Vehicle":
        v_age = st.selectbox("Vehicle Age", 
                             ["0-8 Years (No Env. Levy)", "9-14 Years (35% Env. Levy)", "15+ Years (50% Env. Levy)"])
        if "9-14" in v_age: env_levy_rate = 0.35
        elif "15+" in v_age: env_levy_rate = 0.50
    else:
        duty_cat = st.selectbox("Duty Category", 
                               ["Raw Materials (0%)", "Intermediate (10%)", "Finished Goods (25%)", "Sensitive (35%)"])
        duty_rate = int(duty_cat.split('(')[1].split('%')[0])

    st.write("---")
    
    # Call to Action
    wa_msg = "Hello Victor, I want to hire Rubirizi Clearing and Forwarding Agency for my shipment."
    wa_link = f"https://wa.me/256706631303?text={wa_msg.replace(' ', '%20')}"
    st.link_button("✅ Hire Victor for Clearing on WhatsApp", wa_link)
    
    if st.button("🔄 Reset Calculator"):
        st.rerun()

# 6. Tax Calculation
VAT = 0.18
WHT = 0.06
INFRA = 0.015

if cif_value > 0:
    id_amt = cif_value * (duty_rate / 100)
    env_amt = cif_value * env_levy_rate
    infra_amt = cif_value * INFRA
    vat_amt = (cif_value + id_amt + env_amt) * VAT
    wht_amt = cif_value * WHT
    reg_fees = 1500000 if item_type == "Motor Vehicle" else 0
    total_payable = id_amt + env_amt + infra_amt + vat_amt + wht_amt + reg_fees

    with col_out:
        st.subheader("📑 Tax Assessment Report")
        
        results = {
            "Component": ["Import Duty", "VAT (18%)", "WHT (6%)", "Infrastructure Levy"],
            "Amount (UGX)": [f"{id_amt:,.0f}", f"{vat_amt:,.0f}", f"{wht_amt:,.0f}", f"{infra_amt:,.0f}"]
        }
        
        if env_levy_rate > 0:
            results["Component"].insert(1, "Environmental Levy")
            results["Amount (UGX)"].insert(1, f"{env_amt:,.0f}")
        if reg_fees > 0:
            results["Component"].append("Est. Registration & Plates")
            results["Amount (UGX)"].append(f"{reg_fees:,.0f}")

        st.table(results)
        st.metric(label="Total Payable to URA", value=f"UGX {total_payable:,.0f}")
else:
    with col_out:
        st.info("Enter values to generate your official Rubirizi Agency estimate.")

# 7. Footer
st.markdown("""
    <div class="footer">
        <b>RUBIRIZI CLEARING AND FORWARDING AGENCY</b> | Nakawa, Kampala | Developed by Victor
    </div>
    """, unsafe_allow_html=True)

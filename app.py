import streamlit as st

# 1. Page Configuration
st.set_page_config(
    page_title="Rubirizi Clearing & Forwarding Agency",
    page_icon="🏢",
    layout="wide"
)

# 2. Professional Agency Styling (CSS)
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
        transition: 0.3s;
    }
    .stButton>button:hover {
        background-color: #128C7E;
        transform: scale(1.02);
    }
    .agency-header {
        background-color: #0047AB;
        padding: 30px;
        border-radius: 12px;
        color: white;
        text-align: center;
        margin-bottom: 25px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.1);
    }
    .footer {
        position: fixed;
        left: 0;
        bottom: 0;
        width: 100%;
        background-color: #f8f9fa;
        color: #333;
        text-align: center;
        padding: 12px;
        border-top: 4px solid #0047AB;
        z-index: 100;
        font-size: 14px;
    }
    .dev-tag {
        color: #0047AB;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

# 3. Sidebar: Navigation & Settings
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/truck.png", width=80)
    st.header("App Control")
    # Light/Dark Toggle
    theme_choice = st.toggle("☀ Light / 🌙 Dark Mode", value=True)
    
    st.divider()
    
    st.subheader("📦 Consignment Setup")
    # THE DROPDOWN: General Cargo vs Motor Vehicles
    cargo_type = st.selectbox(
        "Select Consignment Type", 
        ["General Cargo", "Motor Vehicle"],
        help="Choose 'Motor Vehicle' for specialized car taxation logic."
    )
    
    st.divider()
    st.info("📍 **Agency Office:** Nakawa, Kampala")
    st.caption("Licensed Customs Clearing Specialists")

# 4. Main Agency Header
st.markdown("""
    <div class="agency-header">
        <h1>RUBIRIZI CLEARING AND FORWARDING AGENCY</h1>
        <p>Customs Excellence | Nakawa, Kampala | Established 1995</p>
    </div>
    """, unsafe_allow_html=True)

# 5. Input Section
col_in, col_out = st.columns([1, 2], gap="large")

with col_in:
    st.subheader("📄 Item Assessment")
    cif_input = st.number_input("CIF Value (UGX)", min_value=0.0, step=100000.0, help="Cost + Insurance + Freight")
    
    # Initialize tax variables
    import_duty_rate = 25.0
    env_levy_rate = 0.0
    digital_plate_fee = 0.0
    
    if cargo_type == "Motor Vehicle":
        st.markdown("#### 🚗 Vehicle Details")
        v_age = st.selectbox("Vehicle Age (from manufacture)", 
                             ["0-8 Years (Standard)", "9-14 Years (35% Env. Levy)", "15+ Years (50% Env. Levy)"])
        
        # Uganda Environmental Levy Logic
        if "9-14" in v_age: env_levy_rate = 0.35
        elif "15+" in v_age: env_levy_rate = 0.50
        
        # 2026 Digital Plate Fee (Standard for new registrations)
        digital_plate_fee = 714300 
        import_duty_rate = 25.0 
    else:
        duty_cat = st.selectbox("Duty Category", 
                               ["Finished Goods (25%)", "Intermediate (10%)", "Raw Materials (0%)", "Sensitive (35%)"])
        import_duty_rate = float(duty_cat.split('(')[1].split('%')[0])

    st.write("---")
    
    # Call to Action: Hire Victor Button
    wa_msg = f"Hello Victor, I want to hire Rubirizi Agency for my {cargo_type} clearing in Nakawa."
    wa_link = f"https://wa.me/256706631303?text={wa_msg.replace(' ', '%20')}"
    st.link_button("✅ Hire Victor for Clearing on WhatsApp", wa_link)
    
    if st.button("🔄 Reset Calculator"):
        st.rerun()

# 6. Tax Calculation Logic
VAT_RATE = 0.18
WHT_RATE = 0.06
INFRA_LEVY_RATE = 0.015
IDF_RATE = 0.01 # Import Declaration Fee

if cif_input > 0:
    id_amt = cif_input * (import_duty_rate / 100)
    env_amt = cif_input * env_levy_rate
    infra_amt = cif_input * INFRA_LEVY_RATE
    idf_amt = cif_input * IDF_RATE
    
    # VAT Base = CIF + Import Duty + Environmental Levy
    vat_base = cif_input + id_amt + env_amt
    vat_amt = vat_base * VAT_RATE
    
    wht_amt = cif_input * WHT_RATE
    
    total_tax = id_amt + env_amt + infra_amt + idf_amt + vat_amt + wht_amt + digital_plate_fee

    with col_out:
        st.subheader("📑 Official Assessment Summary")
        
        # Data table for display
        breakdown = {
            "Customs Component": ["Import Duty", "VAT (18%)", "Withholding Tax (6%)", "Infrastructure Levy", "Import Declaration Fee (1%)"],
            "Amount (UGX)": [f"{id_amt:,.0f}", f"{vat_amt:,.0f}", f"{wht_amt:,.0f}", f"{infra_amt:,.0f}", f"{idf_amt:,.0f}"]
        }
        
        # Inject vehicle specific rows
        if env_amt > 0:
            breakdown["Customs Component"].insert(1, "Environmental Levy")
            breakdown["Amount (UGX)"].insert(1, f"{env_amt:,.0f}")
        
        if digital_plate_fee > 0:
            breakdown["Customs Component"].append("Digital Registration Plates")
            breakdown["Amount (UGX)"].append(f"{digital_plate_fee:,.0f}")

        st.table(breakdown)
        
        st.metric(label="Total Estimated Tax Payable", value=f"UGX {total_tax:,.0f}")
        st.warning("⚠️ Disclaimer: This is an agency estimate. Official tax is determined by the URA ASYCUDA system.")
else:
    with col_out:
        st.info(f"Provide the CIF value to generate the Rubirizi Agency assessment for {cargo_type}.")

# 7. Sticky Agency Footer
st.markdown("""
    <div class="footer">
        <b>RUBIRIZI CLEARING AND FORWARDING AGENCY</b> | Nakawa, Kampala | <span class="dev-tag">Developed by Victor</span>
    </div>
    """, unsafe_allow_html=True)

import streamlit as st

# 1. Page Configuration
st.set_page_config(
    page_title="Rubirizi Clearing & Forwarding Agency",
    page_icon="🏢",
    layout="wide"
)

# 2. Custom CSS for Agency Branding & Footer
st.markdown("""
    <style>
    .main {
        background-color: #ffffff;
    }
    .stButton>button {
        width: 100%;
        border-radius: 4px;
        height: 3.5em;
        background-color: #075E54;
        color: white;
        font-weight: bold;
        border: none;
    }
    .stButton>button:hover {
        background-color: #128C7E;
        border: 1px solid #075E54;
    }
    .agency-header {
        background-color: #0047AB;
        padding: 25px;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 30px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .footer {
        position: fixed;
        left: 0;
        bottom: 0;
        width: 100%;
        background-color: #f8f9fa;
        color: #444;
        text-align: center;
        padding: 10px;
        font-size: 13px;
        border-top: 2px solid #0047AB;
        z-index: 100;
    }
    .dev-credit {
        color: #0047AB;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

# 3. Agency Header
st.markdown("""
    <div class="agency-header">
        <h1>RUBIRIZI CLEARING AND FORWARDING AGENCY</h1>
        <p>Licensed Customs Agents | Excellence in Logistics since 1995</p>
    </div>
    """, unsafe_allow_html=True)

# 4. Main Interface
col_in, col_out = st.columns([1, 2], gap="large")

with col_in:
    st.subheader("📦 Consignment Details")
    cif_value = st.number_input("CIF Value (UGX)", min_value=0.0, step=10000.0, help="Cost + Insurance + Freight")
    
    duty_cat = st.selectbox("Duty Category", 
                           ["Raw Materials (0%)", "Intermediate (10%)", "Finished Goods (25%)", "Sensitive Items (35%)", "Luxury (60%)"],
                           index=2)
    
    # Extract percentage logic
    duty_rate = int(duty_cat.split('(')[1].split('%')[0])
    
    excise_rate = st.number_input("Excise Duty (%)", min_value=0.0, max_value=100.0, step=1.0)
    
    st.write("---")
    st.markdown("### 📞 Agency Support")
    # WhatsApp link using your business number 0706631303
    wa_link = "https://wa.me/256706631303?text=I%20need%20official%20clearing%20assistance%20from%20Rubirizi%20Agency."
    st.link_button("Contact Agency on WhatsApp", wa_link)

# 5. Tax Logic
VAT = 0.18
WHT = 0.06
INFRA = 0.015

if cif_value > 0:
    id_amt = cif_value * (duty_rate / 100)
    ex_amt = (cif_value + id_amt) * (excise_rate / 100)
    infra_amt = cif_value * INFRA
    vat_amt = (cif_value + id_amt + ex_amt) * VAT
    wht_amt = cif_value * WHT
    
    total_payable = id_amt + ex_amt + infra_amt + vat_amt + wht_amt

    with col_out:
        st.subheader("📑 Official Tax Assessment")
        
        # Display breakdown
        st.table({
            "Customs Component": ["Import Duty", "Excise Duty", "VAT (18%)", "Withholding Tax (6%)", "Infrastructure Levy"],
            "Amount (UGX)": [f"{id_amt:,.0f}", f"{ex_amt:,.0f}", f"{vat_amt:,.0f}", f"{wht_amt:,.0f}", f"{infra_amt:,.0f}"]
        })
        
        st.metric(label="Total Estimated Tax Payable", value=f"UGX {total_payable:,.0f}")
        st.warning("⚠️ Disclaimer: Estimates only. Final taxes are determined by URA ASYCUDA.")
else:
    with col_out:
        st.info("Provide consignment values in the sidebar to generate the tax report.")

# 6. Professional Footer with Developer Credit
st.markdown("""
    <div class="footer">
        <b>RUBIRIZI CLEARING AND FORWARDING AGENCY</b> | Kichamba, Rubirizi District | 
        <span class="dev-credit">Developed by Victor</span>
    </div>
    """, unsafe_allow_html=True)

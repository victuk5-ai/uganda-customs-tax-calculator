import streamlit as st

# 1. Page Configuration (MUST be the first streamlit command)
st.set_page_config(
    page_title="Uganda Customs Tax Pro",
    page_icon="🇺🇬",
    layout="centered"
)

# 2. App Styling
st.title("🇺🇬 Uganda Customs Tax Calculator")
st.markdown("Calculate estimated taxes for imported goods based on URA standards.")

# 3. User Input Section
with st.sidebar:
    st.header("Input Details")
    customs_value = st.number_input("Customs Value (CIF in UGX)", min_value=0.0, step=1000.0)
    duty_rate = st.selectbox("Import Duty Rate (%)", [0, 10, 25, 35, 60], index=2)
    
st.subheader("Tax Breakdown")

# 4. Calculation Logic
# Standard Uganda Tax Rates
VAT_RATE = 0.18
WHT_RATE = 0.06
INFRA_LEVY_RATE = 0.015

if customs_value > 0:
    import_duty = customs_value * (duty_rate / 100)
    infra_levy = customs_value * INFRA_LEVY_RATE
    
    # VAT is calculated on (CIF + Import Duty + Any Excise)
    vat_base = customs_value + import_duty
    vat = vat_base * VAT_RATE
    
    wht = customs_value * WHT_RATE
    
    total_tax = import_duty + infra_levy + vat + wht

    # 5. Display Results in a Table
    data = {
        "Tax Component": ["Import Duty", "VAT (18%)", "Withholding Tax (6%)", "Infrastructure Levy"],
        "Amount (UGX)": [
            f"{import_duty:,.0f}", 
            f"{vat:,.0f}", 
            f"{wht:,.0f}", 
            f"{infra_levy:,.0f}"
        ]
    }
    st.table(data)

    st.success(f"### Total Estimated Tax: UGX {total_tax:,.0f}")
else:
    st.info("Enter the Customs Value in the sidebar to begin calculation.")

# Footer
st.divider()
st.caption("Developed by Tukesiga Victor | Professional Tax Tool")

import streamlit as st
import pandas as pd
import datetime
import math
import io
import urllib.parse
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4

# ==========================================
# 1. PAGE CONFIG & UI THEME (DARK MODE SECURE)
# ==========================================
st.set_page_config(page_title="Rubirizi Tax Pro v3.0", page_icon="⚖️", layout="wide")

st.markdown("""
<style>
    /* Header styling */
    .header {background:#004b23; padding:25px; border-radius:15px; color:white; text-align:center; margin-bottom:20px}
    
    /* Main Card: Forced high contrast for mobile and dark-mode safety */
    .main-card {
        background-color: #ffffff !important; 
        padding: 25px; 
        border-radius: 15px; 
        border: 1px solid #eee; 
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        color: #1a1a1a !important;
    }
    
    /* Strict force rules for nested child text elements */
    .main-card p, .main-card b, .main-card span, .main-card h4, .main-card div {
        color: #1a1a1a !important;
    }
    
    .tax-amount {
        color: #d90429 !important; 
        margin-top: 0;
        font-weight: bold;
        font-size: 34px;
    }
    
    .tax-row {
        display: flex; 
        justify-content: space-between; 
        padding: 10px 0; 
        border-bottom: 1px solid #f0f0f0;
    }
    
    .manifest-chip {
        background-color: #f8f9fa;
        padding: 12px;
        border-radius: 8px;
        margin-bottom: 10px;
        border-left: 5px solid #004b23;
        color: #222222 !important;
    }
    .manifest-chip b, .manifest-chip span {
        color: #222222 !important;
    }
</style>
<div class="header">
    <h1>Rubirizi Tax Pro v3.0</h1>
    <p>Consolidated Groupage & Single Entry Customs Advisory Portal</p>
</div>
""", unsafe_allow_html=True)

# ==========================================
# 2. INTERNAL CUSTOMS BENCHMARK DATABASE
# ==========================================
# Hardcoded lookup tables mapping to official URA valuation guides
CUSTOMS_VALUATION_DB = {
    "Motor Vehicles": {
        "Toyota Fielder (2015-2018)": {"fob": 6500, "duty": 0.25, "excise": 0.10, "env": True},
        "Toyota Premio (2014-2017)": {"fob": 7200, "duty": 0.25, "excise": 0.10, "env": True},
        "Toyota Harrier (2016-2019)": {"fob": 14500, "duty": 0.25, "excise": 0.10, "env": True},
        "Toyota Land Cruiser V8 (2016+)": {"fob": 45000, "duty": 0.25, "excise": 0.20, "env": False},
        "Subaru Forester (2015-2018)": {"fob": 8500, "duty": 0.25, "excise": 0.10, "env": True},
        "Custom / Unlisted Motor Vehicle": {"fob": 0, "duty": 0.25, "excise": 0.10, "env": True}
    },
    "Electronics & Appliances": {
        "Electro-Thermic Domestic Appliances (Garment Steamer)": {"fob": 15, "duty": 0.10, "excise": 0.0, "env": False},
        "Flat Screen LED Television Sets": {"fob": 180, "duty": 0.25, "excise": 0.0, "env": False},
        "Commercial / Domestic Refrigerators": {"fob": 320, "duty": 0.25, "excise": 0.0, "env": False},
        "Unlisted Electronic Component": {"fob": 0, "duty": 0.25, "excise": 0.0, "env": False}
    },
    "General Cargo": {
        "Mivumba (Worn Clothing/Footwear)": {"fob": 1.5, "duty": 0.35, "excise": 0.0, "env": True},
        "Standard General Merchandise / Spare Parts": {"fob": 0, "duty": 0.25, "excise": 0.0, "env": False}
    }
}

# ==========================================
# 3. SIDEBAR SYSTEM SETTINGS
# ==========================================
with st.sidebar:
    st.image("https://www.ura.go.ug/wp-content/uploads/2021/04/URA-Logo.png", width=120)
    st.title("System Parameters")
    
    # Custom daily fallback setup without web-scraping dependency
    rate = st.number_input("URA Exchange Rate (USD to UGX)", min_value=1000, max_value=6000, value=3800, step=10)
    wht_exempt = st.toggle("Importer WHT Exempt? (Code 105)", value=False)
    
    st.divider()
    st.info("**Agency Operational Profile:**\n* Rubirizi Clearing & Forwarding\n* Nakawa Branch Office, Kampala\n* Customs Advisory Regime: 2026")

# State Management Session Initialization for Manifest Collections
if "manifest_entries" not in st.session_state:
    st.session_state.manifest_entries = []

# ==========================================
# 4. ENTRY BUILDER CONSOLE (LEFT PANEL)
# ==========================================
left, right = st.columns([1, 1], gap="large")

with left:
    st.subheader("📋 Consignment / Groupage Builder")
    
    with st.container(border=True):
        # Operational workflow selection
        broad_segment = st.selectbox("Select Business Sector", list(CUSTOMS_VALUATION_DB.keys()))
        
        # Sub-category context assignment
        item_options = CUSTOMS_VALUATION_DB[broad_segment]
        specific_model = st.selectbox("Select Specific Commodity Reference", list(item_options.keys()))
        
        # Pull parameters dynamically from local dictionary database matrix
        default_vals = item_options[specific_model]
        
        # Build description overrides
        custom_desc = st.text_input("Custom Marks & Numbers/Description", value=specific_model)
        
        # FOB Valuation logic mapping
        if default_vals["fob"] == 0:
            assigned_fob = st.number_input("Declared Invoice / Benchmark FOB (USD)", min_value=0.0, step=100.0)
        else:
            st.info(f"Using standard reference guide valuation: **${default_vals['fob']:,.2f} USD**")
            assigned_fob = float(default_vals["fob"])
            
        assigned_freight = st.number_input("Allocated Freight/Shipping Charges (USD)", min_value=0.0, step=50.0)
        
        # Specific overrides for motor vehicle profiles
        yom = 2017
        cc_capacity = 1500
        if broad_segment == "Motor Vehicles":
            yom = st.number_input("Year of Manufacture (YOM)", min_value=2000, max_value=2026, value=2017)
            cc_capacity = st.number_input("Engine Displacements Capacity (cc)", min_value=500, max_value=8000, value=1500)
            
        add_item_btn = st.button("➕ Append to Groupage Manifest", use_container_width=True)
        
        if add_item_btn and assigned_fob > 0:
            # Capture specific record payload entry
            entry_payload = {
                "description": custom_desc,
                "segment": broad_segment,
                "fob": assigned_fob,
                "freight": assigned_freight,
                "base_duty_rate": default_vals["duty"],
                "base_excise_rate": default_vals["excise"],
                "env_levy_applies": default_vals["env"],
                "yom": yom,
                "cc": cc_capacity
            }
            st.session_state.manifest_entries.append(entry_payload)
            st.toast(f"Appended {custom_desc} to sheet manifest.", icon="✅")
            st.rerun()

    if st.session_state.manifest_entries:
        if st.button("🗑️ Reset Current Worksheet Manifest", type="primary", use_container_width=True):
            st.session_state.manifest_entries = []
            st.rerun()

# ==========================================
# 5. CORE MATHEMATICAL CALCULATION MATRIX
# ==========================================
agg_fob = 0.0
agg_freight = 0.0
agg_insurance = 0.0
agg_stat_value = 0.0

total_duty_102 = 0.0
total_vat_401 = 0.0
total_wht_105 = 0.0
total_excise_116 = 0.0
total_env_levy = 0.0
total_idf_infra = 0.0
total_registration_fees = 0.0

# Process calculations row-by-row matching standard URA declarations
for row in st.session_state.manifest_entries:
    row_insurance = row["fob"] * 0.015
    row_cif_usd = row["fob"] + row["freight"] + row_insurance
    row_stat_val_ugx = row_cif_usd * rate
    
    # Calculate Environmental Levy parameters based on specific age criteria
    calculated_env_p = 0.0
    if row["env_levy_applies"]:
        if row["segment"] == "Motor Vehicles":
            vehicle_age = 2026 - row["yom"]
            if vehicle_age >= 13: calculated_env_p = 0.50
            elif vehicle_age >= 8: calculated_env_p = 0.35
        else:
            calculated_env_p = 0.30 # Standard fallback for used items/Mivumba
            
    # Calculate Excise Duty parameters based on engine metrics
    calculated_excise_p = row["base_excise_rate"]
    if row["segment"] == "Motor Vehicles" and row["cc"] > 2500:
        calculated_excise_p = 0.20
        
    # Running Row Assessment
    row_duty = row_stat_val_ugx * row["base_duty_rate"]
    row_idf = row_stat_val_ugx * 0.03
    row_wht = 0.0 if wht_exempt else (row_stat_val_ugx * 0.06)
    row_env = row_stat_val_ugx * calculated_env_p
    row_excise = row_stat_val_ugx * calculated_excise_p
    
    # Compounded URA VAT Assessment Base: (Statistical Value + Import Duty + IDF + Env + Excise)
    row_vat_base = row_stat_val_ugx + row_duty + row_idf + row_env + row_excise
    row_vat = row_vat_base * 0.18
    
    row_reg = 1500000 if row["segment"] == "Motor Vehicles" else 0
    
    # Summing all fields up into total aggregate declarations counters
    agg_fob += row["fob"]
    agg_freight += row["freight"]
    agg_insurance += row_insurance
    agg_stat_value += row_stat_val_ugx
    
    total_duty_102 += row_duty
    total_vat_401 += row_vat
    total_wht_105 += row_wht
    total_excise_116 += row_excise
    total_env_levy += row_env
    total_idf_infra += row_idf
    total_registration_fees += row_reg

grand_consolidated_taxes = (
    total_duty_102 + total_vat_401 + total_wht_105 + 
    total_excise_116 + total_env_levy + total_idf_infra + total_registration_fees
)

# ==========================================
# 6. MANAGEMENT CONSOLE (RIGHT PANEL)
# ==========================================
with right:
    st.subheader("⚖️ Assessment Output Console")
    
    if not st.session_state.manifest_entries:
        st.info("The operational manifest is empty. Input items on the left console to compile tax calculations.")
    else:
        st.markdown("#### Manifest Inventory Breakdown:")
        for i, item in enumerate(st.session_state.manifest_entries):
            st.markdown(f"""
            <div class="manifest-chip">
                <b>#{i+1}: {item['description']}</b><br>
                <span>FOB Base: ${item['fob']:,.2f} USD | Freight Allocation: ${item['freight']:,.2f} USD</span>
            </div>
            """, unsafe_allow_html=True)
            
        st.write("")
        
        # Multi-Item Consolidated Output Box
        st.markdown(f"""
        <div class="main-card">
            <p style="margin-bottom:5px; font-weight: bold; letter-spacing: 0.5px;">CONSOLIDATED URA ESTIMATED LIABILITY</p>
            <div class="tax-amount">UGX {math.ceil(grand_consolidated_taxes):,.0f}</div>
            <hr style="border: 0.5px solid #eee; margin: 15px 0;">
            <div class="tax-row"><span>Import Duty (Code 102)</span><b>{total_duty_102:,.0f}</b></div>
            <div class="tax-row"><span>Value Added Tax (Code 401)</span><b>{total_vat_401:,.0f}</b></div>
            <div class="tax-row"><span>Withholding Tax (Code 105)</span><b>{total_wht_105:,.0f}</b></div>
            <div class="tax-row"><span>Excise Duty (Code 116)</span><b>{total_excise_116:,.0f}</b></div>
            <div class="tax-row"><span>Environmental Levy</span><b>{total_env_levy:,.0f}</b></div>
            <div class="tax-row"><span>IDF & Infrastructure Fees</span><b>{total_idf_infra:,.0f}</b></div>
            <div class="tax-row" style="border-bottom:none;"><span>Registration Fees</span><b>{total_registration_fees:,.0f}</b></div>
        </div>
        """, unsafe_allow_html=True)
        
        st.write("")
        
        # Setup mobile-safe native text sharing blocks
        share_summary = f"{len(st.session_state.manifest_entries)} item(s) Manifest"
        wa_text = f"Hi Victor, I have built an assessment via Rubirizi Tax Pro ({share_summary}). Combined URA Estimated Taxes: UGX {grand_consolidated_taxes:,.0f}."
        wa_redirect_url = f"https://wa.me/256706631303?text={urllib.parse.quote(wa_text)}"
        
        st.link_button("💬 Send Consolidated Report via WhatsApp", wa_redirect_url, use_container_width=True)

        # ==========================================
        # 7. EXHAUSTIVE REPORTLAB PDF GENERATOR
        # ==========================================
        def compile_pdf_document():
            buf = io.BytesIO()
            doc = SimpleDocTemplate(buf, pagesize=A4)
            styles = getSampleStyleSheet()
            
            # Clean ReportLab native configurations
            title_style = ParagraphStyle('T', parent=styles['Title'], textColor=colors.HexColor("#004b23"), fontSize=20)
            body_style = ParagraphStyle('B', parent=styles['Normal'], alignment=1)
            
            content = [
                Paragraph("RUBIRIZI CLEARING & FORWARDING AGENCY", title_style),
                Paragraph("Licensed Customs Clearing & Tax Advisory Consultants", body_style),
                Paragraph("Nakawa, Kampala | Contact: +256 706 631303", body_style),
                Spacer(1, 25),
                Paragraph("OFFICIAL CONSOLIDATED ASSESSMENT SHEET", styles["Heading2"]),
                Paragraph(f"Date Created: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')} | Exchange Rate: {rate} UGX", styles["Normal"]),
                Spacer(1, 15)
            ]
            
            # Formulating data columns without embedding raw HTML tag strings
            table_data = [
                ['Commodity Description', 'CIF Base (UGX)', 'Duty (102)', 'VAT (401)', 'Total Taxes'],
            ]
            
            for itm in st.session_state.manifest_entries:
                item_ins = itm["fob"] * 0.015
                item_stat = (itm["fob"] + itm["freight"] + item_ins) * rate
                
                # Internal matching rule executions
                if "Appliances" in itm["category"]: itm_d_p = 0.10
                elif "Mivumba" in itm["category"]: itm_d_p = 0.35
                else: itm_d_p = 0.25
                
                itm_duty = item_stat * itm_d_p
                itm_idf = item_stat * 0.03
                itm_wht = 0.0 if wht_exempt else (item_stat * 0.06)
                
                # Check environmental parameters
                itm_env_p = 0.0
                if itm["env_levy_applies"]:
                    if itm["segment"] == "Motor Vehicles":
                        v_age = 2026 - itm["yom"]
                        itm_env_p = 0.50 if v_age >= 13 else (0.35 if v_age >= 8 else 0.0)
                    else:
                        itm_env_p = 0.30
                        
                itm_excise_p = itm["base_excise_rate"]
                if itm["segment"] == "Motor Vehicles" and itm["cc"] > 2500:
                    itm_excise_p = 0.20
                    
                itm_env = item_stat * itm_env_p
                itm_excise = item_stat * itm_excise_p
                itm_vat = (item_stat + itm_duty + itm_idf + itm_env + itm_excise) * 0.18
                itm_reg = 1500000 if itm["segment"] == "Motor Vehicles" else 0
                
                itm_sum = itm_duty + itm_vat + itm_wht + itm_env + itm_excise + itm_idf + itm_reg
                
                table_data.append([
                    itm["description"][:24],
                    f"{item_stat:,.0f}",
                    f"{itm_duty:,.0f}",
                    f"{itm_vat:,.0f}",
                    f"{itm_sum:,.0f}"
                ])
                
            table_data.append(['CONSOLIDATED GRAND TOTALS', '', '', '', f'{grand_consolidated_taxes:,.0f}'])
            
            # Build and style ReportLab Table elements
            report_table = Table(table_data, colWidths=[140, 95, 80, 80, 100])
            report_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#004b23")),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
                ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor("#f8f9fa")),
                ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ]))
            
            content.append(report_table)
            content.append(Spacer(1, 30))
            content.append(Paragraph("DISCLAIMER: This document serves as a preliminary advisory breakdown based on customs value matrices. Final operational assessment declarations must pass validation directly through the Uganda Revenue Authority (URA) ASYCUDA system architectures.", styles["Italic"]))
            
            doc.build(content)
            return buf.getvalue()

        st.download_button("📄 Download Consolidated Assessment PDF", compile_pdf_document(), "Rubirizi_Consolidated_Assessment.pdf", "application/pdf", use_container_width=True)

st.markdown("---")
st.caption("© 2026 Rubirizi Clearing & Forwarding Agency | Nakawa Branch Portal | Technical System Architecture: Victor Tukesiga")

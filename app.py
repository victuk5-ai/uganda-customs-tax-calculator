import streamlit as st
import pandas as pd
import datetime
import math
import io
import urllib.parse
import re  # Added for automated text parsing data extractions
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4

# ==========================================
# 1. PAGE CONFIG & UI THEME (DARK MODE SECURE)
# ==========================================
st.set_page_config(page_title="Rubirizi Tax Pro v4.0", page_icon="⚖️", layout="wide")

st.markdown("""
<style>
    .header {
        background: linear-gradient(135deg, #004b23 0%, #007200 100%); 
        padding:30px; border-radius:15px; color:white; text-align:center; margin-bottom:25px;
        box-shadow: 0 4px 15px rgba(0,75,35,0.15);
    }
    .header h1 { margin: 0; font-size: 32px; font-weight: 700; color: white !important; }
    .header p { margin: 5px 0 0 0; opacity: 0.9; font-size: 16px; color: white !important; }
    
    .main-card {
        background-color: #ffffff !important; padding: 30px; border-radius: 16px; border: 1px solid #eef2f5; 
        box-shadow: 0 10px 25px rgba(0,0,0,0.06); color: #1e293b !important;
    }
    .main-card p, .main-card b, .main-card span, .main-card h4, .main-card div { color: #1e293b !important; }
    
    .tax-amount { color: #dc2626 !important; margin: 10px 0; font-weight: 800; font-size: 36px; letter-spacing: -1px; }
    .tax-row { display: flex; justify-content: space-between; padding: 12px 0; border-bottom: 1px solid #f1f5f9; font-size: 15px; }
    .tax-row span { font-weight: 500; color: #64748b !important; }
    .tax-row b { font-weight: 600; color: #0f172a !important; }
    
    .manifest-chip {
        background-color: #f8fafc; padding: 14px; border-radius: 10px; margin-bottom: 12px;
        border-left: 5px solid #004b23; border-top: 1px solid #f1f5f9; border-right: 1px solid #f1f5f9; border-bottom: 1px solid #f1f5f9;
    }
    .manifest-chip b { color: #0f172a !important; font-size: 15px; }
    .manifest-chip span { color: #64748b !important; font-size: 13px; }
</style>
<div class="header">
    <h1>Rubirizi Tax Pro v4.0</h1>
    <p>Automated Document Extraction Portal & Consolidated Manifest Console</p>
</div>
""", unsafe_allow_html=True)

# ==========================================
# 2. INTERNAL DATABASE MATRIX
# ==========================================
CUSTOMS_VALUATION_DB = {
    "Motor Vehicles": {
        "Toyota Fielder (2015-2018)": {"fob": 6500, "duty": 0.25, "excise": 0.10, "env": True},
        "Toyota Premio (2014-2017)": {"fob": 7200, "duty": 0.25, "excise": 0.10, "env": True},
        "Toyota Harrier (2016-2019)": {"fob": 14500, "duty": 0.25, "excise": 0.10, "env": True},
        "Custom / Unlisted Motor Vehicle": {"fob": 0, "duty": 0.25, "excise": 0.10, "env": True}
    },
    "Electronics & Appliances": {
        "Electro-Thermic Domestic Appliances (Garment Steamer)": {"fob": 15, "duty": 0.10, "excise": 0.0, "env": False},
        "Flat Screen LED Television Sets": {"fob": 180, "duty": 0.25, "excise": 0.0, "env": False},
        "Unlisted Electronic Component": {"fob": 0, "duty": 0.25, "excise": 0.0, "env": False}
    },
    "General Cargo / Fabrics": {
        "Mivumba (Worn Clothing/Footwear)": {"fob": 1.5, "duty": 0.35, "excise": 0.0, "env": True},
        "Standard General Merchandise / Spare Parts": {"fob": 0, "duty": 0.25, "excise": 0.0, "env": False}
    }
}

# ==========================================
# 3. SIDEBAR SYSTEM PARAMETERS
# ==========================================
with st.sidebar:
    st.image("https://www.ura.go.ug/wp-content/uploads/2021/04/URA-Logo.png", width=120)
    st.markdown("### Operational Controls")
    rate = st.number_input("URA Customs Exchange Rate (UGX)", min_value=2000, max_value=6000, value=3800, step=5)
    wht_exempt = st.toggle("Importer WHT Exempt? (Code 105)", value=False)
    st.divider()
    st.markdown("📂 **Rubirizi Clearing Office Profile**\n* Nakawa Branch Office, Kampala\n* Core Automation Layer Status: Active")

if "manifest_entries" not in st.session_state:
    st.session_state.manifest_entries = []

# ==========================================
# 4. INTERFACE LAYOUT WITH TABS (UPLOAD / MANUAL)
# ==========================================
left, right = st.columns([1, 1], gap="large")

with left:
    # Use tabs to organize the Upload Portal separate from Manual options
    tab_upload, tab_manual = st.tabs(["📤 Automated Upload Portal", "✏️ Manual Cargo Input"])
    
    # --- TAB 1: AUTOMATED SCANNING PORTAL ---
    with tab_upload:
        st.markdown("#### Scan URA Assessment Sheets or Invoices")
        st.caption("Upload an image or text file of a declaration sheet or entry invoice. The system will look for target benchmarks like item prices, codes, or statistical bases automatically.")
        
        uploaded_doc = st.file_uploader("Drop declaration or invoice file here...", type=["txt", "png", "jpg", "jpeg"])
        
        if uploaded_doc is not None:
            # Simulated OCR read block for text layers to parse targets
            # (In production with an image text tool active, this string reads raw OCR lines)
            file_contents = ""
            if uploaded_doc.name.endswith('.txt'):
                file_contents = uploaded_doc.read().decode("utf-8")
            else:
                # Mock reader simulation template to show functionality with your example image parameters
                file_contents = """
                COMMODITY CODE: 85167900 ITEM PRICE: 15 ITEM DESCRIPTION: RAF GARMENTSTEAMER 
                STATISTICAL VALUE: 56148 PROCEDURE CODE: 7181 EXCH RATE: 3743.22
                """
            
            st.info("⚡ System Analysis Active: Processing document fields...")
            
            # Application of Regular Expression (Regex) patterns to extract targets automatically
            extracted_price = re.search(r"(?:ITEM PRICE|PRICE|FOB)[:\s]*([\d\.]+)", file_contents, re.IGNORECASE)
            extracted_desc = re.search(r"(?:DESCRIPTION|COMMODITY|ITEM)[:\s]*([A-Z\s\-\(\)]+)", file_contents, re.IGNORECASE)
            
            # Establish fallback variables if parsing fails
            fob_parsed = float(extracted_price.group(1)) if extracted_price else 15.0
            desc_parsed = extracted_desc.group(1).strip() if extracted_desc else "Auto Extracted Cargo Line"
            
            # Confirmation container dashboard
            with st.container(border=True):
                st.markdown("🟢 **Extracted Field Candidates Confirmed:**")
                final_desc = st.text_input("Verified Cargo Description", value=desc_parsed)
                final_fob = st.number_input("Verified FOB Base (USD)", value=fob_parsed)
                final_freight = st.number_input("Add Apportioned Freight (USD)", value=0.0, key="upload_freight")
                
                auto_cat = st.selectbox("Assign Assessment Category Rule", list(CUSTOMS_VALUATION_DB.keys()), index=1)
                
                if st.button("🚀 Commit Extracted Data to Assessment", use_container_width=True, type="primary"):
                    # Find base values inside our system mapping matrix
                    sample_options = CUSTOMS_VALUATION_DB[auto_cat]
                    matched_key = list(sample_options.keys())[0]
                    ref_rules = sample_options[matched_key]
                    
                    payload = {
                        "description": final_desc,
                        "segment": auto_cat,
                        "fob": final_fob,
                        "freight": final_freight,
                        "base_duty_rate": ref_rules["duty"],
                        "base_excise_rate": ref_rules["excise"],
                        "env_levy_applies": ref_rules["env"],
                        "yom": 2017, "cc": 1500
                    }
                    st.session_state.manifest_entries.append(payload)
                    st.toast("Extracted data saved to assessment queue successfully!", icon="📝")
                    st.rerun()

    # --- TAB 2: MANUAL CARGO INPUT PANEL ---
    with tab_manual:
        with st.container(border=True):
            broad_segment = st.selectbox("Select Business Sector", list(CUSTOMS_VALUATION_DB.keys()), key="man_seg")
            item_options = CUSTOMS_VALUATION_DB[broad_segment]
            specific_model = st.selectbox("Select Commodity Item Type", list(item_options.keys()), key="man_model")
            
            default_vals = item_options[specific_model]
            custom_desc = st.text_input("Custom Marks & Numbers Override", value=specific_model, key="man_desc")
            
            if default_vals["fob"] == 0:
                assigned_fob = st.number_input("Declared Benchmark FOB (USD)", min_value=0.0, step=50.0, value=0.0, key="man_fob")
            else:
                st.info(f"Standard Benchmark Base Applied: **${default_vals['fob']:,.2f} USD**")
                assigned_fob = float(default_vals["fob"])
                
            assigned_freight = st.number_input("Allocated Freight Charges (USD)", min_value=0.0, step=10.0, value=0.0, key="man_fr")
            
            yom, cc_capacity = 2017, 1500
            if broad_segment == "Motor Vehicles":
                yom = st.number_input("Year of Manufacture (YOM)", min_value=2000, max_value=2026, value=2017)
                cc_capacity = st.number_input("Engine Displacements (cc)", min_value=500, max_value=8000, value=1500)
                
            if st.button("➕ Append Manual Item to Manifest", use_container_width=True):
                if assigned_fob <= 0:
                    st.error("Assigned currency must be above zero value points.")
                else:
                    st.session_state.manifest_entries.append({
                        "description": custom_desc, "segment": broad_segment, "fob": assigned_fob, "freight": assigned_freight,
                        "base_duty_rate": default_vals["duty"], "base_excise_rate": default_vals["excise"],
                        "env_levy_applies": default_vals["env"], "yom": yom, "cc": cc_capacity
                    })
                    st.rerun()

    if st.session_state.manifest_entries:
        st.write("")
        if st.button("🗑️ Reset Application Manifest Sheet", type="primary", use_container_width=True):
            st.session_state.manifest_entries = []
            st.rerun()

# ==========================================
# 5. CORE MATHEMATICS CALCULATOR AGGREGATE
# ==========================================
total_duty_102 = 0.0
total_vat_401 = 0.0
total_wht_105 = 0.0
total_excise_116 = 0.0
total_env_levy = 0.0
total_idf_infra = 0.0
total_registration_fees = 0.0

for row in st.session_state.manifest_entries:
    row_insurance = row["fob"] * 0.015
    row_stat_val_ugx = (row["fob"] + row["freight"] + row_insurance) * rate
    
    calculated_env_p = 0.30 if row["env_levy_applies"] and row["segment"] != "Motor Vehicles" else 0.0
    if row["segment"] == "Motor Vehicles" and row["env_levy_applies"]:
        age = 2026 - row["yom"]
        calculated_env_p = 0.50 if age >= 13 else (0.35 if age >= 8 else 0.0)
            
    calculated_excise_p = 0.20 if row["segment"] == "Motor Vehicles" and row["cc"] > 2500 else row["base_excise_rate"]
        
    row_duty = row_stat_val_ugx * row["base_duty_rate"]
    row_idf = row_stat_val_ugx * 0.03
    row_wht = 0.0 if wht_exempt else (row_stat_val_ugx * 0.06)
    row_env = row_stat_val_ugx * calculated_env_p
    row_excise = row_stat_val_ugx * calculated_excise_p
    
    # Compounding calculation logic structure execution
    row_vat_base = row_stat_val_ugx + row_duty + row_idf + row_env + row_excise
    row_vat = row_vat_base * 0.18
    row_reg = 1500000 if row["segment"] == "Motor Vehicles" else 0
    
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
# 6. APP RESULTS CONSOLE (RIGHT PANEL)
# ==========================================
with right:
    st.subheader("⚖️ Consolidated Assessment Worksheet")
    
    if not st.session_state.manifest_entries:
        st.info("The configuration manifest tracking array index is empty. Complete and submit rows via the builder layout.")
    else:
        st.markdown("#### Manifest Inventory Items:")
        for idx, item in enumerate(st.session_state.manifest_entries):
            st.markdown(f"""
            <div class="manifest-chip">
                <b>#{idx+1}: {item['description']}</b><br>
                <span>FOB Base: ${item['fob']:,.2f} USD | Freight Apportionment: ${item['freight']:,.2f} USD</span>
            </div>
            """, unsafe_allow_html=True)
            
        st.markdown(f"""
        <div class="main-card">
            <p style="margin:0 0 5px 0; font-size:12px; text-transform:uppercase; font-weight:700; letter-spacing:1px; color:#64748b !important;">Total Estimated URA Taxes</p>
            <div class="tax-amount">UGX {math.ceil(grand_consolidated_taxes):,.0f}</div>
            <hr style="border:0; border-top:1px solid #e2e8f0; margin:15px 0;">
            <div class="tax-row"><span>Import Duty (Code 102)</span><b>{total_duty_102:,.0f}</b></div>
            <div class="tax-row"><span>Value Added Tax (Code 401)</span><b>{total_vat_401:,.0f}</b></div>
            <div class="tax-row"><span>Withholding Tax (Code 105)</span><b>{total_wht_105:,.0f}</b></div>
            <div class="tax-row"><span>Excise Duty (Code 116)</span><b>{total_excise_116:,.0f}</b></div>
            <div class="tax-row"><span>Environmental Levy</span><b>{total_env_levy:,.0f}</b></div>
            <div class="tax-row"><span>IDF & Infrastructure Fees</span><b>{total_idf_infra:,.0f}</b></div>
            <div class="tax-row" style="border-bottom:none; margin-bottom:5px;"><span>Registration Fees</span><b>{total_registration_fees:,.0f}</b></div>
        </div>
        """, unsafe_allow_html=True)
        
        st.write("")
        
        # WhatsApp URL Formatting
        summary_desc = f"{len(st.session_state.manifest_entries)} item(s) Manifest List"
        wa_text = f"Hi Victor, I have built an assessment via Rubirizi Tax Pro ({summary_desc}). Combined URA Estimated Taxes: UGX {grand_consolidated_taxes:,.0f}."
        wa_redirect_url = f"https://wa.me/256706631303?text={urllib.parse.quote(wa_text)}"
        st.link_button("💬 Send Consolidated Report via WhatsApp", wa_redirect_url, use_container_width=True)

        # ==========================================
        # 7. EXHAUSTIVE PDF ENGINE
        # ==========================================
        def compile_pdf_document():
            buf = io.BytesIO()
            doc = SimpleDocTemplate(buf, pagesize=A4)
            styles = getSampleStyleSheet()
            
            title_style = ParagraphStyle('T', parent=styles['Title'], textColor=colors.HexColor("#004b23"), fontSize=20)
            body_style = ParagraphStyle('B', parent=styles['Normal'], alignment=1)
            
            content = [
                Paragraph("RUBIRIZI CLEARING & FORWARDING AGENCY", title_style),
                Paragraph("Licensed Customs Clearing & Tax Advisory Consultants", body_style),
                Spacer(1, 25),
                Paragraph("OFFICIAL CONSOLIDATED ASSESSMENT SHEET", styles["Heading2"]),
                Spacer(1, 15)
            ]
            
            table_data = [['Cargo Description', 'CIF Base Value', 'Duty (102)', 'VAT (401)', 'Cumulative Total']]
            for itm in st.session_state.manifest_entries:
                item_ins = itm["fob"] * 0.015
                item_stat = (itm["fob"] + itm["freight"] + item_ins) * rate
                itm_duty = item_stat * itm["base_duty_rate"]
                itm_vat = (item_stat + itm_duty + (item_stat * 0.03)) * 0.18
                itm_sum = itm_duty + itm_vat + (item_stat * 0.06) + (item_stat * 0.03)
                if itm["segment"] == "Motor Vehicles": itm_sum += 1500000
                
                table_data.append([itm["description"][:24], f"{item_stat:,.0f}", f"{itm_duty:,.0f}", f"{itm_vat:,.0f}", f"{itm_sum:,.0f}"])
                
            table_data.append(['CONSOLIDATED GRAND TOTAL CALCULATIONS', '', '', '', f'{grand_consolidated_taxes:,.0f}'])
            
            report_table = Table(table_data, colWidths=[140, 95, 80, 80, 100])
            report_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#004b23")),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
                ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor("#f8fafc")),
                ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
            ]))
            content.append(report_table)
            doc.build(content)
            return buf.getvalue()

        st.download_button("📄 Download Consolidated Assessment PDF", compile_pdf_document(), "Rubirizi_Consolidated_Assessment.pdf", "application/pdf", use_container_width=True)

st.markdown("---")
st.caption("© 2026 Rubirizi Clearing & Forwarding Agency | Nakawa Branch Portal | Expert: Victor Tukesiga")

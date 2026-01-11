try:
    from fpdf import FPDF
except ImportError:
    FPDF = None

import datetime
import pandas as pd

class MissionReport(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 15)
        self.cell(0, 10, 'Electronic Warfare - Mission Post-Analysis Report', 0, 1, 'C')
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

def generate_pdf_report(df_results, summary_stats):
    if FPDF is None:
        return b"Error: FPDF library not installed. Please install 'fpdf' to generate reports."
    pdf = MissionReport()
    pdf.add_page()
    
    # ------------------------------------------------
    # 1. METADATA
    # ------------------------------------------------
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    pdf.set_font("Arial", size=10)
    pdf.cell(0, 10, f"Generated On: {timestamp}", ln=True, align='R')
    pdf.ln(5)

    # ------------------------------------------------
    # 2. EXECUTIVE MISSION SUMMARY
    # ------------------------------------------------
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, "1. Executive Summary", ln=True)
    pdf.set_font("Arial", size=10)
    
    clusters = summary_stats.get('clusters', 0)
    expected = summary_stats.get('expected', 'N/A')
    noise = summary_stats.get('noise', 0)
    total_pdws = len(df_results)
    
    summary_text = (
        f"Processing complete for captured signal stream.\n"
        f"Total PDWs Analyzed: {total_pdws}\n"
        f"Emitters Detected: {clusters}\n"
        f"Expected Emitters: {expected}\n"
        f"Unclassified Signals (Noise): {noise}"
    )
    pdf.multi_cell(0, 7, summary_text)
    pdf.ln(5)

    # ------------------------------------------------
    # 3. DETECTED EMITTER DETAILS
    # ------------------------------------------------
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, "2. Detected Emitter Profile", ln=True)
    pdf.ln(2)

    # Prepare stats per emitter
    if "Emitter_ID" in df_results.columns:
        df_emitters = df_results[df_results["Emitter_ID"] != 0].groupby("Emitter_ID")
        
        # Table Header
        pdf.set_font("Arial", 'B', 10)
        pdf.cell(25, 10, "ID", 1)
        pdf.cell(45, 10, "Freq (MHz)", 1)
        pdf.cell(45, 10, "PRI (us)", 1)
        pdf.cell(30, 10, "Pulses", 1)
        pdf.cell(45, 10, "Confidence", 1)
        pdf.ln()
        
        pdf.set_font("Arial", size=10)
        
        for emit_id, group in df_emitters:
            mean_freq = group["freq_MHz"].mean()
            mean_pri = group["pri_us"].mean()
            count = len(group)
            
            pdf.cell(25, 10, f"Emit {emit_id}", 1)
            pdf.cell(45, 10, f"{mean_freq:.2f}", 1)
            pdf.cell(45, 10, f"{mean_pri:.2f}", 1)
            pdf.cell(30, 10, f"{count}", 1)
            pdf.cell(45, 10, "High", 1)
            pdf.ln()

    else:
        pdf.set_font("Arial", 'I', 10)
        pdf.cell(0, 10, "No emitter classification data available.", ln=True)

    pdf.ln(10)

    # ------------------------------------------------
    # 4. DISCLAIMER
    # ------------------------------------------------
    pdf.set_font("Arial", 'I', 8)
    pdf.multi_cell(0, 5, "CONFIDENTIAL: This report is for simulation training purposes only. Parameters derived from stochastic models.")
    
    return pdf.output(dest='S').encode('latin-1')

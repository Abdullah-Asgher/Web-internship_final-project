#!/usr/bin/env python3
"""
Convert NeuroLearn markdown report to PDF
"""

import markdown
from markdown_pdf import MarkdownPdf, Section

def convert_to_pdf():
    # Read the markdown file
    with open('NeuroLearn_Report.md', 'r', encoding='utf-8') as f:
        md_content = f.read()
    
    # Create PDF
    pdf = MarkdownPdf(toc_level=2)
    
    # Add the markdown content
    pdf.add_section(Section(md_content, toc=True))
    
    # Set metadata
    pdf.meta = {
        "title": "NeuroLearn: Adaptive Multi-Agent AI Tutor",
        "author": "CN7050 Intelligent Systems Coursework",
        "subject": "Multi-Agent Systems, RAG, Reinforcement Learning"
    }
    
    # Save to PDF
    pdf.save('NeuroLearn_Report.pdf')
    print("✅ PDF generated successfully: NeuroLearn_Report.pdf")

if __name__ == "__main__":
    convert_to_pdf()

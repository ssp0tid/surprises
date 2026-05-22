from flask import render_template
import os
import logging

logger = logging.getLogger(__name__)

WEASYPRINT_AVAILABLE = False
try:
    from weasyprint import HTML
    WEASYPRINT_AVAILABLE = True
except (ImportError, OSError):
    pass


def generate_pdf(invoice, template_folder=None):
    if template_folder is None:
        template_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')

    from jinja2 import Environment, FileSystemLoader
    env = Environment(loader=FileSystemLoader(template_folder))
    template = env.get_template('invoice_pdf.html')
    html_content = template.render(invoice=invoice)

    if not WEASYPRINT_AVAILABLE:
        return None

    try:
        pdf_bytes = HTML(string=html_content).write_pdf()
        return pdf_bytes
    except Exception as e:
        logger.error("PDF generation failed for invoice %s: %s", invoice.get('invoice_number', '?'), e)
        return None

"""
Génération de contrats PDF avec QR code de vérification (DIGIT-HAB).
"""

import io
import os
import re
import tempfile
from django.core.files.base import ContentFile
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.enums import TA_CENTER

try:
    import qrcode
    HAS_QR = True
except ImportError:
    HAS_QR = False


def _get_contract_context(contract):
    """Build placeholder context from contract and reservation."""
    res = contract.reservation
    prop = res.property
    agency = getattr(prop, 'agency', None)
    agent = res.assigned_agent or getattr(prop, 'agent', None)
    agent_profile = getattr(agent, 'profile', None) if agent else None
    client_name = res.get_client_name()
    client_email = res.get_client_email() or ''
    amount = (res.purchase_price or res.amount or 0)
    scheduled = res.scheduled_date.strftime('%d/%m/%Y') if res.scheduled_date else ''
    scheduled_time = res.scheduled_date.strftime('%H:%M') if res.scheduled_date else ''
    return {
        # Agency
        'agency_name': getattr(agency, 'name', '') or '',
        'agency_legal_name': getattr(agency, 'legal_name', '') or '',
        'agency_license_number': getattr(agency, 'license_number', '') or '',
        'agency_email': getattr(agency, 'email', '') or '',
        'agency_phone': getattr(agency, 'phone', '') or '',
        'agency_address_line1': getattr(agency, 'address_line1', '') or '',
        'agency_address_line2': getattr(agency, 'address_line2', '') or '',
        'agency_city': getattr(agency, 'city', '') or '',
        'agency_postal_code': getattr(agency, 'postal_code', '') or '',
        'agency_country': getattr(agency, 'country', '') or '',
        # Agent
        'agent_name': agent.get_full_name() if agent else '',
        'agent_email': getattr(agent, 'email', '') if agent else '',
        'agent_phone': getattr(agent, 'phone', '') if agent else '',

        'client_name': client_name,
        'client_email': client_email,
        'property_title': prop.title,
        'property_address': f"{prop.address_line1}, {prop.postal_code} {prop.city}",
        'amount': str(amount),
        'scheduled_date': scheduled,
        'contract_type': contract.get_contract_type_display(),
        'reservation_type': res.get_reservation_type_display(),
        'scheduled_time': scheduled_time,
    }


def _render_template_body(template_body, context):
    """Replace {{key}} placeholders in template body."""
    if not template_body:
        return ''
    text = template_body
    for key, value in context.items():
        text = re.sub(r'\{\{\s*' + re.escape(key) + r'\s*\}\}', str(value), text, flags=re.IGNORECASE)
    return text


def _make_qr_image(verify_url, size_cm=2.5):
    """Generate QR code image as bytes (PNG). verify_url = full URL to verify endpoint."""
    if not HAS_QR:
        return None
    qr = qrcode.QRCode(version=1, box_size=8, border=2)
    qr.add_data(verify_url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    return buf


def generate_contract_pdf(contract, verify_base_url):
    """
    Generate a PDF for the contract with embedded QR code for verification.
    verify_base_url: e.g. https://api.example.com/api/reservations/contracts/verify/
    The QR will point to verify_base_url + contract.verification_code + /
    Returns the PDF bytes (bytes) and the verification URL used.
    """
    contract.ensure_verification_code()
    verify_url = verify_base_url.rstrip('/') + '/' + contract.verification_code + '/'

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm,
    )
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        name='ContractTitle',
        parent=styles['Heading1'],
        fontSize=16,
        spaceAfter=12,
        alignment=TA_CENTER,
    )
    body_style = ParagraphStyle(
        name='ContractBody',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=6,
    )

    story = []

    # Header: Agency + Agent
    res = contract.reservation
    prop = res.property
    agency = getattr(prop, 'agency', None)
    agent = res.assigned_agent or getattr(prop, 'agent', None)
    agent_profile = getattr(agent, 'profile', None) if agent else None

    # Logo agence si disponible en local
    if agency and getattr(agency, 'logo', None):
        try:
            logo_path = agency.logo.path
            if os.path.exists(logo_path):
                story.append(Image(logo_path, width=3.2*cm, height=1.2*cm))
                story.append(Spacer(1, 0.2*cm))
        except Exception:
            pass

    agency_name = getattr(agency, 'name', '') if agency else ''
    if agency_name:
        story.append(Paragraph(f"<b>Agence :</b> {agency_name}", styles['Normal']))
        agency_line = []
        if getattr(agency, 'address_line1', None):
            agency_line.append(getattr(agency, 'address_line1', ''))
        if getattr(agency, 'city', None):
            agency_line.append(getattr(agency, 'city', ''))
        if agency_line:
            story.append(Paragraph(" · ".join([str(x) for x in agency_line if x]), styles['Normal']))
        agency_contacts = []
        if getattr(agency, 'phone', None):
            agency_contacts.append(str(getattr(agency, 'phone', '')))
        if getattr(agency, 'email', None):
            agency_contacts.append(str(getattr(agency, 'email', '')))
        if agency_contacts:
            story.append(Paragraph(" | ".join([c for c in agency_contacts if c]), styles['Normal']))
        if getattr(agency, 'license_number', None):
            story.append(Paragraph(f"N° Licence : {getattr(agency, 'license_number', '')}", styles['Normal']))

    if agent:
        agent_line = f"<b>Agent :</b> {agent.get_full_name() or agent.email}"
        story.append(Spacer(1, 0.1*cm))
        story.append(Paragraph(agent_line, styles['Normal']))
        agent_contacts = []
        if getattr(agent, 'phone', None):
            agent_contacts.append(str(getattr(agent, 'phone', '')))
        if getattr(agent, 'email', None):
            agent_contacts.append(str(getattr(agent, 'email', '')))
        if agent_contacts:
            story.append(Paragraph(" | ".join([c for c in agent_contacts if c]), styles['Normal']))

    story.append(Spacer(1, 0.6*cm))

    # Titre
    story.append(Paragraph("CONTRAT DIGIT-HAB", title_style))
    story.append(Paragraph(f"Type : {contract.get_contract_type_display()}", styles['Heading2']))
    story.append(Spacer(1, 0.5*cm))

    # Contexte pour le corps
    context = _get_contract_context(contract)
    body_text = ""
    if contract.template and contract.template.body:
        body_text = _render_template_body(contract.template.body, context)
    else:
        body_text = (
            f"<b>Entre les parties :</b><br/><br/>"
            f"Le bien : {context['property_title']}<br/>"
            f"Adresse : {context['property_address']}<br/><br/>"
            f"Client : {context['client_name']}<br/>"
            f"Email : {context['client_email']}<br/><br/>"
            f"Montant : {context['amount']} (réservation : {context['reservation_type']})<br/>"
            f"Date prévue : {context['scheduled_time']} {context['scheduled_date']}<br/><br/>"
            "Ce document constitue le contrat établi via la plateforme DIGIT-HAB. "
            "Scannez le QR code pour vérifier son authenticité."
        )

    for block in body_text.replace('<br/><br/>', '\n\n').split('\n\n'):
        block = block.replace('<br/>', ' ').strip()
        if block:
            story.append(Paragraph(block, body_style))

    story.append(Spacer(1, 1*cm))

    # QR code en bas de page (on l'ajoute comme élément)
    # ReportLab Image lit le fichier au moment de doc.build(), il faut garder le fichier jusqu'après
    tmp_path = None
    qr_buf = _make_qr_image(verify_url)
    if qr_buf:
        qr_bytes = qr_buf.getvalue()
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
            tmp.write(qr_bytes)
            tmp_path = tmp.name
        img = Image(tmp_path, width=2.5*cm, height=2.5*cm)
        story.append(Spacer(1, 0.5*cm))
        story.append(Paragraph(
            "<b>Vérification d'authenticité</b> – Scannez le QR code pour valider ce contrat.",
            styles['Normal']
        ))
        story.append(img)
        story.append(Paragraph(
            f"Code : {contract.verification_code}",
            ParagraphStyle(name='Small', parent=styles['Normal'], fontSize=8, textColor=colors.grey)
        ))

    doc.build(story)
    if tmp_path:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
    pdf_bytes = buffer.getvalue()
    return pdf_bytes, verify_url


def save_contract_pdf_to_field(contract, verify_base_url):
    """
    Generate PDF, save to contract.document, and return the verification URL.
    """
    pdf_bytes, verify_url = generate_contract_pdf(contract, verify_base_url)
    filename = f"contrat_{contract.id}.pdf"
    contract.document.save(filename, ContentFile(pdf_bytes), save=True)
    return verify_url

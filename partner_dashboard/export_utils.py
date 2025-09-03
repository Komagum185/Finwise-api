import csv
import io
from django.http import HttpResponse
from django.utils import timezone
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch


def export_to_csv(data, filename, fieldnames=None):
    """
    Export data to CSV format
    """
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{filename}.csv"'
    
    if not data:
        return response
    
    # If fieldnames not provided, use keys from first data item
    if not fieldnames:
        fieldnames = list(data[0].keys())
    
    writer = csv.DictWriter(response, fieldnames=fieldnames)
    writer.writeheader()
    
    for row in data:
        # Ensure all fields are present
        clean_row = {}
        for field in fieldnames:
            clean_row[field] = row.get(field, '')
        writer.writerow(clean_row)
    
    return response


def export_to_pdf(data, filename, title, fieldnames=None, field_labels=None):
    """
    Export data to PDF format using ReportLab
    """
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}.pdf"'
    
    # Create the PDF object
    doc = SimpleDocTemplate(response, pagesize=A4)
    elements = []
    
    # Get styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        spaceAfter=30,
        alignment=1  # Center alignment
    )
    
    # Add title
    elements.append(Paragraph(title, title_style))
    elements.append(Spacer(1, 20))
    
    # Add timestamp
    timestamp = f"Generated on: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}"
    elements.append(Paragraph(timestamp, styles['Normal']))
    elements.append(Spacer(1, 20))
    
    if not data:
        elements.append(Paragraph("No data available", styles['Normal']))
    else:
        # If fieldnames not provided, use keys from first data item
        if not fieldnames:
            fieldnames = list(data[0].keys())
        
        # If field_labels not provided, use fieldnames
        if not field_labels:
            field_labels = [field.replace('_', ' ').title() for field in fieldnames]
        
        # Prepare table data
        table_data = [field_labels]  # Header row
        
        for row in data:
            table_row = []
            for field in fieldnames:
                value = row.get(field, '')
                # Convert to string and handle None values
                if value is None:
                    value = ''
                elif isinstance(value, (int, float)):
                    value = str(value)
                table_row.append(value)
            table_data.append(table_row)
        
        # Create table
        table = Table(table_data)
        
        # Style the table
        table_style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ])
        
        table.setStyle(table_style)
        elements.append(table)
    
    # Build PDF
    doc.build(elements)
    return response


def get_export_filename(report_type, format_type):
    """
    Generate standardized export filename
    """
    timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
    return f"partner_dashboard_{report_type}_{timestamp}"


def get_field_labels(report_type):
    """
    Get human-readable field labels for different report types
    """
    labels = {
        'digitization': [
            'Business Name',
            'Business Type',
            'Lead Participant',
            'Region',
            'District',
            'Beneficiaries',
            'Lead Contact Number',
            'Total Beneficiaries'
        ],
        'loans': [
            'Business Name',
            'Group',
            'Loan Amount Received (UGX)',
            'Total Beneficiaries',
            'Loan Product',
            'Status',
            'Disbursed Date'
        ],
        'digital_services': [
            'Service Used',
            'Business Name',
            'Region',
            'District',
            'Contact',
            'Number of Beneficiaries',
            'Service Type'
        ]
    }
    
    return labels.get(report_type, [])


def get_fieldnames(report_type):
    """
    Get field names for different report types
    """
    fieldnames = {
        'digitization': [
            'business_name',
            'business_type',
            'lead_participant',
            'region',
            'district',
            'beneficiaries',
            'lead_contact_number',
            'total_beneficiaries'
        ],
        'loans': [
            'business_name',
            'group',
            'loan_amount_received',
            'total_beneficiaries',
            'loan_product',
            'status',
            'disbursed_date'
        ],
        'digital_services': [
            'service_used',
            'business_name',
            'region',
            'district',
            'contact',
            'number_of_beneficiaries',
            'service_type'
        ]
    }
    
    return fieldnames.get(report_type, [])

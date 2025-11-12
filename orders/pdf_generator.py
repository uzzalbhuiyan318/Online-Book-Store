"""
ReportLab PDF Invoice Generator
Generates professional PDF invoices matching the HTML invoice template
"""

from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, mm
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, 
    Spacer, PageBreak, Frame, PageTemplate
)
from reportlab.pdfgen import canvas
from datetime import datetime


class InvoicePDFGenerator:
    """
    Professional Invoice PDF Generator using ReportLab
    Matches the styling of invoice.html template
    """
    
    # Color definitions matching CSS
    COLOR_BLACK = colors.HexColor('#333333')
    COLOR_GRAY = colors.HexColor('#666666')
    COLOR_LIGHT_GRAY = colors.HexColor('#dddddd')
    COLOR_WHITE = colors.white
    
    # Status badge colors
    STATUS_COLORS = {
        'pending': colors.HexColor('#ffc107'),
        'confirmed': colors.HexColor('#17a2b8'),
        'processing': colors.HexColor('#007bff'),
        'shipped': colors.HexColor('#17a2b8'),
        'delivered': colors.HexColor('#28a745'),
        'cancelled': colors.HexColor('#dc3545'),
    }
    
    def __init__(self, order):
        """Initialize with order object"""
        self.order = order
        self.buffer = BytesIO()
        self.width, self.height = A4
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Setup custom paragraph styles matching HTML template"""
        
        # Company name style (h1)
        self.styles.add(ParagraphStyle(
            name='CompanyName',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=self.COLOR_BLACK,
            spaceAfter=6,
            fontName='Helvetica-Bold'
        ))
        
        # Company info style
        self.styles.add(ParagraphStyle(
            name='CompanyInfo',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=self.COLOR_GRAY,
            spaceAfter=3,
        ))
        
        # Invoice title style (h2)
        self.styles.add(ParagraphStyle(
            name='InvoiceTitle',
            parent=self.styles['Heading1'],
            fontSize=28,
            textColor=self.COLOR_BLACK,
            alignment=TA_RIGHT,
            spaceAfter=6,
            fontName='Helvetica-Bold'
        ))
        
        # Invoice details style
        self.styles.add(ParagraphStyle(
            name='InvoiceDetails',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=self.COLOR_BLACK,
            alignment=TA_RIGHT,
            spaceAfter=3,
        ))
        
        # Section header style (h3)
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Normal'],
            fontSize=11,
            textColor=self.COLOR_BLACK,
            fontName='Helvetica-Bold',
            spaceAfter=10,
        ))
        
        # Section content style
        self.styles.add(ParagraphStyle(
            name='SectionContent',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=self.COLOR_GRAY,
            spaceAfter=3,
        ))
        
        # Footer style
        self.styles.add(ParagraphStyle(
            name='Footer',
            parent=self.styles['Normal'],
            fontSize=9,
            textColor=self.COLOR_GRAY,
            alignment=TA_CENTER,
            spaceAfter=3,
        ))
        
        # Footer small style
        self.styles.add(ParagraphStyle(
            name='FooterSmall',
            parent=self.styles['Normal'],
            fontSize=8,
            textColor=self.COLOR_GRAY,
            alignment=TA_CENTER,
            spaceAfter=3,
        ))
    
    def _get_payment_method_display(self):
        """Get formatted payment method display"""
        method_map = {
            'cod': 'Cash on Delivery',
            'bkash': 'bKash',
            'nagad': 'Nagad',
            'rocket': 'Rocket',
            'card': 'Card Payment',
            'sslcommerz': 'Card Payment'
        }
        return method_map.get(self.order.payment_method, self.order.payment_method.title())
    
    def _create_header(self):
        """Create invoice header with company info and invoice title"""
        elements = []
        
        # Create header table (2 columns)
        header_data = [
            [
                # Left column - Company Info
                [
                    Paragraph('BookStore', self.styles['CompanyName']),
                    Paragraph('Your trusted online bookstore', self.styles['CompanyInfo']),
                    Paragraph('Email: info@bookstore.com', self.styles['CompanyInfo']),
                    Paragraph('Phone: +880 1234-567890', self.styles['CompanyInfo']),
                ],
                # Right column - Invoice Title
                [
                    Paragraph('INVOICE', self.styles['InvoiceTitle']),
                    Paragraph(f'<b>Order #{self.order.order_number}</b>', self.styles['InvoiceDetails']),
                    Paragraph(f'Date: {self.order.created_at.strftime("%B %d, %Y")}', self.styles['InvoiceDetails']),
                    Paragraph(f'Status: <font color="{self._get_status_color()}">{self.order.get_status_display()}</font>', 
                             self.styles['InvoiceDetails']),
                ]
            ]
        ]
        
        header_table = Table(header_data, colWidths=[self.width/2 - 40, self.width/2 - 40])
        header_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ALIGN', (0, 0), (0, 0), 'LEFT'),
            ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('LINEBELOW', (0, 0), (-1, -1), 2, self.COLOR_BLACK),
        ]))
        
        elements.append(header_table)
        elements.append(Spacer(1, 20))
        
        return elements
    
    def _get_status_color(self):
        """Get color for status badge"""
        return self.STATUS_COLORS.get(self.order.status, self.COLOR_GRAY)
    
    def _create_details_section(self):
        """Create three-column details section (Bill To, Ship To, Payment Info)"""
        elements = []
        
        # Bill To column
        bill_to_items = [
            Paragraph('BILL TO:', self.styles['SectionHeader']),
            Paragraph(f'<b>{self.order.user.get_full_name()}</b>', self.styles['SectionContent']),
            Paragraph(self.order.user.email, self.styles['SectionContent']),
        ]
        
        # Add phone if exists
        if hasattr(self.order.user, 'phone') and self.order.user.phone:
            bill_to_items.append(Paragraph(self.order.user.phone, self.styles['SectionContent']))
        
        # Ship To column
        ship_to_items = [
            Paragraph('SHIP TO:', self.styles['SectionHeader']),
            Paragraph(f'<b>{self.order.shipping_full_name}</b>', self.styles['SectionContent']),
            Paragraph(self.order.shipping_phone, self.styles['SectionContent']),
            Paragraph(self.order.shipping_address_line1, self.styles['SectionContent']),
        ]
        
        if self.order.shipping_address_line2:
            ship_to_items.append(Paragraph(self.order.shipping_address_line2, self.styles['SectionContent']))
        
        ship_to_items.extend([
            Paragraph(f'{self.order.shipping_city}, {self.order.shipping_state}', self.styles['SectionContent']),
            Paragraph(self.order.shipping_postal_code, self.styles['SectionContent']),
        ])
        
        # Payment Info column
        payment_status = 'Paid' if self.order.payment_status == 'paid' else 'Pending'
        payment_info_items = [
            Paragraph('PAYMENT INFO:', self.styles['SectionHeader']),
            Paragraph(f'<b>Method:</b> {self._get_payment_method_display()}', self.styles['SectionContent']),
            Paragraph(f'<b>Status:</b> {payment_status}', self.styles['SectionContent']),
        ]
        
        # Create details table
        details_data = [[bill_to_items, ship_to_items, payment_info_items]]
        
        col_width = (self.width - 80) / 3
        details_table = Table(details_data, colWidths=[col_width, col_width, col_width])
        details_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ]))
        
        elements.append(details_table)
        elements.append(Spacer(1, 20))
        
        return elements
    
    def _create_items_table(self):
        """Create order items table"""
        elements = []
        
        # Table header
        table_data = [
            ['Item', 'Author', 'Unit Price', 'Quantity', 'Total']
        ]
        
        # Add order items
        for item in self.order.items.all():
            table_data.append([
                item.book.title if item.book else item.book_title,
                item.book.author if item.book else item.book_author,
                f'৳{item.price}',
                str(item.quantity),
                f'৳{item.subtotal}'
            ])
        
        # Create table
        col_widths = [
            (self.width - 80) * 0.35,  # Item
            (self.width - 80) * 0.25,  # Author
            (self.width - 80) * 0.15,  # Unit Price
            (self.width - 80) * 0.10,  # Quantity
            (self.width - 80) * 0.15,  # Total
        ]
        
        items_table = Table(table_data, colWidths=col_widths)
        
        # Apply table styling
        table_style = [
            # Header row styling
            ('BACKGROUND', (0, 0), (-1, 0), self.COLOR_BLACK),
            ('TEXTCOLOR', (0, 0), (-1, 0), self.COLOR_WHITE),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('TOPPADDING', (0, 0), (-1, 0), 12),
            
            # Data rows styling
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('TEXTCOLOR', (0, 1), (-1, -1), self.COLOR_BLACK),
            ('TOPPADDING', (0, 1), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 12),
            
            # Borders
            ('LINEBELOW', (0, 1), (-1, -1), 1, self.COLOR_LIGHT_GRAY),
            
            # Alignment
            ('ALIGN', (0, 0), (1, -1), 'LEFT'),
            ('ALIGN', (2, 0), (-1, -1), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]
        
        items_table.setStyle(TableStyle(table_style))
        
        elements.append(items_table)
        elements.append(Spacer(1, 20))
        
        return elements
    
    def _create_totals_section(self):
        """Create totals section (right-aligned)"""
        elements = []
        
        # Totals data
        totals_data = [
            ['Subtotal:', f'৳{self.order.subtotal:.2f}'],
            ['Shipping:', f'৳{self.order.shipping_cost:.2f}'],
        ]
        
        # Add discount if applicable
        if self.order.discount > 0:
            totals_data.append(['Discount:', f'-৳{self.order.discount:.2f}'])
        
        # Total row
        totals_data.append(['Total Amount:', f'৳{self.order.total:.2f}'])
        
        # Create totals table
        totals_table = Table(totals_data, colWidths=[150, 100])
        
        # Styling
        totals_style = [
            ('FONTNAME', (0, 0), (-1, -3), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -3), 11),
            ('TEXTCOLOR', (0, 0), (-1, -3), self.COLOR_GRAY),
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('LINEBELOW', (0, 0), (-1, -2), 1, self.COLOR_LIGHT_GRAY),
            
            # Total row (bold and larger)
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, -1), (-1, -1), 14),
            ('TEXTCOLOR', (0, -1), (-1, -1), self.COLOR_BLACK),
            ('LINEABOVE', (0, -1), (-1, -1), 2, self.COLOR_BLACK),
            ('LINEBELOW', (0, -1), (-1, -1), 2, self.COLOR_BLACK),
            ('TOPPADDING', (0, -1), (-1, -1), 12),
        ]
        
        # Handle discount row color if present
        if self.order.discount > 0:
            discount_row = len(totals_data) - 2  # Second to last row
            totals_style.append(('TEXTCOLOR', (0, discount_row), (-1, discount_row), colors.HexColor('#28a745')))
        
        totals_table.setStyle(TableStyle(totals_style))
        
        # Right-align the totals table
        totals_container = Table([[totals_table]], colWidths=[self.width - 80])
        totals_container.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, 0), 'RIGHT'),
        ]))
        
        elements.append(totals_container)
        elements.append(Spacer(1, 20))
        
        return elements
    
    def _create_notes_section(self):
        """Create order notes section if notes exist"""
        elements = []
        
        if hasattr(self.order, 'customer_notes') and self.order.customer_notes:
            # Create notes box
            notes_style = ParagraphStyle(
                name='Notes',
                parent=self.styles['Normal'],
                fontSize=10,
                textColor=self.COLOR_GRAY,
                leftIndent=10,
                rightIndent=10,
            )
            
            notes_header = Paragraph('<b>Order Notes:</b>', notes_style)
            notes_content = Paragraph(self.order.customer_notes, notes_style)
            
            notes_data = [[notes_header], [notes_content]]
            notes_table = Table(notes_data, colWidths=[self.width - 80])
            notes_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f9f9f9')),
                ('LEFTPADDING', (0, 0), (-1, -1), 15),
                ('RIGHTPADDING', (0, 0), (-1, -1), 15),
                ('TOPPADDING', (0, 0), (-1, -1), 15),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 15),
                ('LINEBEFORE', (0, 0), (0, -1), 4, colors.HexColor('#007bff')),
            ]))
            
            elements.append(notes_table)
            elements.append(Spacer(1, 20))
        
        return elements
    
    def _create_footer(self):
        """Create invoice footer"""
        elements = []
        
        # Footer line
        line_data = [['']]
        line_table = Table(line_data, colWidths=[self.width - 80])
        line_table.setStyle(TableStyle([
            ('LINEABOVE', (0, 0), (-1, 0), 1, self.COLOR_LIGHT_GRAY),
            ('TOPPADDING', (0, 0), (-1, 0), 20),
        ]))
        
        elements.append(line_table)
        elements.append(Spacer(1, 10))
        
        # Footer content
        elements.append(Paragraph('Thank you for shopping with us!', self.styles['Footer']))
        elements.append(Paragraph('For any queries, please contact us at support@bookstore.com or call +880 1234-567890', 
                                 self.styles['Footer']))
        elements.append(Spacer(1, 10))
        elements.append(Paragraph('This is a computer-generated invoice and does not require a signature.', 
                                 self.styles['FooterSmall']))
        
        return elements
    
    def generate(self):
        """Generate the complete PDF invoice"""
        # Create document
        doc = SimpleDocTemplate(
            self.buffer,
            pagesize=A4,
            rightMargin=40,
            leftMargin=40,
            topMargin=40,
            bottomMargin=40,
        )
        
        # Build content
        story = []
        
        # Add all sections
        story.extend(self._create_header())
        story.extend(self._create_details_section())
        story.extend(self._create_items_table())
        story.extend(self._create_totals_section())
        story.extend(self._create_notes_section())
        story.extend(self._create_footer())
        
        # Build PDF
        doc.build(story)
        
        # Get PDF content
        pdf_content = self.buffer.getvalue()
        self.buffer.close()
        
        return pdf_content


def generate_invoice_pdf(order):
    """
    Convenience function to generate invoice PDF
    
    Args:
        order: Order instance
    
    Returns:
        bytes: PDF file content
    """
    generator = InvoicePDFGenerator(order)
    return generator.generate()

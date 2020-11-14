# -*- coding: utf-8 -*-
{
    'name': "Impresion de Facturas de Venta en impresora Fiscal",
    'summary': """Integración y uso de impresora fiscales en el módulo de contabilidad y facturación.""",
    'description': """Integración y uso de impresora fiscales en el módulo de contabilidad y facturación""",
    'author': "Neonety",
    'website': "http://www.neonety.com",
    'category': 'Administration',
    'version': '1.6.1',
    'depends': ['base', 'account', 'account_invoicing', 'fpi'],
    'data': [
        'security/security_data.xml',
        'security/ir.model.access.csv',
        #'views/fpi_invoice_views.xml'
    ],
}

# -*- coding: utf-8 -*-
{
    'name': 'Ajustes en el proyecto Ancon',
    'summary': 'Ajustes en el proyecto Ancon',
    'description': 'Ajustes en el proyecto Ancon',
    'author': 'Neonety',
    'website': "http://www.neonety.com",
    'category': 'Sales',
    'depends': ['base', 'contacts', 'product', 'account', 'sale', 'product_brand', 'neonety', 'fpi_invoice', 'purchase', 'stock', 'account_multi_store'],
    'version': '1.12.9',
    'data': [
        #'trigger.sql',
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/partner_concept_views.xml',
        'views/partner_views.xml',
        'views/commission_views.xml',
        'views/delivery_zone_views.xml',
        'views/product_brand_views.xml',
        'views/credit_note_views.xml',
        'views/account_invoice_views.xml',
        'views/account_payment_views.xml',
        'views/res_company_views.xml',
        'views/sale_order_views.xml',
        'views/account_tax_views.xml',
        'views/stock_picking_form.xml',
        'views/account_menuitem.xml', # comment before to deploy
        'views/account_invoice_supplier_views.xml', # comment before to deploy
        'views/account_account_views.xml',
        'views/withholding_certificate_views.xml',
        'views/annex_report_views.xml',
        'views/daily_sales_report_wizard_views.xml',
        'data/withholding_certificate_sequence.xml',
        'report/withholding_certificate_report.xml',
        'report/withholding_certificate_report_templates.xml',
        'report/daily_sales_report.xml',
        'report/daily_sales_report_template.xml',
    ]
}

# -*- coding: utf-8 -*-
from odoo import models, fields, api, tools
import logging
_logger = logging.getLogger(__name__)

class FpiApiInvoiceDocumentsPendingList(models.Model):
    _name = 'fpi.invoice.documents.pending.list'
    _auto = False
    position = fields.Integer(string='Field', readonly=True)
    id = fields.Integer(string='Field', readonly=True)
    partner_name = fields.Char(string='Field', readonly=True)
    partner_ruc = fields.Char(string='Field', readonly=True)
    partner_street = fields.Char(string='Field', readonly=True)
    partner_zip = fields.Char(string='Field', readonly=True)
    partner_province = fields.Char(string='Field', readonly=True)
    partner_district = fields.Char(string='Field', readonly=True)
    partner_sector = fields.Char(string='Field', readonly=True)
    partner_country = fields.Char(string='Field', readonly=True)
    payments_total = fields.Float(string='Field', readonly=True)
    cash_payment_total = fields.Float(string='Field', readonly=True)
    bank_payment_total = fields.Float(string='Field', readonly=True)
    credit_card_payment_total = fields.Float(string='Field', readonly=True)
    debit_card_payment_total = fields.Float(string='Field', readonly=True)
    amount_total = fields.Float(string='Field', readonly=True)
    amount_untaxed = fields.Float(string='Field', readonly=True)
    amount_tax = fields.Float(string='Field', readonly=True)
    discount_total = fields.Float(string='Field', readonly=True)
    tax_percentage = fields.Float(string='Field', readonly=True)
    invoice_type = fields.Char(string='Field', readonly=True)
    refund_type = fields.Char(string='Field', readonly=True)
    refund_note = fields.Char(string='Field', readonly=True)
    parent_invoice_filename_assigned = fields.Char(string='Field', readonly=True)
    parent_invoice_fiscal_invoice_number = fields.Integer(string='Field', readonly=True)
    parent_invoice_fiscal_printer_serial = fields.Char(string='Field', readonly=True)
    refund_date = fields.Char(string='Field', readonly=True)
    refund_time = fields.Char(string='Field', readonly=True)
    master_filename_assigned = fields.Char(string='Field', readonly=True)
    lines_filename_assigned = fields.Char(string='Field', readonly=True)
    user_login = fields.Char(string='Field', readonly=True)

    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self._cr, 'fpi_invoice_documents_pending_list')
        self._cr.execute("""
            CREATE OR REPLACE VIEW fpi_invoice_documents_pending_list AS
            SELECT
                row_number() over() AS position,
                FD.id AS id,
                FD.partner_name AS partner_name,
                FD.partner_ruc AS partner_ruc,
                FD.partner_street AS partner_street,
                FD.partner_zip AS partner_zip,
                FD.partner_province AS partner_province,
                FD.partner_district AS partner_district,
                FD.partner_sector AS partner_sector,
                FD.partner_country AS partner_country,
                FD.payments_total AS payments_total,
                FD.cash_payment_total AS cash_payment_total,
                FD.bank_payment_total AS bank_payment_total,
                FD.credit_card_payment_total AS credit_card_payment_total,
                FD.debit_card_payment_total AS debit_card_payment_total,
                FD.amount_total AS amount_total,
                FD.amount_untaxed AS amount_untaxed,
                FD.amount_tax AS amount_tax,
                FD.discount_total AS discount_total,
                FD.tax_percentage AS tax_percentage,
                FD.invoice_type AS invoice_type,
                FD.refund_type AS refund_type,
                FD.refund_note AS refund_note,
                FD.parent_invoice_filename_assigned AS parent_invoice_filename_assigned,
                FD.parent_invoice_fiscal_printer_serial AS parent_invoice_fiscal_printer_serial,
                FD.parent_invoice_fiscal_invoice_number AS parent_invoice_fiscal_invoice_number,
                FD.refund_date AS refund_date,
                FD.refund_time AS refund_time,
                FD.master_filename_assigned AS master_filename_assigned,
                FD.lines_filename_assigned AS lines_filename_assigned,
                RU.login AS user_login
            FROM
                fpi_document FD
            INNER JOIN
                account_invoice AI
                ON AI.id = FD.invoice_id
            INNER JOIN
                res_users RU
                ON RU.id = FD.write_uid
            WHERE
                FD.print_status LIKE 'pending'
                AND FD.printer_id IS NOT NULL
                AND FD.documents_type_printed LIKE 'account_invoice'
                AND AI.state IN ('open', 'paid')
                AND FD.fiscal_invoice_number = 0
            ORDER BY
                FD.create_date""")


class FpiApiInvoiceLineDocumentsPendingList(models.Model):
    _name = 'fpi.invoice.line.documents.pending.list'
    _auto = False
    position = fields.Integer(string='Field', readonly=True)
    id = fields.Integer(string='Field', readonly=True)
    fpi_document_id = fields.Integer(string='Field', readonly=True)
    product_code = fields.Char(string='Field', readonly=True)
    product_code_2 = fields.Char(string='Field', readonly=True)
    product_name = fields.Char(string='Field', readonly=True)
    product_price = fields.Float(string='Field', readonly=True)
    quantity = fields.Float(string='Field', readonly=True)
    unit_type = fields.Char(string='Field', readonly=True)
    group_type = fields.Integer(string='Field', readonly=True)
    tax_percentage = fields.Float(string='Field', readonly=True)
    master_filename_assigned = fields.Char(string='Field', readonly=True)
    lines_filename_assigned = fields.Char(string='Field', readonly=True)
    user_login = fields.Char(string='Field', readonly=True)

    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self._cr, 'fpi_invoice_line_documents_pending_list')
        self._cr.execute("""
            CREATE OR REPLACE VIEW fpi_invoice_line_documents_pending_list AS
            SELECT 
                row_number() over() AS position,
                AIL.id AS id,
                FD.id AS fpi_document_id,
                PT.default_code AS product_code,
                PP.default_code AS product_code_2,
                REPLACE(AIL.name, '\n', '') AS product_name,
                AIL.price_unit AS product_price,
                AIL.quantity AS quantity,
                'UNIDADES' as unit_type,
                2 AS group_type,
                AT.amount AS tax_percentage,
                FD.master_filename_assigned AS master_filename_assigned,
                FD.lines_filename_assigned AS lines_filename_assigned,
                RU.login AS user_login
            FROM
                account_invoice_line AIL
            INNER JOIN
                account_invoice AI
                on AI.id = AIL.invoice_id
            INNER JOIN
                fpi_document FD
                ON FD.invoice_id = AI.id
                    AND FD.print_status LIKE 'pending'
                    AND FD.printer_id IS NOT NULL
                    AND FD.documents_type_printed LIKE 'account_invoice'
                    AND FD.fiscal_invoice_number = 0
            INNER JOIN
                product_product PP
                ON PP.id = AIL.product_id
            INNER JOIN 
                product_template PT
                ON PT.id = PP.product_tmpl_id
            INNER JOIN
                res_users RU
                ON RU.id = FD.write_uid
            LEFT JOIN
                account_invoice_line_tax AILT
                ON AILT.invoice_line_id = AIL.id
            LEFT JOIN
                account_tax AT
                ON AT.id = AILT.tax_id""")
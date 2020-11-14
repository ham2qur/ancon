# -*- coding: utf-8 -*-
from odoo import models, fields, api, tools
import logging
_logger = logging.getLogger(__name__)


class CommissionsReport(models.Model):
    _name = 'ancon.commissions.report'
    _auto = False
    id = fields.Integer(string='ID', readonly=True)
    account_invoice_line_id = fields.Integer(string='Id del item de Factura', readonly=True)
    invoice_id = fields.Integer(string='ID de Factura', readonly=True)
    product_id = fields.Integer(string='ID del Producto', readonly=True)
    commission_id = fields.Integer(string='ID de Commission', readonly=True)
    category_id = fields.Integer(string='ID de Categoría', readonly=True)
    vendor_id = fields.Integer(string='Vendor ID', readonly=True)
    payment_term_id = fields.Integer(string='ID del plazo de pago', readonly=True)
    product_name = fields.Char(string='Producto', readonly=True)
    category_name = fields.Char(string='Categoría', readonly=True)
    invoice_number = fields.Char(string='Número de Factura', readonly=True)
    vendor_name = fields.Char(string='Vendedor', readonly=True)
    payment_term_name = fields.Char(string='Plazo de Pago', readonly=True)
    invoice_state = fields.Char(string='Estado de Factura', readonly=True)
    invoice_date = fields.Date(string='Fecha de Factura', readonly=True)
    quantity = fields.Integer(string='Cantidad', readonly=True)
    product_price_unit = fields.Float(string='Precio Unitario', readonly=True)
    subtotal = fields.Float(string='Subtotal', readonly=True)
    total = fields.Float(string='Total', readonly=True)
    discount = fields.Float(string='Descuento', readonly=True)
    commission_percentage = fields.Float(string='Porcentaje de comisión', readonly=True)
    commission_total = fields.Float(string='Comisión', readonly=True)
    _order = 'account_invoice_line_id'

    def init(self):
        tools.drop_view_if_exists(self._cr, 'ancon_commission_report')
        self._cr.execute("""
            CREATE OR REPLACE VIEW ancon_commissions_report AS
            SELECT
                AIL.id AS id,
                AIL.id AS account_invoice_line_id,
                AI.id AS invoice_id,
                AIL.product_id AS product_id,
                AIL.commission_id AS commission_id,
                PT.categ_id AS category_id,
                AI.user_id AS vendor_id,
                AI.payment_term_id AS payment_term_id,
                AIL.name AS product_name,
                PC.name AS category_name,
                AI.number AS invoice_number,
                RP.name AS vendor_name,
                APT.name AS payment_term_name,
                AI.state AS invoice_state,
                AI.date_invoice AS invoice_date,
                AIL.quantity AS quantity,
                AIL.price_unit AS product_price_unit,
                AIL.price_subtotal AS subtotal,
                AIL.price_total AS total,
                AIL.discount AS discount,
                AIL.commission_percentage AS commission_percentage,
                AIL.commission_total AS commission_total
            FROM
                account_invoice_line AIL
                INNER JOIN ancon_commission AC ON AC.id = AIL.commission_id
                INNER JOIN product_product PP ON PP.id = AIL.product_id
                INNER JOIN product_template PT ON PT.id = PP.product_tmpl_id
                INNER JOIN product_category PC ON PC.id = PT.categ_id
                INNER JOIN account_invoice AI ON AI.id = AIL.invoice_id AND AI.state LIKE 'paid'
                INNER JOIN res_users RU ON RU.id = AI.user_id
                INNER JOIN res_partner RP ON RP.id = RU.partner_id
                INNER JOIN account_payment_term APT ON APT.id = AI.payment_term_id""")

# -*- coding: utf-8 -*-
from odoo import models, fields, api, tools
import logging
_logger = logging.getLogger(__name__)


class Annex72(models.Model):
    _name = 'ancon.annex72.report'
    _auto = False
    id = fields.Integer(string='ID', readonly=True)
    account_invoice_line_id = fields.Integer(string='ID de la línea de factura', readonly=True)
    account_invoice_id = fields.Integer(string='ID de la factura', readonly=True)
    account_account_id = fields.Integer(string='ID de la cuenta contable', readonly=True)
    neonety_partner_concept_id = fields.Integer(string='ID del concepto del proveedor', readonly=True)
    res_partner_id = fields.Integer(string='ID del proveedor', readonly=True)
    company_id = fields.Integer(string='ID de la compañía', readonly=True)
    partner_type = fields.Integer(string='Tipo de persona', readonly=True)
    partner_ruc = fields.Char(string='RUC', readonly=True)
    partner_dv = fields.Char(string='DV', readonly=True)
    partner_name = fields.Char(string='Nombre o razón social', readonly=True)
    partner_concept_type = fields.Integer(string='Tipo de pago', readonly=True)
    partner_concept_code = fields.Integer(string='Concepto', readonly=True)
    account_invoice_line_price = fields.Float(string='Monto (B/.)', readonly=True)
    account_invoice_state = fields.Integer(string='Período de aplicación', readonly=True)
    account_invoice_number = fields.Char(string='Número de factura', readonly=True)
    account_invoice_line_name = fields.Char(string='Nombre del producto en la línea de factura', readonly=True)
    partner_concept_name = fields.Char(string='Descripción del concepto del proveedor', readonly=True)
    account_account_name = fields.Char(string='Descripción de la cuenta contable', readonly=True)
    account_invoice_date = fields.Date(string='Fecha de facturación', readonly=True)
    account_invoice_create_date = fields.Datetime(string='Fecha de creación de la factura', readonly=True)
    _order = 'account_invoice_line_id'

    def init(self):
        tools.drop_view_if_exists(self._cr, 'ancon_annex72_report')
        self._cr.execute("""
            CREATE OR REPLACE VIEW ancon_annex72_report AS
            SELECT
                AIL.id as id,
                AIL.id AS account_invoice_line_id,
                AI.id AS account_invoice_id,
                AA.id AS account_account_id,
                NPC.id AS neonety_partner_concept_id,
                RP.id AS res_partner_id,
                RC.id AS company_id,
                (CASE when RP.is_company IS TRUE THEN 1 ELSE 2 END) AS partner_type,
                RP.ruc AS partner_ruc,
                RP.dv AS partner_dv,
                RP.name AS partner_name,
                NPC.type AS partner_concept_type,
                to_number(NPC.code, '999') AS partner_concept_code,
                AIL.price_subtotal AS account_invoice_line_price,
                (CASE when AI.state LIKE 'paid' THEN 1 WHEN AI.state LIKE 'open' THEN 2 END) AS account_invoice_state,
                AI.number AS account_invoice_number,
                AIL.name AS account_invoice_line_name,
                NPC.name AS partner_concept_name,
                AA.name AS account_account_name,
                AI.date_invoice AS account_invoice_date,
                AI.create_date AS account_invoice_create_date
            FROM
                account_invoice_line AIL
                INNER JOIN account_account AA ON AA.id = AIL.account_id AND AA.partner_concept_id IS NOT NULL
                INNER JOIN account_invoice AI ON AI.id = AIL.invoice_id AND AI.type LIKE 'in_invoice' AND AI.state IN ('open', 'paid')
                INNER JOIN res_partner RP ON RP.id = AI.partner_id AND RP.supplier IS TRUE
                INNER JOIN neonety_partner_concept NPC ON NPC.id = AA.partner_concept_id
                INNER JOIN res_company RC ON RC.id = AIL.company_id""")

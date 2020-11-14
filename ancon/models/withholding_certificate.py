# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError
from datetime import datetime
import logging
_logger = logging.getLogger(__name__)

EMPTY_SEQUENCE = 'Borrador'


class WithholdingCertificate(models.Model):
    _name = 'ancon.withholding.certificate'
    _order = 'id desc'
    _rec_name = 'number'
    number = fields.Char(
        string='Certificado Número',
        required=True,
        copy=False,
        readonly=True,
        index=True,
        default=lambda self: EMPTY_SEQUENCE
    )
    state = fields.Selection([
        ('draft', 'Borrador'),
        ('approved','Validado')],
        default='draft')
    certificated_on = fields.Date(
        string='Fecha'
    )
    company_id = fields.Many2one(
        'res.company',
        string='Generado por',
    )
    company_ruc = fields.Char(
        string="RUC",
        related='company_id.ruc'
        )
    company_dv = fields.Char(
        string="DV",
        related='company_id.dv'
        )
    supplier_id = fields.Many2one(
        'res.partner',
        string='Proveedor'
    )
    supplier_ruc = fields.Char(
        string="RUC",
        related='supplier_id.ruc'
        )
    supplier_dv = fields.Char(
        string="DV",
        related='supplier_id.dv'
        )
    account_tax_id = fields.Many2one(
        'account.tax',
        string='Impuesto',
    )
    withholding_percentage = fields.Float(
        string='Porcentaje de retención',
        default=0.00
    )
    invoice_id = fields.Many2one(
        'account.invoice',
        string='Factura',
    )
    invoice_subtotal = fields.Float(
        string='Monto sujeto a retención',
        default=0.00
    )
    withholding_amount = fields.Float(
        string='Monto retenido',
        default=0.00
    )
    comments = fields.Char(
        string='Área Responsable',
        required=False
    )
    withholding_percentage_formatted = fields.Char(
        string='Porcentaje de retención',
        store=False,
        compute='_get_fields_formatted'
    )
    withholding_amount_formatted = fields.Char(
        string='Monto retenido',
        store=False,
        compute='_get_fields_formatted'
    )
    create_date_formatted = fields.Char(
        string='Fecha de Creación',
        store=False,
        compute='_get_fields_formatted'
    )

    @api.one
    def _get_fields_formatted(self):
        self.withholding_percentage_formatted = '0.00 %'
        if self.account_tax_id:
            self.withholding_percentage_formatted = '{0:.2f} %'.format(self.account_tax_id.amount*-1)
        self.withholding_amount_formatted = '0.00'
        if self.invoice_id:
            self.withholding_amount_formatted = '{0:.2f}'.format(self.invoice_id.withholding_tax*-1)
        if self.create_date:
            date_obj = datetime.strptime(self.create_date, '%Y-%m-%d %H:%M:%S')
            if date_obj:
                self.create_date_formatted = date_obj.date().strftime('%d/%m/%Y')

    @api.onchange('company_id')
    def _onchange_company_id(self):
        self.company_ruc = self.company_id.ruc if self.company_id else None
        self.company_dv = self.company_id.dv if self.company_id else None

    @api.onchange('supplier_id')
    def _onchange_supplier_id(self):
        self.supplier_ruc = self.supplier_id.ruc if self.supplier_id else None
        self.supplier_dv = self.supplier_id.dv if self.supplier_id else None
        self.invoice_subtotal = 0.00
        self.withholding_amount = 0.00
        res = {}
        if self.supplier_id:
            res['domain'] = {'invoice_id': [
                ('partner_id', '=', self.supplier_id.id),
                ('withholding_tax', '<', 0.00),
                ('has_withholding_certificate', '=', False),
                ('state', 'in', ['open', 'paid'])]}
        return res

    @api.onchange('account_tax_id')
    def _onchange_account_tax_id(self):
        self.withholding_percentage = self.account_tax_id.amount if self.account_tax_id else 0.00

    @api.onchange('invoice_id')
    def _onchange_invoice_id(self):
        self.invoice_subtotal = self.invoice_id.amount_untaxed if self.invoice_id else 0.00
        self.withholding_amount = self.invoice_id.withholding_tax if self.invoice_id else 0.00

    @api.multi
    def validate_action(self):
        invoice = self.invoice_id
        invoice.write({'has_withholding_certificate': True})
        return self.write({'state': 'approved'})

    @api.multi
    def print_action(self):
        return self.env.ref('ancon.withholding_certificate_report_action').report_action(self)

    @api.model
    def create(self, vals):
        vals['number'] = self.env['ir.sequence'].next_by_code('withholding_cert') or EMPTY_SEQUENCE
        certificate = super(WithholdingCertificate, self).create(vals)
        if certificate.invoice_id:
            certificate.supplier_id = certificate.invoice_id.partner_id
        return certificate

    @api.multi
    def unlink(self):
        for certificate in self:
            if 'approved' in certificate.state:
                raise UserError("Sólo puedes borrar este certificado si esta en borrador.")
        return super(WithholdingCertificate, self).unlink()

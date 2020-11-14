# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError
from datetime import date, datetime
import logging
_logger = logging.getLogger(__name__)


PAYMENT_TERM_TYPE = [
    ('cash_payment', 'Pago de Contado'),
    ('credit_payment', 'Abono / Pago a Crédito'),
]

CREDIT_NOTE_STATES = [
    ('draft', 'Borrador'),
    ('pending', 'Pendiente de Aprobación'),
    ('approved', 'Solicitud Aprobada'),
]

class AccountPaymentTerm(models.Model):
    _inherit = 'account.payment.term'

    payment_term_type = fields.Selection(
        PAYMENT_TERM_TYPE,
        string="Tipo de Pago (Contado / Abono)",
        default='credit_payment')


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'
    credit_note_state = fields.Selection(
        CREDIT_NOTE_STATES,
        string="Estado de la solicitud de Nota de Crédito",
        default='draft')
    withholding_tax = fields.Monetary(
        string='Monto de retención',
        default=0.00)
    has_withholding_certificate = fields.Boolean(
        string='Tiene Certificado de retención',
        default=False)
    partner_ruc = fields.Char(
        string='RUC',
        related='partner_id.ruc',
        inverse='_inverse_ruc',
        compute='_get_ancon_parnter_info')

    def _get_ancon_parnter_info(self, partner):
        return {
            'partner_ruc': partner.ruc}

    def _inverse_ruc(self):
        for invoice in self:
            invoice.partner_id.ruc = invoice.partner_ruc

    def _date_invoice_validator(self, date_invoice=None):
        if date_invoice:
            #date_obj = datetime.strptime(date_invoice, '%Y-%m-%d')
            date_obj = date_invoice.strftime('%Y-%m-%d')
            #if date_obj.date() < date.today():
            #    raise ValidationError('No puede crear esta factura ya que la fecha de facturación es menor a la fecha actual.')

    @api.model
    def create(self, vals):
        comment = '' if not 'comment' in vals or not vals['comment'] else vals['comment']
        if 'partner_id' in vals:
            partner_id = self.env['res.partner'].browse(vals['partner_id'])
            if partner_id:
                if hasattr(partner_id, 'sector_id'):
                    delivery_zones = self.env['ancon.delivery.zone'].search_read([
                        ('sector_ids', 'in', [partner_id.sector_id.id])], fields=['id', 'name', 'description'])
                    if len(delivery_zones) > 0:
                        delivery_info = "\n"
                        for dz in delivery_zones:
                            delivery_info += 'Ruta de entrega: {0}, información: {1}'.format(dz['name'], dz['description'])
                        if not delivery_info in comment:
                            comment = "{0}\n{1}".format(delivery_info, comment)
        vals['comment'] = comment
        invoice = super(AccountInvoice, self).create(vals)
        date_invoice = vals['date_invoice'] if 'date_invoice' in vals and vals['date_invoice'] else None
        self._date_invoice_validator(date_invoice=date_invoice)
        invoice.withholding_tax = 0.00
        if 'in_invoice' in invoice.type:
            for tax_line_id in invoice.tax_line_ids:
                if tax_line_id.tax_id:
                    if tax_line_id.tax_id.is_withholding_tax:
                        invoice.withholding_tax = tax_line_id.amount
        return invoice

    # @api.multi
    # def write(self, vals):
    #     if self.type:
    #         if 'in_invoice' in self.type:
    #             withholding_tax = self.withholding_tax
    #             if withholding_tax >= 0:
    #                 for tax_line_id in self.tax_line_ids:
    #                     if tax_line_id.tax_id:
    #                         if tax_line_id.tax_id.is_withholding_tax:
    #                             withholding_tax = tax_line_id.amount
    #             vals['withholding_tax'] = withholding_tax
    #     return super(AccountInvoice, self).write(vals)

    @api.multi
    def invoice_validate(self):
        invoice = super(AccountInvoice, self).invoice_validate()
        date_invoice = self.date_invoice if self.date_invoice else False
        self._date_invoice_validator(date_invoice=date_invoice)
        comment = self.comment if self.comment else ''
        product_brand_ids = []
        support_warranty_info = ''
        for invoice_line in self.invoice_line_ids:
            product_brand_id = invoice_line.product_id.product_tmpl_id.product_brand_id.id \
                if invoice_line.product_id.product_tmpl_id.product_brand_id else None
            product_brand_ids.append(product_brand_id)
        product_brand_fixed_ids = list(set(product_brand_ids))
        product_brands = self.env['product.brand'].search_read([('id', 'in', product_brand_fixed_ids)])
        if len(product_brands) > 0:
            warranty_info_list = [pd['support_warranty_info'] for pd in product_brands if len(pd['support_warranty_info']) > 0]
            if warranty_info_list and len(warranty_info_list) > 0:
                support_warranty_info = "\n".join(warranty_info_list)
        if len(support_warranty_info) > 0:
            if not support_warranty_info in comment:
                comment = "{0}\n{1}".format(comment, support_warranty_info)
            self.write({'comment': comment})
        return invoice

    def get_commission_by_line(self, payment_term_id, category, invoice_line):
        commission = self.env['ancon.commission'].search([
            ('payment_term_id', '=', payment_term_id),
            ('category_id', '=', category.id)])
        if not commission:
            if category.parent_id:
                self.get_commission_by_line(
                    payment_term_id=payment_term_id, category=category.parent_id, invoice_line=invoice_line)
        else:
            total = invoice_line.price_subtotal*(commission.percentage/100)
            invoice_line.write({
                'commission_percentage': commission.percentage,
                'commission_total': total,
                'commission_id': commission.id
                })

    @api.multi
    def action_invoice_paid(self):
        res = super(AccountInvoice, self).action_invoice_paid()
        if self.state:
            if 'paid' in self.state:
                payment_term_id = self.payment_term_id.id if self.payment_term_id else None
                if payment_term_id:
                    if len(self.invoice_line_ids) > 0:
                        for invoice_line in self.invoice_line_ids:
                            category_id = invoice_line.product_id.product_tmpl_id.categ_id if invoice_line.product_id.product_tmpl_id \
                                and invoice_line.product_id.product_tmpl_id.categ_id else None
                            self.get_commission_by_line(
                                payment_term_id=payment_term_id, category=category_id, invoice_line=invoice_line)
        return res

    @api.multi
    def action_credit_note_request_approve(self):
        for invoice in self:
            invoice.write({'credit_note_state': 'approved'})
        return True

    @api.multi
    def action_credit_note_request(self):
        for invoice in self:
            invoice.write({'credit_note_state': 'pending'})
        return True

    @api.multi
    def action_credit_note_request_reject(self):
        for invoice in self:
            invoice.write({'credit_note_state': 'draft'})
        return True


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'
    commission_id = fields.Many2one(
        'ancon.commission',
        string='Comisión',
        required=False,
        default=None)
    commission_percentage = fields.Float(
        string='Porcentaje de Comisión',
        default=0.00)
    commission_total = fields.Float(
        string='Monto de comisión',
        default=0.00)
    vendor_id = fields.Char(
        string='Vendedor',
        related='invoice_id.user_id.name')
    custom_discount = fields.Float(
        string='Descuento',
        default=0.00)

    # @api.one
    # @api.depends('price_unit', 'discount', 'invoice_line_tax_ids', 'quantity',
    #     'product_id', 'invoice_id.partner_id', 'invoice_id.currency_id', 'invoice_id.company_id',
    #     'invoice_id.date_invoice', 'invoice_id.date')
    # def _compute_price(self):
    #     self.compute_custom_discount()
    #     invoice_line = super(AccountInvoiceLine, self)._compute_price()
    #     product_brand_ids = []
    #     support_warranty_info = ''
    #     for invoice_line in self.invoice_id.invoice_line_ids:
    #         product_brand_id = invoice_line.product_id.product_tmpl_id.product_brand_id.id \
    #             if invoice_line.product_id.product_tmpl_id.product_brand_id else None
    #         product_brand_ids.append(product_brand_id)
    #     product_brand_fixed_ids = list(set(product_brand_ids))
    #     product_brands = self.env['product.brand'].search_read([('id', 'in', product_brand_fixed_ids)])
    #     if len(product_brands) > 0:
    #         warranty_info_list = [pd['support_warranty_info'] for pd in product_brands if len(pd['support_warranty_info']) > 0]
    #         if warranty_info_list and len(warranty_info_list) > 0:
    #             support_warranty_info = "\n".join(warranty_info_list)
    #     self.invoice_id.comment = support_warranty_info
    #     product_price = self.product_id.product_tmpl_id.list_price
    #     if 'in_invoice' in self.invoice_id.type:
    #         product_price = self.product_id.product_tmpl_id.standard_price
    #     if self.price_unit < product_price:
    #         raise ValidationError('El monto ${0:.2f} del producto {1} no puede ser menor de ${2:.2f}'.format(
    #             self.price_unit, self.name, product_price))

    # @api.one
    # @api.model
    # def compute_custom_discount(self):
    #     price_subtotal = self.quantity * self.price_unit
    #     percentage = 0.00
    #     if price_subtotal > 0 and self.custom_discount > 0:
    #         percentage = (self.custom_discount/price_subtotal) * 100
    #     self.discount = percentage

    # @api.model
    # def create(self, vals):
    #     invoice_line = super(AccountInvoiceLine, self).create(vals)
    #     invoice_line.compute_custom_discount()
    #     return invoice_line

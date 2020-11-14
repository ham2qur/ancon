# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import date
import logging
_logger = logging.getLogger(__name__)


class AccountPayment(models.Model):
    _inherit = ['account.payment']

    communication=fields.Char(string='Memo', readonly=True)

    @api.model
    def _get_order_id_domain_filter(self):
        payment_term_ids = self.env['account.payment.term'].search_read([('payment_term_type', 'like', 'credit_payment')], {'fields': ['id']})
        ids = [i['id'] for i in payment_term_ids if i['id'] > 0]
        return [('state', 'like', 'sale'), ('payment_term_id', 'in', ids), ('invoice_status','like', 'to invoice')]

    sale_order_id = fields.Many2one(
        'sale.order',
        compute='_sale_orders_by_partner_id',
        string='Presupuesto asociado',
        default=None,
        required=False,
        readonly=False,
        stored=True,
    #    domain=_get_order_id_domain_filter
        )

    @api.model
    def create(self, vals):
        account_payment = super(AccountPayment, self).create(vals)
        amount = vals['amount']
        # if amount < 5.00:
        #     raise ValidationError('El monto del pago / abono es muy pequeño, solo se permiten pagos mayores o igual a $5.00')
        if 'sale_order_id' in vals:
            sale_order_id = vals['sale_order_id']
            if sale_order_id:
                counter = self.env['account.payment'].search_count([
                    ('sale_order_id', '=', sale_order_id),
                    ('id', 'not in', [account_payment.id])])
                if counter < 1:
                    sale_order = self.env['sale.order'].browse(sale_order_id)
                    if 'to invoice' in sale_order.invoice_status and 'sale' in sale_order.state and 'credit_payment' in sale_order.payment_term_id.payment_term_type:
                        sale_order.write({
                            'first_payment_date': date.today()})
        return account_payment


    @api.onchange('partner_id')
    def _sale_orders_by_partner_id(self):
        res = {}
        if self.partner_id:
            res['domain'] = {'sale_order_id': [('partner_id', '=', self.partner_id.id)]}
        return res
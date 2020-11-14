# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError
import logging
_logger = logging.getLogger(__name__)


class AnconCommission(models.Model):
    _name = 'ancon.commission'
    percentage = fields.Float(
        string='Porcentaje de comisión',
        required=True)
    category_id = fields.Many2one(
        'product.category', 'Categoría',
        required=True)
    payment_term_id = fields.Many2one(
        'account.payment.term',
        string='Plazo de pago',
        required=True)

    @api.model
    def create(self, vals):
        commission = super(AnconCommission, self).create(vals)
        category_id = vals['category_id']
        payment_term_id = vals['payment_term_id']
        percentage = vals['percentage']
        if self._category_id_exists(category_id, payment_term_id):
            raise ValidationError('Ya existe una comisión con la misma categoría y plazo de pago')
        if percentage <= 0:
            raise ValidationError('El monto del porcentaje debe ser mayor a 0')
        return commission

    @api.multi
    def write(self, vals):
        commission = super(AnconCommission, self).write(vals)
        category_id = vals['category_id'] if 'category_id' in vals else self.category_id.id
        payment_term_id = vals['payment_term_id'] if 'payment_term_id' in vals else self.payment_term_id.id
        percentage = vals['percentage'] if 'percentage' in vals else self.percentage
        if self._category_id_exists(category_id, payment_term_id):
            raise ValidationError('Ya existe una comisión con la misma categoría y plazo de pago')
        if percentage <= 0:
            raise ValidationError('El monto del porcentaje debe ser mayor a 0')
        return commission

    @api.multi
    def unlink(self):
        for commission in self:
            counter = self.env['account.invoice.line'].search_count([('commission_id', '=', commission.id)])
            if counter > 0:
                raise UserError("No puede eliminar esta comisión ya que tiene facturas asociadas con estatus 'PAGADO'")
        return super(AnconCommission, self).unlink()

    def _category_id_exists(self, category_id, payment_term_id):
        c = self.env['ancon.commission'].search_count([
            ('category_id', '=', category_id), ('payment_term_id', '=', payment_term_id)])
        c -= 1
        return True if c > 0 else False

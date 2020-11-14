# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError
import logging
_logger = logging.getLogger(__name__)


class ResCompany(models.Model):
    _inherit = "res.company"
    ruc = fields.Char(
        string='RUC',
        related='partner_id.ruc',
        inverse='_inverse_ruc',
        compute='_get_ancon_parnter_info')
    dv = fields.Char(
        string='DV',
        related='partner_id.dv',
        inverse='_inverse_dv',
        compute='_get_ancon_parnter_info')

    def _get_ancon_parnter_info(self, partner):
        return {
            'ruc': partner.ruc,
            'dv': partner.dv
        }

    def _inverse_ruc(self):
        for company in self:
            company.partner_id.ruc = company.ruc
    
    def _inverse_dv(self):
        for company in self:
            company.partner_id.dv = company.dv

    @api.model
    def create(self, vals):
        if 'street' in vals:
            if not vals['street'] or (vals['street'] and len(vals['street']) <= 0):
                vals.pop('street', None)
        partner = self.env['res.partner'].create(vals)
        if partner:
            vals['partner_id'] = partner.id
        company = super(ResCompany, self).create(vals)
        return company

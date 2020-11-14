# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError
import logging
_logger = logging.getLogger(__name__)


HOME_TYPES = [
    ('edificio',"Edificio"),
    ('casa',"Casa"),
]


class ResPartner(models.Model):
    _name = 'res.partner'
    _inherit = 'res.partner'
    reference = fields.Char(
        string='Referencia del lugar',
        required=False,
        translate=True)
    home_type = fields.Selection(
        HOME_TYPES,
        string='Tipo de lugar',
        required=False,
        default='casa')
    home_number = fields.Char(
        string='Numero de lugar',
        required=False,
        default=None)

    def _check_fields_required(self, vals):
        errors = []
        if 'email' in vals:
            if vals['email']:
                import re
                match = re.match('^[_a-z0-9-]+(\.[_a-z0-9-]+)*@[a-z0-9-]+(\.[a-z0-9-]+)*(\.[a-z]{2,4})$', vals['email'])
                if match == None:
                    errors.append('El Email tiene un formato inválido, formado esperado: "example@domain.com"')
        if len(errors) > 0:
            raise ValidationError("\n".join(errors))

    def _check_ruc_exists(self, vals, pk=0):
        """
        Check if the ruc exists before to create / write
        """
        if 'ruc' in vals:
            if vals['ruc']:
                ruc = vals.get('ruc', False)
                if ruc:
                    ruc = ruc.replace('-', '') if '-' in ruc else ruc
                    ruc = ruc.replace(" ", '') if " " in ruc else ruc
                    if pk > 0:
                        counter = self.env['res.partner'].search_count([('ruc', '=', ruc), ('id', '!=', pk)])
                    else:
                        counter = self.env['res.partner'].search_count([('ruc', '=', ruc)])
                    if counter > 0:
                        raise ValidationError('El RUC ya se encuentra registrado en otra cuenta.')

    @api.model
    def create(self, vals):
        self._check_ruc_exists(vals=vals)
        if 'ruc' in vals:
            ruc = vals.get('ruc', False)
            if ruc:
                ruc = ruc.replace('-', '') if '-' in ruc else ruc
                ruc = ruc.replace(" ", '') if " " in ruc else ruc
                vals['ruc'] = ruc
        partner = super(ResPartner, self).create(vals)
        self._check_fields_required(vals=vals)
        return partner

    @api.multi
    def write(self, vals):
        if 'ruc' in vals:
            ruc = vals.get('ruc', False)
            if ruc:
                ruc = ruc.replace('-', '') if '-' in ruc else ruc
                ruc = ruc.replace(" ", '') if " " in ruc else ruc
                vals['ruc'] = ruc
        partner = super(ResPartner, self).write(vals)
        self._check_fields_required(vals=vals)
        self._check_ruc_exists(vals=vals, pk=self.id)
        return partner

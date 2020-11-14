# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError
import logging
_logger = logging.getLogger(__name__)


class AnconDeliveryZone(models.Model):
    _name = 'ancon.delivery.zone'
    name = fields.Char(string='Nombre')
    description = fields.Text(string='Descripción (Días y Horarios de entrega)')
    country_id = fields.Many2one(
        'res.country',
        string='País',
        required=False,
        translate=True,
        default=lambda self: self._get_country_id())
    sector_ids = fields.Many2many(
        'neonety.sector',
        string='Corregimientos')

    @api.model
    def _get_country_id(self):
        self._cr.execute("SELECT id FROM res_country WHERE code LIKE 'PA' LIMIT 1")
        country_id = self._cr.fetchone()
        return country_id

    @api.onchange('sector_ids')
    def onchange_sector_ids(self):
        res = {}
        for sector in self.sector_ids:
            counter = self.env['ancon.delivery.zone'].search_count([('sector_ids', 'in', [sector.id])])
            if counter > 0:
                raise ValidationError("El sector {0} ya ha sido asignado a otra Ruta de Entrega.".format(sector.name))
        return res

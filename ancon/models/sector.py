# -*- coding: utf-8 -*-
from odoo import models, fields, api
import logging
_logger = logging.getLogger(__name__)


class NeonetySector(models.Model):
    _inherit = 'neonety.sector'
    _rec_name = 'full_name'
    full_name = fields.Char(
        string='Nombre completo',
        compute='_get_full_name',
        store=True)

    @api.depends('province_id', 'district_id', 'name')
    @api.one
    def _get_full_name(self):
        self.full_name = '{0} / {1} / {2}'.format(
            self.province_id.name, self.district_id.name, self.name)



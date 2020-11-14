# -*- coding: utf-8 -*-
from odoo import models, fields, api
import logging
_logger = logging.getLogger(__name__)


class ProductBrand(models.Model):
    _inherit = 'product.brand'

    support_warranty_info = fields.Text(
        string='Información para soporte y garantía',
        required=False,
        default='')

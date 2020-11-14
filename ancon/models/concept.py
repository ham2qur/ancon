# -*- coding: utf-8 -*-
from odoo import models, fields, api
import logging
_logger = logging.getLogger(__name__)


CONCEPT_TYPES = [
    (1,"Costo"),
    (2,"Gasto"),
]


class NeonetyPartnerConcept(models.Model):
    _inherit = 'neonety.partner.concept'
    code = fields.Char(
        string='Código',
        size=20,
        required=True,
        translate=True,
        unique=True)
    type = fields.Selection(
        CONCEPT_TYPES,
        string='Tipo de Concepto',
        required=False,
        default=None)

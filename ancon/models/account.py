# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError
from datetime import date, datetime
import logging
_logger = logging.getLogger(__name__)


class AccountTax(models.Model):
    _inherit = 'account.tax'

    is_withholding_tax = fields.Boolean(
        string='Usar como retención de impuestos',
        default=False
    )


class AccountAccount(models.Model):
    _inherit = 'account.account'

    partner_concept_id = fields.Many2one(
        'neonety.partner.concept',
        string='Concepto del Proveedor',
        default=None)


class AccountJournal(models.Model):
    _inherit = 'account.journal'

    x_porcentaje_comision = fields.Float("Porcentaje de comision", store=True, copy=True)

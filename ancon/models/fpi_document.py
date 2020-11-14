# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError
from datetime import date, datetime
import logging
_logger = logging.getLogger(__name__)


class FpiDocument(models.Model):
    _inherit = 'fpi.document'

    @api.model
    def create(self, vals):
        document = super(FpiDocument, self).create(vals)
        if hasattr(document, 'invoice_id'):
            invoice = document.invoice_id
            # custom_discount = 0.00
            # for invoice_line in invoice.invoice_line_ids:
            #     if hasattr(invoice_line, 'custom_discount'):
            #         custom_discount += invoice_line.custom_discount
            document.discount_total = invoice.amount_discount
        return document

# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import date, datetime, timedelta
import logging
_logger = logging.getLogger(__name__)


class ProcurementGroup(models.Model):
    """
    Override the default procurement.group model
    Adding a warehouse to group by warehouse when a sale.order is created with different warehouses.
    """
    _name = 'procurement.group'
    _inherit = 'procurement.group'

    stock_warehouse_id = fields.Many2one(
        'stock.warehouse',
        string='Almacen')

# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError
import logging
_logger = logging.getLogger(__name__)


class StockQuant(models.Model):
    _name = 'stock.quant'
    _inherit = 'stock.quant'

    @api.multi
    def name_get(self):
        res = []
        for sq in self:
            warehouse = self.env['stock.warehouse'].search([('lot_stock_id', '=', sq.location_id.id)], limit=1)
            stock = sq.quantity - sq.reserved_quantity
            res.append((sq.id, '{0} ({1})'.format(warehouse.name, round(stock))))
        return res

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        recs = self.browse()
        if name:
            names = self.env['stock.warehouse'].search_read([('name', 'ilike', name)], fields=['lot_stock_id'])
            items = [i['lot_stock_id'][0] for i in names]
            if len(items) > 0:
                recs = self.search([('location_id.id', 'in', items)] + args, limit=limit)
        if not recs:
            recs = self.search([('location_id.name', operator, name)] + args, limit=limit)
        return recs.name_get()

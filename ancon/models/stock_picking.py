# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError
import logging
_logger = logging.getLogger(__name__)

class Picking(models.Model):
    _inherit = 'stock.picking'

    factura = fields.Char(
        'Factura relacionada',
        default = 0.0,
        readonly = True
        )



    # @api.depends('invoice_related','origin')
    # def get_width_default(self):
    #     print(self.invoice_related)
    #     REPLACE DOMAIN WITH SOMETHING RELEVANT
    #     domain = ["origin","=","SO349"]
    #     res = self.env['account.invoice'].browse('origin','ilike','SO349')
    #     res= self.invoice_related
    #     for invoice in self.invoice_related:
    #         if invoice.origin == 'SO349':
    #             print(invoice.id)
    #     x = res.browse(['origin','ilike','SO349'])
    #     print (test)

    # _defaults = {
    #     'factura': 0.0,
    # }


    # invoice_related = fields.Many2one(
    #     'account.invoice',
    #     'Factura relacionada',
    #     default=get_width_default,
    #     stored=True,
    #     readonly=False,
    #     domain=["origin","=","SO349"]
    #     )


# def _get_width_default(self): 
#     #REPLACE DOMAIN WITH SOMETHING RELEVANT
#     domain = []
#     res = self.env['sale.order.line.width'].search(domain)
#     _logger.info("PREPARING DEFAULT VALUE")
#     _logger.info(res)
#     return res[0].id or False

# width_id = fields.many2one('sale.order.line.width',default=_get_width_default)
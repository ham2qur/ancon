# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from odoo.tools import float_compare
from datetime import date, datetime, timedelta
import logging
_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = 'sale.order'
    canceled_at = fields.Date(
        string='Cancelado en',
        required=False,
        default=None)
    notified_at = fields.Date(
        string='Notificar en',
        required=False,
        default=None)
    first_payment_date = fields.Date(
        string='Fecha del primer abono',
        required=False,
        default=None)

    custom_discount = fields.Float(
        string='Descuento',
        default=0.00)
        
    state = state = fields.Selection([
        ('draft', 'Quotation'),
        ('approved','Aprobado'),
        ('pending', 'Pendiente de Aprobación'),
        ('sent', 'Quotation Sent'),
        ('sale', 'Sales Order'),
        ('done', 'Locked'),
        ('cancel', 'Cancelled')])
    
    def get_user_id(self):
        #print(self.env['res_store'].search(['id', '=', self.env['res.users'].browse(['id','=',self.current_user]).store_id])
        return self.env.uid
    
    current_user = fields.Many2one('res.users','Current User', default=get_user_id) 

    def get_user_store_id(self):
        store = self.env['res.users'].search([('id','=',self.env.uid)])
        print(store.store_id)
        for x in store:
            print(x)
        return store.store_id

    @api.multi
    @api.depends('res.users')
    def get_warehouse_id_default(self):
        related_warehouse_id = self.env['stock.warehouse'].search(['store_id', '=', self.env['res.users'].browse(['id','=',self.current_user])])
        print(related_warehouse_id)

    warehouse_id = fields.Many2one(
        'stock.warehouse',
        string='Warehouse',
        #default=_get_warehouse_id_default
    )

    # store_id = fields.Integer(string='Store ID', readonly=False)

    partner_ruc = fields.Char(
        string='RUC',
        related='partner_id.ruc',
        inverse='_inverse_ruc',
        compute='_get_ancon_parnter_info')

    def _get_ancon_parnter_info(self, partner):
        return {
            'partner_ruc': partner.ruc}

    def _inverse_ruc(self):
        for sale_order in self:
            sale_order.partner_id.ruc = sale_order.partner_ruc

    @api.model
    def create(self, vals):
        note = '' if not 'note' in vals else vals['note']
        if 'partner_id' in vals:
            partner_id = self.env['res.partner'].browse(vals['partner_id'])
            if partner_id:
                if hasattr(partner_id, 'sector_id'):
                    delivery_zones = self.env['ancon.delivery.zone'].search_read([
                        ('sector_ids', 'in', [partner_id.sector_id.id])], fields=['id', 'name', 'description'])
                    if len(delivery_zones) > 0:
                        delivery_info = "\n"
                        for dz in delivery_zones:
                            delivery_info += 'Ruta de entrega: {0}, información: {1}'.format(dz['name'], dz['description'])
                        note = '{0}{1}'.format(note, delivery_info)
        vals['note'] = note
        return super(SaleOrder, self).create(vals)

    @api.multi
    def write(self, vals):
        if 'first_payment_date' in vals:
            if vals['first_payment_date']:
                first_payment_date = vals['first_payment_date']
                date_obj = None
                if 'str' in first_payment_date.__class__.__name__:
                    date_obj = datetime.strptime(vals['first_payment_date'], '%Y-%m-%d')
                elif 'date' in first_payment_date.__class__.__name__:
                    date_obj = first_payment_date
                if date_obj:
                    vals['canceled_at'] = date_obj + timedelta(days=90)
                    vals['notified_at'] = date_obj + timedelta(days=80)
        return super(SaleOrder, self).write(vals)

    def _check_order_available_to_send(self, type):
        pass
        # has_discount_products = 0
        # counter = 0
        # for line in self.order_line:
        #     if line.custom_discount > 0:
        #         counter += 1
        # if counter > 0 and not 'approved' in self.state:
        #     raise ValidationError(
        #         "No es posible {0}, Necesita solicitar aprobación o eliminar el descuento.".format(type))

    @api.multi
    def action_confirm(self):
        self._check_order_available_to_send("Confirmar el presupuesto")
        return super(SaleOrder, self).action_confirm()

    @api.multi
    def action_reject(self):
        self.action_cancel()
        self.action_draft()

    @api.multi
    def action_by_approve(self):
        return self.write({'state': 'pending'})

    @api.multi
    def action_approve(self):
        return self.write({'state': 'approved'})

    @api.multi
    def print_quotation(self):
        self._check_order_available_to_send("Imprimir")
        return super(SaleOrder, self).print_quotation()

    @api.multi
    def action_quotation_send(self):
        self._check_order_available_to_send("Enviar por correo")
        return super (SaleOrder, self).action_quotation_send()


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'
    custom_discount = fields.Float(
        string='Descuento',
        default=0.00)
    stock_quant_id = fields.Many2one(
        'stock.quant',
        string='Existencia en almacenes')
    
    procurement_group_id = fields.Many2one(
        'procurement.group', 'Procurement Group', copy=False)

    current_user = fields.Many2one('res.users','Current User', default=lambda self: self.env.user.id)

    # @api.multi
    # @api.depends('res.users')
    # def _get_sel_warehouse_default(self):
    #     related_model_id = self.env['stock.warehouse'].browse(['store_id', '=', self.env['res.users'].browse(['id','=','current_user.id'])])
    #     return related_model_id


    sel_warehouse = fields.Many2one(
        'stock.warehouse',
        string='Selecionar almacen'
        #,default = _get_sel_warehouse_default
        )


    @api.depends('product_id')
    @api.onchange('product_id')
    def _onchange_product_id(self):
        """
        Method added to return the stock.quants objects list related with a product selected.
        """
        res = {}
        if self.product_id:
            res['domain'] = {'stock_quant_id': [
                ('product_id', '=', self.product_id.id),
                ('company_id', '!=', None),
                ('quantity', '>', 0)
            ]}
        return res

    # @api.one
    # @api.model
    # def compute_custom_discount(self):
    #     price_subtotal = self.product_uom_qty * self.price_unit
    #     percentage = 0.00
    #     if price_subtotal > 0 and self.custom_discount > 0:
    #         percentage = (self.custom_discount/price_subtotal) * 100
    #     self.discount = percentage

    @api.depends('product_uom_qty', 'discount', 'price_unit', 'tax_id')
    def _compute_amount(self):
        order_line = super(SaleOrderLine, self)._compute_amount()
        for line in self:
            price_subtotal = line.product_uom_qty * line.price_unit
            if line.price_unit < line.product_id.product_tmpl_id.list_price:
                raise ValidationError('El monto ${0:.2f} del producto {1} no puede ser menor de ${2:.2f}'.format(
                    line.price_unit, line.name, line.product_id.product_tmpl_id.list_price))
            price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            taxes = line.tax_id.compute_all(price, line.order_id.currency_id, line.product_uom_qty, product=line.product_id, partner=line.order_id.partner_shipping_id)
            line.update({
                'price_tax': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
                'price_total': taxes['total_included'],
                'price_subtotal': taxes['total_excluded'],
                'discount': line.discount
            })

    # @api.multi
    # def _prepare_invoice_line(self, qty):
    #     res = super(SaleOrderLine, self)._prepare_invoice_line(qty)
    #     res['custom_discount'] = self.custom_discount
    #     return res

#'product_uom_qty', 'product_uom', 'route_id'
    # @api.onchange('stock_quant_id')
    # def _onchange_product_id_check_availability(self):
    #     """
    #     Override default method _onchange_product_id_check_availability() to check the producs available on any warehouse.
    #     """
    #     if not self.product_id or not self.product_uom_qty or not self.product_uom:
    #         self.product_packaging = False
    #         return {}
    #     if self.product_id.type == 'product':
    #         precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
    #         # START CODE fix to check the warehouse related with the sale.order.line selected.
    #         sw = self.env['stock.warehouse'].browse(self.stock_quant_id.id)
    #         product = self.product_id.with_context(warehouse=sw.id)
    #         # END CODE fix to check the warehouse related with the sale.order.line selected.
    #         product_qty = self.product_uom._compute_quantity(self.product_uom_qty, self.product_id.uom_id)
    #         if float_compare(product.virtual_available, product_qty, precision_digits=precision) == -1:
    #             is_available = self._check_routing()
    #             if not is_available:
    #                 # START CODE fix to display the producs available by the sale.order.line and warehouse selected..
    #                 message =  _('You plan to sell %s %s but you only have %s %s available in %s warehouse.') % \
    #                         (self.product_uom_qty, self.product_uom.name, product.virtual_available, product.uom_id.name, sw.name)
    #                 # END CODE fix to display the producs available by the sale.order.line and warehouse selected..
    #                 if float_compare(product.virtual_available, self.product_id.virtual_available, precision_digits=precision) == -1:
    #                     message += _('\nThere are %s %s available accross all warehouses.') % \
    #                             (self.product_id.virtual_available, product.uom_id.name)
    #                 warning_mess = {
    #                     'title': _('Not enough inventory!'),
    #                     'message' : message
    #                 }
    #                 return {'warning': warning_mess}
    #     return {}

    # @api.multi
    # def _action_launch_procurement_rule(self):
    #     """
    #     Override the default method _action_launch_procurement_rule() adjusting the logic
    #     to generate group_id depending from the warehouse used on each sale.order.line.
    #     file found:
    #     sale_stock/models/sale_order.py > SaleOrderLine > _action_launch_procurement_rule() (Line: 225)
    #     """
    #     precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
    #     errors = []
    #     for line in self:
    #         if line.state != 'sale' or not line.product_id.type in ('consu','product'):
    #             continue
    #         qty = 0.0
    #         for move in line.move_ids.filtered(lambda r: r.state != 'cancel'):
    #             qty += move.product_uom._compute_quantity(move.product_uom_qty, line.product_uom, rounding_method='HALF-UP')
    #         if float_compare(qty, line.product_uom_qty, precision_digits=precision) >= 0:
    #             continue
    #         ### START CODE multiple warehouses on the same sale.order
    #         location_id = line.stock_quant_id.view_location_id.id or False
    #         if location_id:
    #             group_id = self.env['procurement.group'].search([
    #                 ('stock_warehouse_id.lot_stock_id', '=', location_id), ('sale_id', '=', line.order_id.id)], limit=1)
    #             if not group_id:
    #                 sw = self.env['stock.warehouse'].search([('lot_stock_id', '=', location_id)], limit=1)
    #                 group_values = {
    #                     'name': line.order_id.name,
    #                     'move_type': line.order_id.picking_policy,
    #                     'sale_id': line.order_id.id,
    #                     'partner_id': line.order_id.partner_shipping_id.id,
    #                     'stock_warehouse_id': sw.id}
    #                 group_id = self.env['procurement.group'].create(group_values)
    #             else:
    #                 updated_vals = {}
    #                 if group_id.partner_id != line.order_id.partner_shipping_id:
    #                     updated_vals.update({'partner_id': line.order_id.partner_shipping_id.id})
    #                 if group_id.move_type != line.order_id.picking_policy:
    #                     updated_vals.update({'move_type': line.order_id.picking_policy})
    #                 if updated_vals:
    #                     group_id.write(updated_vals)
    #             ### END CODE multiple warehouses on the same sale.order
    #             values = line._prepare_procurement_values(group_id=group_id)
    #             product_qty = line.product_uom_qty - qty
    #             procurement_uom = line.product_uom
    #             quant_uom = line.product_id.uom_id
    #             get_param = self.env['ir.config_parameter'].sudo().get_param
    #             if procurement_uom.id != quant_uom.id and get_param('stock.propagate_uom') != '1':
    #                 product_qty = line.product_uom._compute_quantity(product_qty, quant_uom, rounding_method='HALF-UP')
    #                 procurement_uom = quant_uom
    #             try:
    #                 self.env['procurement.group'].run(
    #                     line.product_id, product_qty, procurement_uom, line.order_id.partner_shipping_id.property_stock_customer,
    #                     line.name, line.order_id.name, values)
    #                 line.write({'procurement_group_id': group_id.id})
    #             except UserError as error:
    #                 errors.append(error.name)
    #     if errors:
    #         raise UserError('\n'.join(errors))
    #     # START CODE update the location and company info to each stock.picking related with the line.procurement.group.id
    #     for line in self:
    #         if line.procurement_group_id:
    #             if line.procurement_group_id.stock_warehouse_id:
    #                 warehouse_id = line.procurement_group_id.stock_warehouse_id.id
    #                 warehouse_location_id = line.procurement_group_id.stock_warehouse_id.lot_stock_id.id
    #                 spt = self.env['stock.picking.type'].search([
    #                     ('warehouse_id', '=', warehouse_id), 
    #                     ('default_location_src_id', '=', warehouse_location_id),
    #                     ('default_location_dest_id', '=', None),
    #                     ('code', 'like', 'outgoing')], limit=1)
    #                 sp = self.env['stock.picking'].search([('group_id', '=', line.procurement_group_id.id), ('sale_id', '=', line.order_id.id)])
    #                 sp.write({
    #                     'location_id': line.procurement_group_id.stock_warehouse_id.lot_stock_id.id, 'picking_type_id': spt.id})
    #     # END CODE update the location and company info to each stock.picking related with the line.procurement.group.id
    #     return True

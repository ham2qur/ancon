# -*- coding: utf-8 -*-
from odoo import models, fields, api, tools, _
from odoo.exceptions import ValidationError, UserError
from datetime import date, datetime
import logging
_logger = logging.getLogger(__name__)


class SaleOrderToCancelReport(models.Model):
    _name = 'ancon.sale.order.to.cancel.report'
    _auto = False
    _order = 'id'
    id = fields.Integer(
        string='ID',
        readonly=True)

    def init(self):
        tools.drop_view_if_exists(self._cr, 'ancon_sale_order_to_cancel_report')
        self._cr.execute("""
            CREATE OR REPLACE VIEW ancon_sale_order_to_cancel_report AS
            SELECT
                sale_order.id AS id
            FROM
                sale_order
                INNER JOIN account_payment_term
                    on account_payment_term.id = sale_order.payment_term_id
                        AND account_payment_term.payment_term_type LIKE 'credit_payment'
            WHERE
                sale_order.state LIKE 'sale'
                AND sale_order.invoice_status LIKE 'to invoice'
                AND sale_order.canceled_at = '{0}'
            ORDER BY
                sale_order.id
                        """.format(date.today().strftime('%Y-%m-%d')))

    @api.multi
    def cancel_sale_order(self):
        """
        Automatic task settings:
        Select the model "ancon.sale.order.to.cancel.report"
        type to task select "execute python code"
        on the textarea to add python code add: "model.cancel_sale_order()"
        """
        for sale_order in self.env['ancon.sale.order.to.cancel.report'].search_read([], {'fields': ['id']}):
            sale_order_id = sale_order['id']
            if sale_order_id and sale_order_id > 0:
                order = self.env['sale.order'].browse(sale_order_id)
                if order:
                    order.action_cancel()


class ReportDailySales(models.AbstractModel):
    _name = 'report.ancon.daily_sales_report_queryset'

    def _build_output(self, items, keyword_id, keyword_amount, keyword_name):
        """
        Build the default output as output formatted
        """
        results = {}
        distincts = []
        for i in items:
            if not i[keyword_id] in distincts:
                distincts.append(i[keyword_id])
        totals = {}
        for d in distincts:
            totals[d] = 0
            for i in items:
                if i[keyword_id] == d:
                    totals[d] += i[keyword_amount]
        output = {}
        objects_list = []
        for d in distincts:
            for i in items:
                if i[keyword_id] == d:
                    output[d] = {'name': i[keyword_name], 'total': totals[d]}
        for d in distincts:
            objects_list.append(output[d])
        total = 0
        for t in totals:
            total += totals[t]
        results['data'] = objects_list
        results['total'] = total
        return results


    @api.model
    def generate_data(self, start_on, end_on, user_id, get_store):
        """
        Building output data displayed on the Q-Web PDF report
        """
        data = {}
        if user_id and start_on and end_on and get_store:
            data['store_id'] = self.env['res.store'].browse(get_store)
            if not data['store_id']:
                data['store_id'] = self.env.user.store_id
            invoices = self.env['ancon.daily.sales.report'].search_read(
                [('store_id', '=', get_store), ('date_invoice', '>=', start_on), ('date_invoice', '<=', end_on)])
            invoices_total = 0
            for invoice in invoices:
                invoices_total += invoice['amount_total']
            data['invoices'] = invoices
            data['invoices_total'] = invoices_total
            payments = self.env['ancon.daily.sales.payments.report'].search_read(
                [('store_id', '=', get_store), ('date_invoice', '>=', start_on), ('date_invoice', '<=', end_on)])
            payments_output = self._build_output(
                items=payments, keyword_id='payment_journal_id', keyword_amount='payment_amount', keyword_name='journal_name')
            data['payments'] = payments_output.get('data', False)
            data['payments_total'] = payments_output.get('total', 0.00)
            ############################################################
            subtotals = self.env['ancon.daily.sales.payments.report'].search_read(
                [('store_id', '=', get_store), ('date_invoice', '>=', start_on), ('date_invoice', '<=', end_on)])
            subtotals_output = self._build_output(
                items=subtotals, keyword_id='payment_journal_id', keyword_amount='subtotal', keyword_name='journal_name')
            data['subtotals'] = subtotals_output.get('data', False)
            data['subtotals_total'] = subtotals_output.get('total', 0.00)
            ############################################################
            percentages = self.env['ancon.daily.sales.payments.report'].search_read(
                [('store_id', '=', get_store), ('date_invoice', '>=', start_on), ('date_invoice', '<=', end_on)])
            percentages_output = self._build_output(
                items=percentages, keyword_id='payment_journal_id', keyword_amount='percentage_amount', keyword_name='journal_name')
            data['percentages'] = percentages_output.get('data', False)
            data['percentages_total'] = percentages_output.get('total', 0.00)
            ############################################################
            taxes = self.env['ancon.daily.sales.taxes.report'].search_read(
                [('store_id', '=', get_store), ('date_invoice', '>=', start_on), ('date_invoice', '<=', end_on)])
            taxes_output = self._build_output(items=taxes, keyword_id='tax_id', keyword_amount='tax_amount', keyword_name='tax_description')
            data['taxes'] = taxes_output.get('data', False)
            data['taxes_total'] = taxes_output.get('total', 0.00)
        data['currency_precision'] = self.env.user.company_id.currency_id.decimal_places
        return data


    @api.multi
    def _get_report_values(self, docids, data=None):
        data = dict(data or {})
        data.update(self.generate_data(
            start_on=data.get('start_on', False),
            end_on=data.get('end_on', False),
            user_id=data.get('user_id', False),
            get_store=data.get('store_id', False)))
        return data


class DailySalesReportWizard(models.TransientModel):
    """
    Daily sales report Wizard form
    """
    _name = 'ancon.daily_sales_report_wizard'
    start_on = fields.Date(string=_('Fecha Inicial'), required=True)
    end_on = fields.Date(string=_('Fecha Final'), required=True)
    get_store = fields.Many2one('res.store', _('Store'))


    @api.depends('start_on')
    @api.onchange('end_on')
    def _onchangget_storee_end_on(self):
        if self.start_on and self.end_on:
            #start_on_obj = datetime.strptime(self.start_on, '%Y-%m-%d')
            #end_on_obj = datetime.strptime(self.end_on, '%Y-%m-%d')
            #if end_on_obj < start_on_obj:
            if self.end_on < self.start_on:
                raise ValidationError(_("La fecha es inválida, la Fecha Final no puede ser menor que la Fecha inicial"))

    @api.multi
    def generate_report(self):
        data = {}
        if (not self.env.user.company_id.logo):
            raise UserError(_("You have to set a logo or a layout for your company."))
        elif (not self.env.user.company_id.external_report_layout_id):
            raise UserError(_("You have to set your reports's header and footer layout."))
        if self.env.user:
            data['user_id'] = self.env.user.id
            if self.get_store:
                data['store_id'] = self.get_store.id
        if self.start_on:
            data['start_on'] = self.start_on
        if self.end_on:
            data['end_on'] = self.end_on
        return self.env.ref('ancon.daily_sales_report_action').report_action([], data=data)


class DailySalesReport(models.Model):
    """
    Daily sales report
    """
    _name = 'ancon.daily.sales.report'
    _auto = False
    _order = 'id asc'
    #id = fields.Integer(string='ID',readonly=True)
    #partner_id = fields.Integer(string='Partner ID',readonly=True)
    #write_uid = fields.Integer(string='Write UID',readonly=True)
    
    invoice_number = fields.Char(string=_('Invoice Number'),readonly=True)
    
    #state = fields.Char(string='Invoice State',readonly=True)
    #type = fields.Char(string='Invoice Type',readonly=True)
    
    partner_name = fields.Char(string=_('Partner Name'), readonly=True)
    #store_name = fields.Char(string='Store Name',readonly=True)
    journal_name = fields.Char(string=_('Método de Pago'), readonly=True)
    date_invoice = fields.Date(string=_('Date Invoice'), readonly=True)
    store_id = fields.Integer(string=_('Store ID'), readonly=True)
    amount_total = fields.Float(string=_('Amount Total'), readonly=True)
    
    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self._cr, 'ancon_daily_sales_report')
        self._cr.execute("""
            CREATE OR REPLACE VIEW ancon_daily_sales_report AS                                       
            select
                ap.id,
                case
                WHEN (ap.communication IS NULL) THEN 'ABONO'::CHARACTER VARYING
                ELSE ap.communication
                END AS invoice_number,
                rp.name as partner_name,
                aj.name as journal_name,
                am.date as date_invoice,
                am.store_id as store_id,
                ap.payment_type,
                CASE
                WHEN am.ref LIKE '%Inversa%' or ap.payment_type = 'outbound'
                THEN (round(((((am.amount)::DOUBLE PRECISION ))::NUMERIC), 2) * ('-1'::INTEGER)::NUMERIC)
                ELSE round(((((am.amount)::DOUBLE PRECISION ))::NUMERIC), 2)
                END AS amount_total
                FROM account_move am
                LEFT
                JOIN account_payment ap ON ap.move_name = am.name
                LEFT
                JOIN res_store rs ON rs.id = ap.store_id
                LEFT
                JOIN res_partner rp ON rp.id = am.partner_id
                LEFT JOIN account_journal aj ON aj.id = am.journal_id
                WHERE am.amount != 0  and aj.type in ('bank', 'cash') order by rp.name, amount_total
        """)


class DailySalesPaymentsReport(models.Model):
    """
    Daily sales report
    """
    _name = 'ancon.daily.sales.payments.report'
    _auto = False
    _order = 'payment_journal_id asc'
    #id = fields.Integer(string='ID',readonly=True)
    #invoice_id = fields.Integer(string='Invoice ID',readonly=True)
    payment_journal_id = fields.Integer(string='Payment Journal ID',readonly=True)
    #payment_write_uid = fields.Integer(string='Payment write UID',readonly=True)
    journal_name = fields.Char(string='Journal Name',readonly=True)
    subtotal = fields.Float(string='Subtotal',readonly=True)
    percentage_amount = fields.Float(string='Comisión',readonly=True)
    payment_amount = fields.Float(string='Payment Amount',readonly=True)
    store_id = fields.Integer(string='Store ID',readonly=True)
    #invoice_number = fields.Char(string='Invoice Number',readonly=True)
    date_invoice = fields.Date(string='Date Invoice',readonly=True)
    #store_name = fields.Char(string='Store Name',readonly=True)
    
    

    def init(self):
        tools.drop_view_if_exists(self._cr, 'ancon_daily_sales_payments_report')
        self._cr.execute("""
            CREATE OR REPLACE VIEW ancon_daily_sales_payments_report AS
                select
                    ap.id as id,
                    aj.id as payment_journal_id,
                    aj.name as journal_name,
                    sum(CASE 
                        WHEN am.ref LIKE '%Inversa%'
                        THEN (round(( (((am.amount)::DOUBLE PRECISION))::NUMERIC), 2) * ('-1'::INTEGER)::NUMERIC)
                        ELSE round(( (((am.amount)::DOUBLE PRECISION))::NUMERIC), 2)
                        END) as subtotal,
                    sum(CASE 
                        WHEN am.ref LIKE '%Inversa%'
                        THEN (round(((((am.amount)::DOUBLE PRECISION * aj.x_porcentaje_comision))::NUMERIC), 2) * ('-1'::INTEGER)::NUMERIC)
                        ELSE round(((((am.amount)::DOUBLE PRECISION * aj.x_porcentaje_comision))::NUMERIC), 2)
                        END) as percentage_amount,
                    sum(CASE 
                        WHEN am.ref LIKE '%Inversa%'
                        THEN (round((am.amount - (((am.amount)::DOUBLE PRECISION * aj.x_porcentaje_comision))::NUMERIC), 2) * ('-1'::INTEGER)::NUMERIC)
                        ELSE round((am.amount - (((am.amount)::DOUBLE PRECISION * aj.x_porcentaje_comision))::NUMERIC), 2)
                        END) as payment_amount,
                    am.store_id as store_id,
                    am.date as date_invoice
                    FROM account_move am 
                    LEFT 
                    JOIN account_payment ap ON ap.move_name = am.name
                    LEFT
                    JOIN res_store rs ON rs.id  = ap.store_id
                    LEFT
                    JOIN res_partner rp ON rp.id = am.partner_id
                    LEFT JOIN account_journal aj ON aj.id = am.journal_id
                    where aj.at_least_one_outbound = false
                    group by ap.id ,aj.id, aj.name, am.store_id, am.date
        
        """)


class DailySalesTaxesReport(models.Model):
    """
    Daily sales report
    """
    _name = 'ancon.daily.sales.taxes.report'
    _auto = False
    _order = 'id asc'
    id = fields.Integer(string='ID',readonly=True)
    tax_id = fields.Integer(string='Tax ID',readonly=True)
    write_uid = fields.Integer(string='Write UID',readonly=True)
    store_id = fields.Integer(string='Store ID',readonly=True)
    invoice_number = fields.Char(string='Invoice Number',readonly=True)
    date_invoice = fields.Date(string='Date Invoice',readonly=True)
    tax_description = fields.Char(string='Tax Description',readonly=True)
    tax_amount = fields.Float(string='Tax Amount',readonly=True)
    invoice_amount_tax = fields.Float(string='Invoice Amount Tax',readonly=True)
    store_name = fields.Char(string='Store Name',readonly=True)

    def init(self):
        tools.drop_view_if_exists(self._cr, 'ancon_daily_sales_taxes_report')
        self._cr.execute("""
            CREATE OR REPLACE VIEW ancon_daily_sales_taxes_report AS
            SELECT
                AI.id AS id,
                AIT.tax_id AS tax_id,
                AI.write_uid AS write_uid,
                RU.store_id AS store_id,
                AI.number AS invoice_number,
                AI.date_invoice AS date_invoice,
                ATAX.description AS tax_description,
                AIT.amount AS tax_amount,
                AI.amount_tax AS invoice_amount_tax,
                RS.name AS store_name
            FROM 
                account_invoice AI 
                INNER JOIN account_invoice_tax AIT ON AIT.invoice_id = AI.id
                INNER JOIN account_tax ATAX ON ATAX.id = AIT.tax_id
                INNER JOIN res_partner RP ON RP.id = AI.partner_id
                INNER JOIN res_users RU ON RU.id = AI.write_uid
                INNER JOIN res_store RS ON RS.id = RU.store_id
            WHERE 
                AI.state LIKE 'paid'
                AND AI.type  LIKE 'out_invoice'""")

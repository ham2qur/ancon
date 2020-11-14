# -*- coding: utf-8 -*-
from odoo import models, fields, api, osv, tools
from openerp.tools.translate import _
from odoo.exceptions import UserError, ValidationError, Warning
import logging
_logger = logging.getLogger(__name__)


PRINT_STATUS_TYPES = [
    ('incomplete', 'No ha sido impreso'),
    ('pending', 'Por imprimir'),
    ('in_progress', 'Imprimiendo...'),
    ('completed', 'Factura impresa'),
    ('failed', 'Impresión fallida')
]


class ErrorMessages:
    PRINTER_NOT_ASSIGNED = "No se ha podido imprimir el documento ya que el usuario no tiene una impresora fiscal asignada."
    PRINTING_IN_PROGRESS = 'La factura se encuentra en proceso de impresión'
    PRINTING_COMPLETED = 'El documento ya ha sido impreso por la impresora fiscal asignada, el mismo no se puede volver a imprimir.'
    PRINTING_DENIED = 'La Nota de Crédito no se puede imprimir debido a que la factura de venta todavia no ha sido impresa por la impresora fiscal asignada.'
    CANCEL_PRINTING_NOT_ALLOWED = "No se puede cancelar la impresión mientras este en proceso."
    PRINTING_NOT_ALLOWED = "No se puede imprimir esta factura en la impresora fiscal, su monto total es menor o igual a cero"


class FpiDocument(models.Model):
    _name = 'fpi.document'
    _inherit = 'fpi.document'
    invoice_id = fields.Many2one(
        'account.invoice',
        string='Factura de Venta',
        default=None,
        required=False)

    @api.multi
    def unlink(self):
        for document in self:
            if 'in_progress' in self.print_status:
                raise UserError(ErrorMessages.CANCEL_PRINTING_NOT_ALLOWED)
            else:
                if 'account_invoice' in document.documents_type_printed:
                    if document.invoice_id:
                        invoice = self.env['account.invoice'].browse(document.invoice_id.id)
                        if invoice:
                            invoice.write({'fpi_document_id': None})
        return super(FpiDocument, self).unlink()


class FpiInvoice(models.Model):
    _name = 'account.invoice'
    _inherit = 'account.invoice'
    fpi_document_id = fields.Many2one(
        'fpi.document',
        string='Impresión asociada',
        default=None,
        required=False)
    print_status = fields.Selection(
        PRINT_STATUS_TYPES,
        string='Estatus de la impresión',
        required=False,
        default='incomplete')
    print_filename_assigned = fields.Char(
        string='Nombre de impresión asignado',
        required=False,
        default=None,
        size=100)
    fiscal_printer_invoice_id = fields.Integer(
        string='Número de Factura Fiscal',
        default=0)
    document_print_status = fields.Selection(
        related='fpi_document_id.print_status')
    document_fiscal_invoice_number = fields.Integer(
        related='fpi_document_id.fiscal_invoice_number')

    @api.model
    def create(self, vals):
        obj = super(FpiInvoice, self).create(vals)
        obj.fpi_document_id = None
        return obj

    @api.one
    def send_fiscal_printer_action(self):
        if self.amount_total <= 0 and 'out_invoice' in self.type:
            raise UserError(ErrorMessages.PRINTING_NOT_ALLOWED)
        else:
            if self.fpi_document_id:
                if self.document_print_status in ['pending', 'in_progress']:
                    raise UserError(ErrorMessages.PRINTING_IN_PROGRESS)
                elif 'completed' in self.document_print_status and self.document_fiscal_invoice_number > 0:
                    raise UserError(ErrorMessages.PRINTING_COMPLETED)
            else:
                printer = self.env['fpi.printer'].search([('employee_id', '=', self.write_uid.id)])
                if not printer:
                    raise UserError(ErrorMessages.PRINTER_NOT_ASSIGNED)
                else:
                    parent_invoice_filename_assigned = None
                    parent_invoice_fiscal_printer_serial = None
                    parent_invoice_fiscal_invoice_number = 0
                    refund_type = None
                    refund_note = None
                    refund_date = None
                    refund_time = None
                    invoice_type = self.type
                    partner_address = None
                    if 'out_refund' in self.type:
                        invoice_parent = self.env['account.invoice'].search([('id', '=', self.refund_invoice_id.id)])
                        if invoice_parent.fpi_document_id:
                            if invoice_parent.document_fiscal_invoice_number == 0:
                                raise UserError(ErrorMessages.PRINTING_DENIED)
                            else:
                                parent_invoice_filename_assigned = invoice_parent.fpi_document_id.master_filename_assigned
                                parent_invoice_fiscal_printer_serial = invoice_parent.fpi_document_id.serial
                                parent_invoice_fiscal_invoice_number = invoice_parent.fpi_document_id.fiscal_invoice_number
                        else:
                            raise UserError(ErrorMessages.PRINTING_DENIED)
                        refund_info = self.env['account.invoice.refund'].search([('description', '=', self.name)])
                        if refund_info:
                            refund_type = refund_info.filter_refund
                            refund_note = refund_info.description
                            if refund_info.date_invoice:
                                refund_date_object = refund_info.date_invoice.split("-")
                                refund_date = "{0}/{1}/{2}".format(
                                    refund_date_object[2], refund_date_object[1], refund_date_object[0])
                            if refund_info.create_date:
                                import datetime
                                refund_time_object = datetime.datetime.strptime(refund_info.create_date, "%Y-%m-%d %H:%M:%S")
                                minute = str(refund_time_object.minute)
                                if refund_time_object.minute < 10:
                                    minute = '0{0}'.format(refund_time_object.minute)
                                refund_time = "{0}:{1}".format(refund_time_object.hour, minute)
                    partner_street = self.partner_id.street if self.partner_id.street else ""
                    partner_zip = self.partner_id.zip if self.partner_id.zip else ""
                    partner_province = self.partner_id.province_id.name if self.partner_id.province_id else ""
                    partner_district = self.partner_id.district_id.name if self.partner_id.district_id else ""
                    partner_sector = self.partner_id.sector_id.name.encode('utf-8') if self.partner_id.sector_id else ""
                    partner_country = self.partner_id.neonety_country_id.name if self.partner_id.neonety_country_id else ""
                    payments_total = 0.00
                    cash_payment_total = 0.00
                    bank_payment_total = 0.00
                    credit_card_payment_total = 0.00
                    debit_card_payment_total = 0.00
                    tax_percentage = 0.00
                    discount_total = 0.00
                    if len(self.payment_ids) > 0:
                        payments_total = sum( map(lambda x: x.amount, self.payment_ids))
                        cash_payment_total = sum( map(lambda x: x.amount if 'CSH1' in x.journal_id.code else 0.00, self.payment_ids))
                        bank_payment_total = sum( map(lambda x: x.amount if 'BNK1' in x.journal_id.code else 0.00, self.payment_ids))
                        credit_card_payment_total = sum( map(lambda x: x.amount if 'TC-' in x.journal_id.code[:3] else 0.00, self.payment_ids))
                        debit_card_payment_total = sum( map(lambda x: x.amount if 'TD-' in x.journal_id.code[:3] else 0.00, self.payment_ids))
                    invoice_tax = self.env['account.invoice.tax'].search([('invoice_id', '=', self.id)])
                    if invoice_tax:
                        tax_percentage = invoice_tax.tax_id.amount if invoice_tax.tax_id else 0.00
                    if len(self.invoice_line_ids) > 0:
                        for line in self.invoice_line_ids:
                            discount = (line.price_unit*line.discount)/100
                            discount_total = discount_total + discount
                    new_printer_obj = self.env['fpi.document'].create({
                        'user_id': self.write_uid.id,
                        'printer_id': printer.id,
                        'printer_serial_number': printer.serial,
                        'documents_type_printed': 'account_invoice',
                        'invoice_id': self.id,
                        'partner_name': self.partner_id.name,
                        'partner_ruc': self.partner_id.ruc if self.partner_id.ruc else 'N/D',
                        'partner_street': partner_street,
                        'partner_zip': partner_zip,
                        'partner_province': partner_province,
                        'partner_district': partner_district,
                        'partner_sector': partner_sector,
                        'partner_country': partner_country,
                        'payments_total': payments_total,
                        'cash_payment_total': cash_payment_total,
                        'bank_payment_total': bank_payment_total,
                        'credit_card_payment_total': credit_card_payment_total,
                        'debit_card_payment_total': debit_card_payment_total,
                        'amount_total': self.amount_total,
                        'amount_untaxed': self.amount_untaxed,
                        'amount_tax': self.amount_tax,
                        'tax_percentage': tax_percentage,
                        'discount_total': discount_total,
                        'parent_invoice_filename_assigned': parent_invoice_filename_assigned,
                        'parent_invoice_fiscal_invoice_number': parent_invoice_fiscal_invoice_number,
                        'parent_invoice_fiscal_printer_serial': parent_invoice_fiscal_printer_serial,
                        'refund_type': refund_type,
                        'refund_note': refund_note,
                        'invoice_type': invoice_type,
                        'refund_date': refund_date,
                        'refund_time': refund_time,
                        'number': self.number
                    })
                    if new_printer_obj and 'pending' in new_printer_obj.print_status:
                        self.fpi_document_id = new_printer_obj.id

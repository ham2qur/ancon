# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import datetime
import logging
_logger = logging.getLogger(__name__)


CREDIT_NOTE_STATES = [
    ('draft', 'Borrador'),
    ('pending', 'Pendiente de Aprobación'),
    ('approved', 'Solicitud Aprobada'),
    ('rejected', 'Solicitud Rechazada'),
]


class AnconCreditNote(models.Model):
    _name = 'ancon.credit.note'
    _order = 'invoice_id asc, id desc'

    @api.model
    def _get_invoice_id(self):
        context = dict(self._context or {})
        active_id = context.get('active_id', False)
        invoice_id = None
        if active_id:
            invoice = self.env['account.invoice'].browse(active_id)
            invoice_id = invoice
        return invoice_id

    invoice_id = fields.Many2one(
        'account.invoice',
        string='Factura',
        default=_get_invoice_id)
    state = fields.Selection(
        CREDIT_NOTE_STATES,
        string='Estado de la Solicitud',
        default='draft')
    reason = fields.Text(
        string='Motivo de la solicitud',
        required=False,
        default=None)
    reject_reason = fields.Text(
        string='Motivo de rechazo de la solicitud',
        required=False,
        default=None)
    requested_on = fields.Datetime(
        string='Solicitado el',
        required=False,
        default=None)
    approved_on = fields.Datetime(
        string='Aprobado el',
        required=False,
        default=None)
    rejected_on = fields.Datetime(
        string='Rechazado el',
        required=False,
        default=None)
    current_reason = fields.Text(
        string='Motivo de la solicitud',
        compute='_get_current_reason', readonly=True)
    current_id = fields.Text(
        string='ID de la solicitud anterior',
        compute='_get_current_reason', readonly=True)
    current_requested_on = fields.Datetime(
        string='Solicitado el',
        compute='_get_current_reason', readonly=True)
    current_state = fields.Selection(
        CREDIT_NOTE_STATES,
        string='Estado de la Solicitud',
        compute='_get_current_reason', readonly=True)

    @api.depends('invoice_id')
    def _get_current_reason(self):
        for credit_note in self:
            invoice_id = credit_note.invoice_id
            credit_note.update({
                'current_id': invoice_id.credit_note_last_id,
                'current_reason': invoice_id.credit_note_reason,
                'current_requested_on': invoice_id.credit_note_requested_on,
                'current_state': invoice_id.credit_note_state})

    @api.model
    def create(self, vals):
        invoice = self._get_invoice_id()
        if not 'invoice_id' in vals and invoice:
            vals['invoice_id'] = invoice.id
        if 'reject_reason' in vals:
            if hasattr(invoice, 'credit_note_reason'):
                vals['reason'] = invoice.credit_note_reason
            if hasattr(invoice, 'credit_note_requested_on'):
                vals['requested_on'] = invoice.credit_note_requested_on
            vals['state'] = 'rejected'
            vals['rejected_on'] = datetime.now()
            if hasattr(invoice, 'credit_note_last_id'):
                if invoice.credit_note_last_id:
                    credit_note = self.env['ancon.credit.note'].browse(invoice.credit_note_last_id)
                    credit_note.write({
                        'state': 'rejected',
                        'reject_reason': vals['reject_reason']})
        else:
            vals['state'] = 'pending'
            vals['requested_on'] = datetime.now()
        counter = self.env['ancon.credit.note'].search_count([
            ('invoice_id', '=', vals['invoice_id']),
            ('state', 'in', ['pending', 'approved'])])
        if counter > 0:
            raise ValidationError("Esta factura ya tiene una solicitud de garantía en proceso")
        if vals['state']:
            invoice.write({'cn_state': vals['state']})
        return super(AnconCreditNote, self).create(vals)

    @api.multi
    def write(self, vals):
        if 'state' in vals:
            if 'approved' in vals['state']:
                vals['approved_on'] = datetime.now()
            elif 'rejected' in vals['state']:
                vals['rejected_on'] = datetime.now()
        if vals['state']:
            self.invoice_id.write({'cn_state': vals['state']})
        return super(AnconCreditNote, self).write(vals)

    @api.multi
    def action_add_credit_note(self):
        return True

    @api.multi
    def action_credit_note_reject(self):
        return True

    @api.one
    def is_approved(self):
        return True if 'approved' in self.state else False

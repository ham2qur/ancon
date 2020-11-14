# -*- coding: utf-8 -*-
from odoo import models, fields, api, tools
import logging
_logger = logging.getLogger(__name__)


class FpiApiDocumentsInProgressList(models.Model):
    _name = 'fpi.documents.in.progress.list'
    _auto = False
    position = fields.Integer(string='Field', readonly=True)
    id = fields.Integer(string='Field', readonly=True)
    master_filename_assigned = fields.Char(string='Field', readonly=True)
    user_login = fields.Char(string='Field', readonly=True)
    fiscal_printer_serial = fields.Char(string='Field', readonly=True)

    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self._cr, 'fpi_documents_in_progress_list')
        self._cr.execute("""
            CREATE OR REPLACE VIEW fpi_documents_in_progress_list AS
            SELECT
                row_number() over() AS position,
                FD.id AS id,
                FD.master_filename_assigned AS master_filename_assigned,
                RU.login AS user_login,
                FP.serial AS fiscal_printer_serial
            FROM
                fpi_document FD
            INNER JOIN
                res_users RU
                ON RU.id = FD.write_uid
            INNER JOIN
                fpi_printer FP
                ON FP.id = FD.printer_id
            WHERE
                FD.print_status LIKE 'in_progress'
                AND FD.fiscal_invoice_number = 0""")
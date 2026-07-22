# Copyright (C) 2023 Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    audi_business_unit = fields.Char(string="Business Unit")
    audi_applicant_email = fields.Char(string="Applicant email")
    audi_flag = fields.Boolean(compute="_compute_audi_flag", store=True)
    audi_tax_code = fields.Char(string="Tax Code")
    audi_fiscal_document_type = fields.Char(string="Fiscal Document Type")
    audi_document_type = fields.Char(string="Document Type")

    @api.depends("partner_id.l10n_mx_edi_addenda_ids")
    def _compute_audi_flag(self):
        addenda = self.env.ref(
            "l10n_mx_edi_addenda_audi.l10n_mx_edi_addenda_audi",
            raise_if_not_found=False,
        )
        for record in self:
            record.audi_flag = bool(
                addenda and addenda in record.partner_id.l10n_mx_edi_addenda_ids
            )

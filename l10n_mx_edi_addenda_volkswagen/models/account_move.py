# Copyright (C) 2023 Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    vw_division = fields.Char(string="VW Division")
    vw_applicant_name = fields.Char(string="VW Applicant Name")
    vw_applicant_email = fields.Char(string="VW Applicant email")
    vw_flag = fields.Boolean(compute="_compute_vw_flag", store=True)

    @api.depends("partner_id.l10n_mx_edi_addenda_ids")
    def _compute_vw_flag(self):
        addenda = self.env.ref(
            "l10n_mx_edi_addenda_volkswagen.l10n_mx_edi_addenda_volkswagen",
            raise_if_not_found=False,
        )
        for record in self:
            record.vw_flag = bool(
                addenda and addenda in record.partner_id.l10n_mx_edi_addenda_ids
            )

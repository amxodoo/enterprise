# Copyright (C) 2023 Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    ford_ref = fields.Char(string="Ford Reference", default="NA")
    ford_flag = fields.Boolean(compute="_compute_ford_flag", store=True)

    @api.depends("partner_id.l10n_mx_edi_addenda_ids")
    def _compute_ford_flag(self):
        addenda = self.env.ref(
            "l10n_mx_edi_addenda_ford.l10n_mx_edi_addenda_ford",
            raise_if_not_found=False,
        )
        for record in self:
            record.ford_flag = bool(
                addenda and addenda in record.partner_id.l10n_mx_edi_addenda_ids
            )

# Copyright (C) 2026 Gray Matter Logic (<https://www.graymatterlogic.com>).
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import models
from odoo.exceptions import UserError
from odoo.modules.module import current_test
from odoo.tools import config

from odoo.addons.l10n_mx_sat_69b.models.sat_69b import (
    BLOCKED_STATUSES,
    GENERIC_RFCS,
    SatListError,
    lookup_taxpayer,
    normalize_rfc,
)


class AccountMove(models.Model):
    _inherit = "account.move"

    def _l10n_mx_edi_cfdi_invoice_try_send(self):
        """Skip PAC signing when the customer is on the SAT 69-B blacklist."""
        self.ensure_one()
        if self.state == "posted" and self.l10n_mx_edi_cfdi_state in (
            False,
            "cancel",
            "global_cancel",
        ):
            self._l10n_mx_edi_blacklist_stop_stamp()
        return super()._l10n_mx_edi_cfdi_invoice_try_send()

    def _l10n_mx_edi_blacklist_applies(self):
        """Customer invoices and credit notes of a Mexican company."""
        self.ensure_one()
        return (
            self.country_code == "MX"
            and self.move_type in ("out_invoice", "out_refund")
            and not self.l10n_mx_edi_cfdi_to_public
        )

    def _l10n_mx_edi_customer_rfc(self):
        self.ensure_one()
        partner = self.partner_id.commercial_partner_id
        return normalize_rfc(partner.vat)

    def _l10n_mx_edi_blacklist_record_block(self, message):
        """Store the refusal on the chatter and as a failed CFDI document."""
        self.ensure_one()
        self.message_post(body=message)
        self._l10n_mx_edi_cfdi_invoice_document_sent_failed(message)

    def _l10n_mx_edi_blacklist_notify(self, message):
        """Show a dialog and keep the same text on the invoice.

        ``UserError`` rolls back the send request. Commit first so the
        chatter message and the failed CFDI document survive that rollback.
        """
        self.ensure_one()
        self._l10n_mx_edi_blacklist_record_block(message)
        if not config["test_enable"] and not current_test:
            # pylint: disable=invalid-commit
            self.env.cr.commit()
        raise UserError(message)

    def _l10n_mx_edi_blacklist_stop_stamp(self):
        """Raise when the customer is on the SAT blacklist."""
        self.ensure_one()
        if not self._l10n_mx_edi_blacklist_applies():
            return
        rfc = self._l10n_mx_edi_customer_rfc()
        if not rfc or rfc in GENERIC_RFCS:
            return
        record = None
        try:
            record = lookup_taxpayer(rfc)
        except SatListError:
            self._l10n_mx_edi_blacklist_notify(
                self.env._(
                    "Could not verify the SAT blacklist (article 69-B) for customer "
                    "RFC %(rfc)s. The invoice was not stamped.",
                    rfc=rfc,
                )
            )
        if not record or record["status"] not in BLOCKED_STATUSES:
            return
        self._l10n_mx_edi_blacklist_notify(
            self.env._(
                "Cannot stamp the invoice: %(customer)s (RFC %(rfc)s) is on the "
                "SAT blacklist (article 69-B, status %(status)s). "
                "Reference: %(reference)s.",
                customer=record["name"] or self.partner_id.display_name,
                rfc=rfc,
                status=record["status"],
                reference=record["reference"] or self.env._("n/a"),
            )
        )

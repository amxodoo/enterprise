# Copyright (C) 2026 Gray Matter Logic (<https://www.graymatterlogic.com>).
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import models

from .sat_69b import (
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
        if (
            self.state == "posted"
            and self.l10n_mx_edi_cfdi_state in (False, "cancel", "global_cancel")
            and self._l10n_mx_edi_blacklist_stop_stamp()
        ):
            return
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

    def _l10n_mx_edi_blacklist_notify(self, message):
        """Leave the reason on the chatter and keep the CFDI unstamped."""
        self.ensure_one()
        self.message_post(body=message)
        self._l10n_mx_edi_cfdi_invoice_document_sent_failed(message)

    def _l10n_mx_edi_blacklist_stop_stamp(self):
        """Post the SAT reference and return whether stamping must stop."""
        self.ensure_one()
        if not self._l10n_mx_edi_blacklist_applies():
            return False
        rfc = self._l10n_mx_edi_customer_rfc()
        if not rfc or rfc in GENERIC_RFCS:
            return False
        try:
            record = lookup_taxpayer(rfc)
        except SatListError:
            message = self.env._(
                "Could not verify the SAT blacklist (article 69-B) for customer "
                "RFC %(rfc)s. The invoice was not stamped.",
                rfc=rfc,
            )
            self._l10n_mx_edi_blacklist_notify(message)
            return True
        if not record or record["status"] not in BLOCKED_STATUSES:
            return False
        message = self.env._(
            "Cannot stamp the invoice: %(customer)s (RFC %(rfc)s) is on the SAT "
            "blacklist (article 69-B, status %(status)s). Reference: %(reference)s.",
            customer=record["name"] or self.partner_id.display_name,
            rfc=rfc,
            status=record["status"],
            reference=record["reference"] or self.env._("n/a"),
        )
        self._l10n_mx_edi_blacklist_notify(message)
        return True

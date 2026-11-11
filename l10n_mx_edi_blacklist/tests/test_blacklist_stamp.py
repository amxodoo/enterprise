# Copyright (C) 2026 Gray Matter Logic (<https://www.graymatterlogic.com>).
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from unittest.mock import patch

from odoo.tests import tagged

from odoo.addons.l10n_mx_edi.models.account_move import AccountMove as MxAccountMove
from odoo.addons.l10n_mx_edi.tests.common import TestMxEdiCommon
from odoo.addons.l10n_mx_edi_blacklist.models.sat_69b import SatListError


@tagged("post_install", "-at_install")
class TestBlacklistStamp(TestMxEdiCommon):
    def _patch_parent_send(self):
        return patch.object(
            MxAccountMove,
            "_l10n_mx_edi_cfdi_invoice_try_send",
            return_value=None,
        )

    def _chatter(self, invoice):
        return " ".join(invoice.message_ids.mapped("body"))

    def test_customer_rfc_uses_commercial_partner(self):
        contact = self.env["res.partner"].create(
            {
                "name": "Accounts payable",
                "parent_id": self.partner_mx.id,
                "type": "invoice",
            }
        )
        invoice = self._create_invoice_mx(partner_id=contact.id)
        self.assertEqual(invoice._l10n_mx_edi_customer_rfc(), "ICV060329BY0")

    def test_blacklist_does_not_apply_to_bills_or_public_or_foreign_company(self):
        lookup_path = (
            "odoo.addons.l10n_mx_edi_blacklist.models.account_move.lookup_taxpayer"
        )
        bill = self._create_invoice_mx(move_type="in_invoice")
        self.assertFalse(bill._l10n_mx_edi_blacklist_applies())
        with patch(lookup_path) as lookup:
            self.assertFalse(bill._l10n_mx_edi_blacklist_stop_stamp())
            lookup.assert_not_called()

        invoice = self._create_invoice_mx()
        invoice.l10n_mx_edi_cfdi_to_public = True
        self.assertFalse(invoice._l10n_mx_edi_blacklist_applies())
        with patch(lookup_path) as lookup:
            self.assertFalse(invoice._l10n_mx_edi_blacklist_stop_stamp())
            lookup.assert_not_called()

    def test_stop_ignores_generic_and_empty_rfc(self):
        invoice = self._create_invoice_mx()
        partner = invoice.partner_id.commercial_partner_id
        original_vat = partner.vat
        with (
            patch.object(
                type(invoice), "_l10n_mx_edi_blacklist_applies", return_value=True
            ),
            patch(
                "odoo.addons.l10n_mx_edi_blacklist.models.account_move.lookup_taxpayer"
            ) as lookup,
        ):
            partner.vat = False
            self.assertFalse(invoice._l10n_mx_edi_blacklist_stop_stamp())
            partner.vat = "XAXX010101000"
            self.assertFalse(invoice._l10n_mx_edi_blacklist_stop_stamp())
            lookup.assert_not_called()
        partner.vat = original_vat

    def test_definitivo_posts_reference_and_does_not_stamp(self):
        invoice = self._create_invoice_mx()
        record = {
            "name": "ACME, S.A.",
            "status": "Definitivo",
            "reference": "500-05-2024-9 de fecha 02 de febrero de 2024",
        }
        with (
            patch(
                "odoo.addons.l10n_mx_edi_blacklist.models.account_move.lookup_taxpayer",
                return_value=record,
            ),
            self._patch_parent_send() as parent_send,
        ):
            invoice._l10n_mx_edi_cfdi_invoice_try_send()
        parent_send.assert_not_called()
        chatter = self._chatter(invoice)
        self.assertIn("500-05-2024-9 de fecha 02 de febrero de 2024", chatter)
        self.assertIn("Definitivo", chatter)
        self.assertIn("ICV060329BY0", chatter)
        document = invoice.l10n_mx_edi_invoice_document_ids.filtered(
            lambda doc: doc.state == "invoice_sent_failed"
        )
        self.assertTrue(document)
        self.assertIn(record["reference"], document[-1].message)
        self.assertNotEqual(invoice.l10n_mx_edi_cfdi_state, "sent")

    def test_presunto_and_empty_name_or_reference(self):
        invoice = self._create_invoice_mx()
        with patch(
            "odoo.addons.l10n_mx_edi_blacklist.models.account_move.lookup_taxpayer",
            return_value={"name": "", "status": "Presunto", "reference": ""},
        ):
            self.assertTrue(invoice._l10n_mx_edi_blacklist_stop_stamp())
        chatter = self._chatter(invoice)
        self.assertIn("Presunto", chatter)
        self.assertIn(invoice.partner_id.display_name, chatter)
        self.assertIn("n/a", chatter)

    def test_cleared_or_unknown_status_still_stamps(self):
        invoice = self._create_invoice_mx()
        for record in (
            None,
            {"name": "GAMMA", "status": "Desvirtuado", "reference": "500-05-4"},
            {
                "name": "DELTA",
                "status": "Sentencia Favorable",
                "reference": "500-05-7",
            },
            {"name": "ZETA", "status": "Otro", "reference": ""},
        ):
            with (
                patch(
                    "odoo.addons.l10n_mx_edi_blacklist.models.account_move.lookup_taxpayer",
                    return_value=record,
                ),
                self._patch_parent_send() as parent_send,
            ):
                invoice._l10n_mx_edi_cfdi_invoice_try_send()
            parent_send.assert_called()

    def test_refund_is_blocked_like_an_invoice(self):
        refund = self._create_invoice_mx(move_type="out_refund")
        with (
            patch(
                "odoo.addons.l10n_mx_edi_blacklist.models.account_move.lookup_taxpayer",
                return_value={
                    "name": "ACME",
                    "status": "Definitivo",
                    "reference": "500-05-REF",
                },
            ),
            self._patch_parent_send() as parent_send,
        ):
            refund._l10n_mx_edi_cfdi_invoice_try_send()
        parent_send.assert_not_called()
        self.assertIn("500-05-REF", self._chatter(refund))

    def test_unavailable_list_blocks_stamp(self):
        invoice = self._create_invoice_mx()
        with (
            patch(
                "odoo.addons.l10n_mx_edi_blacklist.models.account_move.lookup_taxpayer",
                side_effect=SatListError("down"),
            ),
            self._patch_parent_send() as parent_send,
        ):
            invoice._l10n_mx_edi_cfdi_invoice_try_send()
        parent_send.assert_not_called()
        self.assertIn("Could not verify the SAT blacklist", self._chatter(invoice))

    def test_draft_invoice_does_not_query_the_list(self):
        invoice = self._create_invoice_mx(post=False)
        with (
            patch(
                "odoo.addons.l10n_mx_edi_blacklist.models.account_move.lookup_taxpayer"
            ) as lookup,
            self._patch_parent_send() as parent_send,
        ):
            invoice._l10n_mx_edi_cfdi_invoice_try_send()
        lookup.assert_not_called()
        parent_send.assert_called()

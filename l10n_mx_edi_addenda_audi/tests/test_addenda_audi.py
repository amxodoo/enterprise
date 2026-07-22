# Copyright (C) 2026 Gray Matter Logic (<https://www.graymatterlogic.com>).
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestAddendaAudi(AccountTestInvoicingCommon):
    @classmethod
    @AccountTestInvoicingCommon.setup_country("mx")
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.addenda = cls.env.ref("l10n_mx_edi_addenda_audi.l10n_mx_edi_addenda_audi")
        cls.sale_journal = cls.company_data["default_journal_sale"]

    def test_addenda_record_loaded(self):
        self.assertEqual(self.addenda.name, "Addenda Audi")
        self.assertIn("Factura", self.addenda.arch)

    def test_audi_flag_and_partner_selection(self):
        partner = self.env["res.partner"].create(
            {
                "name": "Audi Partner",
                "l10n_mx_edi_addenda_ids": [(6, 0, self.addenda.ids)],
                "audi_supplier_number": "A123",
            }
        )
        self.assertTrue(partner.audi_addenda_selected)
        move = self.env["account.move"].create(
            {
                "move_type": "out_invoice",
                "partner_id": partner.id,
                "journal_id": self.sale_journal.id,
            }
        )
        self.assertTrue(move.audi_flag)

    def test_audi_flag_false_without_addenda(self):
        partner = self.env["res.partner"].create({"name": "Other"})
        self.assertFalse(partner.audi_addenda_selected)
        move = self.env["account.move"].create(
            {
                "move_type": "out_invoice",
                "partner_id": partner.id,
                "journal_id": self.sale_journal.id,
            }
        )
        self.assertFalse(move.audi_flag)

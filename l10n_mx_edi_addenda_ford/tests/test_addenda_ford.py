# Copyright (C) 2026 Gray Matter Logic (<https://www.graymatterlogic.com>).
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestAddendaFord(AccountTestInvoicingCommon):
    @classmethod
    @AccountTestInvoicingCommon.setup_country("mx")
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.addenda = cls.env.ref("l10n_mx_edi_addenda_ford.l10n_mx_edi_addenda_ford")
        cls.sale_journal = cls.company_data["default_journal_sale"]

    def test_addenda_record_loaded(self):
        self.assertEqual(self.addenda.name, "Addenda Ford")
        self.assertIn("fomadd", self.addenda.arch)

    def test_ford_flag_when_addenda_assigned(self):
        partner = self.env["res.partner"].create(
            {
                "name": "Ford Partner",
                "l10n_mx_edi_addenda_ids": [(6, 0, self.addenda.ids)],
            }
        )
        move = self.env["account.move"].create(
            {
                "move_type": "out_invoice",
                "partner_id": partner.id,
                "journal_id": self.sale_journal.id,
            }
        )
        self.assertTrue(move.ford_flag)

    def test_ford_flag_false_without_addenda(self):
        partner = self.env["res.partner"].create({"name": "Other Partner"})
        move = self.env["account.move"].create(
            {
                "move_type": "out_invoice",
                "partner_id": partner.id,
                "journal_id": self.sale_journal.id,
            }
        )
        self.assertFalse(move.ford_flag)

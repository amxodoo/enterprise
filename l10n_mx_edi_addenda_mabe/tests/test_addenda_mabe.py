# Copyright (C) 2026 Gray Matter Logic (<https://www.graymatterlogic.com>).
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo.addons.base.tests.common import BaseCommon


class TestAddendaMabe(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.addenda = cls.env.ref("l10n_mx_edi_addenda_mabe.l10n_mx_edi_addenda_mabe")

    def test_addenda_record_loaded(self):
        self.assertEqual(self.addenda.name, "Addenda Mabe")
        self.assertIn("mabe", self.addenda.arch)

    def test_mabe_flag_and_plant_code(self):
        partner = self.env["res.partner"].create(
            {
                "name": "Mabe Partner",
                "l10n_mx_edi_addenda_ids": [(6, 0, self.addenda.ids)],
                "mabe_plant_code": "S001",
            }
        )
        self.assertTrue(partner.mabe_addenda_selected)
        move = self.env["account.move"].create(
            {
                "move_type": "out_invoice",
                "partner_id": partner.id,
                "mabe_ref1": "R1",
            }
        )
        self.assertTrue(move.mabe_flag)
        self.assertEqual(move.mabe_ref1, "R1")

    def test_mabe_flag_false(self):
        partner = self.env["res.partner"].create({"name": "Other"})
        self.assertFalse(partner.mabe_addenda_selected)
        move = self.env["account.move"].create(
            {
                "move_type": "out_invoice",
                "partner_id": partner.id,
            }
        )
        self.assertFalse(move.mabe_flag)

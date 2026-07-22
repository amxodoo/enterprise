# Copyright (C) 2026 Gray Matter Logic (<https://www.graymatterlogic.com>).
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo.addons.base.tests.common import BaseCommon


class TestAddendaVolkswagen(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.addenda = cls.env.ref(
            "l10n_mx_edi_addenda_volkswagen.l10n_mx_edi_addenda_volkswagen"
        )

    def test_addenda_record_loaded(self):
        self.assertEqual(self.addenda.name, "Addenda Volkswagen")
        self.assertIn("PSV", self.addenda.arch)

    def test_vw_flag(self):
        partner = self.env["res.partner"].create(
            {
                "name": "VW Partner",
                "l10n_mx_edi_addenda_ids": [(6, 0, self.addenda.ids)],
            }
        )
        move = self.env["account.move"].create(
            {
                "move_type": "out_invoice",
                "partner_id": partner.id,
            }
        )
        self.assertTrue(move.vw_flag)

    def test_vw_flag_false(self):
        partner = self.env["res.partner"].create({"name": "Other"})
        move = self.env["account.move"].create(
            {
                "move_type": "out_invoice",
                "partner_id": partner.id,
            }
        )
        self.assertFalse(move.vw_flag)

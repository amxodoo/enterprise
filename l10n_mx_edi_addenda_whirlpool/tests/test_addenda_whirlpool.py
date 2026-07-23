# Copyright (C) 2026 Gray Matter Logic (<https://www.graymatterlogic.com>).
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo.tests import tagged

from odoo.addons.base.tests.common import BaseCommon


@tagged("post_install", "-at_install")
class TestAddendaWhirlpool(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.addenda = cls.env.ref(
            "l10n_mx_edi_addenda_whirlpool.l10n_mx_edi_addenda_whirlpool"
        )

    def test_addenda_record_loaded(self):
        self.assertEqual(self.addenda.name, "Addenda Whirlpool")
        self.assertIn("detallista", self.addenda.arch)
        self.assertIn("t-xml-node", self.addenda.arch)

    def test_partner_can_assign_addenda(self):
        partner = self.env["res.partner"].create(
            {
                "name": "Whirlpool Test Partner",
                "l10n_mx_edi_addenda_ids": [(6, 0, self.addenda.ids)],
            }
        )
        self.assertIn(self.addenda, partner.l10n_mx_edi_addenda_ids)

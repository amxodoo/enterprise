# Copyright (C) 2026 Gray Matter Logic (https://www.graymatterlogic.com)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from lxml import etree

from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon

KN_NS = {"kn": "http://www.w3.org/2001/XMLSchema"}


@tagged("post_install", "-at_install")
class TestKnAddenda(AccountTestInvoicingCommon):
    @classmethod
    @AccountTestInvoicingCommon.setup_country("mx")
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.addenda = cls.env.ref(
            "l10n_mx_edi_addenda_kuehne_nagel.l10n_mx_edi_addenda_kuehne_nagel"
        )
        cls.partner_kn = cls.env["res.partner"].create(
            {
                "name": "Kuehne Nagel Test",
                "company_type": "company",
                "l10n_mx_edi_addenda_ids": [(6, 0, cls.addenda.ids)],
            }
        )
        cls.partner_other = cls.env["res.partner"].create(
            {
                "name": "Other Customer",
                "company_type": "company",
            }
        )

    def _create_invoice(self, partner, **extra):
        invoice = self.init_invoice(
            "out_invoice",
            partner=partner,
            products=self.product_a,
        )
        if extra:
            invoice.write(extra)
        return invoice

    def _render_kn_addenda(self, invoice):
        """Render the KN addenda QWeb arch for an invoice.

        In 19.0 the addenda is ``l10n_mx_edi.addenda``, not ``ir.ui.view``, so
        ``ir.qweb._render(self.addenda.id)`` is invalid. Decode the arch the
        same way CFDI generation does, then render that fragment.
        """
        decoded = self.addenda._decode_single_addenda_arch()
        self.assertNotIn("error", decoded, decoded.get("error"))
        nsmap = {
            **decoded.get("comprobante", {}).get("nsmap", {}),
            **decoded.get("addenda", {}).get("nsmap", {}),
        }
        if not nsmap:
            nsmap = dict(KN_NS)
        template_xml = self.env["l10n_mx_edi.addenda"]._wrap_xml_with_namespaces(
            decoded["addenda"]["arch"], nsmap
        )
        rendered = self.env["ir.qweb"]._render(
            etree.fromstring(template_xml),
            {"record": invoice},
        )
        return etree.fromstring(rendered)

    def _kn_field_text(self, root, name):
        element = root.find(f".//kn:{name}", namespaces=KN_NS)
        self.assertIsNotNone(element, name)
        return (element.text or "").strip()

    def test_addenda_record_loaded(self):
        self.assertEqual(self.addenda.name, "Addenda Kuehne Nagel")

    def test_kn_flag_on_partner_with_addenda(self):
        invoice = self._create_invoice(self.partner_kn)
        self.assertTrue(invoice.kn_flag)
        self.assertIn(self.addenda, self.partner_kn.l10n_mx_edi_addenda_ids)

    def test_kn_flag_false_for_other_partner(self):
        invoice = self._create_invoice(self.partner_other)
        self.assertFalse(invoice.kn_flag)

    def test_normalize_kn_values(self):
        invoice = self._create_invoice(
            self.partner_kn,
            kn_file_type="file",
            kn_file_number_gl=" 7310880180505405 ",
            kn_branch_centre=" 10dwt ",
            kn_transport_ref=" 2886541 ",
        )
        self.assertEqual(invoice.kn_file_number_gl, "7310880180505405")
        self.assertEqual(invoice.kn_branch_centre, "10DWT")
        self.assertEqual(invoice.kn_transport_ref, "2886541")

    def test_ref_is_preserved_for_kn(self):
        invoice = self._create_invoice(
            self.partner_kn,
            ref="Customer PO/abc-123",
        )
        self.assertEqual(invoice.ref, "Customer PO/abc-123")

    def test_arbitrary_kn_field_formats_are_allowed(self):
        invoice = self._create_invoice(self.partner_kn)
        invoice.write(
            {
                "kn_file_type": "file",
                "kn_file_number_gl": "12345",
                "kn_branch_centre": "AB",
                "kn_transport_ref": "123",
            }
        )
        self.assertEqual(invoice.kn_file_number_gl, "12345")
        self.assertEqual(invoice.kn_branch_centre, "AB")
        self.assertEqual(invoice.kn_transport_ref, "123")

    def test_empty_optional_fields_are_allowed(self):
        invoice = self._create_invoice(self.partner_kn, ref=False)
        self.assertFalse(invoice.ref)
        self.assertFalse(invoice.kn_file_type)
        self.assertFalse(invoice.kn_file_number_gl)
        self.assertFalse(invoice.kn_branch_centre)
        self.assertFalse(invoice.kn_transport_ref)

    def test_qweb_addenda_xml_structure(self):
        invoice = self._create_invoice(
            self.partner_kn,
            ref=False,
            kn_file_type="file",
            kn_file_number_gl="7310880180505405",
            kn_branch_centre="10DWT",
            kn_transport_ref="2886541",
        )
        root = self._render_kn_addenda(invoice)
        self.assertTrue(root.tag.endswith("KNRECEPCION"))
        self.assertEqual(self._kn_field_text(root, "Purchase_Order"), "")
        self.assertEqual(self._kn_field_text(root, "FileNumber_GL"), "7310880180505405")
        self.assertEqual(self._kn_field_text(root, "Branch_Centre"), "10DWT")
        self.assertEqual(self._kn_field_text(root, "TransportRef"), "2886541")

    def test_qweb_addenda_with_purchase_order(self):
        invoice = self._create_invoice(
            self.partner_kn,
            ref="Customer PO/abc-123",
            kn_file_type="tracking",
            kn_file_number_gl="1023950106-1815",
            kn_branch_centre="99NFP",
            kn_transport_ref="1234567",
        )
        root = self._render_kn_addenda(invoice)
        self.assertTrue(root.tag.endswith("KNRECEPCION"))
        self.assertEqual(
            self._kn_field_text(root, "Purchase_Order"), "Customer PO/abc-123"
        )
        self.assertEqual(self._kn_field_text(root, "FileNumber_GL"), "1023950106-1815")
        self.assertEqual(self._kn_field_text(root, "Branch_Centre"), "99NFP")
        self.assertEqual(self._kn_field_text(root, "TransportRef"), "1234567")

    def test_qweb_addenda_with_empty_optional_fields(self):
        invoice = self._create_invoice(self.partner_kn, ref=False)
        root = self._render_kn_addenda(invoice)
        self.assertTrue(root.tag.endswith("KNRECEPCION"))
        for field_name in (
            "Purchase_Order",
            "FileNumber_GL",
            "Branch_Centre",
            "TransportRef",
        ):
            self.assertEqual(self._kn_field_text(root, field_name), "")

# Copyright (C) 2023 Gray Matter Logic (https://www.graymatterlogic.com)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
{
    "name": "Mexican Addendum For Invoices For MABE",
    "version": "17.0.1.3.0",
    "license": "LGPL-3",
    "summary": "Mexican Localization Addendum For MABE",
    "author": "Gray Matter Logic, Odoo Mexican Association (AMOdoo)",
    "maintainer": "Gray Matter Logic",
    "website": "https://github.com/amxodoo/enterprise",
    "depends": ["account", "l10n_mx_edi", "l10n_mx_edi_extended"],
    "data": [
        "views/account_move_views.xml",
        "views/l10n_mx_addenda_mabe_view.xml",
        "views/res_partner_views.xml",
    ],
    "application": False,
    "maintainers": ["max3903"],
}

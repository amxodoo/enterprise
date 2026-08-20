# Copyright (C) 2026 Gray Matter Logic (https://www.graymatterlogic.com)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

{
    "name": "Mexican Addendum For Invoices For Kuehne+Nagel",
    "version": "19.0.1.0.0",
    "license": "LGPL-3",
    "summary": "Mexican Localization Addendum KNRECEPCION For Kuehne+Nagel",
    "author": "Gray Matter Logic, Odoo Mexican Association (AMOdoo)",
    "maintainer": "Gray Matter Logic",
    "website": "https://github.com/amxodoo/enterprise",
    "depends": [
        "account",
        "l10n_mx_edi",
    ],
    "data": [
        "data/l10n_mx_edi_addenda_kuehne_nagel_data.xml",
        "views/account_move_views.xml",
    ],
    "images": [
        "static/description/icon.png",
    ],
    "icon": "/l10n_mx_edi_addenda_kuehne_nagel/static/description/icon.png",
    "installable": True,
    "application": False,
    "maintainers": ["max3903"],
}

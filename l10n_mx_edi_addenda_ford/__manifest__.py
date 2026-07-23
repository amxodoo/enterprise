# Copyright (C) 2023 Open Source Integrators
# Copyright (C) 2026 Gray Matter Logic
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
{
    "name": "Mexican Addendum For Invoices For Ford",
    "version": "19.0.1.0.1",
    "license": "LGPL-3",
    "summary": "Mexican Localization Addendum For Ford",
    "author": "Open Source Integrators, "
    "Gray Matter Logic, "
    "Odoo Mexican Association (AMOdoo)",
    "website": "https://github.com/amxodoo/enterprise",
    "depends": ["account", "l10n_mx_edi"],
    "data": [
        "data/l10n_mx_edi_addenda_ford_data.xml",
        "views/account_move_views.xml",
    ],
    "application": False,
    "installable": True,
}

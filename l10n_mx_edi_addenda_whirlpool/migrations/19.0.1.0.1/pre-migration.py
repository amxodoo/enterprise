# Copyright (C) 2026 Gray Matter Logic
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
"""Clear a stale ``ir.ui.view`` xmlid before the addenda data is (re)loaded.

Databases first built on Odoo <= 17 stored the addenda as an ``ir.ui.view``
record (flagged with ``l10n_mx_edi_addenda_flag``) under the external id
``l10n_mx_edi_addenda_whirlpool.l10n_mx_edi_addenda_whirlpool``.  On Odoo 19 the same
external id is declared for model ``l10n_mx_edi.addenda``, so loading the data
file raises::

    For external id l10n_mx_edi_addenda_whirlpool.l10n_mx_edi_addenda_whirlpool when
    trying to create/update a record of model l10n_mx_edi.addenda found record
    of different model ir.ui.view

This pre-migration resolves the collision *before* the data load:

* If ``l10n_mx_edi.addenda`` has its own table (the Odoo 18+ dedicated model),
  the stale ``res_id`` points at an ``ir.ui.view`` row that is not a valid
  addenda, so the stale ``ir_model_data`` row (and the orphaned view) are
  removed and the data file recreates a fresh addenda record.
* If ``l10n_mx_edi.addenda`` shares the ``ir_ui_view`` table (delegation on the
  same ids), the external id is remapped in place, preserving any
  partner <-> addenda links and updating the arch during the data load.

The script is idempotent and a no-op on fresh installs (``version`` is falsy).
"""

import logging

_logger = logging.getLogger(__name__)

MODULE = "l10n_mx_edi_addenda_whirlpool"
XMLID_NAME = "l10n_mx_edi_addenda_whirlpool"


def _table_exists(cr, table):
    cr.execute(
        "SELECT 1 FROM information_schema.tables WHERE table_name = %s",
        (table,),
    )
    return bool(cr.fetchone())


def migrate(cr, version):
    # Migration scripts never run on a fresh install, but guard anyway.
    if not version:
        return

    cr.execute(
        "SELECT id, res_id, model FROM ir_model_data WHERE module = %s AND name = %s",
        (MODULE, XMLID_NAME),
    )
    row = cr.fetchone()
    if not row:
        return
    imd_id, res_id, model = row

    # Nothing to do if the xmlid already points at the addenda model.
    if model != "ir.ui.view":
        return

    if _table_exists(cr, "l10n_mx_edi_addenda"):
        # Dedicated table: the stale res_id is an ir.ui.view, not an addenda.
        cr.execute("DELETE FROM ir_model_data WHERE id = %s", (imd_id,))
        if res_id:
            try:
                with cr.savepoint():
                    cr.execute("DELETE FROM ir_ui_view WHERE id = %s", (res_id,))
            except Exception:  # pragma: no cover - defensive against FK refs
                _logger.warning(
                    "%s: could not delete orphaned ir.ui.view %s; leaving it.",
                    MODULE,
                    res_id,
                )
        _logger.info(
            "%s: removed stale ir.ui.view xmlid %s (res_id=%s); a fresh "
            "l10n_mx_edi.addenda will be created by the data file.",
            MODULE,
            XMLID_NAME,
            res_id,
        )
    else:
        # Shared ir_ui_view table: remap in place to preserve links/arch.
        cr.execute(
            "UPDATE ir_model_data SET model = 'l10n_mx_edi.addenda' WHERE id = %s",
            (imd_id,),
        )
        _logger.info(
            "%s: remapped stale xmlid %s from ir.ui.view to l10n_mx_edi.addenda "
            "(res_id=%s).",
            MODULE,
            XMLID_NAME,
            res_id,
        )

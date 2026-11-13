Block CFDI stamping of customer invoices and credit notes when the
customer RFC is on the SAT blacklist of article 69-B of the CFF
(Presunto or Definitivo).

The check runs before the invoice is sent to the PAC. When the RFC is
listed, Odoo stops stamping with an error dialog and posts the same
text on the invoice chatter, including the official SAT reference
(número y fecha de oficio).
Taxpayers published as Desvirtuado or Sentencia Favorable are not
blocked.

Block CFDI stamping of customer invoices and credit notes when the
customer RFC is on the SAT blacklist of article 69-B of the CFF
(Presunto or Definitivo).

The check runs before the invoice is sent to the PAC. When the RFC is
listed, Odoo posts a message on the invoice chatter with the official
SAT reference (número y fecha de oficio) and does not stamp the CFDI.
Taxpayers published as Desvirtuado or Sentencia Favorable are not
blocked.

1. Install **Mexican EDI - SAT Blacklist** on a company that already
   uses Mexican EDI.
2. Confirm a customer invoice (or credit note) whose partner RFC is a
   real taxpayer RFC.
3. Send the CFDI the usual way (Send & Print, or the CFDI retry
   action).
4. When the RFC is **Presunto** or **Definitivo** on SAT list 69-B:
   - the CFDI is not stamped;
   - the invoice chatter shows the customer, the RFC, the SAT status,
     and the official reference (oficio);
   - the send wizard reports that same text.
5. When the RFC is not on the list, or is **Desvirtuado** or
   **Sentencia Favorable**, stamping continues as usual.
6. When the SAT list cannot be downloaded and there is no cached copy,
   the invoice is not stamped and the chatter explains that the
   blacklist could not be verified.

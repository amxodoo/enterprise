import base64
import logging
from datetime import date

from odoo import _, api, fields, models

_logger = logging.getLogger(__name__)


class HrPayrollSUAReports(models.Model):
    _name = "hr.payroll.sua.reports"
    _description = "Payroll SUA Reports"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char()
    date_start = fields.Date()
    date_end = fields.Date()
    report_type = fields.Selection(
        [
            ("alta", "SUA Registration"),
            ("movt", "SUA Movements"),
        ]
    )
    movt_type = fields.Selection(
        [
            ("02", "Deregistration"),
            ("07", "Salary Modification"),
            ("08", "Reinstatement"),
        ],
        default="02",
        string="Movement Type",
    )
    line_ids = fields.One2many(
        "hr.payroll.sua.reports.line", "line_id", string="Payment Lines"
    )
    notes = fields.Html()
    movs_count = fields.Integer(compute="_compute_movs_count")
    txt_file = fields.Binary(string="txt file")
    affiliation_file = fields.Binary(string="Affiliation txt file")
    company_id = fields.Many2one(
        "res.company", string="Company", default=lambda self: self.env.company
    )
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("calculated", "Calculated"),
            ("done", "Done"),
            ("cancel", "Cancel"),
        ],
        default="draft",
    )

    def _compute_movs_count(self):
        for movs in self:
            movs.movs_count = len(movs.line_ids)

    def action_open_payroll_movs_sua(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "res_model": "hr.payroll.sua.reports.line",
            "views": [[False, "tree"], [False, "form"]],
            "domain": [["id", "in", self.line_ids.ids]],
            "name": "Payroll Movements of SUA",
        }

    @api.onchange("report_type", "date_start", "date_end", "name", "movt_type")
    def _onchange_name(self):
        for sua in self:
            if sua.report_type == "alta":
                sua.name = "SUA Report - Registration "
            elif sua.report_type == "movt":
                sua.name = "SUA Report - Movements "
            elif sua.report_type == "movt" and sua.movt_type == "08":
                sua.name = "SUA Report - Reinstatement"
            else:
                sua.name = ""

    def sua_done(self):
        for sua in self:
            sua.state = "done"
            sua.message_post(body=_("Payroll SUA Report has been Calculated"))
            return True

    def sua_cancel(self):
        for sua in self:
            sua.state = "cancel"
            sua.message_post(body=_("Payroll SUA Report has been Cancelled"))
            return True

    def _create_contract_lines(self, sua, contract_ids):
        sua.line_ids.unlink()
        for contract_id in contract_ids:
            self.env["hr.payroll.sua.reports.line"].create(
                {
                    "line_id": sua.id,
                    "date": fields.Date.context_today(self),
                    "name": contract_id.employee_id.id,
                    "contract_id": contract_id.id,
                    "ssnid": contract_id.employee_id.ssnid,
                    "company_id": sua.company_id.id,
                }
            )

    def sua_calculate(self):
        for sua in self:
            sua.state = "calculated"
            date_start = sua.date_start
            date_end = sua.date_end

            if sua.report_type == "alta":
                sua.name = "SUA Report- Registration "
                contract_ids = self.env["hr.contract"].search(
                    [
                        "&",
                        "&",
                        ("date_start", ">=", date_start),
                        ("date_start", "<=", date_end),
                        ("state", "=", "open"),
                        ("company_id", "=", sua.company_id.id),
                    ]
                )
                self._create_contract_lines(sua, contract_ids)
            elif sua.report_type == "movt":
                self.movements(sua)
            else:
                sua.name = "SUA Report - without specifying the type of movement"

            sua.message_post(body=_("Payroll SUA Report has been Calculated"))
            return True

    def movements(self, sua):
        if sua.movt_type == "02":
            sua.name = "SUA Report - Deregistration "
            contract_ids = self.env["hr.contract"].search(
                [
                    "&",
                    ("date_end", ">=", sua.date_start),
                    ("date_end", "<=", sua.date_end),
                    ("state", "=", "cancel"),
                ]
            )
            self.line_ids.unlink()
            for contract_id in contract_ids:
                self.env["hr.payroll.sua.reports.line"].create(
                    {
                        "line_id": self.id,
                        "date": fields.Date.context_today(self),
                        "name": contract_id.employee_id.id,
                        "contract_id": contract_id.id,
                        "ssnid": contract_id.employee_id.ssnid,
                        "company_id": sua.company_id.id,
                    }
                )
        if self.movt_type == "07":
            sua.name = "SUA Report - Salary Modification"
            sua.line_ids.unlink()
            salary_history_ids = self.env["hr.contract.salary_history"].search(
                [
                    "&",
                    "&",
                    ("state", "=", "applied"),
                    ("date_applied", ">=", sua.date_start),
                    ("date_applied", "<=", sua.date_end),
                ]
            )
            sua.line_ids.unlink()
            for salary_id in salary_history_ids:
                self.env["hr.payroll.sua.reports.line"].create(
                    {
                        "line_id": sua.id,
                        "date": salary_id.date_applied,
                        "name": salary_id.employee_id.id,
                        "contract_id": salary_id.contract_id.id,
                        "ssnid": salary_id.employee_id.ssnid,
                        "company_id": sua.company_id.id,
                    }
                )
        if sua.movt_type == "08":
            sua.name = "SUA Report- Reinstatement"
            contract_ids = self.env["hr.contract"].search(
                [
                    "&",
                    "&",
                    ("date_start", ">=", sua.date_start),
                    ("date_start", "<=", sua.date_end),
                    ("state", "=", "open"),
                    ("company_id", "=", sua.company_id.id),
                ]
            )
            contract_olders_ids = self.env["hr.contract"].search(
                [
                    ("state", "in", ["cancel", "close"]),
                    ("company_id", "=", sua.company_id.id),
                ]
            )
            if contract_ids and contract_olders_ids:
                for contract_id in contract_ids:
                    self.env["hr.payroll.sua.reports.line"].create(
                        {
                            "line_id": sua.id,
                            "date": fields.Date.context_today(self),
                            "name": contract_id.employee_id.id,
                            "contract_id": contract_id.id,
                            "ssnid": contract_id.employee_id.ssnid,
                            "company_id": sua.company_id.id,
                        }
                    )

    def sua_back_to_draft(self):
        for sua in self:
            sua.state = "draft"
            sua.message_post(body=_("Payroll SUA Report has been draft"))
            return True

    def sua_txt(self):
        data = ""

        for sua in self:
            # Determine file name based on report type and movement type
            if sua.report_type == "alta":
                file_name = "aseg.txt"
            elif sua.report_type == "movt" and sua.movt_type == "02":
                file_name = "baja.txt"
            elif sua.report_type == "movt" and sua.movt_type == "07":
                file_name = "movimiento.txt"
            elif sua.report_type == "movt" and sua.movt_type == "08":
                file_name = "reingreso.txt"

            for line in sua.line_ids:
                contract = line.contract_id
                employee = line.name

                # Get employer register (11 chars)
                employer_register = str(
                    employee.employer_register.name
                    if employee.employer_register
                    else ""
                )
                employer_register_padded = employer_register[:11].ljust(11)

                # NSS (11 chars)
                ssnid = str(employee.ssnid or "")
                if len(ssnid) == 10:
                    nss = "0" + ssnid
                elif len(ssnid) == 11:
                    nss = ssnid
                else:
                    nss = ssnid.zfill(11)
                nss_padded = nss[:11].ljust(11)

                # Check if this is a Baja (deregistration) process
                if sua.report_type == "movt" and sua.movt_type == "02":
                    # Baja (deregistration) format (49 characters total)
                    # 1-11: Employer Register (11 chars)
                    # 12-22: NSS (11 chars)
                    # 23-24: Deregistration cause (2 chars) - hardcoded as "02"
                    # 25-26: Deregistration day (2 chars)
                    # 27-28: Deregistration month (2 chars)
                    # 29-32: Deregistration year (4 chars)
                    # 33-40: Empty spaces (8 chars)
                    # 41-49: Fixed zeros (9 chars)

                    # Deregistration cause - hardcoded as "02"
                    deregistration_cause = "02"

                    # Get date components from line.date
                    if line.date:
                        deregistration_date = line.date
                    else:
                        deregistration_date = fields.Date.context_today(self)

                    day = str(deregistration_date.day).zfill(2)
                    month = str(deregistration_date.month).zfill(2)
                    year = str(deregistration_date.year)[
                        -4:
                    ]  # Get last 4 digits of year

                    # Empty spaces (8 chars)
                    empty_spaces = " " * 8

                    # Fixed zeros (9 chars)
                    fixed_zeros = "000000000"

                    record = (
                        employer_register_padded
                        + nss_padded  # 1-11: Employer Register
                        + deregistration_cause  # 12-22: NSS
                        + day  # 23-24: Deregistration cause
                        + month  # 25-26: Deregistration day
                        + year  # 27-28: Deregistration month
                        + empty_spaces  # 29-32: Deregistration year
                        + fixed_zeros  # 33-40: Empty spaces  # 41-49: Fixed zeros
                    )
                elif sua.report_type == "movt" and sua.movt_type == "07":
                    # Salary change (movt_type 07) format (49 characters total)
                    # 1-11: Employer Register (11 chars)
                    # 12-22: NSS (11 chars) - If 10 digits → "0"&NSS; if 11 → as is
                    # 23-24: Movement code (2 chars) - FIJO "07"
                    # 25-26: Day of modification (2 chars) - DD
                    # 27-28: Month of modification (2 chars) - MM
                    # 29-32: Year of modification (4 chars) - YYYY
                    # 33-40: Empty spaces (8 chars)
                    # 41-42: Fixed zeros (2 chars) - "00"
                    # 43-47: Salary integer (5 chars)
                    # 48-49: Salary decimals (2 chars)

                    # Movement code - hardcoded as "07"
                    movement_code = "07"

                    # Get date components from line.date
                    if line.date:
                        modification_date = line.date
                    else:
                        modification_date = fields.Date.context_today(self)

                    day = str(modification_date.day).zfill(2)
                    month = str(modification_date.month).zfill(2)
                    year = str(modification_date.year)[-4:]

                    # Empty spaces (8 chars)
                    empty_spaces = " " * 8

                    # Fixed zeros (2 chars)
                    fixed_zeros_2 = "00"

                    # Get salary from contract
                    sdi = contract.sdi or 0.0
                    sdi_integer = int(sdi)
                    sdi_decimal = int(round((sdi - sdi_integer) * 100))

                    # Format salary: integer (5 digits) + decimals (2 chars)
                    salary_integer = str(sdi_integer).zfill(5)[-5:]
                    salary_decimals = str(sdi_decimal).zfill(2)[-2:]

                    record = (
                        employer_register_padded  # 1-11: Employer Register (11 chars)
                        + nss_padded  # 12-22: NSS (11 chars)
                        + movement_code  # 23-24: Movement code "07" (2 chars)
                        + day  # 25-26: Day of modification (2 chars)
                        + month  # 27-28: Month of modification (2 chars)
                        + year  # 29-32: Year of modification (4 chars)
                        + empty_spaces  # 33-40: Empty spaces (8 chars)
                        + fixed_zeros_2  # 41-42: Fixed zeros "00" (2 chars)
                        + salary_integer  # 43-47: Salary integer (5 chars)
                        + salary_decimals  # 48-49: Salary decimals (2 chars)
                    )  # Total: 49 characters
                elif sua.report_type == "movt" and sua.movt_type == "08":
                    # Re-registration (movt_type 08) format (49 characters total)
                    # 1-11: Employer Register (11 chars)
                    # 12-22: NSS (11 chars) - If 10 digits → "0"&NSS; if 11 → as is
                    # 23-24: Movement code (2 chars) - FIJO "08"
                    # 25-26: Day of re-registration (2 chars) - DD
                    # 27-28: Month of re-registration (2 chars) - MM
                    # 29-32: Year of re-registration (4 chars) - YYYY
                    # 33-40: Empty spaces (8 chars)
                    # 41-42: Fixed zeros (2 chars) - "00"
                    # 43-47: Salary integer (5 chars)
                    # 48-49: Salary decimals (2 chars)

                    # Movement code - hardcoded as "08"
                    movement_code = "08"

                    # Get date components from line.date
                    if line.date:
                        reregistration_date = line.date
                    else:
                        reregistration_date = fields.Date.context_today(self)

                    day = str(reregistration_date.day).zfill(2)
                    month = str(reregistration_date.month).zfill(2)
                    year = str(reregistration_date.year)[-4:]

                    # Empty spaces (8 chars)
                    empty_spaces = " " * 8

                    # Fixed zeros (2 chars)
                    fixed_zeros_2 = "00"

                    # Get salary from contract
                    sdi = contract.sdi or 0.0
                    sdi_integer = int(sdi)
                    sdi_decimal = int(round((sdi - sdi_integer) * 100))

                    # Format salary: integer (5 digits) + decimals (2 chars)
                    salary_integer = str(sdi_integer).zfill(5)[-5:]
                    salary_decimals = str(sdi_decimal).zfill(2)[-2:]

                    record = (
                        employer_register_padded  # 1-11: Employer Register (11 chars)
                        + nss_padded  # 12-22: NSS (11 chars)
                        + movement_code  # 23-24: Movement code "08" (2 chars)
                        + day  # 25-26: Day of re-registration (2 chars)
                        + month  # 27-28: Month of re-registration (2 chars)
                        + year  # 29-32: Year of re-registration (4 chars)
                        + empty_spaces  # 33-40: Empty spaces (8 chars)
                        + fixed_zeros_2  # 41-42: Fixed zeros "00" (2 chars)
                        + salary_integer  # 43-47: Salary integer (5 chars)
                        + salary_decimals  # 48-49: Salary decimals (2 chars)
                    )  # Total: 49 characters

                else:
                    # Alta format (164 characters total)
                    # Get contract date components
                    reg_date = contract.date_start
                    day = str(reg_date.day).zfill(2)
                    month = str(reg_date.month).zfill(2)
                    year = str(reg_date.year)

                    # Get employee name components
                    lastname = str(employee.lastname or "").upper()
                    second_lastname = str(employee.second_lastname or "").upper()
                    firstname = str(employee.firstname or "").upper()

                    # Get RFC (13 chars) from employee's VAT
                    rfc = str(employee.address_home_id.vat or "").upper()
                    rfc_padded = (rfc + " " * 13)[:13]

                    # Get CURP (18 chars) from employee
                    curp = str(employee.address_home_id.curp or "").upper()
                    curp_padded = (curp + " " * 18)[:18]

                    # Full name with $ separator, padded to 50 characters
                    # Format: Lastname P. $ Second Lastname M. $ Firstname
                    full_name = f"{lastname}${second_lastname}${firstname}"
                    full_name_padded = (full_name + " " * 50)[:50]

                    # Worker type: from contract_type
                    # Mapping contract_type to worker type (1=Perm, 2=Eventual, 3=Ev.Constr.)
                    contract_type = contract.contract_type or "01"
                    if contract_type in ["01", "03"]:  # Indefinite, Specific period
                        worker_type = "1"
                    elif contract_type in ["02", "04", "05", "06", "07", "08"]:
                        worker_type = "2"
                    else:
                        worker_type = "1"  # Default to permanent

                    # Work shift type: from journal_type
                    # 0=Full, 1-5=days worked, 6=less than 1 day
                    journal_type = contract.journal_type or "00"
                    if journal_type == "00":
                        work_shift_type = "0"
                    elif journal_type in ["01", "02", "03", "04", "05"]:
                        work_shift_type = journal_type[
                            -1
                        ]  # Get last digit: 1, 2, 3, 4, 5
                    elif journal_type == "06":
                        work_shift_type = "6"
                    else:
                        work_shift_type = "0"

                    # Salary type: from salary_type
                    # New mapping: 0=Fixed, 1=Variable, 2=Mixed
                    salary_type = contract.salary_type or "01"
                    if salary_type == "01":
                        salary_type_code = "0"  # Fixed -> 0 (Fixed)
                    elif salary_type == "03":
                        salary_type_code = "1"  # Variable -> 1 (Variable)
                    else:
                        salary_type_code = "2"  # Mixed -> 2 (Mixed)

                    # Integrated daily salary (SDI)
                    sdi = contract.sdi or 0.0
                    sdi_integer = int(sdi)
                    sdi_decimal = int(round((sdi - sdi_integer) * 100))

                    # Format salary: integer (5 digits) + decimals (2 digits)
                    salary_integer = str(sdi_integer).zfill(5)[
                        -5:
                    ]  # RIGHT("00000"& INT(sal), 5)
                    salary_decimals = str(sdi_decimal).zfill(2)[
                        -2:
                    ]  # RIGHT(FIXED(sal,2), 2)

                    # Occupation code: employee_number (17 chars)
                    occupation_code = (" " * 17)[:17]

                    # Salary type code (8 chars)
                    salary_type_code_padded = salary_type_code * 8

                    record = (
                        employer_register[:11].ljust(11)
                        + nss  # 1-11: Employer Register
                        + rfc_padded  # 12-22: NSS
                        + curp_padded  # 23-35: RFCC
                        + full_name_padded  # 36-53: CURP
                        + worker_type  # 54-103: Full name
                        + work_shift_type  # 104: Worker type
                        + day  # 105: Work shift type
                        + month  # 106-107: Day
                        + year  # 108-109: Month
                        + salary_integer  # 110-113: Year
                        + salary_decimals  # 114-118: Salary integer
                        + occupation_code  # 119-120: Salary decimals
                        + " " * 10  # 121-137: Occupation code
                        + day  # 138-147: Empty spaces
                        + month  # 148-149: Day repeated
                        + year  # 150-151: Month repeated
                        + " "  # 152-155: Year repeated
                        + salary_type_code_padded  # 157-164: Salary type code
                    )

                data += record + "\r\n"

        self.txt_file = base64.b64encode(data.encode("cp1252"))
        return {
            "type": "ir.actions.act_url",
            "url": "/web/content/hr.payroll.sua.reports/"
            + "%s/txt_file/%s?download=true" % (self.id, file_name),
            "target": "self",
        }

    def affiliation_txt(self):
        """Generate Affiliation TXT file for IMSS registration"""
        lines = ""
        for sua in self:
            for line in sua.line_ids:
                contract = line.contract_id
                employee = line.name

                # Get employer register (11 chars)
                employer_register = str(
                    employee.employer_register.name
                    if employee.employer_register
                    else ""
                )
                employer_register_padded = employer_register[:11].ljust(11)

                # NSS (11 chars)
                ssnid = str(employee.ssnid or "")
                if len(ssnid) == 10:
                    nss = "0" + ssnid
                elif len(ssnid) == 11:
                    nss = ssnid
                else:
                    nss = ssnid.zfill(11)
                nss_padded = nss[:11].ljust(11)

                # Postal code from employee address (5 chars)
                zip_code = str(employee.address_home_id.zip or "")
                postal_code = zip_code[:5].zfill(5)

                # Birth date components from CURP (positions 5-10 = YYMMDD)
                curp = str(employee.address_home_id.curp or "").upper()
                if curp and len(curp) >= 10:
                    birth_day = curp[8:10]
                    birth_month = curp[6:8]
                    birth_yy = int(curp[4:6])
                    current_yy = date.today().year % 100
                    birth_year = str(
                        1900 + birth_yy if birth_yy > current_yy else 2000 + birth_yy
                    )
                else:
                    birth_day = "01"
                    birth_month = "01"
                    birth_year = "0000"

                # State code from CURP (positions 10-11, characters 11-12 in 1-based)
                # Mapping CURP state codes to numeric keys (1-33)
                curp_state_code = curp[11:13] if curp and len(curp) >= 13 else ""

                # State code mapping table (CURP code -> numeric key)
                state_code_mapping = {
                    "AS": 1,  # Aguascalientes
                    "BC": 2,  # Baja California
                    "BS": 3,  # Baja California Sur
                    "CC": 4,  # Campeche
                    "CS": 5,  # Chiapas
                    "CH": 6,  # Chihuahua
                    "DF": 7,  # Ciudad de México
                    "CL": 8,  # Coahuila
                    "CM": 9,  # Colima
                    "DG": 10,  # Durango
                    "GT": 11,  # Guanajuato
                    "GR": 12,  # Guerrero
                    "HG": 13,  # Hidalgo
                    "JC": 14,  # Jalisco
                    "MC": 15,  # Estado de México
                    "MN": 16,  # Michoacán
                    "MS": 17,  # Morelos
                    "NT": 18,  # Nayarit
                    "NL": 19,  # Nuevo León
                    "OC": 20,  # Oaxaca
                    "PL": 21,  # Puebla
                    "QT": 22,  # Querétaro
                    "QR": 23,  # Quintana Roo
                    "SP": 24,  # San Luis Potosí
                    "SL": 25,  # Sinaloa
                    "SR": 26,  # Sonora
                    "TC": 27,  # Tabasco
                    "TS": 28,  # Tamaulipas
                    "TL": 29,  # Tlaxcala
                    "VZ": 30,  # Veracruz
                    "YN": 31,  # Yucatán
                    "ZS": 32,  # Zacatecas
                    "NE": 33,  # Nacido en el Extranjero
                }

                # Get numeric state key from CURP code
                state_key = state_code_mapping.get(curp_state_code, 0)

                # State code (2 chars) - use the numeric key padded to 2 digits
                state_code_padded = str(state_key).zfill(2) if state_key > 0 else "00"

                # State name (25 chars, right aligned) - mapping numeric key to state name
                # Using ANSI/CP1252 compatible format in UPPERCASE
                state_name_mapping = {
                    1: "AGUASCALIENTES",
                    2: "BAJA CALIFORNIA",
                    3: "BAJA CALIFORNIA SUR",
                    4: "CAMPECHE",
                    5: "CHIAPAS",
                    6: "CHIHUAHUA",
                    7: "CIUDAD DE MEXICO",
                    8: "COAHUILA",
                    9: "COLIMA",
                    10: "DURANGO",
                    11: "GUANAJUATO",
                    12: "GUERRERO",
                    13: "HIDALGO",
                    14: "JALISCO",
                    15: "ESTADO DE MEXICO",
                    16: "MICHOACAN",
                    17: "MORELOS",
                    18: "NAYARIT",
                    19: "NUEVO LEON",
                    20: "OAXACA",
                    21: "PUEBLA",
                    22: "QUERETARO",
                    23: "QUINTANA ROO",
                    24: "SAN LUIS POTOSI",
                    25: "SINALOA",
                    26: "SONORA",
                    27: "TABASCO",
                    28: "TAMAULIPAS",
                    29: "TLAXCALA",
                    30: "VERACRUZ",
                    31: "YUCATAN",
                    32: "ZACATECAS",
                    33: "NACIDO EN EL EXTRANJERO",
                }

                state_name = state_name_mapping.get(state_key, "")
                state_name_padded = state_name[-25:].rjust(25)

                # UMF - Family Medical Unit (3 chars)
                umf = str(employee.umf or "001")
                umf_padded = umf[:3].zfill(3)

                # Occupation code - employee_number (12 chars)
                employee_number = str(employee.employee_number or "")
                occupation_code = employee_number[:12].ljust(12)

                # Gender (1 char) from CURP position 11 (index 10)
                # CURP position 11: H = hombre (man), M = mujer (woman)
                # Mapping: H -> M (Male), M -> F (Female)
                if curp and len(curp) >= 11:
                    curp_gender = curp[10]  # Position 11 in 1-based indexing
                    if curp_gender == "H":
                        gender = "M"  # Man -> M
                    elif curp_gender == "M":
                        gender = "F"  # Woman -> F
                    else:
                        gender = " "
                else:
                    gender = " "

                # Work shift type (1 char) - from contract.journal_type
                journal_type = contract.journal_type or "00"
                if journal_type == "00":
                    work_shift_type = "0"
                elif journal_type in ["01", "02", "03", "04", "05"]:
                    work_shift_type = journal_type[-1]
                elif journal_type == "06":
                    work_shift_type = "6"
                else:
                    work_shift_type = "0"

                # Space (1 char)
                space = " "

                # Build the record (80 characters total)
                # Position mapping:
                # 1-11: Employer Register (11 chars)
                # 12-22: NSS (11 chars)
                # 23-27: Postal code (5 chars)
                # 28-29: Birth day (2 chars)
                # 30-31: Birth month (2 chars)
                # 32-35: Birth year (4 chars)
                # 36-60: State name (25 chars, right aligned)
                # 61-62: State code (2 chars)
                # 63-65: UMF (3 chars)
                # 66-77: Occupation code (12 chars)
                # 78: Gender (1 char)
                # 79: Work shift type (1 char)
                # 80: Space (1 char)

                record = (
                    employer_register_padded
                    + nss_padded  # 1-11: Employer Register
                    + postal_code  # 12-22: NSS
                    + birth_day  # 23-27: Postal code
                    + birth_month  # 28-29: Birth day
                    + birth_year  # 30-31: Birth month
                    + state_name_padded  # 32-35: Birth year
                    + state_code_padded  # 36-60: State name
                    + umf_padded  # 61-62: State code
                    + occupation_code  # 63-65: UMF
                    + gender  # 66-77: Occupation code
                    + work_shift_type  # 78: Gender
                    + space  # 79: Work shift type  # 80: Space
                )

                lines += record + "\r\n"

            # Encode to CP1252 and then Base64
            encoded_bytes = lines.encode("cp1252")
            base64_encoded = base64.b64encode(encoded_bytes)

            self.affiliation_file = base64_encoded

            return {
                "type": "ir.actions.act_url",
                "url": "/web/content/hr.payroll.sua.reports/%s/affiliation_file?download=true&filename=affiliation.txt"
                % (self.id),
                "target": "self",
            }


class HrPayrollSUAReportsLine(models.Model):
    _name = "hr.payroll.sua.reports.line"
    _description = "Payroll SUA Reports Line"

    line_id = fields.Many2one(
        "hr.payroll.sua.reports", required=True, ondelete="cascade"
    )
    name = fields.Many2one("hr.employee")
    date = fields.Date()
    contract_id = fields.Many2one("hr.contract")
    ssnid = fields.Char(string="NSS", related="name.ssnid", store=True)

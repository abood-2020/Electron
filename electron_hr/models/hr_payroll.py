# -*- coding: utf-8 -*-
import time
import babel
import base64
from odoo import models, fields, api, tools, _
from collections import defaultdict
from datetime import datetime
from datetime import timedelta
from datetime import date, datetime, time
from dateutil.relativedelta import relativedelta
from pytz import timezone
from pytz import utc
from odoo.tools.misc import format_date
from odoo.tools import float_round, date_utils
from odoo.tools.safe_eval import safe_eval


from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_utils
ROUNDING_FACTOR = 16


class HrPayslipInput(models.Model):
    _inherit = 'hr.payslip.input'

    loan_line_id = fields.Many2one('hr.loan.line', string="Loan Installment", help="Loan installment")


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    @api.onchange('employee_id', 'struct_id', 'contract_id', 'date_from', 'date_to')
    def _onchange_employee(self):
        if (not self.employee_id) or (not self.date_from) or (not self.date_to):
            return

        employee = self.employee_id
        date_from = self.date_from
        date_to = self.date_to
        # is_input = 0
        # id = 1
        # amount = 0.0
        # line_id=1
        # inputs = self.env['hr.payslip.input.type'].search([('code','=','LO')])
        # lon_obj = self.env['hr.loan'].search([('employee_id', '=', employee.id), ('state', '=', 'approve')])
        # for loan in lon_obj:
        #     for loan_line in loan.loan_lines:
        #         if date_from <= loan_line.date <= date_to and not loan_line.paid:
        #             is_input = 1
        #             id = inputs.id
        #             amount  =loan_line.amount
        #             line_id =loan_line.id
                    
        
        # if is_input == 1:
        #     for rec in self:
        #         rec.write({
        #                     'input_line_ids': [(0, 0, {
        #                         'input_type_id': id,
        #                         'amount': amount,
        #                         'loan_line_id':line_id,
        #                     })]
        #                 })
                    
                    
        self.company_id = employee.company_id
        if not self.contract_id or self.employee_id != self.contract_id.employee_id: # Add a default contract if not already defined
            contracts = employee._get_contracts(date_from, date_to)
            # input_line_ids = self.get_inputs(contracts, date_from, date_to)
            # input_lines = self.input_line_ids.browse([])
            # for r in input_line_ids:
            #     input_lines += input_lines.new(r)
            # self.input_line_ids = input_lines

            if not contracts or not contracts[0].structure_type_id.default_struct_id:
                self.contract_id = False
                self.struct_id = False
                return
            self.contract_id = contracts[0]
            self.struct_id = contracts[0].structure_type_id.default_struct_id

        lang = employee.sudo().address_home_id.lang or self.env.user.lang
        context = {'lang': lang}
        payslip_name = self.struct_id.payslip_name or _('Salary Slip')
        del context


        self.name = '%s - %s - %s' % (
            payslip_name,
            self.employee_id.name or '',
            format_date(self.env, self.date_from, date_format="MMMM y", lang_code=lang)
        )

        if date_to > date_utils.end_of(fields.Date.today(), 'month'):
            self.warning_message = _(
                "This payslip can be erroneous! Work entries may not be generated for the period from %(start)s to %(end)s.",
                start=date_utils.add(date_utils.end_of(fields.Date.today(), 'month'), days=1),
                end=date_to,
            )
        else:
            self.warning_message = False

        self.worked_days_line_ids = self._get_new_worked_days_lines()
        return

    # @api.onchange('employee_id',  'date_from', 'date_to')
    # def onchange_employee(self):
    #     if (not self.employee_id) or (not self.date_from) or (not self.date_to):
    #         return
    #     employee = self.employee_id
    #     date_from = self.date_from
    #     date_to = self.date_to
   
    #     is_input = 0
    #     id = 1
    #     amount = 0.0
    #     line_id=1
    #     inputs = self.env['hr.payslip.input.type'].search([('code','=','LO')])
    #     lon_obj = self.env['hr.loan'].search([('employee_id', '=', employee.id), ('state', '=', 'paid')])
    #     for loan in lon_obj:
    #         for loan_line in loan.loan_lines:
    #             if date_from <= loan_line.date <= date_to and not loan_line.paid:
    #                 is_input = 1
    #                 id = inputs.id
    #                 amount  =loan_line.amount
    #                 line_id =loan_line.id
                    
        
    #     if is_input == 1:
    #         for rec in self:
    #             rec.write({
    #                         'input_line_ids': [(0, 0, {
    #                             'input_type_id': id,
    #                             'amount': amount,
    #                             'loan_line_id':line_id,
    #                         })]
    #                     })


    # def action_payslip_done(self):
    #     if any(slip.state == 'cancel' for slip in self):
    #         raise ValidationError(_("You can't validate a cancelled payslip."))
    #     self.write({'state' : 'done'})
    #     self.mapped('payslip_run_id').action_close()
    #     # Validate work entries for regular payslips (exclude end of year bonus, ...)
    #     regular_payslips = self.filtered(lambda p: p.struct_id.type_id.default_struct_id == p.struct_id)
    #     for regular_payslip in regular_payslips:
    #         work_entries = self.env['hr.work.entry'].search([
    #             ('date_start', '<=', regular_payslip.date_to),
    #             ('date_stop', '>=', regular_payslip.date_from),
    #             ('employee_id', '=', regular_payslip.employee_id.id),
    #         ])
    #         work_entries.action_validate()
    #     for line in self.input_line_ids:
    #         if line.loan_line_id:
    #             line.loan_line_id.paid = True
    #             line.loan_line_id.loan_id._compute_loan_amount()

    #     if self.env.context.get('payslip_generate_pdf'):
    #         for payslip in self:
    #             if not payslip.struct_id or not payslip.struct_id.report_id:
    #                 report = self.env.ref('hr_payroll.action_report_payslip', False)
    #             else:
    #                 report = payslip.struct_id.report_id
    #             pdf_content, content_type = report.sudo()._render_qweb_pdf(payslip.id)
    #             if payslip.struct_id.report_id.print_report_name:
    #                 pdf_name = safe_eval(payslip.struct_id.report_id.print_report_name, {'object': payslip})
    #             else:
    #                 pdf_name = _("Payslip")
    #             # Sudo to allow payroll managers to create document.document without access to the
    #             # application
    #             attachment = self.env['ir.attachment'].sudo().create({
    #                 'name': pdf_name,
    #                 'type': 'binary',
    #                 'datas': base64.encodebytes(pdf_content),
    #                 'res_model': payslip._name,
    #                 'res_id': payslip.id
    #             })
    #             # Send email to employees
    #             subject = '%s, a new payslip is available for you' % (payslip.employee_id.name)
    #             template = self.env.ref('hr_payroll.mail_template_new_payslip', raise_if_not_found=False)
    #             if template:
    #                 email_values = {
    #                     'attachment_ids': attachment,
    #                 }
    #                 template.send_mail(
    #                     payslip.id,
    #                     email_values=email_values,
    #                     notif_layout='mail.mail_notification_light')
                    
                    
    @api.model
    def get_contract(self, employee, date_from, date_to):

        """
        @param employee: recordset of employee
        @param date_from: date field
        @param date_to: date field
        @return: returns the ids of all the contracts for the given employee that need to be considered for the given dates
        """
        # a contract is valid if it ends between the given dates
        clause_1 = ['&', ('date_end', '<=', date_to), ('date_end', '>=', date_from)]
        # OR if it starts between the given dates
        clause_2 = ['&', ('date_start', '<=', date_to), ('date_start', '>=', date_from)]
        # OR if it starts before the date_from and finish after the date_end (or never finish)
        clause_3 = ['&', ('date_start', '<=', date_from), '|', ('date_end', '=', False), ('date_end', '>=', date_to)]
        clause_final = [('employee_id', '=', employee.id), ('state', '=', 'open'), '|',
                        '|'] + clause_1 + clause_2 + clause_3
        return self.env['hr.contract'].search(clause_final).ids

    @api.model
    def get_worked_day_lines(self, contracts, date_from, date_to):

        """
        @param contract: Browse record of contracts
        @return: returns a list of dict containing the input that should be applied for the given contract between date_from and date_to
        """
        res = []
        # fill only if the contract as a working schedule linked
        for contract in contracts.filtered(lambda contract: contract.resource_calendar_id):
            day_from = datetime.combine(fields.Date.from_string(date_from), time.min)
            day_to = datetime.combine(fields.Date.from_string(date_to), time.max)

            # compute leave days
            leaves = {}
            calendar = contract.resource_calendar_id
            tz = timezone(calendar.tz)
            day_leave_intervals = contract.employee_id.list_leaves(day_from, day_to,
                                                                   calendar=contract.resource_calendar_id)
            for day, hours, leave in day_leave_intervals:
                holiday = leave.holiday_id
                current_leave_struct = leaves.setdefault(holiday.holiday_status_id, {
                    'name': holiday.holiday_status_id.name or _('Global Leaves'),
                    'sequence': 5,
                    'code': holiday.holiday_status_id.code or 'GLOBAL',
                    'number_of_days': 0.0,
                    'number_of_hours': 0.0,
                    'contract_id': contract.id,
                })
                current_leave_struct['number_of_hours'] += hours
                work_hours = calendar.get_work_hours_count(
                    tz.localize(datetime.combine(day, time.min)),
                    tz.localize(datetime.combine(day, time.max)),
                    compute_leaves=False,
                )
                if work_hours:
                    current_leave_struct['number_of_days'] += hours / work_hours

            # compute worked days
            work_data = contract.employee_id.get_work_days_data(day_from, day_to,
                                                                calendar=contract.resource_calendar_id)
            attendances = {
                'name': _("Normal Working Days paid at 100%"),
                'sequence': 1,
                'code': 'WORK100',
                'number_of_days': work_data['days'],
                'number_of_hours': work_data['hours'],
                'contract_id': contract.id,
            }

            res.append(attendances)
            res.extend(leaves.values())
        return res


  


class HrContract(models.Model):
    """
    Employee contract based on the visa, work permits
    allows to configure different Salary structure
    """
    _inherit = 'hr.contract'
    _description = 'Employee Contract'

    struct_id = fields.Many2one('hr.payroll.structure', string='Salary Structure')
    def get_all_structures(self):

        """
        @return: the structures linked to the given contracts, ordered by hierachy (parent=False first,
                 then first level children and so on) and without duplicata
        """
        structures = self.mapped('struct_id')
        if not structures:
            return []
        # YTI TODO return browse records
        return list(set(structures._get_parent_structure().ids))




class ResourceMixin(models.AbstractModel):
    _inherit = "resource.mixin"

    def get_work_days_data(self, from_datetime, to_datetime, compute_leaves=True, calendar=None, domain=None):
        """
            By default the resource calendar is used, but it can be
            changed using the `calendar` argument.

            `domain` is used in order to recognise the leaves to take,
            None means default value ('time_type', '=', 'leave')

            Returns a dict {'days': n, 'hours': h} containing the
            quantity of working time expressed as days and as hours.
        """
        resource = self.resource_id
        calendar = calendar or self.resource_calendar_id

        # naive datetimes are made explicit in UTC
        if not from_datetime.tzinfo:
            from_datetime = from_datetime.replace(tzinfo=utc)
        if not to_datetime.tzinfo:
            to_datetime = to_datetime.replace(tzinfo=utc)

        # total hours per day: retrieve attendances with one extra day margin,
        # in order to compute the total hours on the first and last days
        from_full = from_datetime - timedelta(days=1)
        to_full = to_datetime + timedelta(days=1)
        intervals = calendar._attendance_intervals(from_full, to_full, resource)
        day_total = defaultdict(float)
        for start, stop, meta in intervals:
            day_total[start.date()] += (stop - start).total_seconds() / 3600

        # actual hours per day
        if compute_leaves:
            intervals = calendar._work_intervals(from_datetime, to_datetime, resource, domain)
        else:
            intervals = calendar._attendance_intervals(from_datetime, to_datetime, resource)
        day_hours = defaultdict(float)
        for start, stop, meta in intervals:
            day_hours[start.date()] += (stop - start).total_seconds() / 3600

        # compute number of days as quarters
        days = sum(
            float_utils.round(ROUNDING_FACTOR * day_hours[day] / day_total[day]) / ROUNDING_FACTOR
            for day in day_hours
        )
        return {
            'days': days,
            'hours': sum(day_hours.values()),
        }

class HrPayrollStructure(models.Model):
    """
    Salary structure used to defined
    - Basic
    - Allowances
    - Deductions
    """
    _inherit = 'hr.payroll.structure'


    def _get_parent_structure(self):

       
        return self
    def get_all_rules(self):

        """
        @return: returns a list of tuple (id, sequence) of rules that are maybe to apply
        """
        all_rules = []
        for struct in self:
            for rule in struct.rule_ids.filtered(lambda rule: rule):
                all_rules += [(rule.id, rule.sequence) for rule in self.rule_ids] 

        return all_rules

 
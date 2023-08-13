from odoo import api , fields , models , _
from odoo.exceptions import UserError , ValidationError
from datetime import datetime , date ,timedelta
import calendar

class ElectronPayslipWorked(models.Model):
    _inherit = 'hr.payslip.worked_days'
    
    @api.depends('is_paid', 'number_of_hours', 'payslip_id', 'contract_id.wage', 'payslip_id.sum_worked_hours')
    def _compute_amount(self):
        return
    
class CustomPayrollStructure(models.Model):
    _inherit = "hr.payroll.structure"
    
    journal_loan = fields.Many2one('account.journal' , string="Loans Journal")
    
    credit_account_loan = fields.Many2one('account.account' , string="Credit Account Loan")
    
class ElectronPayslip(models.Model):
    _inherit = 'hr.payslip'
    
    loan_line_id = fields.Many2one('hr.loan.line' )
    salary_advance = fields.Many2one('salary.advance')
    loan_amount = fields.Float(string="Amount Loan" , compute="_amount_loan_and_salary_advance",  readonly=True )
    # entry_loan = fields.Many2one('account.move' , string="Accounting Entry Loan"  )
    entry_partial_payment = fields.Many2many('account.move' , string="Accounting Partial Payment")
    # currency_id = fields.Many2one('res.currency', string='Currency', required=True)
    working_days = fields.Integer(string="Working of Days" , compute="_calculate_working_days")
    partial_amounts = fields.Float(string="Partial Amount" , default=0.0 )
           
    # journal_loan = fields.Many2one(
    #     'account.journal' ,
    #     string="Loans Journal" ,
    #     related='struct_id.journal_loan',
    # )
    # credit_account_loan = fields.Many2one(
    #     'account.account',
    #     string="Credit Account Loan",
    #     related = 'struct_id.credit_account_loan'
    # )
    
    
    def count_firday(self):
        num_days = 4
        
        year =  int(self.date_from.strftime("%Y"))
        month =  int(self.date_from.strftime("%m"))
        day_to_count = calendar.FRIDAY
        
        matrix = calendar.monthcalendar(year,month)

        num_days = sum(1 for x in matrix if x[day_to_count] != 0)
        
        return num_days
       
    # def create_loan_entry(self):
    #     loan_amount = float(self.loan_amount)

    #     if loan_amount <= 0:
    #         self.entry_loan = False
    #         return

    #     date_now = datetime.now()
    #     employee_account = int(self.employee_id.employee_account.id)
    #     account_to = self.credit_account_loan.id
    #     currency_id = self.currency_id.id
    #     journal_loan_id = self.journal_loan.id
    #     name = "Loan installments & SA"

    #     if not journal_loan_id or not account_to:
    #         raise ValidationError("Please add Loan Journal to Structure Employee to Create Entry loan")

    #     lines = [
    #         (0, 0, {
    #             'name': name,
    #             'account_id': account_to,
    #             'currency_id': currency_id,
    #             'amount_currency': loan_amount,
    #             'debit': 0,
    #             'credit': loan_amount
    #         }),
    #         (0, 0, {
    #             'name': name,
    #             'account_id': employee_account,
    #             'currency_id': currency_id,
    #             'amount_currency': loan_amount,
    #             'debit': loan_amount,
    #             'credit': 0
    #         })
    #     ]
    #     vals = {
    #         'journal_id': journal_loan_id,
    #         'ref': f'{date_now.strftime("%B")} - {date_now.strftime("%Y")}',
    #         'currency_id': currency_id,
    #         'line_ids': lines
    #     }
    #     move_list = [vals]
    #     entry_id = self.env['account.move'].sudo().create(move_list)
    #     self.entry_loan = entry_id 
            
    def count_firday_due(self):
        date_friday = self.date_from
        start_date = self.date_from
        employee_id = int(self.employee_id.id)
        num_friday = 0
        
        while date_friday <= self.date_to and start_date <= start_date:
            date_friday = start_date + timedelta((4 - start_date.weekday()) % 7)
            delta = date_friday - start_date
            delta = int(delta.days)
            attendance = self.env['hr.attendance'].search([('employee_id', '=', employee_id),
                                                           ('check_in','>=',start_date),
                                                           ('check_in','<',date_friday),
                                                           ('is_absent','=' , False)
                                                           ])
            num_working = len(attendance)
            attendance_rate = num_working / delta
            if attendance_rate >= 0.8:
                num_friday += 1
            
            start_date = date_friday + timedelta(days=1)
            date_friday = start_date + timedelta((4 - start_date.weekday()) % 7)
        return num_friday
    
    def get_loan_line(self, date_from, employee_id):
        loan = self.env['hr.loan'].search([('employee_id', '=', employee_id), 
                                        ('state', '=', 'paid')], limit=1)
        if not loan:
            return False

        # Find the first unpaid loan line before or on the payslip date
        line_loan = self.env['hr.loan.line'].search([('loan_id' , '=' , loan.id),
                                                      ('paid' , '=' , False)]
                                                      ,order='date asc' , limit = 1)

        if not line_loan:
            return False

        # Check if the loan line is within the same month and year as the payslip
        month_loan_line = line_loan.date.month
        year_loan_line = line_loan.date.year
        if date_from.month == month_loan_line and date_from.year == year_loan_line:
            return line_loan.id

        return False
             
    def get_salary_advance(self, date_from, employee_id):
        employee_id = int(employee_id)
        salary_advance = self.env['salary.advance'].search([('employee_id', '=', employee_id),
                                                            ('state', '=', 'approve'),
                                                            ('paid', '=', False)],
                                                        order='date asc', limit=1)
        if not salary_advance:
            return False

        # Calculate the expected payment month based on the previous salary advance date
        previous_date = salary_advance.date
        if previous_date.month == 12:
            expected_month = 1
        else:
            expected_month = previous_date.month + 1
            
        if int(date_from.strftime('%m')) == expected_month:
            return salary_advance.id
        
        return False

    def calucate_deduction_loan(self):
        employee_id = int(self.employee_id.id)
        loan = self.env['hr.loan'].search([('employee_id' , '=' , employee_id) , 
                                           ('state' , '=' , 'paid')] , limit = 1)

        type_entry_loan = self.env['hr.work.entry.type'].search([('code', '=', 'LODED')])
        month_payslip = self.date_from.strftime('%B %Y')
        if loan:
            
            line_loan = self.env['hr.loan.line'].search([('loan_id' , '=' , loan.id),
                                                           ('paid' , '=' , False)], order='date asc' , limit = 1)
            if line_loan:
                month_loan_line = line_loan.date.strftime('%B %Y')
                if month_payslip == month_loan_line :
                    self.worked_days_line_ids = [
                                                    (
                                                        0,
                                                        0,
                                                        {
                                                        'work_entry_type_id' : int(type_entry_loan.id), 
                                                        'name':f'Request Loan to {loan.name}',
                                                        'number_of_days': 0 ,
                                                        'number_of_hours':0,
                                                        'amount':- line_loan.amount,
                                                        }
                                                    )
                                                ]
                    
    def calucate_salary_advance(self , employee_id , month_payslip):
        salary_advance = self.env['salary.advance'].search([('employee_id' , '=' , employee_id),
                                                            ('state' , '=' , 'approve'),
                                                            ('paid' , '=' , False)
                                                            ] , limit = 1)
        if salary_advance:
            payment_month = int(salary_advance.date.strftime('%m'))
            if payment_month == 12:
                payment_month = 1
            else:
                payment_month = payment_month + 1
            if month_payslip == payment_month:
                type_entry_salary_advance = self.env['hr.work.entry.type'].search([('code', '=', 'SADV-07')])
                self.worked_days_line_ids =  [
                    (
                        0,
                        0,
                        {
                        'work_entry_type_id' : int(type_entry_salary_advance.id), 
                        'name':f'Request Salary Advance to {salary_advance.name}',
                        'number_of_days': 0 ,
                        'number_of_hours':0,
                        'amount':-salary_advance.advance,
                        }
                    )
                ]
                return True
        return False

    def calucate_paid_leave(self, emp_id, contract, count_month_days):
        duration = 0
        # Get leaves for the employee during the salary month
        leaves = self.env['hr.leave'].search([
            ('employee_id' , '=' , emp_id),
            ('request_date_from' , '>=' , self.date_from),
            ('request_date_to' , '<=' , self.date_to),
            ('state' , '=' , 'validate')
        ])
        
        for rec in leaves:
            if rec.holiday_status_id.is_paid == True and rec.holiday_status_id.is_public == False:
                duration = rec.number_of_days + duration
        
        type_entry_leave = self.env['hr.work.entry.type'].search([('code', '=', 'LEVE-06')])

        salary = contract.wage + contract.housing_allowance 
        salary = salary / count_month_days  if self.company_id.name == "Electron Trading 2023" else salary / 30 
        leave_salary = int(salary * duration)
        if leave_salary > 0:
            self.worked_days_line_ids =  [
                    (
                        0,
                        0,
                        {
                        'work_entry_type_id' : int(type_entry_leave.id), 
                        'name':f'Allowance Paid Leave ',
                        'number_of_days': duration ,
                        'number_of_hours':0.0,
                        'amount': leave_salary,
                        }
                    )
                ] 
    
    def calucate_paid_public_leave(self, emp_id, total_salary, count_month_days):
        duration = 0
        # Get leaves for the employee during the salary month
        leaves = self.env['hr.leave'].search([
                                                ('employee_id' , '=' , emp_id),
                                                ('request_date_from' , '>=' , self.date_from),
                                                ('request_date_from' , '<' , self.date_to),
                                                ('holiday_status_id.is_paid' , '=' , True),
                                                ('holiday_status_id.is_public' , '=' , True),
                                                ('state' , '=' , 'validate')
                                            ])
        
        for rec in leaves:
            duration = rec.number_of_days + duration
        
        type_entry_leave = self.env['hr.work.entry.type'].search([('code', '=', 'PCLV-08')])

        salary = total_salary/ count_month_days if self.company_id.name == "Electron Trading 2023" else total_salary/30

        leave_salary = int(salary * duration)
        if leave_salary > 0:
            self.worked_days_line_ids =  [
                    (
                        0,
                        0,
                        {
                        'work_entry_type_id' : int(type_entry_leave.id), 
                        'name':f'Allowance Public Paid Leave ',
                        'number_of_days': duration ,
                        'number_of_hours':0.0,
                        'amount': leave_salary,
                        }
                    )
                ] 
          
    def calucate_basic_salary(self, working_days, total_salary, count_month_days):
        type_entry_attendance = self.env['hr.work.entry.type'].search([('code', '=', 'BASA-01')])
        
        working_days1 = working_days + self.count_firday_due()
        
        rate_month = working_days1 / count_month_days if self.company_id.name == "Electron Trading 2023" else working_days / 30
            
        basic_salary = rate_month * total_salary
        
        return [
                (
                    0,
                    0,
                    {
                    'work_entry_type_id' : int(type_entry_attendance.id), 
                    'name':'Basic Salary Based on Attendance',
                    'number_of_days':working_days1,
                    'number_of_hours':0.0,
                    'amount':int(basic_salary),
                    }
                )
            ]
    
    def calucate_friday_overtime(self , working_hours , total_salary, count_month_days):
        type_entry_friday_OT = self.env['hr.work.entry.type'].search([('code', '=', 'FNOT-03')])
        
        rate_hour = total_salary / (count_month_days*8) if self.company_id.name == "Electron Trading 2023" else total_salary / (30*8)
        
        salary = working_hours * rate_hour * 1.5
        if salary > 0:
            self.worked_days_line_ids = [
                (
                    0,
                    0,
                    {
                    'work_entry_type_id' : int(type_entry_friday_OT.id), 
                    'name':'Friday Overtime Salary',
                    'number_of_days': 0 ,
                    'number_of_hours':working_hours,
                    'amount':salary,
                    }
                )
            ] 
        
    def calucate_normal_overtime(self , normal_overtime, total_salary, count_month_days):
        type_entry_normal_OT = self.env['hr.work.entry.type'].search([('code', '=', 'NOTS-04')])
        
        rate_hour = total_salary / (count_month_days*8) if self.company_id.name == "Electron Trading 2023" else total_salary / (30*8)
        
        salary = normal_overtime * rate_hour * 1.25
        if salary > 0:
            self.worked_days_line_ids =  [
                (
                    0,
                    0,
                    {
                    'work_entry_type_id' : int(type_entry_normal_OT.id), 
                    'name':'Normal Overtime Salary',
                    'number_of_days': 0 ,
                    'number_of_hours':normal_overtime,
                    'amount':salary,
                    }
                )
            ] 
    
    def check_absent_employee(self , employee_id):
        total_hours = 0
        attendance = self.env['hr.attendance'].search([('employee_id', '=', employee_id),
                                                ('check_in','>=',self.date_from),
                                                ('check_in','<=',self.date_to),
                                                ('is_absent','=' , True)
                                                ])
        for rec in attendance:
            year = int(rec.check_in.strftime('%Y'))
            month = int(rec.check_in.strftime('%m'))
            day = int(rec.check_in.strftime('%d'))
            check_in = datetime(year , month , day)
            
            leave = self.env['hr.leave'].search([('employee_id' , '=' , employee_id),
                                                ('request_date_from' , '=' , check_in),
                                                ('state' , '=' , 'validate')
                                                ] ,limit = 1)
            
            if leave.holiday_status_id.code == "SHTL-02":
                if total_hours <= 9 and len(leave) == 1:
                    rec.is_absent = False
                    rec.note = "Short time leave is Accepted"
                    total_hours = total_hours + leave.number_of_hours_display
                else :
                    rec.note = "The leave balance has Expired"
    
    def deduction_unauthorized_leave(self, employee_id, total_salary, working_days, count_month_days):
        duration = 0
        leaves = self.env['hr.leave'].search([
                                                ('employee_id' , '=' , employee_id),
                                                ('request_date_from' , '>=' , self.date_from),
                                                ('request_date_from' , '<' , self.date_to),
                                                ('state' , '=' , 'validate'),
                                                ('holiday_status_id.code' , '=' , 'AULE-02')
                                            ])
        leaves_paid = self.env['hr.leave'].search([
                                                ('employee_id' , '=' , employee_id),
                                                ('request_date_from' , '>=' , self.date_from),
                                                ('request_date_from' , '<' , self.date_to),
                                                ('holiday_status_id.is_paid' , '=' , True),
                                                ('state' , '=' , 'validate')
                                            ])
        
        for rec in leaves:
            duration = rec.number_of_days + duration
        
        for rec in leaves_paid:
            duration += rec.number_of_days
        type_entry_deduction = self.env['hr.work.entry.type'].search([('code', '=', 'UNDE-99')])

        
        working_days1 = working_days + self.count_firday_due() + duration
        unauthroized_day = count_month_days - working_days1 if self.company_id.name == "Electron Trading 2023" else 30 - working_days1
        rate_month = unauthroized_day / count_month_days if self.company_id.name == "Electron Trading 2023" else unauthroized_day / 30
        deduction_salary = rate_month * total_salary
        
        if True:
            self.worked_days_line_ids = [
                                            (
                                                0,
                                                0,
                                                {
                                                'work_entry_type_id' : int(type_entry_deduction.id), 
                                                'name':'Unauthorized Absence Deductions',
                                                'number_of_days':unauthroized_day,
                                                'number_of_hours':0.0,
                                                'amount':float(deduction_salary * -1) ,
                                                }
                                            )
                                        ]
    
    def calucate_end_services_paid(self):
        employee = self.employee_id
        contract_emp = self.contract_id
        total_salary = contract_emp.total_start
        days = int(self.working_days)
        rate = (days / 365) * 21
        rate_day_salary = (1 / 30) * total_salary
        amount_service = rate * rate_day_salary
        
        employee.worked_day += days
        employee.end_service_amount = employee.end_service_amount + amount_service
        
    def calucate_leave_allowance(self):
        employee = self.employee_id
        contract = self.contract_id
        salary = contract.wage + contract.housing_allowance 
        date = contract.first_contract_date
        date1 = self.date_to
        try:
            num_day = 21
            diff = (date1 - date).total_seconds() / (3600 * 24)

            if diff > 1825.0:
                num_day = 28
                
            rate = (self.working_days / 365) * num_day
            rate_day_salary = (1 / 30) * salary
            leave_allowance = rate * rate_day_salary
            employee.end_leave_allowance = employee.end_leave_allowance + leave_allowance
        except:
            pass
    
    def create_entry(self):
        self.action_payslip_done()
        self.loan_line_id.paid = True
        self.loan_line_id.loan_id.total_paid_amount += self.loan_line_id.amount    
        self.loan_line_id.payslip_id = self.id   
           

    # def group_project(self):
    #     attendance = self.env['hr.attendance'].search([('employee_id', '=', self.employee_id.id),
    #                                             ('check_in','>=',self.date_from),
    #                                             ('check_in','<=',self.date_to),
    #                                             ('is_absent','=' , False)
    #                                             ])
    #     grouped_project = {}
    #     for rec in attendance:
    #         project = rec.projects.name
            
    #         if project not in grouped_project:
    #             grouped_project[project] = []
            
    #             grouped_project[project].append(rec)   
                
    #         keys = ""
    #         for x in grouped_project.keys():
    #             keys += str(x) + " - "  + str(len(grouped_project[x]))
    #         raise UserError(keys)
        
    # @api.depends('worked_days_line_ids')
    # def _amount_loan_and_salary_advance(self):
    #     amount = 0
    #     for record in self:
    #         for rec in record.worked_days_line_ids:
    #             if rec.work_entry_type_id.code == 'LODED' or rec.work_entry_type_id.code == "SADV-07":
    #                 amount = rec.amount + amount
    
    @api.depends('worked_days_line_ids')
    def _calculate_working_days(self):
        days = 0
        for record in self:
            for rec in record.worked_days_line_ids:
                if rec.work_entry_type_id.code == "BASA-01":
                    days = rec.number_of_days
            record.working_days = days
            
    @api.onchange('struct_id','date_form','date_to')
    def calculate_salary(self):
        working_days , fridays_overtime , normal_overtime = 0 , 0 , 0
        month_payslip , year_payslip = int(self.date_from.month) , int(self.date_from.year)
        
        if self.struct_id:
            # # Get Basic Information to Calucate Salary  
            employee_id = int(self.employee_id.id)
            contract_emp = self.contract_id
            total_salary = contract_emp.total_start
            wage = contract_emp.wage
            is_overtime = contract_emp.is_overtime
            count_month_days = calendar.monthrange(year_payslip, month_payslip)[1]
            # Attendance to Empolyee 
            attendance = self.env['hr.attendance'].search([('employee_id', '=', employee_id),
                                                           ('check_in','>=',self.date_from),
                                                           ('check_in','<=',self.date_to),
                                                           ('is_absent','=' , False)
                                                           ])
            # check absent records if any Short Time off leave is accepted
            
            self.check_absent_employee(employee_id)
            
            for record in attendance:
                day = record.check_in.strftime('%A')
                
                if day == "Friday":
                    fridays_overtime = fridays_overtime + record.worked_hours  
                else:
                    working_days = working_days + 1
                    normal_overtime = normal_overtime + record.normal_overtime
                    
            self.worked_days_line_ids = [(5,0,0)]
            self.working_days = working_days
            self.worked_days_line_ids = self.calucate_basic_salary(working_days, total_salary, count_month_days)
             
            if is_overtime:
                self.calucate_friday_overtime(fridays_overtime, wage, count_month_days)
                self.calucate_normal_overtime(normal_overtime, wage, count_month_days)
                
            self.calucate_paid_leave(employee_id, contract_emp, count_month_days)
            
            self.calucate_paid_public_leave(employee_id , total_salary,count_month_days)
            
            self.calucate_deduction_loan()
            self.calucate_salary_advance(employee_id , month_payslip)            

            self.deduction_unauthorized_leave(employee_id, total_salary, working_days, count_month_days)  
      
    @api.model
    def create(self, values):
        date_from = 0
        if isinstance(values['date_from'], datetime):
            date_from = values['date_from']
        else:
            date_string = str(values['date_from'])            
            date_format = '%Y-%m-%d' 
            date_from = datetime.strptime(date_string, date_format)
            
        employee_id = int(values['employee_id'])
        values['loan_line_id'] = self.get_loan_line(date_from , employee_id)
        values['salary_advance'] = self.get_salary_advance(date_from , employee_id)
        
        record = super(ElectronPayslip, self).create(values)
        return record

    def write(self, vals):
        date_from = 0
        if self.date_from:
            date_from = self.date_from
        else:
            date_string = vals['date_from']            
            date_format = '%Y-%m-%d' 
            date_from = datetime.strptime(date_string, date_format)

        
        employee_id = 0
        if self.employee_id:
            employee_id = self.employee_id.id
        else :
            employee_id = int(vals['employee_id'])
        vals['loan_line_id'] = self.get_loan_line(date_from , employee_id)
        vals['salary_advance'] = self.get_salary_advance(date_from , employee_id)
        
        res = super(ElectronPayslip, self).write(vals)
        return res
    
    def open_partial_payment_wizard(self):
       
        return {
            'name': 'Partial Payment Wizard',
            'type': 'ir.actions.act_window',
            'res_model': 'partial.payment.payslip',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_payslip_id': self.id}
        }
    
    def partial_payment_payslip(self , amount, date, account):
        if self.state == 'verify':
            if amount >= self.net_wage:
                raise UserError('The amount to be paid is greater than the amount due for this salary slip')

            date_now = datetime.now()
            employee_account = int(self.employee_id.employee_account.id)
            account_from = account.id
            currency_id = self.currency_id.id
            journal_salary_id = self.journal_id.id
            name = "Partial Payment Payslip"

            if not journal_salary_id or not account_from:
                raise ValidationError("Please add Account From ..!")

            lines = [
                (0, 0, {
                    'name': name,
                    'account_id': employee_account,
                    'currency_id': currency_id,
                    'amount_currency': amount,
                    'debit': 0,
                    'credit': amount
                }),
                (0, 0, {
                    'name': name,
                    'account_id': account_from,
                    'currency_id': currency_id,
                    'amount_currency': amount,
                    'debit': amount,
                    'credit': 0
                })
            ]
            
            vals = {
                'journal_id': journal_salary_id,
                'ref': f'Partial Payment to Payslip {date_now.strftime("%B")} - {date_now.strftime("%Y")} ',
                'currency_id': currency_id,
                'date':date , 
                'line_ids': lines
            }
            
            move_list = [vals]
            entry_id = self.env['account.move'].sudo().create(move_list)
            self.entry_partial_payment += entry_id
            activity = self.activity_schedule(
                    activity_type_id=self.env.ref('mail.mail_activity_data_todo').id,
                    summary= "Partial Payment",
                    note=f"A partial payment has been made to an employee in the amount of {amount}",
                    user_id=self.env.user.id
                )
            
            activity.action_done()
            
            payslip_input_type = self.env['hr.payslip.input.type'].search([('code' , '=' , 'PPDED')])
            records = self.env['hr.payslip']
            
            self.input_line_ids = [
                                            (
                                                0,
                                                0,
                                                {
                                                    'input_type_id' : int(payslip_input_type.id),
                                                    'amount':amount,
                                                    'entry_id' : entry_id.id
                                                }
                                            )
                                        ]
            self.partial_amounts += amount
            # self.employee_id.payslip_amount += amount
            # self.employee_id.payslip_paid += amount
            self.compute_sheet()
            
        elif self.state == 'done':
            raise UserError('The payment of the salary has been finalized, meaning that the necessary financial transactions have been recorded to account for the value of the salary.')
        else:
            raise UserError("Partial payment cannot be made as long as the days are not Compute Sheet")
           
class ElecBatchesPayslip(models.Model):
    _inherit = 'hr.payslip.run'
   
    total_balance = fields.Integer(
        string="Total Balance",
        compute="_compute_total_balance"
    )
      
    
    @api.depends('slip_ids')
    def _compute_total_balance(self):
        total = 0
        for rec in self:
            for slip in rec.slip_ids:
                total = slip.net_wage + total
            rec.total_balance = total
         
class PartialPayment(models.TransientModel):
    _name = "partial.payment.payslip"
    
    amount = fields.Float(string="Amount", required=True)
    date = fields.Date(string="Date")
    debit_account = fields.Many2one('account.account' , string="Debit Account" , required=True)
    payslip_id = fields.Many2one(string = "Payslip")
    
    def action_payment(self):
        pay_id = self.payslip_id.id
        payslip = self.env['hr.payslip'].search([('id', '=' , pay_id)])
        amount = self.amount
        date = self.date
        account = self.debit_account
        payslip.partial_payment_payslip(amount , date , account)

class InputsPayslipInherit(models.Model):
    _inherit = 'hr.payslip.input'             
    entry_id = fields.Many2one('account.move' , string="Entry")
    
    def unlink(self):
        for rec in self:
            if rec.entry_id.state == 'posted' or rec.entry_id == False:
                raise UserError('Partial payments cannot be deleted if the payment is related to a posted entry')
            self.payslip_id.partial_amounts -= self.amount
            rec.entry_id.unlink()
        return super(InputsPayslipInherit, self).unlink()
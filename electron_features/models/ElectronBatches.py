from odoo import api , fields , models ,_
from odoo.exceptions import UserError , ValidationError
from datetime import datetime , timedelta
from calendar import monthrange
import calendar

class ElectronBatches(models.Model):
    _inherit = 'hr.payslip.run'
    
    def check_absent_employee(self , employee_id ):
        total_hours = 0
        attendance = self.env['hr.attendance'].search([('employee_id', '=', employee_id),
                                                ('check_in','>=',self.date_start),
                                                ('check_in','<=',self.date_end),
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
    
    def create_payslips_monthly(self):
        # Select all empolyee in company
        employees = self.env['hr.employee'].search([])
        today = datetime.now()
        
        for employee in employees:
            contract = self.env['hr.contract'].search([
            ('employee_id', '=', employee.id)],limit=1)
            employee_id = int(employee.id)
            if contract and contract.state == 'open':
                total_salary = contract.total_start
                is_overtime = contract.is_overtime
                working_days = 0
                fridays_overtime = 0
                normal_overtime = 0
                month_payslip = int(self.date_start.strftime('%m'))
                
                attendance = self.env['hr.attendance'].search([('employee_id', '=', employee_id),
                                                            ('check_in','>=',self.date_start),
                                                            ('check_in','<=',self.date_end),
                                                            ('is_absent','=' , False)
                                                            ])
                self.check_absent_employee(employee.id)
                
                for rec in attendance:
                    day = rec.check_in.strftime('%A')
                
                    if day == "Friday":
                        fridays_overtime = fridays_overtime + rec.worked_hours  
                    else:
                        working_days = working_days + 1
                        normal_overtime = normal_overtime + rec.normal_overtime
                    
                # Calucate Number of Days Based on Daily Hours Working 
               
                vals = {
                    'name' : f"Salary Slip - {employee.name} - {today.strftime('%B')} - {today.strftime('%Y')}",
                    'date_from' : self.date_start,
                    'date_to' : self.date_end,
                    'company_id' : 1,
                    'contract_id':contract.id,
                    'struct_id':6,
                    'employee_id' : employee_id,
                    'payslip_run_id' : self.id,
                }
                payslip = self.env['hr.payslip'].create(vals)
                payslip.number = "SLP/0" + str(payslip.id)
                payslip.worked_days_line_ids = [(5,0,0)]

                payslip.calculate_salary()
      
                payslip.compute_sheet()
                payslip.create_entry()
                
        return True

    def first_and_last_day_of_month(self , date):
        # Get the first day of the month
        first_day = date.replace(day=1)
        
        # Get the last day of the month
        if date.month == 12:
            last_day = date.replace(year=date.year+1, month=1, day=1) - timedelta(days=1)
        else:
            last_day = date.replace(month=date.month+1, day=1) - timedelta(days=1)
        first_day = first_day.date()
        last_day = last_day.date()
        
        return (first_day, last_day)
    
    @api.model
    def create_batch_salary(self):
        today = datetime.now()
        month = int(today.strftime('%m'))
        year = int(today.strftime('%Y'))
        
        if month == 1:
            month = 12
            year = year - 1
        else:
            month = month - 1

        date = datetime(year , month , 1)
        first_day, last_day = self.first_and_last_day_of_month(date)
        vals = {
            'name': f"{today.strftime('%B')} - {today.strftime('%Y')}",
            'date_start': first_day,
            'date_end': last_day,
        }
        new_batche = self.env['hr.payslip.run'].create(vals)
        new_batche.create_payslips_monthly()
        new_batche.state = 'close'
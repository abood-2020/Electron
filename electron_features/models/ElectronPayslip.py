from odoo import api , fields , models , _
from odoo.exceptions import UserError , ValidationError

class ElectronPayslipWorked(models.Model):
    _inherit = 'hr.payslip.worked_days'
    
    @api.depends('is_paid', 'number_of_hours', 'payslip_id', 'contract_id.wage', 'payslip_id.sum_worked_hours')
    def _compute_amount(self):
        return
    
class ElectronPayslip(models.Model):
    _inherit = 'hr.payslip'
    
    def calculate_payslip(self , actual_hours , required_hours , overtime_pay , basic_salary):
        salary = 0

        if actual_hours >= required_hours:
            diff_hours = actual_hours - required_hours
            salary = basic_salary + (diff_hours * overtime_pay)
        else:
            if required_hours > 0:
                amount_per_hour = basic_salary / required_hours
                salary = actual_hours *  amount_per_hour
            else:
                ValidationError("Please insert the basic information about the salary in the employee contract")
        return salary
    
    @api.onchange('struct_id','date_form','date_to')
    def calculate_salary(self):
        salary = 0
        working_hours = 0
        working_days = 0
        
        if self.struct_id:
            employee_id = int(self.employee_id.id)
            contract_emp = self.env['hr.contract'].search([
                            ('employee_id', '=', employee_id)
                            ],limit=1)
            original_working_hours = contract_emp.working_hours
            original_salary = contract_emp.wage
            daily_working_hours = contract_emp.daily_hours
            pay_overtime = contract_emp.pay_overtime
            
            # Attendance to Empolyee 
            attendance = self.env['hr.attendance'].search([('employee_id', '=', employee_id),
                                                           ('check_in','>=',self.date_from),
                                                           ('check_in','<=',self.date_to)
                                                           ])
            
            for record in attendance:
                working_hours = working_hours + record.worked_hours
                working_days = working_days + 1
                
            working_hours = int(working_hours)
            if daily_working_hours > 0:
                working_days = "%.1f" %(working_hours / daily_working_hours)
            else:
               raise  ValidationError("Please insert the basic information about the salary in the employee contract")

            # calculate salary to empolyee based on working hours 
            salary = self.calculate_payslip(working_hours,original_working_hours,pay_overtime,original_salary)
                
            # add salary to worked days line 
            type_work_entry = self.env['hr.work.entry.type'].search([('id', '=', 1)])
            
            attendance_salary = [
                        (
                            0,
                            0,
                            {
                            'work_entry_type_id' : type_work_entry, 
                            'name':'Attendance Salary Code',
                            'number_of_days':working_days,
                            'number_of_hours':working_hours,
                            'amount':int(salary),
                            }
                        )
                    ]
            self.worked_days_line_ids = [(5,0,0)]
            self.worked_days_line_ids = attendance_salary


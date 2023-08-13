from odoo import api, fields, models, _
from odoo.exceptions import UserError

class ElecEmployee(models.Model):
    _inherit = 'hr.employee'
    
    # leave_ids = fields.One2many('hr.leave.report' , 'employee_id' ,string="Leaves")
    employee_account = fields.Many2one('account.account' , string="Account Empolyee")
    
    amount_loan = fields.Float(string="Amount Loan")
    amount_paid_loan = fields.Float(string="Amount Paid Loan" , compute="_get_info_loan")
    
    payslip_amount = fields.Float(string="Total Payslips Owed" , compute="_compute_amount_payslip")
    payslip_paid = fields.Float(string="Total Payslips Paid")
   
    worked_day = fields.Integer(string="Worked Days" , readonly=True)
    end_service_amount = fields.Float(string="End of Services" , readonly = True)
    end_service_paid = fields.Float(string="End of Services Paid" , readonly=True)
    
    end_leave_allowance = fields.Float(string="Leave Allowance" , readonly = True)
    end_leave_paid = fields.Float(string="Leave Allowance Paid" , readonly=True)
    
    struct_id = fields.Many2one('hr.payroll.structure' , string="Structure")
    
    @api.depends('slip_ids')
    def _compute_amount_payslip(self):
        for rec in self:
            amount = 0
            amount_paid = 0
            for record in self.slip_ids:
                amount += record.basic_wage
                if record.move_id.state == 'posted':
                    amount_paid = amount_paid + record.basic_wage
                for entry in  record.entry_partial_payment:
                    if entry.state =='posted':
                         amount_paid += entry.amount_total_signed
            rec.payslip_amount = amount
            rec.payslip_paid = amount_paid
            
    
    @api.onchange('leave_ids.number_of_days')
    def _compute_balence_casual(self):
        balance_leave = 0
        id_user = int(self.id)
        for rec in self:
            for leave in rec.leave_ids:
                if leave.holiday_status_id.name == 'casual_leave' and leave.state == "validate":
                    balance_leave = balance_leave + leave.number_of_days
        self.casual_leave = balance_leave
        self.env.cr.execute(f"""UPDATE hr_employee SET casual_leave= {balance_leave} WHERE id={id_user}""")
        

            
    def button_balance(self):
        employees = self.env['hr.employee'].search([])
        for rec in employees:
            rec._compute_balence_casual()
            
    def _get_info_loan(self):
        for rec in self:
            employee_id = rec.id
            loan = self.env['hr.loan'].search([('employee_id', '=', employee_id)] , limit=1)
            if loan:
                rec.amount_paid_loan = loan.total_paid_amount
                rec.amount_loan = loan.total_amount
            else:
                rec.amount_loan = 0.0
                rec.amount_paid_loan = 0.0
                
    def compute_salary_advacnce(self , employee_id ):
        for rec in self:
            loans = self.env['account.move'].search([
                'employee_id' , "=" , employee_id
            ])
from odoo import models, fields, api
from datetime import datetime, timedelta

# class CustomPayment(models.Model):
#     _inherit = 'account.payment'
#     sale_person = fields.Many2one('res.users' ,String ='Sale Person')
                
class CommissionPayment(models.Model):
    _name = 'commission.payment'
    _order = "month_number asc"
    
    user = fields.Many2one('res.users' , String="User")
    month = fields.Char(String="Month")
    month_number = fields.Integer(String="Month Number" ,default=0)
    bank_journal = fields.Float(String="Bank Journal Amount")
    cash_journal = fields.Float(String="Cash Journal Amount")
    sales_amount = fields.Float(String="Receivable Amount")
    commission = fields.Float(String="Commission", compute="_compute_commission")
    
    @api.depends('sales_amount')
    def _compute_commission(self):
        for rec in self:
            if 0 <= rec.sales_amount <= 10000:
                rec.commission = round(rec.sales_amount * 0, 1)
            elif 10000 < rec.sales_amount <= 30000:
                rec.commission = round(rec.sales_amount * 0.01, 1)
            elif 30000 < rec.sales_amount <= 50000:
                rec.commission = round(rec.sales_amount * 0.02, 1)
            elif 50000 < rec.sales_amount <= 100000:
                rec.commission = round(rec.sales_amount * 0.03, 1)
            else:
                rec.commission = round(rec.sales_amount * 0.04, 1)
                
    @api.model
    def update_records_commissions_payments(self):
        users = self.env['res.users'].search([('company_id', '=', 5)])
        records = self.search([])
        
        for rec in records:
            rec.unlink()
        
        for user in users:
            # Check if a record already exists for the current month
            payments = self.env['account.payment'].search([('sale_person', '=', int(user.id)) ,('payment_type', '=', 'inbound')],order="date ASC")
            for rec in payments:
                current_month = rec.date.strftime('%B %Y')
                existing_record = self.search([('month', '=', current_month) , ('user', '=', user.id)])
            
                if not existing_record:
                    record = self.create({
                        'user': user.id,
                        'month': current_month,
                        'month_number':int(rec.date.strftime('%m')), 
                        'bank_journal': 0,
                        'cash_journal': 0,
                        'sales_amount': 0,
                    })
                else:
                    record = existing_record
                    
                if rec.journal_id.code == 'CSH1':
                    record.cash_journal += rec.amount
                elif rec.journal_id.code == 'BNK1':
                    record.bank_journal += rec.amount
                    
                record.sales_amount += rec.amount
           
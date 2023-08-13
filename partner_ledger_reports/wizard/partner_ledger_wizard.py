from odoo import fields, models, api
from datetime import date, datetime
from odoo.exceptions import UserError

class AccountPartnerLedger(models.TransientModel):
    _name = "account.report.partner.ledger"
    _description = "Account Partner Ledger"

    date_from = fields.Date(string="Date From" , default =date.today() , required=True)
    date_to = fields.Date(string="Date To" , default=date.today() , required=True)
    partner_id = fields.Many2one('res.partner',string="Partner")
    journal_id = fields.Many2one('account.journal',string="Journal" )
    payable_account = fields.Boolean(string="Paypal Account" , default=True)
    recievable_account = fields.Boolean(string="Recievable Account" , default=True)
    is_summary = fields.Boolean(string="Summary", default=False)    
    user_ids = fields.Many2many('res.users',string="Sales Person")

    def check_report(self):
        if not self.partner_id and not self.is_summary:
            raise UserError("Please select a Partner")
        
        data = {}
        data['date_from'] = self.date_from
        data['date_to'] = self.date_to
        data['partner_id'] = self.partner_id.name
        data['journal'] = self.journal_id.name
        
        data['lines'] = []
        move_line_pervious = self.env['account.move.line'].search([
            ('date' , '<' , self.date_from),
            ('partner_id' , '=' ,self.partner_id.id),
            ('move_id.state' , '=' , 'posted'),
            '|',
            ('account_id.internal_type', '=', 'payable' if self.payable_account else ''),
            ('account_id.internal_type', '=', 'receivable' if self.recievable_account else '')
        ])
        initial_balance = 0 
        for rec in move_line_pervious:
            initial_balance += rec.balance

        data['initial_balance'] = round(initial_balance , 1)
        
        move_lines = self.env['account.move.line'].search([
            ('date', '>=', self.date_from),
            ('date', '<=', self.date_to),
            ('partner_id', '=', self.partner_id.id),
            ('move_id.state' , '=' , 'posted'),
            '|',
            ('account_id.internal_type', '=', 'payable' if self.payable_account else ''),
            ('account_id.internal_type', '=', 'receivable' if self.recievable_account else '')
        ], order='date')
        
        payments = self.env['account.payment'].search([
            ('move_id.line_ids' , 'in' , move_lines.ids)
        ])
        for rec in move_lines:
            initial_balance += rec.balance
            initial_balance = round(initial_balance , 1)
            memo = ' - '
            for payment in payments:
                if payment.move_id.id == rec.move_id.id:
                    memo = str(payment.ref)
            else:
                memo = rec.move_id.payment_reference or rec.move_id.ref
                    # memo = rec.move_id.payment_reference 
            new_object = [rec.date ,             # 0
                          rec.move_id.name,     # 1
                          rec.account_id.code,  # 2
                          rec.journal_id.code,  # 3
                          rec.date_maturity,    # 5
                          rec.name,             # 4
                          rec.debit,            # 6
                          rec.credit,           # 7
                          rec.balance,          # 8
                          rec.matching_number,  # 9
                          initial_balance,      # 10
                          memo]  # 11
            
            data['lines'].append(new_object)
        report_action = None
        if self.is_summary:
            report_action =  self.get_data_summary_partnes_report()
        elif self.user_ids:
            report_action =  self.get_data_summary_partnes_report()
        else:
            report_action =  self.env.ref('partner_ledger_reports.action_report_partner_ledger').report_action(5,data=data)
        
        return report_action

    def get_total_recievable_payable(self):
        
        # move_line_pervious = self.env['account.move.line'].search([
        #     ('date' , '<' , self.date_from),
        #     ('move_id.state' , '=' , 'posted'),
        #     '|',
        #     ('account_id.internal_type', '=', 'payable'),
        #     ('account_id.internal_type', '=', 'receivable')
        # ])
        # balance_payable = 0
        # balance_receivable = 0 
        # for rec in move_line_pervious:
        #     if rec.account_id.internal_type == 'payable':
        #         balance_receivable += rec.balance
        #     elif rec.account_id.internal_type == 'receivable':
        #         balance_receivable += rec.balance
                
                
        move_lines = self.env['account.move.line'].search([
            ('date', '<=', self.date_to),
            ('move_id.state' , '=' , 'posted'),
            '|',
            ('account_id.internal_type', '=', 'payable'),
            ('account_id.internal_type', '=', 'receivable')
        ], order='date')
        
        balance_payable = 0
        balance_receivable = 0 
        
        for rec in move_lines:
            if rec.account_id.internal_type == 'payable':
                balance_payable += rec.balance
            elif rec.account_id.internal_type == 'receivable':
                balance_receivable += rec.balance
        data = [balance_payable, balance_receivable]        
        return data
    
    def get_data_summary_partnes_report(self):
        new_data = {}
        new_data['lines'] = []
        new_data['users'] = []
        new_data['date_from'] = self.date_from
        new_data['date_to'] = self.date_to
        new_data['journal'] = self.journal_id.name
        
        new_data['lines'] = []
                
        move_lines = self.env['account.move.line'].search([
            ('date', '>=', self.date_from),
            ('date', '<=', self.date_to),
            ('move_id.state' , '=' , 'posted'),
            '|',
            ('account_id.internal_type', '=', 'payable' if self.payable_account else ''),
            ('account_id.internal_type', '=', 'receivable' if self.recievable_account else '')
        ], order='date')
        
        partner_ids = set(move_line.partner_id.id for move_line in move_lines)
        balance_receivable = 0
        for rec in partner_ids:
            partner = self.env['res.partner'].search([('id' , '=' , rec)])
            move_line_pervious = self.env['account.move.line'].search([
                ('date' , '<' , self.date_from),
                ('partner_id' , '=' ,partner.id),
                ('move_id.state' , '=' , 'posted'),
                '|',
                ('account_id.internal_type', '=', 'payable' if self.payable_account else ''),
                ('account_id.internal_type', '=', 'receivable' if self.recievable_account else '')
            ])
            
            move_lines = self.env['account.move.line'].search([
                ('date', '>=', self.date_from),
                ('date', '<=', self.date_to),
                ('partner_id', '=', partner.id),
                ('move_id.state' , '=' , 'posted'),
                '|',
                ('account_id.internal_type', '=', 'payable' if self.payable_account else ''),
                ('account_id.internal_type', '=', 'receivable' if self.recievable_account else '')
            ], order='date')
            
            initial_balance = 0
            for rec in move_line_pervious:
                initial_balance += rec.balance

            balance = initial_balance
            for rec in move_lines:
                balance = balance + rec.balance
            
            new_object = [partner.name , round(balance , 1), partner.user_id.name]
            
            if balance > 0:
                balance_receivable += balance
                new_data['lines'].append(new_object)

        for user in self.user_ids:
            new_data['users'].append(user.name)
            
        new_data['balance_receivable'] = round(balance_receivable , 1)
        if len(new_data['users']) != 0:
            return self.env.ref('partner_ledger_reports.action_summary_report_partner_ledger_filter_as_users').report_action(5,data=new_data)
         
        return self.env.ref('partner_ledger_reports._action_summary_report_partner_ledger').report_action(5,data=new_data)     
    
    def print_xlsx_report(self):
        if not self.partner_id and not self.is_summary:
            raise UserError("Please select a Partner")
        
        data = {}
        data['date_from'] = self.date_from
        data['date_to'] = self.date_to
        data['partner_id'] = self.partner_id.name
        data['journal'] = self.journal_id.name
        
        data['lines'] = []
        move_line_pervious = self.env['account.move.line'].search([
            ('date' , '<' , self.date_from),
            ('partner_id' , '=' ,self.partner_id.id),
            ('move_id.state' , '=' , 'posted'),
            '|',
            ('account_id.internal_type', '=', 'payable' if self.payable_account else ''),
            ('account_id.internal_type', '=', 'receivable' if self.recievable_account else '')
        ])
        initial_balance = 0 
        for rec in move_line_pervious:
            initial_balance += rec.balance

        data['initial_balance'] = round(initial_balance , 1)
        
        move_lines = self.env['account.move.line'].search([
            ('date', '>=', self.date_from),
            ('date', '<=', self.date_to),
            ('partner_id', '=', self.partner_id.id),
            ('move_id.state' , '=' , 'posted'),
            '|',
            ('account_id.internal_type', '=', 'payable' if self.payable_account else ''),
            ('account_id.internal_type', '=', 'receivable' if self.recievable_account else '')
        ], order='date')
        
        payments = self.env['account.payment'].search([
            ('move_id.line_ids' , 'in' , move_lines.ids)
        ])
        for rec in move_lines:
            initial_balance += rec.balance
            initial_balance = round(initial_balance , 1)
            memo = ' - '
            for payment in payments:
                if payment.move_id.id == rec.move_id.id:
                    memo = str(payment.ref)
            else:
                memo = rec.move_id.payment_reference or rec.move_id.ref
                    # memo = rec.move_id.payment_reference 
            new_object = [rec.date ,             # 0
                          rec.move_id.name,     # 1
                          rec.account_id.code,  # 2
                          rec.journal_id.code,  # 3
                          rec.date_maturity,    # 4
                          memo,             # 5
                          rec.debit,            # 6
                          rec.credit,           # 7
                          rec.balance,          # 8
                          initial_balance,      # 9
                          ]  #
            
            data['lines'].append(new_object)
        return self.env.ref('partner_ledger_reports.partner_xlsx').report_action(5,data=data)  
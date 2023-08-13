from odoo import models, fields, api, _
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo.exceptions import ValidationError, UserError


class ELECPETTYCASH(models.Model):
    _name = 'hr.pettycash'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']
    _description = "Petty Cash Request"


    name = fields.Char(string="Loan Name", default="/",  help="Name of the loan")
    date = fields.Date(string="Date", default=fields.Date.today(), help="Date")
    employee_id = fields.Many2one('hr.employee', string="Employee", required=True, help="Employee")
    department_id = fields.Many2one('hr.department', related="employee_id.department_id", readonly=True,
                                    string="Department", help="Employee")
    petty_amount = fields.Float(string="Amount", required=True, help="Petty Cash Amount")

    state = fields.Selection([
        ('draft', 'Draft'),
        ('waiting_approval_1', 'Submitted'),
        ('waiting_approval_2', 'ED Approval'),
        ('approve', 'Approved'),
        ('paid', 'Paid'),
        ('closed', 'Closed'),
        ('refuse', 'Refused'),
        ('cancel', 'Canceled'),
    ], string="State", default='draft', track_visibility='onchange', copy=False, )


    company_id = fields.Many2one('res.company', 'Company', readonly=True, help="Company",
                                 default=lambda self: self.env.company,
                                 states={'draft': [('readonly', False)]})
    currency_id = fields.Many2one('res.currency', string='Currency', required=True, help="Currency",
                                  default=lambda self: self.env.user.company_id.currency_id)

    reason = fields.Text(string = "Reason", required = True)

    activity_accountant =fields.Many2one('mail.activity',string='Activity')

    activity_gm =fields.Many2one('mail.activity',string='Activity')
    
    journal = fields.Many2one("account.journal", string="Journal" , default=lambda self: self.env['account.journal'].search([('id' , '=' ,3)] ,limit=1))
    account_from_id = fields.Many2one("account.account", string="Credit Account" , default=lambda self :self.env['account.account'].search([('id' , '=' , 2239 )] , limit=1))
    account_to_id = fields.Many2one("account.account", string="Debit Account" , default=lambda self :self.env['account.account'].search([('id' , '=' , 2302)] , limit=1))
    
    entry_count = fields.Integer(string='Count', compute='_compute_entry')
    entry_count_posted = fields.Integer(string='Count Posted', compute='_compute_entry')
    petty_close_count = fields.Integer(string="Petty Closing Count", compute='_compute_closing')
    petty_close_amount = fields.Float(string = "Closed Amount",compute = '_compute_closed_amount')
    petty_close_amount_due = fields.Float(string = "Petty Amount Due",compute = '_compute_closed_amount_due')
    is_amount_due_zero = fields.Boolean(string = "Is amount due zero" , default = False,compute = '_compute_is_zero')
    is_GM = fields.Boolean(string = "Is GM" , default = False)
    is_ACCOUNTANT = fields.Boolean(string = "Is ACCOUNTANT" , default = False)
    

    def _compute_closing(self):
        """This compute the pettycash closing count of an employee.
            """
        self.petty_close_count = self.env['hr.pettycash.closing.model'].search_count([('petty_cash_id', '=', self.id)])
    
    @api.depends('petty_close_amount')
    def _compute_closed_amount(self):
        for rec in self:
            petty_close_ids = self.env['hr.pettycash.closing.model'].search([('petty_cash_id', '=', rec.id)])
            if petty_close_ids:
                for close_id in petty_close_ids:
                    rec.petty_close_amount += close_id.petty_closing_amount
            else:
                rec.petty_close_amount = 0

    @api.depends('petty_close_amount_due')    
    def _compute_closed_amount_due(self):
        for rec in self:
            rec.petty_close_amount_due = rec.petty_amount - rec.petty_close_amount
   
    @api.depends('is_amount_due_zero')
    def _compute_is_zero(self):
        if self.petty_amount == self.petty_close_amount or self.petty_close_amount_due < 0: 
            self.is_amount_due_zero = True
            return self.write({'state': 'closed'})
        else:
            self.is_amount_due_zero = False


    def action_refuse(self):
        return self.write({'state': 'refuse'})
    
    def action_set_draft(self):
        return self.write({'state': 'draft'})

    def action_submit(self):
        accountant = self.env['res.users'].search(
            [('elec_user_type', '=', 'project_accountant')])
        res_model_id = self.env['ir.model'].search(
            [('name', '=', self._description)]).id
        if accountant:
            if self.company_id.name == "Electron Trading 2023":
                self.is_ACCOUNTANT =True
                elec_trading_manager = self.env['res.users'].search(
                    [('login', '=', 'abdullah@electronqatar.com')])
                if elec_trading_manager:
                    self.write({'state': 'waiting_approval_1'})
                    activity = self.env['mail.activity'].create([{'activity_type_id': 4,
                                                                    'date_deadline': datetime.today(),
                                                                    'summary': "Approve Petty Request",
                                                                    'user_id': elec_trading_manager.id,
                                                                    'res_id': self.id,
                                                                    'res_model_id': res_model_id,
                                                                    'note': 'Task',
                                                                    }])
                    self.activity_accountant = activity.id
                    return activity
            else:
                self.is_ACCOUNTANT =True
                self.write({'state': 'waiting_approval_1'})
                activity = self.env['mail.activity'].create([{'activity_type_id': 4,
                                                                'date_deadline': datetime.today(),
                                                                'summary': "Approve Petty Request",
                                                                'user_id': accountant.id,
                                                                'res_id': self.id,
                                                                'res_model_id': res_model_id,
                                                                'note': 'Task',
                                                                }])
                self.activity_accountant = activity.id
                return activity
        else:
            raise UserError('No Accountant with Project Accountant role is selected, please contact your admin.')

    @api.model
    def set_name(self):
        objects = self.env['hr.pettycash'].search(['|', ('name', '=', False), ('name', '=', ' ')])
        for rec in objects:
            rec.name = self.env['ir.sequence'].get('hr.petty.cash.seq') or ' '
    
    def action_cancel(self):
        self.write({'state': 'cancel'})

    def action_approve(self):
        gm = self.env['res.users'].search(
            [('elec_user_type', '=', 'gmanager')])
        accountant = self.env['res.users'].search(
            [('elec_user_type', '=', 'project_accountant')])
        res_model_id = self.env['ir.model'].search(
            [('name', '=', self._description)]).id
        if self.activity_accountant:
            self.activity_accountant.action_feedback()
        if self.company_id.name == "Electron Trading 2023":
            self.write({'state': 'approve'})
        else:
            if gm:
                self.is_GM = True
                self.write({'state': 'waiting_approval_2'})
                activity = self.env['mail.activity'].create([{'activity_type_id': 4,
                                                                'date_deadline': datetime.today(),
                                                                'summary': "Approve Petty Request",
                                                                'user_id': gm.id,
                                                                'res_id': self.id,
                                                                'res_model_id': res_model_id,
                                                                'note': 'Task',
                                                                }])
                self.activity_gm = activity.id
                return activity


    def action_approve_gm(self):
        if self.activity_gm:
            self.activity_gm.action_feedback()
        self.write({'state': 'approve'})


    # def unlink(self):
    #     for rec in self:
    #         if rec.state not in ('draft', 'cancel'):
    #             raise UserError(
    #                 'You cannot delete a Petty Cash Request which is not in draft or cancelled state')
    #     return super(ELECPETTYCASH, self).unlink()


    @api.model
    def create(self, values):
        values['name'] = self.env['ir.sequence'].get('hr.petty.cash.seq') or ' '
        res = super(ELECPETTYCASH, self).create(values)
        return res

    def action_create_journal_record(self):
        af = self.account_from_id.id
        at = self.account_to_id.id
        cr =self.currency_id.id
        jr = self.journal.id
        name = self.reason
        amount = self.petty_amount
        move_list= []
        for rec in self:
            lines=[(0, 0,{'name':name,'account_id': af, 'currency_id': cr, 'debit': 0,'credit': amount}),
                   (0, 0,{'name':name,'account_id': at, 'currency_id': cr,'debit': amount,'credit': 0})]
            vals = {
                'journal_id': jr,
                'ref': self.name,
                'currency_id':cr,
                'line_ids': lines,
            }
            move_list.append(vals)
        entry_id = self.env['account.move'].sudo().create(move_list)
        self.write({'state': 'paid'})


        return {
            "type": "ir.actions.act_window",
            "res_model": "account.move",
            "views": [[False, "form"]],
            'view_type': 'form',
            'view_mode': 'form',
            'res_id': entry_id.id,
            # 'context': {'default_journal_id':jr,
            #             'default_ref':self.name,
            #             'default_currency_id':cr,
            #             'default_line_ids':lines,
            #             },
        }
    

    def action_hr_pettycash_close_form(self):
        return {
            "type": "ir.actions.act_window",
            "res_model": "hr.pettycash.closing.model",
            "views": [[False, "form"]],
            'view_type': 'form',
            'view_mode': 'form',
            'context': {'default_employee_id':self.employee_id.id,
                        'default_reason':self.reason,
                        'default_petty_closing_amount':self.petty_close_amount_due,
                        'default_petty_cash_id':self.id,
                        },
        }


    def action_view_entry(self):
        return{
            'name': _('Journal Entry'),
            'domain': [('ref', '=', self.name)],
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'account.move',
            'view_id': False,
            'type': 'ir.actions.act_window',
        }

    def action_view_petty_cash_closing_module(self):
        return{
            'name': _('Petty Closings'),
            'domain': [('petty_cash_id', '=',  self.name)],
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'hr.pettycash.closing.model',
            'view_id': False,
            'type': 'ir.actions.act_window',
        }

    def _compute_entry(self):
        for rec in self:
            rec.entry_count_posted = rec.env['account.move'].search_count([('ref', '=', self.name),('state', 'in',['draft','posted'] )])
            rec.entry_count = rec.env['account.move'].search_count([('ref', '=', self.name)])


class HrEmployeePettyClosingModel(models.Model):
    _name = "hr.pettycash.closing.model"
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']
    _description = "Petty Cash Close"

    name = fields.Char(string="Reference", default="New", readonly=True, help="Petty Cash Reference")
    date = fields.Date(string="Date", default=fields.Date.today(), help="Date")
    employee_id = fields.Many2one('hr.employee', string="Employee", required=True, help="Employee")
    department_id = fields.Many2one('hr.department', related="employee_id.department_id", readonly=True,
                                    string="Department", help="Employee Department")
    petty_closing_amount = fields.Float(string="Amount", help="Petty Cash Closing Amount", compute = '_compute_total_closing' )
    petty_cash_id = fields.Many2one('hr.pettycash',string = "Petty Request")
    closed_entry_count_posted = fields.Integer(string='Count Posted', compute='_compute_entry')
    closed_entry_count = fields.Integer(string='Count Posted', compute='_compute_entry')
    is_GM = fields.Boolean(string = "Is GM" , default = False)
    is_ACCOUNTANT = fields.Boolean(string = "Is ACCOUNTANT" , default = False)

    state = fields.Selection([
        ('draft', 'Draft'),
        ('waiting_approval_1', 'Submitted'),
        ('waiting_approval_2', 'ED Approval'),
        ('approve', 'Approved'), 
        ('closed', 'Closed'),
        ('refuse', 'Refused'),
        ('cancel', 'Canceled'),
    ], string="State", default='draft', track_visibility='onchange', copy=False, )


    company_id = fields.Many2one('res.company', 'Company', readonly=True, help="Company",
                                 default=lambda self: self.env.company,
                                 states={'draft': [('readonly', False)]})
    currency_id = fields.Many2one('res.currency', string='Currency', required=True, help="Currency",
                                  default=lambda self: self.env.user.company_id.currency_id)

    reason = fields.Text(string = "Reason", required = True)

    project_id = fields.Many2one('project.project',string='Project')
    
    journal = fields.Many2one("account.journal", string="Journal" , default= lambda self : self.env['account.journal'].search([('id' , '=' , 3)]))
    
    account_from_id = fields.Many2one("account.account", string="Credit Account" , default=lambda self :self.env['account.account'].search([('id' , '=' , 2302)]))
    

    petty_close_line_id = fields.One2many('hr.pettycash.closing.line', 'petty_close_id', string='Petty Close Line',index=True)

    activity_accountant =fields.Many2one('mail.activity',string='Activity')
    activity_accountant_2 =fields.Many2one('mail.activity',string='Activity')
    activity_gm =fields.Many2one('mail.activity',string='Activity')

    @api.onchange('reason','employee_id')
    def _set_analytic_group(self):
        group = self.env['account.analytic.group'].search([('name', '=', 'PETTY CASH')], limit=1).id
        if group:
            for rec in self:
                rec.analytic_group_id = group

    analytic_group_id = fields.Many2one("account.analytic.group", string="Analytic Group" , domain =([('name', '=','PETTY CASH')]))

    @api.model
    def create(self, values):
        values['name'] = self.env['ir.sequence'].get('hr.petty.cash.close.seq') or ' '
        res = super(HrEmployeePettyClosingModel, self).create(values)
        return res


    def action_refuse(self):
        return self.write({'state': 'refuse'})
    
    def action_set_draft(self):
        return self.write({'state': 'draft'})

    def action_submit(self):
        accountant = self.env['res.users'].search(
            [('elec_user_type', '=', 'project_accountant')],limit = 1)
        res_model_id = self.env['ir.model'].search(
            [('name', '=', self._description)]).id
        if accountant:
            if self.company_id.name == "Electron Trading 2023":
                self.is_ACCOUNTANT =True
                elec_trading_manager = self.env['res.users'].search(
                    [('login', '=', 'abdullah@electronqatar.com')])
                if elec_trading_manager:
                    self.is_ACCOUNTANT = True
                    self.write({'state': 'waiting_approval_1'})
                    activity = self.env['mail.activity'].create([{'activity_type_id': 4,
                                                                    'date_deadline': datetime.today(),
                                                                    'summary': "Approve Petty Cash Close",
                                                                    'user_id': elec_trading_manager.id,
                                                                    'res_id': self.id,
                                                                    'res_model_id': res_model_id,
                                                                    'note': 'Please Approve Petty Close',
                                                                    }])
                    self.activity_accountant = activity.id
                    return activity
            else:
                self.is_ACCOUNTANT = True
                self.write({'state': 'waiting_approval_1'})
                activity = self.env['mail.activity'].create([{'activity_type_id': 4,
                                                                'date_deadline': datetime.today(),
                                                                'summary': "Approve Petty Cash Close",
                                                                'user_id': accountant.id,
                                                                'res_id': self.id,
                                                                'res_model_id': res_model_id,
                                                                'note': 'Please Approve Petty Close',
                                                                }])
                self.activity_accountant = activity.id
                return activity
        else:
            raise UserError('No Accountant with Project Accountant role is selected, please contact your admin.')


    def action_cancel(self):
        self.write({'state': 'cancel'})

    def action_approve(self):
        gm = self.env['res.users'].search(
            [('elec_user_type', '=', 'gmanager')],limit = 1)
        accountant = self.env['res.users'].search(
            [('elec_user_type', '=', 'project_accountant')])
        res_model_id = self.env['ir.model'].search(
            [('name', '=', self._description)]).id
        if self.activity_accountant:
            self.activity_accountant.action_feedback()
        if self.company_id.name == "Electron Trading 2023":
            self.write({'state': 'approve'})
        else:
            if gm:
                self.is_GM = True
                self.write({'state': 'waiting_approval_2'})
                activity = self.env['mail.activity'].create([{'activity_type_id': 4,
                                                                'date_deadline': datetime.today(),
                                                                'summary': "Approve Petty Cash Close",
                                                                'user_id': gm.id,
                                                                'res_id': self.id,
                                                                'res_model_id': res_model_id,
                                                                'note': 'Please Approve Petty Close',
                                                                }])
                self.activity_gm = activity.id
                return activity

    def action_approve_gm(self):
        if self.activity_gm:
            self.activity_gm.action_feedback()
        self.write({'state': 'approve'})
        accountant = self.env['res.users'].search(
            [('elec_user_type', '=', 'project_accountant')],limit = 1)
        res_model_id = self.env['ir.model'].search(
            [('name', '=', self._description)]).id
        if accountant:
            self.is_ACCOUNTANT = True
            activity = self.env['mail.activity'].create([{'activity_type_id': 4,
                                                            'date_deadline': datetime.today(),
                                                            'summary': "Please create Journal Entry for Petty Close",
                                                            'user_id': accountant.id,
                                                            'res_id': self.id,
                                                            'res_model_id': res_model_id,
                                                            'note': 'Create Journal Entry',
                                                            }])
            self.activity_accountant_2 = activity.id
            return activity

    def _compute_entry(self):
        for rec in self:
            rec.closed_entry_count_posted = rec.env['account.move'].search_count([('ref', '=', self.name),('state', 'in',['draft','posted'] )])
            rec.closed_entry_count = rec.env['account.move'].search_count([('ref', '=', self.name)])
    @api.depends('petty_close_line_id','petty_closing_amount')
    def _compute_total_closing(self):
        for rec in self:
            rec.petty_closing_amount = 0.0
            if rec.petty_close_line_id:
                for line in rec.petty_close_line_id:
                    rec.petty_closing_amount += line.total

    def action_create_journal_record(self):
        af = self.account_from_id.id
        cr =self.currency_id.id
        jr = self.journal.id
        date = self.date
        name = self.reason
        amount = 0.0
        move_list= []
        lines=[]
        if self.petty_close_line_id:
            for line in self.petty_close_line_id:
                amount += line.total
                lines.append((0, 0,{'name':line.desc,'account_id': line.account_to_id.id,'analytic_account_id':line.analytic_account_id.id ,'currency_id': cr, 'debit': line.total,'credit':0.0 }))
                # anayltic_lines.append((0, 0,{'name':line.desc,'account_id': line.analytic_account_id.id, 'amount': line.total, 'date': date,'ref':line.invoice_number }))
            
        lines.append((0, 0,{'name':name,'account_id': af, 'currency_id': cr,'debit':0.0 ,'credit': amount}))
        vals = {
                'journal_id': jr,
                'ref': self.name,
                'currency_id':cr,
                'line_ids': lines,
            }

        move_list.append(vals)
        entry_id = self.env['account.move'].sudo().create(move_list)
        self.write({'state': 'closed'})

        if self.activity_accountant_2:
            self.activity_accountant_2.action_feedback()
        return {
            "type": "ir.actions.act_window",
            "res_model": "account.move",
            "views": [[False, "form"]],
            'view_type': 'form',
            'view_mode': 'form',
            'res_id': entry_id.id,
            # 'context': {'default_journal_id':jr,
            #             'default_ref':self.name,
            #             'default_currency_id':cr,
            #             'default_line_ids':lines,
            #             },
        }
    
class HrEmployeePettyClosingLine(models.Model):
    _name = "hr.pettycash.closing.line"
    _description = "Petty Cash Close Line"

    sequence_ref = fields.Integer('No.', compute="_sequence_ref")

    @api.depends('petty_close_id.petty_close_line_id', 'petty_close_id.petty_close_line_id.desc')
    def _sequence_ref(self):
        for line in self:
            no = 0
            for l in line.petty_close_id.petty_close_line_id:
                no += 1
                l.sequence_ref = no

    desc = fields.Char(string = "description")
    supplier = fields.Char(string = "Supplier Name")
    invoice_number = fields.Char(string = "invoice number")
    total  = fields.Float(string = "Total")

    petty_close_id = fields.Many2one('hr.pettycash.closing.model',string = "Petty Close")

    account_to_id = fields.Many2one("account.account", string="Account" ,default=lambda self :self.env['account.account'].search([('id' , '=' , 2239)]))
    analytic_account_id = fields.Many2one("account.analytic.account", string="Analytic Account" , domain =([('group_id.name', '=','PETTY CASH')]))

class HrEmployeePetty(models.Model):
    _inherit = "hr.employee"

    def _compute_employee_pettycash(self):
        """This compute the pettycash count of an employee.
            """
        petty_cash = self.env['hr.pettycash'].search([('employee_id', '=', self.id),('state', '=', 'paid')])
        if petty_cash:
            for rec in petty_cash:
                self.petty_count += rec.petty_amount
        else:
            self.petty_count = 0.0

    petty_count = fields.Float(string="Petty Cash Amount", compute='_compute_employee_pettycash')



class HrEmployeePettyClosing(models.TransientModel):
    _name = "hr.pettycash.closing"
    _description = "Petty Cash Close Wizard"

    name = fields.Char(string="Reference", default="New", readonly=True, help="Petty Cash Reference")
    date = fields.Date(string="Date", default=fields.Date.today(), help="Date")
    employee_id = fields.Many2one('hr.employee', string="Employee", required=True, help="Employee")
    department_id = fields.Many2one('hr.department', related="employee_id.department_id", readonly=True,
                                    string="Department", help="Employee Department")
    petty_closing_amount = fields.Float(string="Amount", help="Petty Cash Closing Amount")
    petty_cash_id = fields.Many2one('hr.pettycash',string = "Petty Request")

    state = fields.Selection([
        ('draft', 'Draft'),
        ('waiting_approval_1', 'Submitted'),
        ('waiting_approval_2', 'ED Approval'),
        ('approve', 'Approved'),
        ('refuse', 'Refused'),
        ('cancel', 'Canceled'),
    ], string="State", default='draft', track_visibility='onchange', copy=False, )


    company_id = fields.Many2one('res.company', 'Company', readonly=True, help="Company",
                                 default=lambda self: self.env.company,
                                 states={'draft': [('readonly', False)]})
    currency_id = fields.Many2one('res.currency', string='Currency', required=True, help="Currency",
                                  default=lambda self: self.env.user.company_id.currency_id)

    reason = fields.Text(string = "Reason", required = True)


    def action_create_petty_close(self):
        vals = {
               'name': self.name,
               'date': self.date,
               'employee_id': self.employee_id.id,
               'department_id': self.department_id,
               'petty_closing_amount':self.petty_closing_amount,
               'reason': self.reason,
            }
        self.env['hr.pettycash.closing.model'].sudo().create(vals)
        
    # @api.model
    # def create(self, values):
    #     values['name'] = self.env['ir.sequence'].get('hr.petty.cash.close.seq') or ' '
    #     res = super(HrEmployeePettyClosing, self).create(values)
    #     return res

# -*- coding: utf-8 -*-


from odoo import api, fields, models, api, _
from datetime import datetime
from odoo.exceptions import AccessError, UserError, ValidationError


class Purchaserequester(models.Model):
    _name = "purchase.requester"
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']
    _description = 'Purchase Request'
    _rec_name = 'name_seq'

    @api.model
    def create(self, vals):
        if vals.get('name_seq', 'New') == 'New':
            vals['name_seq'] = self.env['ir.sequence'].next_by_code(
                'purchase.requester') or '/'
        return super(Purchaserequester, self).create(vals)

    @api.depends()
    def action_toapprove(self):
        for rec in self:
            rec.state = 'con'
            rec.target = 'new'

    def action_approve(self):
        for rec in self:
            rec.state = 'acc'

    def action_reject(self):
        for rec in self:
            rec.state = 'reject'

    def button_approve(self):
        for rec in self:
            if rec.approver_id:
                rec.state = 'con'
            elif not rec.approver_id:
                rec.state = 'acc'
        self.ensure_one()
        res_model_id = self.env['ir.model'].search(
            [('name', '=', self._description)]).id
        for rec in self:
            if rec.approver_id:
                activity = self.env['mail.activity'].create([{'activity_type_id': 4,
                                                   'date_deadline': datetime.today(),
                                                   'summary': "Approve MR",
                                                   'user_id': self.approver_id.id,
                                                   'res_id': self.id,
                                                   'res_model_id': res_model_id,
                                                   'note': 'Task',
                                                   }])
        self.activity_accountant = activity.id
        return activity

    def action_purchase(self, context=None):
        for rec in self:
            rec.state = 'acc'
        return {
            "type": "ir.actions.act_window",
            "res_model": "purchase.order",
            "views": [[False, "form"]],
            'view_type': 'form',
            'view_mode': 'form',
            'context': {'default_purchase_inhrt_id': self.approver_id.id,
                        'default_new_id': self.name_seq,
                        'default_purchase_requester_id': self.id,
                        'default_project_id': self.project.id,
                        'default_requester': self.user_id.id,
                        },
        }

    def button_convert(self):
        for rec in self:
            rec.state = 'draft'

    def button_cancel(self):
        for rec in self:
            rec.state = 'reject'

    def button_gm_create(self):
        if self.activity_gm:
            self.activity_gm.action_feedback()        
        for rec in self:
            rec.write({'state': 'acc'})

    def button_create(self):
        gm = self.env['res.users'].search(
            [('elec_user_type', '=', 'gmanager')])
        if gm :
            for record in self:
                for rec in record.products: 
                    if rec.product_qty > rec.budget_qyt:
                        record.write({'state': 'gmapprove'})
                        res_model_id = self.env['ir.model'].search(
                            [('name', '=', self._description)]).id
                        for rec in record:
                            if rec.approver_id:
                                if self.activity_accountant:
                                    self.activity_accountant.action_feedback()
                                activity = self.env['mail.activity'].create([{'activity_type_id': 4,
                                                                'date_deadline': datetime.today(),
                                                                'summary': "Approve MR, quantity is over budget",
                                                                'user_id': gm.id,
                                                                'res_id': self.id,
                                                                'res_model_id': res_model_id,
                                                                'note': 'Task',
                                                                }])
                                record.write({'state': 'gmapprove'})
                                self.activity_gm = activity.id
                                return activity
                    else:
                        record.write({'state': 'acc'})
        else:
            for record in self:
                for rec in record.products: 
                    if rec.product_qty > rec.budget_qyt:
                        record.write({'state': 'gmapprove'})
                        res_model_id = self.env['ir.model'].search(
                            [('name', '=', self._description)]).id
                        for rec in record:
                            if rec.approver_id:
                                if self.activity_accountant:
                                    self.activity_accountant.action_feedback()
                                activity = self.env['mail.activity'].create([{'activity_type_id': 4,
                                                                'date_deadline': datetime.today(),
                                                                'summary': "Approve MR, quantity is over budget",
                                                                'user_id': 15,
                                                                'res_id': self.id,
                                                                'res_model_id': res_model_id,
                                                                'note': 'Task',
                                                                }])
                                record.write({'state': 'gmapprove'})
                                self.activity_gm = activity.id
                                return activity
                    else:
                        record.write({'state': 'acc'})

    @api.model
    def _getUserGroupId(self):
        return [('groups_id', '=', self.env.ref('purchase.group_purchase_manager').id)]

    # approver_id = fields.Many2one('res.users', string='Approver',  domain=_getUserGroupId, readonly=False, states={
    #                               'acc': [('readonly', True)]}, track_visibility='always')
    description = fields.Text(string="Description", required=True, states={
                              'acc': [('readonly', True)], 'reject': [('readonly', True)]}, track_visibility='always')
    name_seq = fields.Char(string="Purchase Reference ", required=True, copy=False, readonly=True,  index=True,
                           default=lambda self: _('New'))

    date_order = fields.Datetime('Purchase order date', required=True, index=True, copy=False,
                                 default=datetime.today(),
                                 help="Depicts the date where the Quotation should be validated and converted into a purchase order.", readonly=False, states={'acc': [('readonly', True)], 'reject': [('readonly', True)]}, track_visibility='always')

    user_id = fields.Many2one('res.users', string='Requester', index=True, track_visibility='onchange',
                              default=lambda self: self.env.user)

    gm_id = fields.Many2one('res.users', string='GM', index=True, track_visibility='onchange', domain=[
                            ('elec_user_type', '=', 'gmanager')])

    purchase_order_id = fields.One2many('purchase.order', 'purchase_requester_id',
                                        string='Purchase Order Reference', states={'acc': [('readonly', True)]})

    res_id = fields.Many2one('res.users', string='Approver')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('drft', 'Draft'),
        ('con', 'confirmation'),
        ('gmapprove', 'ED Approval'),
        ('acc', 'acceptance'),
        ('rej', 'rejection'),
        ('toapprove', 'To Approve'),
        ('app', 'Approve'),
        ('reject', 'Reject'),
        # ('lock', [('readonly', True)]),
    ], string='Status', default='draft', readonly=True, track_visibility='always')

    activity_accountant =fields.Many2one('mail.activity',string='Activity')
    activity_gm =fields.Many2one('mail.activity',string='Activity')

class PurchaseOrderInherit(models.Model):
    _inherit = "purchase.order"

    @api.model
    def _getUserGroupId(self):
        return [('groups_id', '=', self.env.ref('purchase.group_purchase_manager').id)]

    approver_id = fields.Many2one(
        string='Approver', domain=_getUserGroupId, readonly=True)

    project_id = fields.Many2one(
        'project.project',
        string='Project',
    )
    requester = fields.Many2one(
        'res.users',
        string='Requester',
    )
    purchase_inhrt_id = fields.Many2one(
        'res.users', string='Approver',  store=True, readonly=False)
    purchase_requester_id = fields.Many2one(
        'purchase.requester', string='Request Reference')

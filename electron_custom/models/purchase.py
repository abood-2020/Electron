# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _, tools
from odoo.exceptions import ValidationError, UserError
from odoo.tools.float_utils import float_is_zero
from itertools import groupby
from datetime import datetime


class ElecCategory(models.Model):
    _inherit = 'product.category'

    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=False,
        default=lambda self: self.env.company
        )

class ElecProduct(models.Model):
    _inherit = 'product.template'

    def _get_default_category_id(self):
        # Deletion forbidden (at least through unlink)
        for rec in self:
            if "ELECTRON MEP" in rec.company_id.name:
                return rec.env.ref('product.product_category_all')
            else:
                return rec.env.ref('product.product_category_all_trading')

    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company
    )

    categ_id = fields.Many2one(
        'product.category', 'Product Category',
        change_default=True, default=_get_default_category_id, group_expand='_read_group_categ_id',
        required=True, help="Select category for the current product")
    
    min_price = fields.Float('Min Price')


class ElecCompany(models.Model):
    _inherit = 'res.company'
    
    elect_purchase_double_validation = fields.Selection([
          ('one_step', 'Confirm Purchase orders in one step'),
          ('two_step', 'Get 2 levels of approvals to confirm a Purchase order')])


class ElecPurchaseConfig(models.TransientModel):
    _inherit = ['res.config.settings']

    
    elec_purchase_order_approval = fields.Boolean(
        string='Electron Purchase Order Approval', default=lambda self: self.env.company.elect_purchase_double_validation == 'two_step'        
    )
    elec_purchase_double_validation = fields.Selection(related='company_id.elect_purchase_double_validation', string="Levels of Approvals *", readonly=False)

    def set_values(self):
        super(ElecPurchaseConfig, self).set_values()
        self.elec_purchase_double_validation = 'two_step' if self.elec_purchase_order_approval else 'one_step'

class ElecPurchase(models.Model):
    _inherit = ['purchase.order']

    is_elec_gm_approved = fields.Boolean(
        string='Executive Director Approved', states={'purchase': [('readonly', True)]}, copy = False
    )
    is_elec_pm_approved = fields.Boolean(
        string='Technical Manager Approved', states={'purchase': [('readonly', True)]}, copy = False
    )
    is_elec_accountant_approved = fields.Boolean(
        string='Finance Manager Approved', states={'purchase': [('readonly', True)]}, copy = False
    )
    is_elec_projectmanager_approved = fields.Boolean(
        string='Project Manager Approved', states={'purchase': [('readonly', True)]}, copy = False
    )
    is_elec_gm_approved_po = fields.Boolean(
        string='Executive Director Approved', states={'done': [('readonly', True)]}, copy = False
    )
    is_elec_pm_approved_po = fields.Boolean(
        string='Technical Manager Approved', states={'done': [('readonly', True)]}, copy = False
    )
    is_elec_accountant_approved_po = fields.Boolean(
        string='Finance Manager Approved', states={'done': [('readonly', True)]}, copy = False
    )
    is_elec_projectmanager_approved_po = fields.Boolean(
        string='Project Manager Approved', states={'done': [('readonly', True)]}, copy = False
    )

    current_user = fields.Many2one(
        'res.users', 'Current User', compute='get_user')

    gm_user_id = fields.Many2one(
        'res.users',
        string='User GM',
        compute='get_user'
    )
    pm_user_id = fields.Many2one(
        'res.users',
        string='User PM',
        compute='get_user'
    )
    accountant_user_id = fields.Many2one(
        'res.users',
        string='User Accountant',
        compute='get_user'
    )

    
    attachments = fields.Text(
        string='Attachments',
    )
    delivery_terms = fields.Text(
        string='Delivery Terms',
    )
    

    is_gm = fields.Boolean(string="Is GM", compute='get_user')
    is_pm = fields.Boolean(string="Is PM", compute='get_user')
    is_accountant = fields.Boolean(string="Is Accountant", compute='get_user')
    is_projectmanager = fields.Boolean(string="Is Project Manager", compute='get_user')
    
    attn = fields.Char(
        string='Attn',
    )
    
    certified = fields.Monetary(string='Certified Amount', store=True, readonly=True, compute='_amount_all_certified')
    
    elect_purchase_double_validation = fields.Selection(related='company_id.elect_purchase_double_validation',string ="Company Validation Related",help ="Validation related for showing the page or not")
    
    

    @api.depends('is_gm', 'is_pm', 'is_accountant','is_projectmanager')
    def get_user(self):
        users = self.env['res.users'].search([])
        context = self._context
        current_uid = context.get('uid')
        logged_user = self.env['res.users'].browse(current_uid)
        self.current_user = logged_user
        for user in users:
            if user.elec_user_type == 'gmanager':
                self.gm_user_id = user.id
            if user.elec_user_type == 'procurment_manager':
                self.pm_user_id = user.id
            if user.elec_user_type == 'project_accountant':
                self.accountant_user_id = user.id

        if logged_user == self.gm_user_id:
            self.is_gm = True
        else:
            self.is_gm = False
        if logged_user == self.pm_user_id:
            self.is_pm = True
        else:
            self.is_pm = False
        if logged_user == self.accountant_user_id:
            self.is_accountant = True
        else:
            self.is_accountant = False
        if logged_user == self.purchase_inhrt_id:
            self.is_projectmanager = True
        else:
            self.is_projectmanager = False

    @api.model
    def write(self, vals):
        res = super(ElecPurchase, self).write(vals)
        if vals.get('is_elec_gm_approved_po') == True :
            self.onchange_is_elec_gm_approved()
            self.write({'state': 'done'})
        return res

    def onchange_is_elec_gm_approved(self):
        acc = self.env['res.users'].search(
            [('elec_user_type', '=', 'project_accountant')])
        if acc :
            for record in self:
                res_model_id = self.env['ir.model'].search(
                    [('name', '=', self._description)]).id
                activity = self.env['mail.activity'].create([{'activity_type_id': 4,
                                                'date_deadline': datetime.today(),
                                                'summary': "Create bill for approved PO",
                                                'user_id': acc.id,
                                                'res_id': self.id,
                                                'res_model_id': res_model_id,
                                                'note': 'Task',
                                                }])
                return activity



    def button_confirm(self):
        res = super(ElecPurchase, self).button_confirm()
        if self.company_id.elect_purchase_double_validation == 'two_step':
            if self.is_elec_gm_approved == False or self.is_elec_pm_approved == False or self.is_elec_accountant_approved == False:
                raise UserError(_('This RFQ needs approval first'))
        else :
            for order in self:
                if order.state not in ['draft', 'sent']:
                    continue
                order._add_supplier_to_product()
                # Deal with double validation process
                if order._approval_allowed():
                    order.button_approve()
                else:
                    order.write({'state': 'to approve'})
                if order.partner_id not in order.message_partner_ids:
                    order.message_subscribe([order.partner_id.id])
            return True
        
    
    @api.depends('order_line.qty_invoiced')
    def _amount_all_certified(self):
        for order in self:
            amount_untaxed = amount_tax = certified =  0.0
            for line in order.order_line:
                line._compute_amount()
                amount_untaxed += line.price_subtotal
                amount_tax += line.price_tax
                certified += line.qty_invoiced * line.price_unit
            order.update({
                'amount_untaxed': order.currency_id.round(amount_untaxed),
                'amount_tax': order.currency_id.round(amount_tax),
                'amount_total': amount_untaxed + amount_tax,
                'certified': certified,
            })

    def action_create_invoice(self):
        """Create the invoice associated to the PO.
        """
        if self.company_id.elect_purchase_double_validation == 'two_step':
            if self.is_elec_gm_approved_po == False or self.is_elec_pm_approved_po == False or self.is_elec_accountant_approved_po == False or self.is_elec_projectmanager_approved_po == False:
                raise UserError(_('This PO needs approval first'))
            else:
                precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
                # 1) Prepare invoice vals and clean-up the section lines
                invoice_vals_list = []
                for order in self:
                    if order.invoice_status != 'to invoice':
                        continue

                    order = order.with_company(order.company_id)
                    pending_section = None
                    # Invoice values.
                    invoice_vals = order._prepare_invoice()
                    # Invoice line values (keep only necessary sections).
                    for line in order.order_line:
                        if line.display_type == 'line_section':
                            pending_section = line
                            continue
                        if not float_is_zero(line.qty_to_invoice, precision_digits=precision):
                            if pending_section:
                                invoice_vals['invoice_line_ids'].append((0, 0, pending_section._prepare_account_move_line()))
                                pending_section = None
                            invoice_vals['invoice_line_ids'].append((0, 0, line._prepare_account_move_line()))
                    invoice_vals_list.append(invoice_vals)

                if not invoice_vals_list:
                    raise UserError(_('There is no invoiceable line. If a product has a control policy based on received quantity, please make sure that a quantity has been received.'))

                # 2) group by (company_id, partner_id, currency_id) for batch creation
                new_invoice_vals_list = []
                for grouping_keys, invoices in groupby(invoice_vals_list, key=lambda x: (x.get('company_id'), x.get('partner_id'), x.get('currency_id'))):
                    origins = set()
                    payment_refs = set()
                    refs = set()
                    ref_invoice_vals = None
                    for invoice_vals in invoices:
                        if not ref_invoice_vals:
                            ref_invoice_vals = invoice_vals
                        else:
                            ref_invoice_vals['invoice_line_ids'] += invoice_vals['invoice_line_ids']
                        origins.add(invoice_vals['invoice_origin'])
                        payment_refs.add(invoice_vals['payment_reference'])
                        refs.add(invoice_vals['ref'])
                    ref_invoice_vals.update({
                        'ref': ', '.join(refs)[:2000],
                        'invoice_origin': ', '.join(origins),
                        'payment_reference': len(payment_refs) == 1 and payment_refs.pop() or False,
                    })
                    new_invoice_vals_list.append(ref_invoice_vals)
                invoice_vals_list = new_invoice_vals_list

                # 3) Create invoices.
                moves = self.env['account.move']
                AccountMove = self.env['account.move'].with_context(default_move_type='in_invoice')
                for vals in invoice_vals_list:
                    moves |= AccountMove.with_company(vals['company_id']).create(vals)

                # 4) Some moves might actually be refunds: convert them if the total amount is negative
                # We do this after the moves have been created since we need taxes, etc. to know if the total
                # is actually negative or not
                moves.filtered(lambda m: m.currency_id.round(m.amount_total) < 0).action_switch_invoice_into_refund_credit_note()
                self.is_elec_gm_approved_po = False
                self.is_elec_pm_approved_po = False
                self.is_elec_accountant_approved_po = False
                self.is_elec_projectmanager_approved_po = False
                return self.action_view_invoice(moves)

        else:
            precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')

            # 1) Prepare invoice vals and clean-up the section lines
            invoice_vals_list = []
            for order in self:
                if order.invoice_status != 'to invoice':
                    continue

                order = order.with_company(order.company_id)
                pending_section = None
                # Invoice values.
                invoice_vals = order._prepare_invoice()
                # Invoice line values (keep only necessary sections).
                for line in order.order_line:
                    if line.display_type == 'line_section':
                        pending_section = line
                        continue
                    if not float_is_zero(line.qty_to_invoice, precision_digits=precision):
                        if pending_section:
                            invoice_vals['invoice_line_ids'].append((0, 0, pending_section._prepare_account_move_line()))
                            pending_section = None
                        invoice_vals['invoice_line_ids'].append((0, 0, line._prepare_account_move_line()))
                invoice_vals_list.append(invoice_vals)

            if not invoice_vals_list:
                raise UserError(_('There is no invoiceable line. If a product has a control policy based on received quantity, please make sure that a quantity has been received.'))

            # 2) group by (company_id, partner_id, currency_id) for batch creation
            new_invoice_vals_list = []
            for grouping_keys, invoices in groupby(invoice_vals_list, key=lambda x: (x.get('company_id'), x.get('partner_id'), x.get('currency_id'))):
                origins = set()
                payment_refs = set()
                refs = set()
                ref_invoice_vals = None
                for invoice_vals in invoices:
                    if not ref_invoice_vals:
                        ref_invoice_vals = invoice_vals
                    else:
                        ref_invoice_vals['invoice_line_ids'] += invoice_vals['invoice_line_ids']
                    origins.add(invoice_vals['invoice_origin'])
                    payment_refs.add(invoice_vals['payment_reference'])
                    refs.add(invoice_vals['ref'])
                ref_invoice_vals.update({
                    'ref': ', '.join(refs)[:2000],
                    'invoice_origin': ', '.join(origins),
                    'payment_reference': len(payment_refs) == 1 and payment_refs.pop() or False,
                })
                new_invoice_vals_list.append(ref_invoice_vals)
            invoice_vals_list = new_invoice_vals_list

            # 3) Create invoices.
            moves = self.env['account.move']
            AccountMove = self.env['account.move'].with_context(default_move_type='in_invoice')
            for vals in invoice_vals_list:
                moves |= AccountMove.with_company(vals['company_id']).create(vals)

            # 4) Some moves might actually be refunds: convert them if the total amount is negative
            # We do this after the moves have been created since we need taxes, etc. to know if the total
            # is actually negative or not
            moves.filtered(lambda m: m.currency_id.round(m.amount_total) < 0).action_switch_invoice_into_refund_credit_note()
            self.is_elec_gm_approved_po = False
            self.is_elec_pm_approved_po = False
            self.is_elec_accountant_approved_po = False
            self.is_elec_projectmanager_approved_po = False
            return self.action_view_invoice(moves)



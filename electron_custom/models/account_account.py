# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.tools import float_compare, date_utils, email_split, email_re
from json import dumps
from odoo.exceptions import ValidationError
import json
from num2words import num2words


class ElecAccountAccount(models.Model):
    _inherit = ['account.account']
    

    is_elec_analytic_accounts = fields.Boolean(
        string='Analytical Accounts',
        )

class ElecAccountMoveLine(models.Model):
    _inherit = ['account.move.line']  

    sequence_ref = fields.Integer('No.', compute="_sequence_ref")

    @api.depends('move_id.invoice_line_ids', 'move_id.invoice_line_ids.product_id')
    def _sequence_ref(self):
        for line in self:
            no = 0
            for l in line.move_id.invoice_line_ids:
                no += 1
                l.sequence_ref = no

    due_date_cheque = fields.Date(
        string='Cheque Due Date',
        # default=fields.Date.context_today,
    ) 

class ElecAccountMove(models.Model):
    _inherit = ['account.move']
    
    inv_origin_id = fields.Many2one(
        'purchase.order',
        string='Origin PO',
        compute = '_compute_po'
        )

    
    dn_number = fields.Char(
        string='DN Number',
    )
    
    lpo_no = fields.Char(
        string='LPO No.',
    )

    discount = fields.Float("Discount",compute = '_compute_total_no_disc')
    total_no_disc = fields.Float('Total',compute = '_compute_total_no_disc')
    

    @api.depends('total_no_disc')
    def _compute_total_no_disc(self):
        self.total_no_disc = 0.0
        self.discount = 0.0
        for rec in self:
            for line in rec.invoice_line_ids:
                if not line.product_id.default_code == "DISC":
                    rec.total_no_disc +=  (line.quantity * line.price_unit)
                if line.product_id.default_code == "DISC": 
                    rec.discount +=  line.price_subtotal

    
    certified_amount_total = fields.Float(string='Certified Total', compute = '_compute_certified_amount_total')

    @api.depends('certified_amount_total')
    def _compute_certified_amount_total(self):
        payments_vals = self._get_reconciled_info_JSON_values()
        total = 0.0        
        for val in payments_vals:
            total += val['amount']
        for rec in self:
            rec.certified_amount_total = total
    

    @api.constrains('line_ids')
    def _check_analytic_account(self):
        for rec in self:
            for line in rec.line_ids:
                if line.account_id.is_elec_analytic_accounts:
                    if not line.analytic_tag_ids:
                        raise ValidationError(_('Please enter anayltic tag for account {account}'.format(account=line.account_id.name)))
                

    @api.depends('inv_origin_id')
    def _compute_po(self):
        
        purchase_orders = self.env['purchase.order'].search([('name', '=', self.invoice_origin)])
        for record in self:
            record.inv_origin_id = purchase_orders.id


    word_amount_total = fields.Char(string='Amount in Words', compute = '_to_words')

    @api.depends('word_amount_total','amount_total')
    def _to_words(self):
        for rec in self:
            int_num  = int(rec.amount_total)
            frac = round((rec.amount_total - int_num) , 2) 
            frac_word = frac*100
            if rec.amount_total - int_num > 0:
                rec.word_amount_total =rec.currency_id.currency_unit_label.upper() +" "+ num2words(int_num).upper() + " AND " + num2words(int(frac_word)).upper() +" "+ rec.currency_id.currency_subunit_label.upper() + " ONLY"
            else:
                rec.word_amount_total = rec.currency_id.currency_unit_label.upper() +" "+ num2words(rec.amount_total).upper() + " ONLY"
    


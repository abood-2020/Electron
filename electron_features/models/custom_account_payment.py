from odoo import models, fields, api, _
from odoo.exceptions import UserError

class CustomAccountPayment(models.Model):
    _inherit = 'account.payment'
    
    sale_person = fields.Many2one('res.users' , string="Sale Person")
    bank_transfer = fields.Date(string="Bank Transfer")
    check = fields.Date(string="Check")
   

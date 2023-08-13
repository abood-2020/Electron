from odoo import api , fields , models 
from odoo.exceptions import UserError

class ContractElectron(models.Model):
    _inherit = ['hr.contract']
    
    daily_hours = fields.Integer(
        string="Daily Working Hours"
    )
    working_hours = fields.Float(
        string="Working Hours (Monthly)",
        help = "Number of working hours per month",
    )
    is_overtime = fields.Boolean(
        string="Overtime",   
    )

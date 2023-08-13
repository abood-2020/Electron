from odoo import models, fields, api

class CustomLeave(models.Model):
    _inherit = 'hr.leave.type'
    
    is_paid = fields.Boolean(string = "Is paid")
    
    is_public = fields.Boolean(string = "Is Public")

    

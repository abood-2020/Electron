from odoo import api, fields, models, _
from datetime import datetime
from odoo.exceptions import AccessError, UserError, ValidationError

class ElecSalesConfig(models.TransientModel):
    _inherit = ['res.config.settings']

    work_start_hour = fields.Integer(string="Work Start Hour",
                                        config_parameter="electron_features.work_start_hour")
    
    thursday_working_hours = fields.Integer(string="Thursday Working Hours" ,
                                        config_parameter="electron_features.thursday_working_hours")
    
    thursday_hours = fields.Integer(string="Thursday Hours" ,
                                        config_parameter="electron_features.thursday_hours")
    
    daily_working_hours = fields.Integer(string="Daily Working Hours",
                                         config_parameter="electron_features.daily_working_hours")
    

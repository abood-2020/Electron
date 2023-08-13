# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class ElecResusers(models.Model):
    _inherit = ['res.users']
    
    
    elec_user_type = fields.Selection(
        string='Project Assigned Position',
        selection=[('gmanager', 'Executive Director'), ('procurment_manager', 'Technical Manager'),('project_accountant', 'Finance Manager')]
    )
    
    
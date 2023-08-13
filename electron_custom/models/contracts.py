from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_compare, date_utils, email_split, email_re
from json import dumps
import json

class ElecPayrollStructureType(models.Model):
    _inherit = ['hr.payroll.structure.type']

    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)
    basic_start = fields.Monetary(
        string='Start',
    )
    basic_end = fields.Monetary(
        string='End',
    )
    housing_allowance = fields.Monetary(
        string='Allowance',
    )
    
    housing_provided = fields.Boolean(
        string='Provided',
    )

    transportation_allowance = fields.Monetary(
        string='Allowance',
    )
    
    transportation_provided = fields.Boolean(
        string='Provided',
    )

    mobile_allowance = fields.Monetary(
        string='Allowance',
    )
    
    mobile_provided = fields.Boolean(
        string='Provided',
    )

    food_allowance = fields.Monetary(
        string='Allowance',
    )
    
    food_provided = fields.Boolean(
        string='Provided',
    )

    ticket_allowance = fields.Monetary(
        string='Allowance',
    )
    
    ticket_provided = fields.Boolean(
        string='Provided',
    )

    reseidence_permit_allowance = fields.Monetary(
        string='Allowance',
    )
    
    reseidence_permit_provided = fields.Boolean(
        string='Provided',
    )

    health_insurance_allowance = fields.Monetary(
        string='Allowance',
    )
    
    health_insurance_provided = fields.Boolean(
        string='Provided',
    )

    other_allowance_start = fields.Monetary(
        string='Start',
    )
    other_allowance_end = fields.Monetary(
        string='End',
    )
    
    other_provided = fields.Boolean(
        string='Provided',
    )

    total_start = fields.Monetary(
        string='Start',
    )
    total_end = fields.Monetary(
        string='End',
    )


class ElecPayrollContract(models.Model):
    _inherit = ['hr.contract']


    is_overtime = fields.Boolean(string = "Overtime", default = False)
    struct_id = fields.Many2one('hr.payroll.structure', string='Structure',
        readonly=True, states={'draft': [('readonly', False)]},
        help='Defines the rules that have to be applied to this payslip, accordingly '
             'to the contract chosen. If you let empty the field contract, this field isn\'t '
             'mandatory anymore and thus the rules applied will be all the rules set on the '
             'structure of all contracts of the employee valid for the chosen period')

    struct_type_name = fields.Char(string="name")

    @api.constrains('wage')
    def _check_wage_limit(self):
        if self.wage:
            if self.wage > self.basic_start and self.wage < self.basic_end :
                return
            else:
                raise ValidationError(_('Wage must be between {start} and {end} !'.format(start=self.basic_start, end=self.basic_end)))

    @api.constrains('other_allowance')
    def _check_wage_limit(self):
        if self.other_allowance:
            if self.other_allowance > self.other_allowance_start and self.other_allowance < self.other_allowance_end :
                return
            else:
                raise ValidationError(_('Other Allowance must be between {start} and {end} !'.format(start=self.other_allowance_start, end=self.other_allowance_end)))

    @api.depends('wage','other_allowance')
    def _compute_total_wage(self):
        for record in self:
            record.total_start =  self.wage + self.housing_allowance + self.transportation_allowance + self.mobile_allowance + self.food_allowance + self.ticket_allowance + self.reseidence_permit_allowance + self.health_insurance_allowance + self.other_allowance

    @api.onchange('structure_type_id')
    def onchange_structure_type_id(self):
        self.struct_type_name =self.structure_type_id.name
    

    # @api.depends('structure_type_id')
    # def _get_structure_data(self):
    #     for rec in self:
    #         if rec.structure_type_id:
    #             # rec.basic_start = rec.structure_type_id.basic_start
    #             rec.basic_end = rec.structure_type_id.basic_end
    #             rec.housing_allowance = rec.structure_type_id.housing_allowance
    #             rec.housing_provided = rec.structure_type_id.housing_provided
    #             rec.transportation_allowance = rec.structure_type_id.transportation_allowance
    #             rec.transportation_provided = rec.structure_type_id.transportation_provided
    #             rec.mobile_allowance = rec.structure_type_id.mobile_allowance
    #             rec.mobile_provided = rec.structure_type_id.mobile_provided
    #             rec.food_allowance = rec.structure_type_id.food_allowance
    #             rec.food_provided = rec.structure_type_id.food_provided
    #             rec.ticket_allowance = rec.structure_type_id.ticket_allowance
    #             rec.ticket_provided = rec.structure_type_id.ticket_provided
    #             rec.reseidence_permit_allowance = rec.structure_type_id.reseidence_permit_allowance
    #             rec.reseidence_permit_provided = rec.structure_type_id.reseidence_permit_provided
    #             rec.health_insurance_allowance = rec.structure_type_id.health_insurance_allowance
    #             rec.health_insurance_provided = rec.structure_type_id.health_insurance_provided
    #             rec.other_allowance_start = rec.structure_type_id.other_allowance_start
    #             rec.other_allowance_end = rec.structure_type_id.other_allowance_end
    #             rec.other_provided = rec.structure_type_id.other_provided
    #             rec.total_start = rec.structure_type_id.total_start
    #             rec.total_end = rec.structure_type_id.total_end
    
    basic_start = fields.Monetary(
        string='Start',
        related='structure_type_id.basic_start',
        store=True
    )
    basic_end = fields.Monetary(
        string='End',
        related='structure_type_id.basic_end',      
        store=True
    )
    housing_allowance = fields.Monetary(
        string='Allowance',
        related='structure_type_id.housing_allowance',     
        store=True
    )
    
    housing_provided = fields.Boolean(
        string='Provided',
        related='structure_type_id.housing_provided',    
        store=True
    )

    transportation_allowance = fields.Monetary(
        string='Allowance',
        related='structure_type_id.transportation_allowance',     
        store=True
    )
    
    transportation_provided = fields.Boolean(
        string='Provided',
        related='structure_type_id.transportation_provided',      
        store=True
    )

    mobile_allowance = fields.Monetary(
        string='Allowance',
        related='structure_type_id.mobile_allowance',      
        store=True
    )
    
    mobile_provided = fields.Boolean(
        string='Provided',
        related='structure_type_id.mobile_provided',       
        store=True
    )

    food_allowance = fields.Monetary(
        string='Allowance',
        related='structure_type_id.food_allowance',      
        store=True
    )
    
    food_provided = fields.Boolean(
        string='Provided',
        related='structure_type_id.food_provided',      
        store=True
    )

    ticket_allowance = fields.Monetary(
        string='Allowance',
        related='structure_type_id.ticket_allowance',      
        store=True
    )
    
    ticket_provided = fields.Boolean(
        string='Provided',
        related='structure_type_id.ticket_provided',      
        store=True
    )

    reseidence_permit_allowance = fields.Monetary(
        string='Allowance',
        related='structure_type_id.reseidence_permit_allowance',
        store=True
    )
    
    reseidence_permit_provided = fields.Boolean(
        string='Provided',
        related='structure_type_id.reseidence_permit_provided',      
        store=True
    )

    health_insurance_allowance = fields.Monetary(
        string='Allowance',
        related='structure_type_id.health_insurance_allowance',       
        store=True
    )
    
    health_insurance_provided = fields.Boolean(
        string='Provided',
        related='structure_type_id.health_insurance_provided',   
        store=True
    )

    other_allowance_start = fields.Monetary(
        string='Start',
        related='structure_type_id.other_allowance_start',    
        store=True
    )
    other_allowance_end = fields.Monetary(
        string='End',
        related='structure_type_id.other_allowance_end',  
        store=True
    )

    other_allowance = fields.Monetary(
        string='Other Allowance',      
        store=True
    )
    
    other_provided = fields.Boolean(
        string='Provided',
        related='structure_type_id.other_provided',      
        store=True
    )

    total_start = fields.Monetary(
        string='Total',
        compute = "_compute_total_wage",
        store=True
    )
    total_end = fields.Monetary(
        string='End',
        related='structure_type_id.total_end',       
        store=True
    )

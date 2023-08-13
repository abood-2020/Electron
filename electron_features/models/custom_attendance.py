from odoo import api , fields , models , _
from odoo.exceptions import UserError , ValidationError
from datetime import datetime , timedelta

class ElectronAttendance(models.Model):
    _inherit = ['hr.attendance']

    is_absent = fields.Boolean(string="Is Absent" , compute="_check_is_absent" , default=False ,store = True)
    normal_overtime = fields.Float(stirng="Normal OT" ,default = 0.0 ,store = True)    
    note = fields.Char(string="Note")
    
    @api.depends('check_in', 'check_out')
    def _compute_worked_hours(self):
        for attendance in self:
            if attendance.check_out and attendance.check_in:
                delta = attendance.check_out - attendance.check_in
                attendance.worked_hours = delta.total_seconds() / 3600.0
            else:
                attendance.worked_hours = False
    
    @api.onchange('check_out')
    def _compute_normal_overtime(self):
        ICPSudo = self.env['ir.config_parameter'].sudo()
        for rec in self:
            # Get Data From Attendance Settings
            daily_hours =int(ICPSudo.get_param('electron_features.daily_working_hours'))
            thu_hours =int(ICPSudo.get_param('electron_features.thursday_hours'))
            day = rec.check_in.strftime('%A')
            
            if day == "Thursday":
                overtime = rec.worked_hours - thu_hours
                rec.normal_overtime = overtime if overtime > 0 else 0.0
            else:
                overtime = rec.worked_hours - daily_hours
                rec.normal_overtime = overtime if overtime > 0 else 0.0
            
    @api.depends('check_in' , 'check_out')     
    def _check_is_absent(self):
        ICPSudo = self.env['ir.config_parameter'].sudo()
        
        for rec in self:
            # Get Data From Attendance Settings
            daily_hours =int(ICPSudo.get_param('electron_features.daily_working_hours')) - 1
            thu_hours =int(ICPSudo.get_param('electron_features.thursday_hours')) - 1
            
            # Get Data From 
            worked_hours = rec.worked_hours
            day = rec.check_in.strftime('%A')
            
            if day == "Thursday":
                rec.is_absent = True if worked_hours < thu_hours else False
            elif day == "Friday":
                rec.is_absent = False
            else:
                rec.is_absent = True if worked_hours < daily_hours else False
                            


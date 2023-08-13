from odoo import api, fields, models ,_
from odoo.exceptions import ValidationError


class ElectAttendace(models.Model):
    _inherit = "hr.attendance"   
    # worked_hours = fields.Float(string='Worked Hours', compute='_compute_worked_hours_new', store=True, readonly=True)

    @api.depends('check_in', 'check_out')
    def _compute_worked_hours(self):
        for attendance in self:
            if attendance.check_out:
                delta = attendance.check_out - attendance.check_in
                attendance.worked_hours = (delta.total_seconds() - 3600.0) / 3600.0
            else:
                attendance.worked_hours = False


    projects = fields.Many2one(
        'project.project',
        string='Project',
        )
    
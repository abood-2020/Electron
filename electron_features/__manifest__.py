# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Electron Features',
    'version': '1.0',
    'author': "ENG.Abd AlRazzaq AlDahdouh",
    'summary': 'The module was created to customize the Odoo system to be suitable for Electron Company',
    'depends': ['account','hr'],
    'category': 'Custom/stock',
    'data': [
        # data
        'data/work_entry.xml',
        'data/leave_type.xml',
	'data/cron.xml',
        # views
        'security/ir.model.access.csv',
        'views/hr_payslip_run.xml',
        'views/hr_attendance.xml',
        'views/res_config.xml',
        'views/hr_employee.xml',
        'views/custom_leave_view.xml',
        'views/partial_payment.xml',
        'views/custom_payment.xml',
        'views/commission_payment.xml',
        
    ],
    'demo': [
    ],
    'css': [],
    'installable': True,
    'auto_install': False,
    'application': True,
}

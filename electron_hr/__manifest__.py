# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Electron HR',
    'version': '1.0',
    'category': 'HR',
    'author': "Yousuf Hussein",
    'summary': 'HR Customizations',
    'depends': ['web', 'mail','base','hr_payroll','hr_attendance','hr_contract','hr','account'],
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'data/salary_rule_loan.xml',
        'views/hr_loan_seq.xml',
        'views/hr_loan.xml',
        'views/hr_payroll.xml',
        'views/salary_structure.xml',
        'views/salary_advance.xml',
        'views/petty_cash.xml',
    ],
    'demo': [
    ],
    'css': [],
    'installable': True,
    'auto_install': False,
    'application': True,
}

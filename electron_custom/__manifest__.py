# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Electron Custom',
    'version': '1.0',
    'summary': 'Electron Custom Module',
    'depends': ['web','base','purchase','sale','account','hr'],
    'data': [
        
        # 'security/ir.model.access.csv',
        'security/security.xml',
        'views/account_account.xml',
        'views/res_users.xml',
        'views/purchase_report_templates.xml',
        'views/accounting_report_templates.xml',
        'views/petty_close_report_template.xml',
        'views/sale_report_templates.xml',
        'views/delivery_slip_report.xml',
        'views/purchase.xml',
        'views/sale_res_config.xml',
        'views/purchase_res_config.xml',
        'views/product_category.xml',
        'views/contract_payroll_structure_type.xml',
        'views/attendance.xml',
    ],
    'demo': [
    ],
    'css': [],
    'installable': True,
    'auto_install': False,
    'application': False,
}

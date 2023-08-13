# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Partner Ledger Reports',
    'version': '1.0',
    'author': "ENG.Abd AlRazzaq AlDahdouh",
    'summary': 'The module was created in order to Print Partner Ledger Details as Parnter',
    'depends': ['account'],
    'category': 'Custom/stock',
    'data': [
        # security
        'security/ir.model.access.csv',
        # views
        'wizard/partner_ledger_view.xml',
        # reports
        'report/report_partner_ledger_template.xml',
        'report/report_partners_summary_template.xml',
        'report/report_partners_summary_filter_users_template.xml',
        'report/report_actions.xml'
        ],
    'demo': [],
    'css': [],
    'installable': True,
    'auto_install': False,
    'application': True,
}

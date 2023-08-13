# -*- coding: utf-8 -*-

{
    'name': 'Odoo 14 Full Accounting Kit',
    'version': '14.0.3.13.16',
    'category': 'Accounting',
    'summary': " Day-Bank-Cash book reports.",
    'description': """
                    Odoo 14 Accounting,Accounting Reports, Odoo 14 Accounting 
                    Financial Reports, Financial Report for Odoo 14,
                    """,
    'author': 'Cybrosys Techno Solutions, Odoo SA',
    'company': 'Cybrosys Techno Solutions',
    'depends': ['base', 'account', 'sale', 'account_check_printing'],
    'data': [
        'security/ir.model.access.csv',
        'views/reports_config_view.xml',
        'views/accounting_menu.xml',
        'wizard/partner_ledger.xml',
        'wizard/account_bank_book_wizard_view.xml',
        'report/report_partner_ledger.xml',
        'report/account_bank_book_view.xml',
        'report/report.xml'
    ],
    'qweb': [
        'static/src/xml/template.xml',
        'static/src/xml/payment_matching.xml'
    ],
    'images': ['static/description/banner.gif'],
    'installable': True,
    'auto_install': False,
    'application': True,
}

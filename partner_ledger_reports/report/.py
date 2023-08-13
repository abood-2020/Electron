from odoo import models
from openpyxl.drawing.image import Image


class PartnerLedgerXlsx(models.AbstractModel):
    _name = 'report.partner_ledger_reports.report_partner_ledger_xls'
    _inherit = 'report.report_xlsx.abstract'
    
    def generate_xlsx_report(self,workbook, data, partners):
   
        report_name = "Partner Ledger Reports"

        # One Sheet by partner
        sheet = workbook.add_worksheet(report_name[:31])
        bold = workbook.add_format({'bold': True})
        
        sheet.set_column('B:B', 20)
        sheet.set_column('C:C', 15)
        sheet.set_column('E:E', 15)
        sheet.set_column('F:F', 30)
        sheet.set_column('J:J', 14)

        sheet.merge_range(0,0,0,1,"ELECTRON TRADING COMPANY W.L.L",bold)
        sheet.write(1, 0, 'DOHA-QATAR')
        
        sheet.merge_range(3, 1, 3, 2, "Partner Name", bold)
        sheet.merge_range(3, 3, 3, 4, data['partner_id'])
        
        sheet.write(3, 6, "Date From ", bold)
        sheet.merge_range(3, 7,3,8, data['date_from'])
        
        sheet.write(4, 6, "Date To ", bold)
        sheet.merge_range(4, 7, 4, 8, data['date_to'])
        
        sheet.write(5, 0, "Date", bold)
        sheet.write(5, 1, "Entry #", bold)
        sheet.write(5, 2, "Account id", bold)
        sheet.write(5, 3, "JRNL", bold)
        sheet.write(5, 4, "Due Date", bold)
        sheet.write(5, 5, "Memo", bold)
        sheet.write(5, 6, "Initial Balance", bold)
        sheet.write(5, 7, "Debit", bold)
        sheet.write(5, 8, "Credit", bold)
        sheet.write(5, 9, "Balance", bold)
        
        sheet.write(6, 1, "Initial Balance", bold)
        sheet.write(6, 6, data['initial_balance'], bold)
        
        rows = 7
        
        for line in data['lines']:
            balance = data['initial_balance']
            for col in range(0,10,1):
                if col == 6:
                    sheet.write(rows, col, balance)
                sheet.write(rows, col, line[col])
            
            balance = line[8]
            rows += 1
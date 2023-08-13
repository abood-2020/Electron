from odoo import models
from openpyxl.drawing.image import Image
from datetime import datetime, timezone
import pytz


class PartnerLedgerXlsx(models.AbstractModel):
    _name = 'report.partner_ledger_reports.report_partner_ledger_xls'
    _inherit = 'report.report_xlsx.abstract'
    
    def generate_xlsx_report(self,workbook, data, partners):
   
        report_name = "Partner Ledger Reports"
        # Get the current date and time
        qatar_tz = pytz.timezone('Asia/Qatar')
        now = datetime.now(qatar_tz)

        # Format the date and time
        formatted_now = now.strftime("%Y-%m-%d %H:%M:%S")
        # logo_image = io.BytesIO(base64.b64decode('/partner_ledger_reports/static/src/electron-trading.jpg'))
        # One Sheet by partner
        sheet = workbook.add_worksheet(report_name[:31])
        bold = workbook.add_format({'bold': True})
        format_1 = workbook.add_format({'bold': True, 'align': 'center', 'bg_color': '#F7E06E','border': 2})
        format_border_bold = workbook.add_format({'border': 1,'bold': True})
        format_border = workbook.add_format({'border': 1})
        
        
        sheet.set_column('A:A', 14)
        sheet.set_column('B:B', 20)
        sheet.set_column('C:C', 15)
        sheet.set_column('E:E', 15)
        sheet.set_column('F:F', 30)
        sheet.set_column('J:J', 14)

        sheet.merge_range(0,0,0,1,"ELECTRON TRADING COMPANY W.L.L",bold)
        sheet.write(1, 0, 'DOHA-QATAR')
        
        sheet.merge_range(1, 6, 1, 7, 'Printing date')
        sheet.merge_range(1, 8, 1, 9, str(formatted_now))
        
        sheet.merge_range(3, 4, 3, 5, 'Statement of Account(SOA)', format_1)
        
        sheet.write(5, 1, "Partner Name", bold)
        sheet.merge_range(5, 3, 5, 4, data['partner_id'])
        
        sheet.write(5, 6, "Date From ", bold)
        sheet.merge_range(5, 7, 5, 8, data['date_from'])
        
        sheet.write(6, 6, "Date To ", bold)
        sheet.merge_range(6, 7, 6, 8, data['date_to'])
        
        label_table = ["Date", "Entry #","Account id","JRNL","Due Date","Memo","Debit","Credit","Amount","Balance"]
        
        for i in range(0,len(label_table), 1):
            sheet.write(8, i, label_table[i], format_border_bold)
                
        for i in range(0,10,1):
            if i == 1:
                sheet.write(9, 1, "Initial Balance", format_border)
            elif i == 6:
                sheet.write(9, 6, data['initial_balance'], format_border)
            else:
                sheet.write(9, i, " ", format_border)

        rows = 10
        
        for line in data['lines']:
            balance = data['initial_balance']
            for col in range(0,10,1):
                if col == 6:
                    sheet.write(rows, col, balance,format_border)
                sheet.write(rows, col, line[col],format_border)
            
            balance = line[8]
            rows += 1
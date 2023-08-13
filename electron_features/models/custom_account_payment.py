from odoo import models, fields, api, _
from odoo.exceptions import UserError

class CustomAccountPayment(models.Model):
    _inherit = 'account.payment'
    
    sale_person = fields.Many2one('res.users' , string="Sale Person")
    
    # def _seek_for_lines(self):
    #     ''' Helper used to dispatch the journal items between:
    #     - The lines using the temporary liquidity account.
    #     - The lines using the counterpart account.
    #     - The lines being the write-off lines.
    #     :return: (liquidity_lines, counterpart_lines, writeoff_lines)
    #     '''
    #     self.ensure_one()
    #     liquidity_lines = self.env['account.move.line']
    #     counterpart_lines = self.env['account.move.line']
    #     writeoff_lines = self.env['account.move.line']

    #     for line in self.move_id.line_ids:
    #         if line.account_id in (
    #                 self.journal_id.default_account_id,
    #                 self.journal_id.payment_debit_account_id,
    #                 self.journal_id.payment_credit_account_id,
    #         ):
    #             liquidity_lines += line
    #         elif line.account_id.internal_type in ('receivable', 'payable' , 'liquidity') or line.partner_id == line.company_id.partner_id:
    #             counterpart_lines += line
    #         else:
    #             writeoff_lines += line                
    #     return liquidity_lines, counterpart_lines, writeoff_lines

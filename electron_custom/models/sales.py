from odoo import api, fields, models, _
from odoo.exceptions import AccessError, UserError, ValidationError


class ElecSales(models.Model):
    _inherit = ['sale.order']

    attn  = fields.Char("Atten")
    discount = fields.Float("Discount", compute = '_compute_total_no_disc')
    total_no_disc = fields.Float('Total', compute = '_compute_total_no_disc')
    is_lower = fields.Boolean('Is Lower', compute = '_compute_is_lower')


    state = fields.Selection([
        ('to approve', 'To Approve'),
        ('approved', 'Approved'),
        ('draft', 'Quotation'),
        ('sent', 'Quotation Sent'),
        ('sale', 'Sales Order'),
        ('done', 'Locked'),
        ('cancel', 'Cancelled'),
        ], string='Status', readonly=True, copy=False, index=True, tracking=3, default='draft')

    # def _prepare_confirmation_values(self):
    #     for order in self:
    #         if order.amount_total > order.company_id.sale_double_validation_amount:
    #             return {
    #         'state': 'to approve',
    #         'date_order': fields.Datetime.now()
    #         }
    #         else:
    #             return order.button_approve()
    
    @api.depends('total_no_disc')
    def _compute_total_no_disc(self):
        self.total_no_disc = 0.0
        self.discount = 0.0
        for rec in self:
            for line in rec.order_line:
                if not line.product_id.default_code == "DISC":
                    rec.total_no_disc +=  (line.product_uom_qty * line.price_unit)
                if line.product_id.default_code == "DISC": 
                    rec.discount +=  line.price_subtotal

    def action_confirm(self):
        if self._get_forbidden_state_confirm() & set(self.mapped('state')):
            raise UserError(_(
                'It is not allowed to confirm an order in the following states: %s'
            ) % (', '.join(self._get_forbidden_state_confirm())))

        for order in self.filtered(lambda order: order.partner_id not in order.message_partner_ids):
            order.message_subscribe([order.partner_id.id])
        if self.company_id.sale_double_validation == 'two_step' and self.amount_total > self.company_id.sale_double_validation_amount and self.state != 'approved':
            self.write({'state':'to approve','date_order':fields.Datetime.now()})
        else:
            self.write(self._prepare_confirmation_values())

        # Context key 'default_name' is sometimes propagated up to here.
        # We don't need it and it creates issues in the creation of linked records.
        context = self._context.copy()
        context.pop('default_name', None)

        self.with_context(context)._action_confirm()
        if self.env.user.has_group('sale.group_auto_done_setting'):
            self.action_done()
        return True

    @api.model
    def create(self, vals):
        res = super(ElecSales, self).create(vals)
        if res['is_lower'] == True:
            res[ 'state' ] = 'to approve'
        return res

    @api.model
    def write(self, vals):
        res = super(ElecSales, self).write(vals)
        if self.is_lower == True and self.state == 'draft':
            self.write({'state':'to approve'})
        return res


    @api.depends('order_line','is_lower')
    def _compute_is_lower(self):
        for rec in self:
            rec.is_lower = False
            if rec.company_id.sale_double_validation != 'one_step':
                if rec.order_line:
                    for line in rec.order_line:
                        if line.product_id:
                            if line.product_id.min_price != 0.0:
                                if line.product_id.min_price > line.price_unit:
                                    rec.is_lower = True
                                    break
    

    def button_approve(self, force=False):
        self.write({'state': 'approved'})

    def button_refuse(self, force=False):
        self.write({'state': 'cancel'})

class InvoiceMoveElec(models.Model):
    _inherit = 'account.move'

    delivery_note = fields.Char('Delivery', compute = '_get_delivery_note')
    discount = fields.Float("Discount", compute = '_compute_total_no_disc')
    total_no_disc = fields.Float('Total', compute = '_compute_total_no_disc')
    po_num  = fields.Char("PO Num.",readonly=False)

    @api.depends('total_no_disc')
    def _compute_total_no_disc(self):
        self.total_no_disc = 0.0
        self.discount = 0.0
        for rec in self:
            for line in rec.invoice_line_ids:
                if not line.name == "[DISC] Discount":
                    rec.total_no_disc +=  (line.quantity * line.price_unit)
                if line.name == "[DISC] Discount": 
                    rec.discount +=  line.price_subtotal

    @api.depends('delivery_note','po_num')
    def _get_delivery_note(self):
        for rec in self:
            rec.delivery_note = ""
            rec.po_num = ""
            if rec.invoice_origin:
                transfers = self.env['stock.picking'].search([('origin','=',rec.invoice_origin)],limit = 1)
                if transfers:
                    rec.delivery_note = transfers.name
                    rec.po_num = transfers.po_num
                else:
                    rec.delivery_note = ""
                    rec.po_num = ""
            if rec.inv_origin_id:
                transfers = self.env['stock.picking'].search([('origin','=',rec.inv_origin_id.name)],limit = 1)
                if transfers:
                    rec.delivery_note = transfers.name
                    rec.po_num = transfers.po_num
                else:
                    rec.delivery_note = ""
                    rec.po_num = ""
    

class SaleOrderLineElec(models.Model):
    _inherit = 'sale.order.line'

    min_price = fields.Float('Min price')

    page_break = fields.Boolean(
        string="Pagebreak", copy=False, default=False)
    display_title = fields.Boolean(
        string="display_title", copy=False, compute="check_prev_pagebreak")
    line_numb = fields.Integer(
        string="Line Numb", copy=False, compute="check_prev_pagebreak")

    def check_prev_pagebreak(self):
        counter = 0
        for lines in self:
            display_title = False
            counter = counter + 1
            lines.update({'line_numb': counter})
            if lines.page_break:
                display_title = True
            if display_title:
                lines.update({'display_title': display_title})
            else:
                lines.update({'display_title': display_title})

    @api.onchange('product_id')
    def onchange_product_id_min_price(self):
        self.min_price = self.product_id.min_price

    
    # @api.onchange('price_unit')
    # def onchange_price_unit_min_price(self):
    #     if self.price_unit:
    #         if self.product_id.min_price != 0.0 and self.price_unit < self.product_id.min_price:
    #             self.order_id.write({'state': 'to approve'})
                # raise UserError(_("You can't sell below product's %s Min Price, please contact admin!") % (self.product_id.name))
                
class Company(models.Model):
    _inherit = 'res.company'
    
    sale_double_validation_amount = fields.Monetary(string='Double validation amount', default=2000,
        help="Minimum amount for which a double validation is required")
    sale_double_validation = fields.Selection([
          ('one_step', 'Confirm sale orders in one step'),
          ('two_step', 'Get 2 levels of approvals to confirm a sale order')])



class ElecSalesConfig(models.TransientModel):
    _inherit = ['res.config.settings']

    
    sale_order_approval = fields.Boolean(
        string='Sale Order Approval', default=lambda self: self.env.company.sale_double_validation == 'two_step'        
    )
    sale_double_validation = fields.Selection(related='company_id.sale_double_validation', string="Levels of Approvals *", readonly=False)
    sale_double_validation_amount = fields.Monetary(related='company_id.sale_double_validation_amount', string="Minimum Amount", currency_field='company_currency_id', readonly=False)

    def set_values(self):
        super(ElecSalesConfig, self).set_values()
        self.sale_double_validation = 'two_step' if self.sale_order_approval else 'one_step'

class TransferElec(models.Model):
    _inherit = 'stock.picking'

    po_num  = fields.Char("PO Num.",readonly=False,compute="_set_value_po")
    
    @api.depends('origin')
    def _set_value_po(self):
        for rec in self:
            sale_order = self.env['sale.order'].search([('name' , '=' , rec.origin)])
            if len(sale_order) != 0:
                rec.po_num = sale_order.client_order_ref
            else:
                rec.po_num = ''
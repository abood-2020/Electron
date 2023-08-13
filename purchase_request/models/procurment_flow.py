from odoo import api, fields, models, api, _
from datetime import datetime
from odoo.exceptions import AccessError, UserError, ValidationError

class ProcurmentFlow(models.Model):
    _inherit = "purchase.requester"

    @api.onchange('product_material_group')
    def onchange_product_material_group(self):
        for line in self.products:
            line.unlink()

    @api.onchange("product_catagory")
    def _sub_catagory_domin(self):
        res = {}
        res['domain']={'product_sub_catagory':[('parent_id', '=', self.product_catagory.id)]}
        return res

    @api.onchange("product_sub_catagory")
    def _material_group_domin(self):
        res2 = {}
        res2['domain']={'product_material_group':[('parent_id', '=', self.product_sub_catagory.id)]}
        return res2

    @api.model
    def _getUserGroupId(self):
        return [('groups_id', '=', self.env.ref('purchase.group_purchase_manager').id)]

    project = fields.Many2one('project.project', string = 'Project', required = True , states={'acc': [('readonly', True)],'con': [('readonly', True)],'reject': [('readonly', True)]})
    project_budget = fields.Integer(string= 'Project Budget',compute = "_compute_budget")
    approver_id = fields.Many2one('res.users', string='Approver',  domain=_getUserGroupId, readonly=True, track_visibility='always',states={'acc': [('readonly', True)],'con': [('readonly', True)],'reject': [('readonly', True)]},compute='_compute_approver')
    total_material = fields.Integer(string = 'Material Total')
    total = fields.Monetary(compute='_amount_all', string='Total', store=True)
    currency_id = fields.Many2one('res.currency', string='Currency',default=lambda self: self.env.user.company_id.currency_id)
    products = fields.One2many('purchase.requester.order.line','product_procurment',string = "Products" ,states={'acc': [('readonly', True)],'con': [('readonly', True)],'reject': [('readonly', True)]})
    is_not_defined_product = fields.Boolean(string = "New Product" , default = False ,states={'acc': [('readonly', True)]})
    purchase_requisition_id = fields.One2many('purchase.requisition', 'purchase_requester_id',
                                        string='Purchase Agreement Reference', states={'acc': [('readonly', True)]})
    product_catagory = fields.Many2one('product.category',string = "System", domain =[("parent_id","=","All"),('company_id','=','ELECTRON MEP')],states={'acc': [('readonly', True)],'con': [('readonly', True)],'reject': [('readonly', True)]})
    product_sub_catagory = fields.Many2one('product.category',string = "Sub-System",states={'acc': [('readonly', True)],'con': [('readonly', True)],'reject': [('readonly', True)]})
    product_material_group = fields.Many2one('product.category',string = "Material Group",states={'acc': [('readonly', True)],'con': [('readonly', True)],'reject': [('readonly', True)]})
    
    mr_delivery_date = fields.Datetime(
        string='Delivery Date',
        default=fields.Datetime.now,
    )
    

    @api.onchange('project')
    def _compute_budget(self):
        for req in self:
            if req.project:
                req.project_budget= req.project.project_budget_qyt_total


    # @api.onchange('total')
    def _compute_approver(self):
        for req in self:
            if req.project:
                req.approver_id = req.project.user_id.id

            	#this is if we want to give an approver based on the total of budget quantity
                # if req.total > req.project.project_budget_qyt_total:
                #     req.approver_id = req.project.user_id
                # elif req.is_not_defined_product == True:
                #     req.approver_id = req.project.user_id
                # else:
                #     req.approver_id = False

    def button_creat_agreement(self, context=None):
        for rec in self:
            rec.state = 'acc'
        return {
            "type": "ir.actions.act_window",
            "res_model": "purchase.requisition",
            "views": [[False, "form"]],
            'view_type': 'form',
            'view_mode': 'form',
            'context': {'default_purchase_inhrt_id': self.approver_id.id,
                        'default_new_id': self.name_seq,
                        'default_purchase_requester_id': self.id,
                        # 'default_project_id': self.project.id,
                        },
        }



    @api.depends('products.product_id','products.price_unit','products.product_qty')
    def _amount_all(self):
        for order in self:
            order.total = 0.0
            for line in order.products:
                # order.total += (line.price_unit * line.product_qty)
                order.total += (line.product_qty)


class Project(models.Model):
    _inherit = "project.project"


    def purchase_request_tree_view(self):
        return{
        'name':_('Purchase Requests'),
        'domain':[('project','=',self.id)],
        'view_type':'form',
        'view_mode':'tree,form',
        'res_model':'purchase.requester',
        'view_id':False,
        'type':'ir.actions.act_window',
        }

    def project_budget_tree_view(self):
        return{
        'name':_('Budgets'),
        'domain':[('project','=',self.id)],
        'view_type':'form',
        'view_mode':'tree,form',
        'res_model':'project.set.budget',
        'view_id':False,
        'type':'ir.actions.act_window',
        'context': dict(self._context),
        }


    def _compute_request_count(self):
        Requests = self.env['purchase.requester']
        self.request_count = Requests.search_count([
                ('project', '=', self.id),
            ])

    def _compute_project_budget_total(self):
        Budgets = self.env['project.set.budget'].search([('project', '=', self.id),])
        if Budgets:
            for budget in Budgets:
                self.project_budget_total += budget.total
        else:
            self.project_budget_total = 0

    def _compute_project_budget_qyt_total(self):
        Budgets = self.env['project.set.budget'].search([('project', '=', self.id),])
        if Budgets:
            for budget in Budgets:
                self.project_budget_qyt_total += budget.total_qyt
        else:
            self.project_budget_qyt_total = 0
    
    project_code = fields.Char(
        string='Project Code',
    )
    
    budget = fields.Integer(string = 'Budget')
    request_count = fields.Integer(compute='_compute_request_count', string="Number of Purchase Requests")
    project_budget_total = fields.Integer(compute='_compute_project_budget_total', string="Total Budget")
    project_budget_qyt_total = fields.Integer(compute='_compute_project_budget_qyt_total', string="Total Quantity Budget")



class Product(models.Model):
    _name = "purchase.requester.order.line"

    product_id = fields.Many2one('product.product', string='Product',required =True)
    name = fields.Text(string='Description')
    product_qty = fields.Float(string='Quantity', digits='Product Unit of Measure', required=True)
    budget_qyt = fields.Float(string = 'Budget Quantity',store = True ,digits='Product Unit of Measure')
    price_unit = fields.Float(string='Unit Price', required=True, digits='Product Price')
    price_total = fields.Monetary(compute='_compute_amount', string='Total')
    product_id_uom = fields.Many2one('uom.uom', string='UoM', compute  = "_product_get_uom")
    currency_id = fields.Many2one('res.currency', string='Currency',default=lambda self: self.env.user.company_id.currency_id)
    product_procurment = fields.Many2one('purchase.requester',string='Product',index=True, ondelete='cascade')
    project_budget = fields.Many2one('project.set.budget',string='Products',index=True, ondelete='cascade')
    product_sub_catagory = fields.Many2one(string = "Sub Catagory", related = "product_procurment.product_sub_catagory")
    product_material_group_request = fields.Many2one(string = "Material Group", related = "product_procurment.product_material_group")
    product_sub_catagory_budget = fields.Many2one(string = "Sub Catagory", related = "project_budget.product_sub_catagory")
    product_material_group = fields.Many2one(string = "Material Group", related = "project_budget.product_material_group")

    @api.onchange('product_id')
    @api.depends('product_id_uom')
    def _product_get_uom(self):
        for rec in self:
            if rec.product_id:
                rec.product_id_uom = rec.product_id.uom_id
    


    @api.depends('product_qty', 'price_unit')
    def _compute_amount(self):
        for line in self:
            line.price_total += line.price_unit

    @api.onchange('product_id')
    def onchange_product_id(self):
    	# get the quantity set in the projects budge
        project = self.env['project.set.budget'].search([('project', '=', self.product_procurment.project.id)])
        for line in self:
            for budget_line in project.products:
                if budget_line.product_id == line.product_id:
                    line.budget_qyt = budget_line.product_qty
            line.price_unit = line.product_id.standard_price
            line.name = line.product_id.default_code



    def _prepare_purchase_order_line(self, product_qty=0.0, price_unit=0.0):
        self.ensure_one()
        date_planned = self.product_procurment.date_order
        return {
        	'name':self.product_id.name,
            'product_id': self.product_id.id,
            'product_qty': self.product_qty,
            'date_planned': date_planned,
            'product_uom': self.product_id.uom_po_id.id,
            'price_unit': self.product_id.standard_price,
        }

    def _prepare_purchase_agreement_line(self, product_qty=0.0, price_unit=0.0):
        self.ensure_one()
        date_planned = self.product_procurment.date_order
        return {
            'product_id': self.product_id.id,
            'product_uom_id':self.product_id.uom_po_id,
            'product_qty': self.product_qty,
            'price_unit': self.product_id.standard_price,
        }



class PurchaseOrder(models.Model):
    _inherit = "purchase.order"
    @api.onchange("partner_id")
    def fill_order_line(self):
        if self.purchase_requester_id:
            for rec in self:
                request_record = self.env['purchase.requester'].search([('name_seq', '=', self.purchase_requester_id.name_seq)])
                lines = [(5,0,0)]
                for line in request_record.products:
		            # Create PO line
                    order_line_values = line._prepare_purchase_order_line(product_qty=0, price_unit=0)
                    lines.append((0, 0, order_line_values))
                rec.order_line = lines


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"
    
    sequence_ref = fields.Integer('No.', compute="_sequence_ref")

    @api.depends('order_id.order_line', 'order_id.order_line.product_id')
    def _sequence_ref(self):
        for line in self:
            no = 0
            for l in line.order_id.order_line:
                no += 1
                l.sequence_ref = no

class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"
    
    sequence_ref = fields.Integer('No.', compute="_sequence_ref")

    @api.depends('order_id.order_line', 'order_id.order_line.product_id')
    def _sequence_ref(self):
        for line in self:
            no = 0
            for l in line.order_id.order_line:
                no += 1
                l.sequence_ref = no

class StockPickingLine(models.Model):
    _inherit = "stock.move"
    
    sequence_ref = fields.Integer('No.', compute="_sequence_ref")

    @api.depends('picking_id.move_ids_without_package', 'picking_id.move_ids_without_package.product_id')
    def _sequence_ref(self):
        for line in self:
            no = 0
            for l in line.picking_id.move_ids_without_package:
                no += 1
                l.sequence_ref = no


class PurchaseRequisition(models.Model):
    _inherit = "purchase.requisition"


    @api.model
    def _getUserGroupId(self):
        return [('groups_id', '=', self.env.ref('purchase.group_purchase_manager').id)]

    approver_id = fields.Many2one(
        string='Approver', domain=_getUserGroupId, readonly=True)
    project_id = fields.Many2one(
        'project.project',
        string='Project',
        )
    purchase_inhrt_id = fields.Many2one(
        'res.users', string='Approver',  store=True, readonly=False)
    purchase_requester_id = fields.Many2one(
        'purchase.requester', string='Request Reference')



    @api.onchange("user_id")
    def fill_order_line(self):
        if self.purchase_requester_id:
            for rec in self:
                request_record = self.env['purchase.requester'].search([('name_seq', '=', self.purchase_requester_id.name_seq)])
                lines = [(5,0,0)]
                for line in request_record.products:
		            # Create PO line
                    order_line_values = line._prepare_purchase_agreement_line(product_qty=0, price_unit=0)
                    lines.append((0, 0, order_line_values))
                rec.line_ids = lines


class ProjectBudget(models.Model):
    _name = "project.set.budget"
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']
    _description = 'Project Budget'
    _rec_name = 'name_seq'


    @api.model
    def create(self, vals):
        if vals.get('name_seq', 'New') == 'New':
            vals['name_seq'] = self.env['ir.sequence'].next_by_code(
                'project.set.budget') or '/'
        return super(ProjectBudget, self).create(vals)

    @api.onchange("product_catagory")
    def _sub_catagory_domin(self):
        res = {}
        res['domain']={'product_sub_catagory':[('parent_id', '=', self.product_catagory.id)]}
        return res

    @api.onchange("product_sub_catagory")
    def _material_group_domin(self):
        res2 = {}
        res2['domain']={'product_material_group':[('parent_id', '=', self.product_sub_catagory.id)]}
        return res2


    @api.depends('products.product_id','products.price_unit','products.product_qty')
    def _amount_all(self):
        for order in self:
            order.total = 0.0
            for line in order.products:
                order.total += (line.price_unit * line.product_qty)
                order.total_qyt += (line.product_qty)
            
    name_seq = fields.Char(string="Budget Reference", required=True, copy=False, readonly=True,  index=True,
                           default=lambda self: _('New'))
    project = fields.Many2one('project.project',string="Project",required = True)
    product_catagory = fields.Many2one('product.category',string = "System", domain =[("parent_id","=","All")])
    product_sub_catagory = fields.Many2one('product.category',string = "Sub-System")
    product_material_group = fields.Many2one('product.category',string = "Material Group")
    total = fields.Float(string="Total" ,compute = "_amount_all",store=True)
    total_qyt = fields.Float(string="Total Quantity" ,compute = "_amount_all",store=True)
    products = fields.One2many('purchase.requester.order.line','project_budget',string = "Products")










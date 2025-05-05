import logging

from odoo import models, fields, api
from odoo import SUPERUSER_ID
from odoo.exceptions import ValidationError
from odoo.exceptions import AccessDenied, UserError


_logger = logging.getLogger(__name__)

"""
* This module is responsible for managing the purchase of courses in the application.
"""
class CoursePurchase (models.Model):
    
    _name = 'course.purchase'
    _description = "Course Purchase Records"    


    user_id = fields.Many2one('res.users', string='User ID', required=True)
    product_id = fields.Many2one('product.product', string='Course', required=True)
    purchase_date = fields.Datetime(string='Purchase Date', default=fields.Datetime.now)
    invoice_id = fields.Many2one('account.move', string='Invoice')
    state = fields.Selection([
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('cancelled', 'Cancelled'),
    ], default='pending', string='Status')


    @api.model
    def purchaseCourceFlow(self, course_id, user):
        course = self.env['product.product'].search([('id', '=', course_id)], limit=1)
        invoice = self.createProductInvoice(course,user)
        if not invoice:
            raise ValidationError("ERROR: Invoice creation failed.")
        
        invoice = self.purchaseCourse(invoice)

        purchase_record = self.userPurchasedCourse(invoice,course)
        record_purchase = self.env['res.transactions'].record_purchase(user,course)

        return purchase_record.read(['id','invoice_id','product_id','user_id'])
        
        

    @api.model
    def validatePurchase(self, user_id, user_wallet, price, product_id):

        if user_wallet.balance < price:
            return False
        
        check_purchase = self.search([('user_id','=',user_id),('product_id','=',product_id)])
        if check_purchase:
            return False
        
        return True


    @api.model
    def purchaseCourse(self, invoice):

        user = self.env['res.users'].search([('id','=',invoice.partner_id.user_id.id)])
        user_wallet = user.ewallet_id
        
        price = 0  
        for line in invoice.line_ids:
            price += line.quantity * line.price_unit
        if user_wallet.balance < price:
            raise ValidationError("ERROR: User does not have enough balance.")
        if not self.validatePurchase(user.id,user_wallet,price,invoice.line_ids[0].product_id.id):
            raise ValidationError("ERROR: User does already own the course.")
        
        new_balance =  int(user_wallet.balance - price)
        print(new_balance)
        self.env.cr.savepoint()
        user_wallet.write(
            {
                'balance':new_balance,
            }
        )
        invoice.write({
            'payment_state': 'paid',
        })
        self.env.cr.commit()
        return invoice



    @api.model
    def createProductInvoice(self,course,user):

        Currency = self.env.ref('e_wallet_manager.learning_coins')
        if not Currency :
            raise ValidationError("There was an error :Currency.")

        invoice_metadata = {
            'partner_id':user.partner_id.id,
            'move_type':"out_invoice",
            'currency_id':Currency.id
        }

        invoice = self.env['account.move'].create(invoice_metadata)

        if not invoice:
            raise ValidationError("Invoice creation failed.")
        else:
            invoice_line= self._createInvoiceLine(course,1,invoice)
            invoice.action_post()

        """ return {'response':f"Invoice Was successfully created under id: {invoice.id}",
                                    'invoice_id':invoice.id,
                                    'user':user.login,
                                    'course_quantity':invoice_line.quantity,
                                    'price':invoice.amount_total_signed,
                                    'currency':invoice.currency_id.name} """

        return invoice


    def _createInvoiceLine(self,course,course_quantity,invoice):
        return self.env['account.move.line'].create({
            'move_id':invoice.id,
            'product_id':course.id,
            'quantity':course_quantity,
            'price_unit':course.price_lc
        })
    

   
    @api.model
    def userPurchasedCourse(self, invoice,course):
        user_id = invoice.partner_id.user_id.id
        product_id = course.id
        invoice_id = invoice.id
        state = invoice.state
        purchase = self.create({
            'user_id': user_id,
            'product_id': product_id,
            'purchase_date': fields.Datetime.now(),
            'invoice_id': invoice_id,
            'state': 'paid',
        })
        return purchase
    
    @api.model
    def getUserPurchases(self, user_id):
        return self.search([('user_id','=',user_id)]).read()



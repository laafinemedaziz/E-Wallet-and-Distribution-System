import logging
import base64
from odoo import models, fields, api
from odoo import SUPERUSER_ID
from odoo.exceptions import ValidationError
from odoo.exceptions import AccessDenied, UserError


_logger = logging.getLogger(__name__)

"""
* This module is responsible for managing the products of the application.
* A product is essentially defined by a name, a default code, and a type while we add a price in LC.
"""
class ClevoryProduct (models.Model):
    _inherit = 'product.template'
    price_lc = fields.Float("Price in LC")
    category = fields.Char("Course Category") 


    @api.model
    def createNewProduct(self,product_data):
        product = self.create({
            'name': product_data.get('name'),
            'type': 'service',          
            'description_sale': product_data.get('description'), 
            'list_price': product_data.get('price_lc'), 
            'price_lc': product_data.get('price_lc'),
            'category': product_data.get('category'),
        })
        return product.read(['id','name','default_code'])
    
    @api.model
    def getAllProducts(self,user):
        templates = self.search([('name','!=','Learning Coin')])
        products = []
        for record in templates:
            product = self.env['product.product'].search([('product_tmpl_id','=',record.id)],limit=1)
            is_purchased = True if self.env['course.purchase'].search([('product_id','=',product.id),('user_id','=',user.id)],limit=1) else False
            products.append({
                'id':product.id,
                'name':record.name,
                'default_code':record.default_code,
                'description':record.description_sale,
                'type':record.type,
                'price_lc':record.price_lc,
                'date':str(record.write_date),
                'is_purchased':is_purchased,
                'category':record.category,
                'image':product.image_1920.decode() if product.image_1920 else None
            })
        return products



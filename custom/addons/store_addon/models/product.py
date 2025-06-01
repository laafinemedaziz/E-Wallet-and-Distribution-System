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

    # Images are stored as base64 encoded strings
    @api.model
    def createNewProduct(self,product_data):
        product_data['image'] = product_data.get('image').split(",", 1)[1]
        product = self.create({
            'name': product_data.get('name'),
            'type': 'service',          
            'description_sale': product_data.get('description'), 
            'list_price': product_data.get('price_lc'), 
            'price_lc': product_data.get('price_lc'),
            'category': product_data.get('category'),
        })
        product_variant = self.env['product.product'].search([('product_tmpl_id','=',product.id)],limit=1)
        product_variant.write({
            'image_variant_1920': product_data.get('image') if product_data.get('image') else None
        })
        return product.read(['id','name','default_code'])
    
    @api.model
    def getAllProducts(self,user):
        templates = self.search([('name','!=','Learning Coin')])
        active_products = []
        inactive_products = []
        for record in templates:
            product = self.env['product.product'].with_context(active_test=False).search([('product_tmpl_id','=',record.id)],limit=1)
            is_purchased = True if self.env['course.purchase'].search([('product_id','=',product.id),('user_id','=',user.id)],limit=1) else False
            product_obj = {
                'id':product.id,
                'name':record.name,
                'default_code':record.default_code,
                'description':record.description_sale,
                'type':record.type,
                'price_lc':record.price_lc,
                'date':str(record.write_date),
                'is_purchased':is_purchased,
                'category':record.category,
                'image':product.image_1920.decode() if product.image_1920 else None,
                'active':product.active
            }
            if product.active:
                _logger.info(f"Product {record.name} is active")
                active_products.append(product_obj)
            else:
                _logger.info(f"Product {record.name} is inactive")
                inactive_products.append(product_obj)
        if user.type == 'admin':
            return active_products + inactive_products
        else:
            return active_products
        

    @api.model
    def updateProductById(self, user, product_id, product_data):
        if not user or user.type != 'admin':
            raise AccessDenied("You do not have permission to edit products.")
        
        #product.product
        product = self.env['product.product'].with_context(active_test=False).browse(product_id)
        if not product:
            raise UserError("Product not found")
        
        #product.template
        product_template = self.browse(product.product_tmpl_id.id)

        if 'image' in product_data:
            product_data['image'] = product_data.get('image').split(",", 1)[1]
        
        product_template.write({
            'name': product_data.get('name', product_template.name),
            'description_sale': product_data.get('description', product_template.description),
            'list_price': product_data.get('price_lc', product_template.list_price),
            'price_lc': product_data.get('price_lc', product_template.price_lc),
            'category': product_data.get('category', product_template.category),
        })
        
        # Update the image for the variant
        if 'image' in product_data:
            product.write({
                'image_variant_1920': product_data['image'] if product_data['image'] else None
            })
        
        return {
            'id': product.id,
            'name': product_template.name
        }
    
    @api.model
    def activateDeactivateProduct(self, id):

        product = self.env['product.product'].with_context(active_test = False).browse(id)
        
        if not product:
            raise ValidationError("Product with given id does not exist.")
        
        product.write({
            'active' : not product.active,
        })

        return ({
            'product': product.product_tmpl_id.name,
            'active' : product.active
        })




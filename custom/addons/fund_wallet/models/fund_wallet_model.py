import logging
import secrets
from odoo import models, fields, api
from odoo.exceptions import ValidationError
from odoo.exceptions import AccessDenied, UserError
from odoo import SUPERUSER_ID
import requests
import logging


_logger = logging.getLogger(__name__)

"""
---------------------------------Add Comment------------------------------
"""
class FundWallet (models.Model):
    _inherit = 'account.move'

    @api.model
    def createInvoice(self,lc_quantity,user):
        Currency = self.env.ref('base.TND')
        LC = self.env.ref('fund_wallet.learning_coin_product')
        if not Currency :
            raise ValidationError("There was an error :Currency.")
        if not LC :
            raise ValidationError("There was an error :LC.")

        """ if not Currency or LC :
            raise ValidationError("There was an error fulfilling your request.") """
        invoice_metadata = {
            'partner_id':user.partner_id.id,
            'move_type':"out_invoice",
            'currency_id':Currency.id
        }

        invoice = self.with_user(SUPERUSER_ID).create(invoice_metadata)

        if not invoice:
            raise ValidationError("Invoice creation failed.")
        else:
            invoice_line= self._createInvoiceLine(LC,lc_quantity,invoice,user)
            invoice.action_post()

        return {'response':f"Invoice Was successfully created under id: {invoice.id}",
                                    'invoice_id':invoice.id,
                                    'user':user.login,
                                    'LC_quantity':invoice_line.quantity,
                                    'price':invoice.amount_total_signed,
                                    'currency':invoice.currency_id.name}


    def _createInvoiceLine(self,LC,lc_quantity,invoice,user):
        return self.env['account.move.line'].with_user(SUPERUSER_ID).create({
            'move_id':invoice.id,
            'product_id':LC.id,
            'quantity':lc_quantity,
            'price_unit':1
        })
    
    @api.model
    def paypalCreateOrder(self,invoice_id):
        
        access_token = self._getAccessToken().get('access_token')

        HEADERS = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {access_token}'
        }
        URL = 'https://api-m.sandbox.paypal.com/v2/checkout/orders'
        """ DATA = {
            "intent": "CAPTURE", 
            "payment_source": { "paypal": { 
                                            "experience_context": { 
                                                                    "payment_method_preference": "IMMEDIATE_PAYMENT_REQUIRED",
                                                                    "landing_page": "LOGIN", 
                                                                    "shipping_preference": "NO_SHIPPING", 
                                                                    "user_action": "PAY_NOW", 
                                                                    "return_url": "http://localhost:3000/", 
                                                                    "cancel_url": "http://localhost:3000/" } } },
            "purchase_units":[
                {
                    "invoice_id":"INV_XXXXX","amount": { "currency_code": "USD",
                                                        "value": "2000", 
                                                        "breakdown": { 
                                                            "item_total": { 
                                                                "currency_code": "USD", 
                                                                "value": "2000" }, 
                                                                },
                                                                "items": [ { "name": "Learning Coins", "description": "Learning Coins", 
                                                                            "unit_amount": { "currency_code": "USD", 
                                                                            "value": "2000" }, 
                                                                            "quantity": "2000", 
                                                                            "category": "DIGITAL_GOOD", 
                                                                            "sku": "sku01", 
                                                                            "url": "https://example.com/url-to-the-item-being-purchased-1", 
                                                                            "upc": { "type": "UPC-A", 
                                                                                    "code": "123456789012" } }] }
                }
            ]
        } """
        invoice = self.search([('id','=',invoice_id)])
        DATA = self._orederRequestFormatter(invoice)
        order_response = requests.post(URL,json=DATA,headers=HEADERS)
        order_data = order_response.json()
        
        return order_data

    @api.model
    def _getAccessToken(self):
        CLIENT_ID = ""
        CLIENT_SECRET = ""
        URL = "https://api-m.sandbox.paypal.com/v1/oauth2/token"
        HEADERS = {'Content-Type': "application/x-www-form-urlencoded"}
        DATA = {'grant_type':"client_credentials"}
        request_token_res = requests.post(URL, auth=(CLIENT_ID,CLIENT_SECRET), data=DATA, headers=HEADERS)
        request_token_data = request_token_res.json()
        return request_token_data
    
    @api.model
    def capturePaymentPaypal(self,order_id):
        access_token = self._getAccessToken().get('access_token')
        URL = f"https://api-m.sandbox.paypal.com/v2/checkout/orders/{order_id}/capture"
        HEADERS = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {access_token}',
        }
        DATA = '{}'
        response = requests.post(URL,headers=HEADERS,data=DATA)
        response_data = response.json()
        return response_data
    
    @api.model
    def _orederRequestFormatter(self,invoice):
        DATA = {
            "intent": "CAPTURE", 
            "payment_source": { "paypal": { 
                                            "experience_context": { 
                                                                    "payment_method_preference": "IMMEDIATE_PAYMENT_REQUIRED",
                                                                    "landing_page": "LOGIN", 
                                                                    "shipping_preference": "NO_SHIPPING", 
                                                                    "user_action": "PAY_NOW", 
                                                                    "return_url": "http://localhost:3000/", 
                                                                    "cancel_url": "http://localhost:3000/" } } },
            "purchase_units":[
                {
                    "invoice_id":f"{invoice.id}","amount": { "currency_code": "USD",
                                                        "value": f"{invoice.amount_total_signed}", 
                                                        "breakdown": { 
                                                            "item_total": { 
                                                                "currency_code": "USD", 
                                                                "value": f"{invoice.line_ids[0].price_total}"}, 
                                                                },
                                                                #This will be a function that will iterate over line_ids an generate items accordingly
                                                                "items": [ { "name": f"{invoice.name}", "description": f"{invoice.name}", 
                                                                            "unit_amount": { "currency_code": "USD", 
                                                                            "value": f"{invoice.amount_total_signed}" }, 
                                                                            "quantity": f"{invoice.amount_total_signed}", 
                                                                            "category": "DIGITAL_GOOD", 
                                                                            "sku": "sku01", 
                                                                            "url": "", 
                                                                            "upc": { "type": "", 
                                                                                    "code": "" } }] }
                }
            ]
        }
        return DATA


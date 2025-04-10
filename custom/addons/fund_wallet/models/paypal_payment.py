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
class PaypalPay (models.Model):
    _inherit = 'account.payment'

    #front for testing Paypal Integration path: C:\Users\laafi\Downloads\standard_html_javascript\standard\client\html
    @api.model
    def paypalCreateOrder(self,invoice_id):
        #Get an access token to fetch API endpoints
        access_token = self._getAccessToken().get('access_token')

        #Forming the order request
        HEADERS = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {access_token}'
        }

        URL = 'https://api-m.sandbox.paypal.com/v2/checkout/orders'
        
        invoice = self.env['account.move'].search([('id','=',invoice_id)])
        DATA = self._orederRequestFormatter(invoice)
        order_response = requests.post(URL,json=DATA,headers=HEADERS)
        order_data = order_response.json()
        return order_data
        
    @api.model
    def _getAccessToken(self):
        CLIENT_ID = "AdkAgKhLGFuGf9K3hiBKvdat45f4wBbUuJU7Zm26Sx_C4PsrjMtzNrSCw4HWaJS-w2oHwlGLmWcLpRIn"
        CLIENT_SECRET = "EN974vtoRE7FMBMGnD3bjM1_UxsXjG9TJx48wM_dgSTlYYF-dLTWyNHww5INrgo853L-SjWwhnPXrFUF"
        URL = "https://api-m.sandbox.paypal.com/v1/oauth2/token"
        HEADERS = {'Content-Type': "application/x-www-form-urlencoded"}
        DATA = {'grant_type':"client_credentials"}
        request_token_res = requests.post(URL, auth=(CLIENT_ID,CLIENT_SECRET), data=DATA, headers=HEADERS)
        request_token_data = request_token_res.json()
        return request_token_data
    
    @api.model
    def capturePaymentPaypal(self,order_id):
        #Get an access token to fetch API endpoints
        access_token = self._getAccessToken().get('access_token')
        URL = f"https://api-m.sandbox.paypal.com/v2/checkout/orders/{order_id}/capture"
        HEADERS = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {access_token}',
        }
        DATA = '{}'
        response = requests.post(URL,headers=HEADERS,data=DATA)
        payment_data = response.json()
        if payment_data.get('status') != "COMPLETED":
            raise ValidationError('ERROR: Payment is not completed')
        
        record_payment,invoice = self.createPaymentRecord(payment_data)
        if not record_payment:
            raise ValidationError("ERROR: Payment was not recorded.")
        if  invoice.payment_state != "paid":
            raise ValidationError("ERROR: invoice was not paid")
        
        fund_wallet = self.env['res.ewallet'].with_user(SUPERUSER_ID).fundWallet(invoice)

        if not fund_wallet:
            raise ValidationError("ERROR: coins were not added to wallet.")


        
        return payment_data
    
    @api.model
    def _orederRequestFormatter(self,invoice):

        #Generate order items
        lines = []
        for line in invoice.line_ids:
            lines.append({  "name": f"{line.product_id.name}", 
                            "description": f"{line.product_id.name}", 
                            "unit_amount": { "currency_code": "USD", 
                            "value": f"{line.price_total}" }, 
                            "quantity": f"{line.quantity}", 
                            "category": "DIGITAL_GOOD", 
                            "sku": "sku01", 
                            "url": "", 
                            "upc": { "type": "", 
                                "code": "" } 
            })
        #Form the request body
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
                                                                "items": lines }
                }
            ]
        }
        return DATA
    
    @api.model
    def createPaymentRecord(self,paymentData):
        invoice_id = paymentData.get('purchase_units')[0].get('payments', {}).get('captures', [])[0].get('invoice_id')
        invoice = self.env['account.move'].with_user(SUPERUSER_ID).search([('id','=',invoice_id)])
        if not invoice :
            raise ValidationError("ERROR 404: Invoice not found.")
        
        payment_date = paymentData.get('purchase_units')[0].get('payments').get('captures')[0].get('create_time')
        amount_paid = paymentData.get('purchase_units')[0].get('payments').get('captures')[0].get('amount').get('value') 
        Currency = self.env.ref('base.TND')
        payment_record = self.with_user(SUPERUSER_ID).create({
            'journal_id':13,
            'payment_method_id':1,
            #'payment_method_line_id':"",
            'amount':amount_paid,
            'partner_id':invoice.partner_id.id,
            'memo':invoice.name,
            'partner_type':'customer',
            'payment_type':'inbound',
            'invoice_ids': [(6, 0, [invoice.id])],


        })
        if not payment_record:
            raise ValidationError("Something went wrong: payment not recorded.")
        
        payment_record.action_validate()

        #Reconcile payment and invoice
        self._reconcilePaymentInvoice(payment_record,invoice)
        self.env.cr.commit()
        return True,invoice
    
    @api.model
    def _reconcilePaymentInvoice(self,payment,invoice):
        (payment.move_id.line_ids + invoice.line_ids)\
        .filtered(lambda l: l.account_id.account_type == 'asset_receivable' and not l.reconciled)\
        .reconcile()
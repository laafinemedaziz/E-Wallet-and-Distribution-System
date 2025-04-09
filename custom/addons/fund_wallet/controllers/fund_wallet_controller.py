import json
from odoo import http
from odoo.http import request, Response
from odoo.exceptions import ValidationError
from odoo.exceptions import AccessDenied, UserError
from odoo import SUPERUSER_ID
import requests

class FundWalletController(http.Controller):

    @http.route('/fund_wallet/request_invoice', type='http', auth='user', methods=['GET'], csrf=False)
    def createInvoice(self):
        user = request.env.user
        lc_quantity= request.params.get('quantity')
        if not lc_quantity:
            raise ValidationError("Error: Missing parameter 'quantity'")
        else:
            response = request.env['account.move'].with_user(user.id).createInvoice(lc_quantity,user)
            return(Response(json.dumps(response),content_type='application/json'))
        

    @http.route('/fund_wallet/<string:invoice_id>/pay_invoice', type='http', auth='none', method=['POST'], csrf=False, cors="*")
    def payInvoice(self,invoice_id):
        #user = request.env.user
        #quantity = request.params.get('quantity')
        data = {
            ""
        }
        order_data = request.env['account.payment'].with_user(SUPERUSER_ID).paypalCreateOrder(invoice_id)

        return (Response(json.dumps(order_data),content_type='application/json'))
    
    @http.route('/api/orders/<string:orderID>/capture', type='http', auth='none', method=['POST'], csrf=False, cors="*")
    def  capturePaymentPaypal(self,orderID):
        payment_capture = request.env['account.payment'].with_user(SUPERUSER_ID).capturePaymentPaypal(orderID)
        return (Response(json.dumps(payment_capture),content_type='application/json'))

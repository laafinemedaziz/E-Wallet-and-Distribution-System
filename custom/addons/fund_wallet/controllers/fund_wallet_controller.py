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
        

    @http.route('/fund_wallet/pay_invoice', type='http', auth='user', method=['GET'], csrf=False)
    def payInvoice(self):
        user = request.env.user
        #quantity = request.params.get('quantity')
        data = {
            ""
        }
        access_token = request.env['account.move'].with_user(SUPERUSER_ID)._getPaypalAccessToken()

        return (Response(json.dumps(access_token),content_type='application/json'))
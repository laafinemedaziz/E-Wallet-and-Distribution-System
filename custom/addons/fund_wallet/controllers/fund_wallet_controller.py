import json
from odoo import http
from odoo.http import request, Response
from odoo.exceptions import ValidationError
from odoo.exceptions import AccessDenied, UserError


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
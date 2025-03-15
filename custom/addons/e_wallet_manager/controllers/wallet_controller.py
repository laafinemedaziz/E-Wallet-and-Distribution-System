import json
from odoo import http
from odoo.http import request, Response
from odoo.exceptions import ValidationError

class WalletController(http.Controller):

    @http.route('/api/getWallet', type='http', auth='user', methods=['GET'], csrf=False)
    def getWallet(self):
        user = request.env.user
        wallet = request.env['res.ewallet'].with_user(user.id).getWallet(user)
        return (Response(json.dumps(wallet),content_type='application/json'))
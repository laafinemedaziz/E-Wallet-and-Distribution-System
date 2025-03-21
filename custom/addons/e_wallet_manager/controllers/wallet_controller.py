import json
from odoo import http
from odoo.http import request, Response
from odoo.exceptions import ValidationError
from odoo.exceptions import AccessDenied, UserError

class WalletController(http.Controller):

    @http.route('/api/getWallet', type='http', auth='user', methods=['GET'], csrf=False)
    def getWallet(self):
        user = request.env.user
        wallet = request.env['res.ewallet'].with_user(user.id).getWallet(user)
        return (Response(json.dumps(wallet),content_type='application/json'))
    
    @http.route('/api/getEmpsWallet', type='http', auth='user', methods=['GET'], csrf=False)
    def getEmpsWallets(self):
        user = request.env.user
        if user.type != 'hr':
            raise AccessDenied(f"Prohibited action for user type: {user.type}")
        else:
            wallets = request.env['res.ewallet'].with_user(user.id).getEmpsWallets(user)
            return (Response(json.dumps(wallets),content_type='application/json'))
        
    @http.route('/api/sendCredit', type='http', auth='user', methods=['GET'], csrf=False)
    def sendCredit(self):
        sender = request.env.user
        receiver_wallet_id = request.params.get('receiver_wallet_id')
        amount = float(request.params.get('amount'))
        response = request.env['res.ewallet'].with_user(sender.id).transferCredit(sender,receiver_wallet_id,amount)
        return(Response(json.dumps(response),content_type='application/json'))

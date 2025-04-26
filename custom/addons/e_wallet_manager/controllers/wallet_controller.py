import json
from odoo import http
from odoo.http import request, Response
from odoo.exceptions import ValidationError
from odoo.exceptions import AccessDenied, UserError
from odoo import SUPERUSER_ID

class WalletController(http.Controller):

    @http.route('/api/getWallet', type='http', auth='user', methods=['GET'], csrf=False)
    def getWallet(self):
        user = request.env.user
        wallet = request.env['res.ewallet'].with_user(user.id).getWallet(user)
        return (Response(json.dumps(wallet),content_type='application/json'))
    
    @http.route('/api/getEmpsWallet', type='http', auth='user', methods=['GET'], csrf=False)
    def getEmpsWallets(self):
        user = request.env.user
        if not user.has_group('clevory_user.hr_group_manager'):
            raise AccessDenied(f"Prohibited action for user type: {user.type}")
        else:
            wallets = request.env['res.ewallet'].with_user(SUPERUSER_ID).getEmpsWallets(user)
            return (Response(json.dumps(wallets),content_type='application/json'))
    
    @http.route('/api/getTransactions', type='http', auth='user', methods=['GET'], csrf=False)
    def getTransactions(self):
        user = request.env.user
        transactions = request.env['res.transactions'].with_user(SUPERUSER_ID).getTransactions(user)
        return (Response(json.dumps(transactions),content_type='application/json'))
        
    @http.route('/api/sendCredit', type='http', auth='user', methods=['POST'], csrf=False)
    def sendCredit(self):
        sender = request.env.user
        data = json.loads(request.httprequest.data)
        if not sender.has_group('clevory_user.hr_group_manager'):
            raise AccessDenied(f"Prohibited action for user type: {sender.type}")
        else:
            receiver_wallet_id = data.get('recipientWalletId')
            amount = float(data.get('amount'))
            response = request.env['res.ewallet'].with_user(SUPERUSER_ID).transferCredit(sender,receiver_wallet_id,amount)
            return(Response(json.dumps(response),content_type='application/json'))

    @http.route('/api/getTransfers', type='http', auth='user', methods=['GET'], csrf=False)
    def getLatestTransfer(self):
        user = request.env.user
        transactions = request.env['res.transactions'].with_user(SUPERUSER_ID).getTransfers(user)
        return (Response(json.dumps(transactions),content_type='application/json'))
    
    @http.route('/transactions/export', type='http', auth='user', methods=['GET'])
    def export_transactions(self, **kwargs):
        type = request.params.get("type")
        user = request.env.user
        content = None
        headers = None
        if type == "csv":
            content = request.env['res.transactions'].with_user(SUPERUSER_ID).getCSVReport(user)
            headers = [
                    ('Content-Type', 'text/csv'),
                    ('Content-Disposition', 'attachment; filename="transactions.csv"')
                ]
            
        elif type == "pdf":
            content = request.env['res.transactions'].with_user(SUPERUSER_ID).getPDFReport(user)
            headers=[
                    ('Content-Type', 'application/pdf'),
                    ('Content-Disposition', 'attachment; filename="transactions.pdf"')
                ]
        else:
            return Response("Error: File type not supported.", status=404, content_type='text/plain')

        return (Response(content,headers=headers))
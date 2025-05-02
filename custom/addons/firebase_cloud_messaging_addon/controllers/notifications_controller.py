import json
from odoo import http
from odoo.http import request, Response
from odoo.exceptions import ValidationError
from odoo.exceptions import AccessDenied, UserError
from odoo import SUPERUSER_ID

class WalletController(http.Controller):

    @http.route('/api/addDeviceToken', type='http', auth='user', methods=['GET'], csrf=False)
    def addDeviceToken(self):
        user = request.env.user
        token = request.params.get('DeviceToken')
        request.env['firebase.device.token'].with_user(SUPERUSER_ID).addDeviceToken(user,token)
        return(Response(json.dumps({
            'message':f"user token for user {user.name} is added!"
        }),content_type='application/json'))
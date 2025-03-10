import json
from odoo import http
from odoo.http import request, Response
from odoo.exceptions import ValidationError

class OauthController(http.Controller):

    @http.route('/api/googleAuth', type='http', auth='none', methods=['GET'], csrf=False)
    def google_auth(self):
        code = request.params.get('code')
        authenticate = request.env['res.users'].sudo().authenticate_with_google(code)
        return Response(json.dumps(authenticate),content_type='json')
import json
from odoo import http
from odoo.http import request, Response
from odoo.exceptions import ValidationError

class OauthController(http.Controller):

    @http.route('/api/googleAuth', type='http', auth='none', methods=['GET'], csrf=False)
    def google_auth(self):
        
        code = request.params.get('code')
        credentials = request.env['res.users'].sudo().authenticate_with_google(code)
        request.env.cr.commit()
        db = request.db
        auth_infos = request.session.authenticate(db,credentials)
        return Response(json.dumps(auth_infos),content_type='json')
    

        #return Response(json.dumps(credentials),content_type='json') 
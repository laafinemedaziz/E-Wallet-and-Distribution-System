import json
from odoo import http
from odoo.http import request, Response
from odoo.exceptions import ValidationError
class RegisterControler(http.Controller):

    @http.route('/api/sign_up_user', type='json', auth='none', methods=['POST'], csrf=False)
    def sign_up_user(self):
        vals = request.httprequest.get_json()
        print (vals)
        return request.env['res.users'].sudo().sign_up_user(vals)

    """
    #This endpoint would only be available for the admin (to develop later with other company CRUD operations)
    @http.route('/api/add_company', type='json',auth='none', methods=['POST'], csrf=False)
    def add_company(self):
        vals = request.httprequest.get_json()
        print(vals)
        company = request.env['res.partner'].sudo().add_new_company(vals)
        return company.id """ 
    
    @http.route('/api/confirm_user', type='http', auth='none', methods=['GET'], csrf=False)
    def verify_user(self):
        token = request.params.get('token')
        if not token:
            raise ValidationError("No Valid Token Found")
        else:
            response = request.env['res.users'].sudo()._validate_user(token)
            return Response(json.dumps(response),content_type='json') 

import json
from odoo import http
from odoo.http import request, Response
from odoo.exceptions import ValidationError
class RegisterControler(http.Controller):

    @http.route('/api/sign_up_user', type='json', auth='none', methods=['POST'], csrf=False)
    def sign_up_user(self):
        vals = request.httprequest.get_json()
        print (vals)
        user = request.env['res.users'].sudo().sign_up_user(vals)
        return Response(json.dumps(user),content_type='application/json') 


    #This endpoint would only be available for the admin (to develop later with other company CRUD operations)
    @http.route('/api/add_company', type='json',auth='none', methods=['POST'], csrf=False)
    def add_company(self):
        vals = request.httprequest.get_json()
        print(vals)
        company = request.env['res.partner'].sudo().add_new_company(vals)
        return Response(json.dumps(company),content_type='application/json')
    
    @http.route('/api/confirm_user', type='http', auth='none', methods=['GET'], csrf=False)
    def verify_user(self):
        token = request.params.get('token')
        if not token:
            raise ValidationError("No Valid Token Found")
        else:
            response = request.env['res.users'].sudo()._validate_user(token)
            return Response(json.dumps(response),content_type='application/json') 
        
    @http.route('/api/request_passwordReset', type='http', auth='none', methods=['POST'], csrf=False)
    def requestPasswordReset(self):
        
        email = request.httprequest.get_json().get('email')
        check = request.env['res.users'].sudo()._sendpasswordResetEmail(email)
        return Response(json.dumps(check),content_type='application/json')
    
    @http.route('/api/validateResetToken', type='http', auth='none', methods=['GET'], csrf=False)
    def validateResetToken(self):
        token = request.params.get('token')
        validate = request.env['res.users'].sudo().validateResetToken(token)
        return Response(json.dumps(validate),content_type='application/json') 
    
    @http.route('/api/reset_password', type='http', auth='none', methods=['POST'], csrf=False)
    def resetPassword(self):
        vals = request.httprequest.get_json()
        reset = request.env['res.users'].sudo().resetPassword(vals.get('token'),vals.get('newPassword'))
        return Response(json.dumps(reset),content_type='application/json')

import json
from odoo import http
from odoo.http import request, Response
from odoo.exceptions import ValidationError
from odoo import SUPERUSER_ID
import logging


_logger = logging.getLogger(__name__)

class RegisterControler(http.Controller):

    def handleCORSPreflight(self):
        headers = [
                ('Access-Control-Allow-Origin', '*'),
                ('Access-Control-Allow-Methods', 'GET, POST, OPTIONS'),
                ('Access-Control-Allow-Headers', 'Content-Type'),
            ]
        return Response('', status=200, headers=headers)
    
    @http.route('/api/sign_up_user', type='http', auth='none', methods=['POST', 'OPTIONS'], csrf=False)
    def sign_up_user(self):
        
        if request.httprequest.method == 'OPTIONS':
            return self.handleCORSPreflight()

        try:
            data = json.loads(request.httprequest.data)
            print(data)

            user = request.env['res.users'].sudo().sign_up_user(data)

            headers = [
                ('Access-Control-Allow-Origin', '*'),
                ('Content-Type', 'application/json')
            ]
            return Response(json.dumps(user), headers=headers, status=200)

        except Exception as error:
            return Response(json.dumps({'error':str(error)}), status=500, content_type='application/json')




    #This endpoint would only be available for the admin (to develop later with other company CRUD operations)
    @http.route('/api/add_company', type='http',auth='none', methods=['POST'], csrf=False)
    def add_company(self):
        data = json.loads(request.httprequest.data)
        print(data)
        company = request.env['res.partner'].sudo().add_new_company(data)
        return Response(json.dumps(company),content_type='application/json')
    
    @http.route('/api/confirm_user', type='http', auth='none', methods=['GET'], csrf=False)
    def verify_user(self):
        try:
            token = request.params.get('token')
            if not token:
                raise ValidationError("No Valid Token Found")
            else:
                response = request.env['res.users'].sudo()._validate_user(token)
                return Response(json.dumps(response),content_type='application/json') 
        except Exception as error:
            return Response(json.dumps({'error':str(error)}), status=500, content_type='application/json')
        
    @http.route('/api/request_passwordReset', type='http', auth='none', methods=['POST'], csrf=False)
    def requestPasswordReset(self):
        
        email = request.httprequest.get_json().get('email')
        check = request.env['res.users'].sudo()._sendpasswordResetEmail(email)
        return Response(json.dumps(check),content_type='application/json')
    
    @http.route('/api/validateResetToken', type='http', auth='none', methods=['POST'], csrf=False)
    def validateResetToken(self):
        token = request.httprequest.get_json().get('token')
        validate = request.env['res.users'].sudo().validateResetToken(token)
        return Response(json.dumps(validate),content_type='application/json') 
    
    @http.route('/api/reset_password', type='http', auth='none', methods=['POST'], csrf=False)
    def resetPassword(self):
        vals = request.httprequest.get_json()
        reset = request.env['res.users'].sudo().resetPassword(vals.get('token'),vals.get('newPassword'))
        return Response(json.dumps(reset),content_type='application/json')
    
    @http.route('/api/getCompanyCode', type='http', auth='user', methods=['GET'], csrf=False)
    def getCompanyCode(self):
        user = request.env.user
        if not user.has_group('clevory_user.hr_group_manager'):
            raise ValidationError("Unauthorized")
        
        company = user.company_ref
        if not company :
            raise ValidationError("User has no company attached.")
        
        return Response(json.dumps(company.with_user(SUPERUSER_ID).read(['name','company_code'])),content_type='application/json')

    @http.route('/api/changeUserInfos', type='http', auth='user', methods=['POST'], csrf=False)
    def changeUserInfos(self):
        try:
            data = request.httprequest.get_json()
            _logger.info(f"Data received: {data}")
            user = request.env.user
            if not user:
                raise ValidationError("No User Found")
            else:
                request.env['res.users'].with_user(SUPERUSER_ID).changeUserInfos(user,data)
                return Response(json.dumps({'message':'User updated successfully'}),content_type='application/json')
        except Exception as error:
            return Response(json.dumps({'error':str(error)}), status=500, content_type='application/json')

        

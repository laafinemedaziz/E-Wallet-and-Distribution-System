import json
from odoo import http
from odoo.http import request, Response
from odoo.exceptions import ValidationError
from odoo import SUPERUSER_ID
import logging


_logger = logging.getLogger(__name__)

class RegisterControler(http.Controller):
    
    @http.route('/api/sign_up_user', type='http', auth='none', methods=['POST'], csrf=False, cors='*')
    def sign_up_user(self):
        
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

    
    @http.route('/api/confirm_user', type='http', auth='none', methods=['GET'], csrf=False, cors='*')
    def verify_user(self):
        try:
            token = request.params.get('token')
            if not token:
                raise ValidationError("No Valid Token Found")
            else:
                response = request.env['res.users'].with_user(SUPERUSER_ID)._validate_user(token)
                return Response(json.dumps(response),content_type='application/json') 
        except Exception as error:
            return Response(json.dumps({'error':str(error)}), status=500, content_type='application/json')
        
    @http.route('/api/request_passwordReset', type='http', auth='none', methods=['POST'], csrf=False, cors='*')
    def requestPasswordReset(self):
        
        email = request.httprequest.get_json().get('email')
        check = request.env['res.users'].sudo()._sendpasswordResetEmail(email)
        return Response(json.dumps(check),content_type='application/json')
    
    @http.route('/api/validateResetToken', type='http', auth='none', methods=['POST'], csrf=False ,cors='*')
    def validateResetToken(self):
        token = request.httprequest.get_json().get('token')
        validate = request.env['res.users'].sudo().validateResetToken(token)
        return Response(json.dumps(validate),content_type='application/json') 
    
    @http.route('/api/reset_password', type='http', auth='none', methods=['POST'], csrf=False, cors='*')
    def resetPassword(self):
        vals = request.httprequest.get_json()
        reset = request.env['res.users'].sudo().resetPassword(vals.get('token'),vals.get('newPassword'))
        return Response(json.dumps(reset),content_type='application/json')
    
    @http.route('/api/getCompanyCode', type='http', auth='user', methods=['GET'], csrf=False, cors='*')
    def getCompanyCode(self):
        user = request.env.user
        if not user.has_group('clevory_user.hr_group_manager'):
            raise ValidationError("Unauthorized")
        
        company = user.company_ref
        if not company :
            raise ValidationError("User has no company attached.")
        
        return Response(json.dumps(company.with_user(SUPERUSER_ID).read(['name','company_code'])),content_type='application/json')

    @http.route('/api/changeUserInfos', type='http', auth='user', methods=['POST'], csrf=False, cors='*')
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

    @http.route('/api/getAllUsers', type='http', auth='user', methods=['GET'], csrf=False, cors='*')
    def getAllUsers(self):
        try:
            user = request.env.user
            if not user.type == 'admin':
                _logger.info(f"User {user.name} is not an admin.")
                raise ValidationError("Unauthorized")
            else:
                _logger.info(f"User {user.name} is an admin.")
                users = request.env['res.users'].with_user(SUPERUSER_ID).getAllUsers()
                return Response(json.dumps(users),content_type='application/json')
        except Exception as error:
            return Response(json.dumps({'error':str(error)}), status=500, content_type='application/json')
        
    @http.route('/api/AdminActions', type='http', auth='user', methods=['POST'], csrf=False, cors='*')
    def adminActions(self):
        
        try:
            user = request.env.user
            if not user.type == 'admin':
                _logger.info(f"User {user.name} is not an admin.")
                raise ValidationError("Unauthorized")
            
            _logger.info(f"User {user.name} is an admin.")

            data = request.httprequest.get_json()
            _logger.info(f"Data received: {data}")
            action = data.get('action')
            user_id = data.get('user_id')
            if not (action and user_id):
                raise ValidationError("No Action or User ID Found")
            _logger.info(f"Action: {action}, User ID: {user_id}")
            match action:
                case 'delete':
                    response =request.env['res.users'].with_user(SUPERUSER_ID).deleteUser(user_id)
                case 'active':
                    response = request.env['res.users'].with_user(SUPERUSER_ID).activateDeactivateUser(user_id)
                case _:
                    raise ValidationError("No Action Found")
            return Response(json.dumps(response),content_type='application/json')
        except Exception as error:
            return Response(json.dumps({'error':str(error)}), status=500, content_type='application/json')

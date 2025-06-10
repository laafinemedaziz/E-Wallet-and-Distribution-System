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
                raise ValidationError("No valid token found")

            # Validate token - result can be used in HTML
            response = request.env['res.users'].with_user(SUPERUSER_ID)._validate_user(token)
        
            # HTML success response
            html_success = """
            <!DOCTYPE html>
            <html>
            <head>
                <title>Account Confirmed</title>
                <style>
                    body { 
                        font-family: Arial, sans-serif; 
                        text-align: center; 
                        padding: 50px; 
                        background-color: #f8f9fa;
                    }
                    .container {
                        max-width: 600px;
                        margin: 0 auto;
                    }
                    .success-icon {
                        color: #28a745;
                        font-size: 72px;
                    }
                    h1 {
                        color: #28a745;
                    }
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="success-icon">Validated!</div>
                    <h1>Account Confirmed!</h1>
                    <p>Your email address has been successfully verified.</p>
                    <p>You can now close this window and use your account.</p>
                </div>
            </body>
            </html>
            """
            return Response(html_success, content_type='text/html')

        except Exception as error:
            # HTML error response
            html_error = """
            <!DOCTYPE html>
            <html>
            <head>
                <title>Verification Error</title>
                <style>
                    body { 
                        font-family: Arial, sans-serif; 
                        text-align: center; 
                        padding: 50px; 
                        background-color: #f8f9fa;
                    }
                    .container {{
                        max-width: 600px;
                        margin: 0 auto;
                    }}
                    .error-icon {{
                        color: #dc3545;
                        font-size: 72px;
                    }}
                    h1 {{
                        color: #dc3545;
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="error-icon">Error!</div>
                    <h1>Verification Failed</h1>
                    <p>Please contact support for assistance.</p>
                </div>
            </body>
            </html>
            """
            return Response(html_error, status=500, content_type='text/html')
        
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


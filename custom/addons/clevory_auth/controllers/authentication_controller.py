import json
import logging
import operator

from werkzeug.urls import url_encode
from odoo.addons.web.controllers.session import Session
import odoo
import odoo.modules.registry
from odoo import http
from odoo.modules import module
from odoo.exceptions import AccessError, ValidationError, UserError, AccessDenied
from odoo.http import request, Response
from http import HTTPStatus



_logger = logging.getLogger(__name__)

"""
* This module is responsible for basic login/password based authentication
* Loging users in by granting them a session ID and storing it in their browser cookies.
"""

class authController(Session):
    
    def handleCORSPreflight(self):
        headers = [
                ('Access-Control-Allow-Origin', 'http://localhost:4200'),
                ('Access-Control-Allow-Methods', 'GET, OPTIONS'),
                ('Access-Control-Allow-Headers', 'Content-Type'),
                ('Access-Control-Allow-Credentials','true')
            ]
        return Response('', status=204, headers=headers)
    

    @http.route('/api/web/session/authenticate', type='json', methods=['POST', 'OPTIONS'], auth="none", cors="http://localhost:4200")
    def authenticate(self):
        try:
            # Retrieving request body and validating content
            requestBody = request.httprequest.get_json()

            if 'login' not in requestBody or 'password' not in requestBody:
                raise ValidationError("Missing important credentials to authenticate")

            login = requestBody.get('login')
            password = requestBody.get('password')
            db = request.db

            # Check if user is valid (Email verification constraint)
            user = request.env['res.users'].sudo().with_context(active_test=False).search([('login', '=', login)], limit=1)

            if not user:
                raise AccessError('Invalid credentials.')
            elif user.status == 'invalid':
                raise AccessError("User is not valid.")
            if user.signup_type != "password":
                raise ValidationError("Wrong credentials")

            # Calling the Odoo's authentication method with the right parameters
            session_infos = super().authenticate(db, login, password)
            _logger.info(session_infos)
            response = {
                'message': f"User {login} authenticated successfully.",
                'user_id': session_infos.get('uid'),
                'name': session_infos.get('name'),
                'status': 'Active' if user.active else 'Inactive',
                'type': user.type
            }
            return response

        except (ValidationError, AccessError) as e:
            return Response(
                json.dumps({'error': str(e)}),
                status=HTTPStatus.UNAUTHORIZED,
                content_type='application/json'
            )
        except Exception as e:
            # Handle unexpected errors
            return Response(
                json.dumps({'error': 'Internal Server Error', 'details': str(e)}),
                status=HTTPStatus.INTERNAL_SERVER_ERROR,
                content_type='application/json'
            )
        


    #Change this to a method inside the model for better maintainability
    @http.route('/web/session/me', type='http', methods=['GET','OPTIONS'], auth="user")
    def getCurrentUserInfos(self):
        try:
            if request.httprequest.method == 'OPTIONS':
                return self.handleCORSPreflight()

            user = request.env.user
            if not user:
                raise ValidationError("Session is invalid or expiried.")
        
            headers = [
                    ('Access-Control-Allow-Origin', 'http://localhost:4200'),
                    ('Content-Type', 'application/json'),
                    ('Access-Control-Allow-Credentials','true')
                ]
            response = {
                'userID':user.id,
                'userName':user.name,
                'userType':user.type,
                'userEmail':user.email,
                'userBalance':user.ewallet_id.balance,
                'phone':user.phone,
            }
            if user.type == "hr":
                response["companyCode"] = user.company_ref.company_code
            return Response(json.dumps(response), headers=headers,status=200)
        

        except (ValidationError, AccessError) as e:
            return Response(
                json.dumps({'error': str(e)}),
                status=HTTPStatus.UNAUTHORIZED,
                content_type='application/json'
            )
        except Exception as e:
            # Handle unexpected errors
            return Response(
                json.dumps({'error': 'Internal Server Error', 'details': str(e)}),
                status=HTTPStatus.INTERNAL_SERVER_ERROR,
                content_type='application/json'
            )


    @http.route('/web/session/logout', type='http', auth="user")
    def customLogout(self):
        request.session.logout(keep_db=True)
        headers = [
                ('Access-Control-Allow-Origin', 'http://localhost:4200'),
                ('Content-Type', 'application/json'),
                ('Access-Control-Allow-Credentials','true')
            ]
        response = {
                'message': f"User Logged Out successfully."
            }
        return Response(json.dumps(response),headers=headers,status=200)
    
    
    
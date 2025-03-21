import json
import logging
import operator

from werkzeug.urls import url_encode
from odoo.addons.web.controllers.session import Session
import odoo
import odoo.modules.registry
from odoo import http
from odoo.modules import module
from odoo.exceptions import AccessError, UserError, AccessDenied
from odoo.http import request, Response
from odoo.exceptions import ValidationError



_logger = logging.getLogger(__name__)

class authController(Session):
    
    @http.route('/web/session/authenticate', type='json', auth="none")
    def authenticate(self):

        #Retrieving request body and validating content
        requestBody = request.httprequest.get_json()
        if 'login' not in requestBody or 'password' not in requestBody:
            raise ValidationError("Missing important credentials to authenticate")
        

        login = requestBody.get('login')
        password = requestBody.get('password')
        db = request.db
        #credentials = {'login':login, 'password':password, 'type':"password"}

        #Check if user is valid (Email verification constraint)
        user = request.env['res.users'].sudo().with_context(active_test=False).search([('login','=',login)],limit=1)

        
        if not user:
            raise AccessError(f'Error: Invalid credentials.')
        elif user.status == 'invalid':
            raise AccessError("Error: User is not valid.")
        if user.signup_type != "password":
            raise ValidationError("Error: Wrong credentials")
        
        #Calling the odoo's authentication method with the right parameters
        session_infos = super().authenticate(db, login, password)
        
        return {
            'message':f"User {login} authenticated successfully."
        }
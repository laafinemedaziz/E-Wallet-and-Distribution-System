import logging
from queue import Full
import secrets
from odoo import models, fields, api
from odoo import SUPERUSER_ID
from odoo.exceptions import ValidationError
import requests
import json
from odoo.exceptions import AccessDenied, UserError
from odoo.addons.auth_signup.models.res_users import SignupError
import os

_logger = logging.getLogger(__name__)

class ResUsers(models.Model):

    _inherit = 'res.users'

    @api.model
    def authenticate_with_google(self, auth_code):

        #setting up the request
        oauth_credentials_str = os.getenv("OAUTH_CREDENTIALS")
        if oauth_credentials_str:
            oauth_credentials = json.loads(oauth_credentials_str)
        else:
            raise ValueError("OAUTH_CREDENTIALS environment variable not found!")

        data = {"client_id":oauth_credentials["web"]["client_id"],
                "client_secret":oauth_credentials["web"]["client_secret"],
                "code":auth_code,
                "grant_type":"authorization_code",
                "redirect_uri":oauth_credentials["web"]["redirect_uris"][0]
                }
        #request the access token
        response = requests.post(oauth_credentials['web']['token_uri'],json=data)
        resData = response.json()
        
        db, login, access_token = self.with_user(SUPERUSER_ID).auth_oauth(3,resData)
        credentials = {'login':login, 'token':access_token, 'type':'oauth_token'}
        if not login or not access_token or not db:
            raise AccessDenied("There was a problem authenticated you.")
        else:
            return credentials
        

    @api.model
    def _auth_oauth_signin(self, provider, validation, params):
        oauth_uid = validation['user_id']
        oauth_user = self.search([("oauth_uid", "=", oauth_uid), ('oauth_provider_id', '=', provider)])
        if not oauth_user:
            values = self._generate_signup_values(provider, validation, params)
            oauth_user= self.env['res.users'].with_context(no_reset_password=True).with_user(SUPERUSER_ID).create(values)
            login = oauth_user.login
            if not login:
                raise AccessDenied("There was a problem authenticating you in.")
            else:
                return login

        else:
            oauth_user.write({'oauth_access_token': params['access_token']})
            login = oauth_user.login
            if not login:
                raise AccessDenied("There was a problem authenticating you in.")
            else:
                return login

    @api.model
    def _generate_signup_values(self, provider, validation, params):
        oauth_uid = validation['user_id']
        email = validation.get('email', 'provider_%s_user_%s' % (provider, oauth_uid))
        name = validation.get('name', email)
        return {
            'name': name,
            'login': email,
            'email': email,
            'oauth_provider_id': provider,
            'oauth_uid': oauth_uid,
            'oauth_access_token': params['access_token'],
            'active': True,
            'status':"valid",
            'type':"learner",
            'signup_type':'oauth_token'
        }
    
    
 
    
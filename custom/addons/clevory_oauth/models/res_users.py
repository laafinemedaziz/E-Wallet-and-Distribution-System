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
        response = requests.post("https://oauth2.googleapis.com/token",json=data)
        resData = response.json()
        
        #validation = self._auth_oauth_rpc("https://www.googleapis.com/oauth2/v3/userinfo",access_token)

        db, login, access_token = self.sudo().auth_oauth(3,resData)
        if not login or not access_token or not db:
            raise AccessDenied("There was a problem authenticated you.")
        else:
            return {
                "login":login,
                "response":"User with the login has been authenticated successfully!",
                "session_id":'Set to cookies.'
            }
        

    @api.model
    def _auth_oauth_signin(self, provider, validation, params):
        oauth_uid = validation['user_id']
        oauth_user = self.search([("oauth_uid", "=", oauth_uid), ('oauth_provider_id', '=', provider)])
        if not oauth_user:
            values = self._generate_signup_values(provider, validation, params)
            oauth_user= self.env['res.users'].with_context(no_reset_password=True).with_user(SUPERUSER_ID).create(values)
            authenticate = oauth_user.login
            if not authenticate:
                raise AccessDenied("There was a problem authenticating you in.")
            else:
                return authenticate

        else:
            oauth_user.write({'oauth_access_token': params['access_token']})
            authenticate = oauth_user.login
            if not authenticate:
                raise AccessDenied("There was a problem authenticating you in.")
            else:
                return authenticate

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
            'signup_type':"oauth"
        }

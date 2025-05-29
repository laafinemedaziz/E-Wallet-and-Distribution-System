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

"""
* In this module we are going to implement the Google OAuth2 authentication flow.
* For that we customized the odoo's auth.oauth built-in module.
* We added a layer for requesting the access token using an authorization code as 
  the exisitng odoo system assumes that we already have the access token.
* This module also creates a new user if they do not already exist in the database.
* Workflow:
    1. The user clicks on the Google login button in the frontend.
    2. The frontend redirects the user to the Google OAuth2 authorization page.
    3. The user grants permission to the application to access their Google account.
    4. Google redirects the user back to the application with an authorization code.
    5. The application exchanges the authorization code for an access token.
    6. The application uses the access token to retrieve the user's information from Google.
    7. The application creates a new user in the database if they do not already exist.
    8. The application logs the user in returning Credentials as a response to the front-end 
       and storing a session ID in their browser cookies (.authenticate() method the controller).
"""
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
        #request the access token from Google
        response = requests.post(oauth_credentials['web']['token_uri'],json=data)
        resData = response.json()
        if response.status_code != 200:
            raise AccessDenied("There was a problem retrieving your data from the OAuth provider.")
        else: 
            googleOauth = self.env['auth.oauth.provider'].search([('name', '=', 'Google OAuth2')], limit=1)
            db, login, access_token = self.with_user(SUPERUSER_ID).auth_oauth(googleOauth.id,resData)
            credentials = {'login':login, 'token':access_token, 'type':'oauth_token'}
            if not login or not access_token or not db:
                raise AccessDenied("There was a problem authenticated you in.")
            else:
                return credentials
        

    @api.model
    def _auth_oauth_signin(self, provider, validation, params):
        oauth_uid = validation['user_id']
        oauth_user = self.search([("oauth_uid", "=", oauth_uid), ('oauth_provider_id', '=', provider)])
        if not oauth_user:
            values = self._generate_signup_values(provider, validation, params)
            oauth_user= self.env['res.users'].with_context(no_reset_password=True).with_user(SUPERUSER_ID).create(values)
            oauth_user.createWallet()
            partner = oauth_user.partner_id
            partner._assignUserIDToPartner(oauth_user)
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
        portal_group = self.env.ref('base.group_portal')
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
            'signup_type':'oauth_token',
            'groups_id':[(6, 0, [self.assignGroup('learner').id])]
            
        }
    
    
 
    
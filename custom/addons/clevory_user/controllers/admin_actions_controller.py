import json
from odoo import http
from odoo.http import request, Response
from odoo.exceptions import ValidationError
from odoo import SUPERUSER_ID
import logging


_logger = logging.getLogger(__name__)

class adminActionsController(http.Controller):
    
    #This endpoint would only be available for the admin (to develop later with other company CRUD operations)
    @http.route('/api/add_company', type='http',auth='none', methods=['POST'], csrf=False, cors='*')
    def add_company(self):
        data = json.loads(request.httprequest.data)
        print(data)
        company = request.env['res.partner'].sudo().add_new_company(data)
        return Response(json.dumps(company),content_type='application/json')
    
    
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
        


    @http.route('/api/getAllCompanies', type='http', auth='user', methods=['GET'], csrf=False, cors='*')
    def getAllCompanies(self):
        try:
            user = request.env.user
            if not user.type == 'admin':
                _logger.info(f"User {user.name} is not an admin.")
                raise ValidationError("Unauthorized")
            else:
                _logger.info(f"User {user.name} is an admin.")
                companies = request.env['res.partner'].with_user(SUPERUSER_ID).getAllCompanies()
                return Response(json.dumps(companies),content_type='application/json')
        except Exception as error:
            return Response(json.dumps({'error':str(error)}), status=500, content_type='application/json')
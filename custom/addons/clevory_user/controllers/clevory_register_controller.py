import json
from odoo import http
from odoo.http import request
class RegisterControler(http.Controller):

    @http.route('/api/sign_up_user', type='json', auth='none', methods=['POST'], csrf=False)
    def sign_up_user(self):
        vals = request.httprequest.get_json()
        print (vals)
        return request.env['res.users'].sudo().sign_up_user(vals)

    @http.route('/api/add_company', type='json',auth='none', method=['POST'], csrf=False)
    def add_company(self):
        vals = request.httprequest.get_json()
        print(vals)
        company = request.env['res.partner'].sudo().add_new_company(vals)
        return company.id
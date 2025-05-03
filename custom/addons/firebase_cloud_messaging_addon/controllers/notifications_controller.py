import json
from odoo import http
from odoo.http import request, Response
from odoo.exceptions import ValidationError
from odoo.exceptions import AccessDenied, UserError
from odoo import SUPERUSER_ID

class WalletController(http.Controller):

    @http.route('/api/addDeviceToken', type='http', auth='user', methods=['POST'], csrf=False)
    def addDeviceToken(self):
        user = request.env.user
        token = json.loads(request.httprequest.data).get('DeviceToken')
        message = request.env['firebase.device.token'].with_user(SUPERUSER_ID).addDeviceToken(user,token)
        return(Response(json.dumps({
            'message':message
        }),content_type='application/json'))
    
    @http.route('/api/getUserNotifications', type='http', auth='user', methods=['GET'], csrf=False)
    def getUserNotifications(self):
        user = request.env.user
        notifications = request.env['res.notifications'].with_user(SUPERUSER_ID).getUserNotifications(user)
        return(Response(json.dumps(notifications),content_type='application/json'))

    @http.route('/api/countNotifications', type='http', auth='user', methods=['GET'], csrf=False)
    def countNotifications(self):
        user = request.env.user
        count = request.env['res.notifications'].with_user(SUPERUSER_ID).countUnreadNotifications(user)
        return(Response(json.dumps({
            'notifCount':count
        }),content_type='application/json'))
    
    @http.route('/api/markAllAsRead', type='http', auth='user', methods=['POST'], csrf=False)
    def markAllAsRead(self):
        user = request.env.user
        request.env['res.notifications'].with_user(SUPERUSER_ID).markAllNotificationsAsRead(user)
        return(Response(json.dumps({}),content_type='application/json',status=204))
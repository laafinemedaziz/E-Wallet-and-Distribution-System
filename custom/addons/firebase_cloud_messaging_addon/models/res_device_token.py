import os
from odoo import models, fields, api
import firebase_admin
from firebase_admin import credentials, messaging
from odoo import SUPERUSER_ID
# Initialize Firebase app
current_dir = os.path.dirname(os.path.abspath(__file__))
cred_path = os.path.abspath(os.path.join(current_dir, '..', 'static', 'credentials', 'firebase_key.json'))

if not firebase_admin._apps:
    cred = credentials.Certificate(cred_path)
    firebase_admin.initialize_app(cred)


class DeviceToken(models.Model):
    _name = 'firebase.device.token'
    _description = 'User Device Token for Push Notifications'

    user_id = fields.Many2one('res.users', required=True, ondelete='cascade')
    device_token = fields.Char(required=True, string='Device Token', unique=True)

    @api.model
    def send_notification(self, title, body, user, status='info'):
        """
        Send a push notification to a specific device token.
        """
        token = self.with_user(SUPERUSER_ID).search([('user_id','=',user.id)]).device_token
        try:
            message = messaging.Message(
                notification=messaging.Notification(
                    title=title,
                    body=body
                ),
                token=token
            )
            response = messaging.send(message)
            _logger = self.env['ir.logging']
            _logger.create({
                'name': 'FCM Notification',
                'type': 'server',
                'level': 'info',
                'message': f'Notification sent: {response}',
                'path': __file__,
                'func': 'send_notification',
                'line': 35,
            })


            #Record the notification in res.notifications
            self.env['res.notifications'].create({
                'user_id': user.id,
                'title': title,
                'body': body,
                'status': status
            })
            return {'success': True, 'response': response}
        except Exception as e:
            return {'success': False, 'error': str(e)}
        


    @api.model
    def addDeviceToken(self, user, token):
        if not self.search([('user_id','=',user.id)]):
            self.create({'user_id':user.id,'device_token':token})
            return "Device token added successfully!"

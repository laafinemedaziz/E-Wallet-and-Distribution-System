from odoo import models, fields, api
from odoo import SUPERUSER_ID
from odoo.exceptions import ValidationError
from odoo.exceptions import AccessDenied, UserError

class Notifications(models.Model):
    _name = 'res.notifications'
    _description = 'Notification records for users'

    user_id = fields.Many2one('res.users', required=True, ondelete='cascade')
    title = fields.Char(required=True, string='Title')
    body = fields.Text(required=True, string='Body')
    is_read = fields.Boolean(required=True, string='is_read',default=False)


    @api.model
    def getUserNotifications(self, user):
        return self.with_user(SUPERUSER_ID).search([('user_id','=',user.id)])
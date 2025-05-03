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
    status = fields.Selection([('urgent', 'Urgent'), ('alert', 'Alert'), ('info', 'Info')], default='info')
    is_read = fields.Boolean(required=True, string='is_read',default=False)


    @api.model
    def getUserNotifications(self, user):
        notificationRecords = self.search([('user_id','=',user.id)])
        notifications = notificationRecords.read(['id','title','body','status','is_read','create_date'])
        for notification in notifications:
            notification['create_date'] = str(notification.get('create_date'))
        
        return notifications
    
    @api.model
    def countUnreadNotifications(self, user):
        return self.search_count([('user_id','=',user.id),('is_read','=',False)])
    
    @api.model
    def markAllNotificationsAsRead(self, user):
        self.search([('user_id','=',user.id)]).write({'is_read':True})
from odoo import models, fields, api
from odoo import SUPERUSER_ID
from odoo.exceptions import ValidationError
from odoo.exceptions import AccessDenied, UserError
class EWallet(models.Model):

    _name = 'res.ewallet'
    _description = "The EWallet model"

    user_id = fields.Many2one('res.users',string="User ID",required=True,unique=True,ondelete='cascade')
    debit = fields.Float(string="Debit")

    @api.model
    def getWallet(self,user):
        wallet = self.search([('id','=',user.ewallet_id.id)],limit=1)
        if not wallet :
            raise ValueError("No wallet was found.")
        else:
            return {
                "id" : wallet.id,
                "owner": wallet.user_id.name,
                "debit" : wallet.debit
            }
        
    @api.model
    def getEmpsWallets(self, user):
        if user.type != 'hr':
            raise AccessDenied(f"Prohibited action for user type: {user.type}")
        else:
            emps = self.env['res.users'].getEmps(user)
            emps_id = [emp.id for emp in emps]
            
            wallets = self.search([('user_id','in',emps_id)])
            return wallets.read(['id','user_id','debit'])
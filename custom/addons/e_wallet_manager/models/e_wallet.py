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
        
    #--------------------------------------------------------------------------------
    #----------------------------Deposit funds method--------------------------------
    #--------------------------------------------------------------------------------



    @api.model
    def transferCredit(self,sender,receiver_wallet_id,amount):

        if sender.type != 'hr':
            raise AccessDenied("Unauthorized")
        if amount <= 0:
            raise ValidationError("Transfered amount cannot be negative.")
        
        receiver_wallet = self.env['res.ewallet'].search([('id','=',receiver_wallet_id)])
        

        if sender.company_ref != receiver_wallet.user_id.company_ref:
            raise ValidationError("You cannot tranfer credits to employees outside your company.")
        
        if not receiver_wallet.user_id.validate_user():
            raise ValidationError("The receiver is not a valid user.")
        
        sender_wallet = sender.ewallet_id

        if not sender_wallet or not receiver_wallet.exists():
            raise ValidationError("Error: There was a problem retreiving wallets.")
        else:
            if (sender_wallet.debit - amount) < 0 :
                raise ValidationError("Error: Not enough credits. Buy Learning Credits into you account and then re-try.")
            else:
                if self.transfer(sender_wallet,receiver_wallet,amount):
                    return({
                        'response':f"Amount transfered successfully to user {receiver_wallet.user_id.login}",
                        'receiver_id':receiver_wallet.user_id.id,
                        'receiver_wallet_id':receiver_wallet.id,
                        'sender_id':sender.id,
                        'sender_wallet_id':sender_wallet.id,
                        'transfered_amount':amount
                    })
                else:
                    raise ValidationError("Error: There was a problem transfering the credits.")
            
    @api.model
    def transfer(self,sender_wallet,receiver_wallet,amount):
        new_debit_receiver = receiver_wallet.debit + amount
        new_debit_sender = sender_wallet.debit - amount
        with self.env.cr.savepoint():
            receiver_wallet.write({'debit':new_debit_receiver})
            sender_wallet.write({'debit':new_debit_sender})
        return True




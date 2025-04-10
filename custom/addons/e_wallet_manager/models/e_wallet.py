from odoo import models, fields, api
from odoo import SUPERUSER_ID
from odoo.exceptions import ValidationError
from odoo.exceptions import AccessDenied, UserError
class EWallet(models.Model):

    _name = 'res.ewallet'
    _description = "The EWallet model"

    user_id = fields.Many2one('res.users',string="User ID",required=True,unique=True,ondelete='cascade')
    balance = fields.Monetary(string="Balance",currency_field="currency_id")
    currency_id = fields.Many2one('res.currency',
                                    string='Currency',
                                    required=True,
                                    default=lambda self: self.env.ref('e_wallet_manager.learning_coins'),
                                    readonly=True)
    
   
    @api.model
    def getWallet(self,user):
        wallet = self.search([('id','=',user.ewallet_id.id)],limit=1)
        if not wallet :
            raise ValueError("No wallet was found.")
        else:
            return {
                "id" : wallet.id,
                "owner": wallet.user_id.name,
                "balance" : wallet.balance
            }
        
    @api.model
    def getEmpsWallets(self, user):
        if not user.has_group('clevory_user.hr_group_manager'):
            raise AccessDenied(f"Prohibited action for user type: {user.type}")
        else:
            emps = self.env['res.users'].getEmps(user)
            emps_id = [emp.id for emp in emps]
            
            wallets = self.search([('user_id','in',emps_id)])
            return wallets.read(['user_id','balance'])
        
    #--------------------------------------------------------------------------------
    #----------------------------Deposit funds method--------------------------------
    #--------------------------------------------------------------------------------
    @api.model
    def fundWallet(self,invoice):
        if invoice.payment_state != "paid":
            raise ValidationError("ERROR: invoice was not paid")
        
        user = invoice.partner_id.user_id
        user_wallet = user.ewallet_id
        if not user_wallet:
            raise ValidationError("ERROR: User does not have an e-wallet.")
        paid_quantity = 0  
        for line in invoice.line_ids:
            paid_quantity += line.quantity
        new_balance =  int(user_wallet.balance + paid_quantity)
        print(new_balance)
        self.env.cr.savepoint()
        user_wallet.write(
            {
                'balance':new_balance,
            }
        )
        record_payment,response = self.env['res.transactions'].with_user(SUPERUSER_ID).record_payment(user,paid_quantity)
        self.env.cr.commit()
        return True



    @api.model
    def transferCredit(self,sender,receiver_wallet_id,amount):

        if not sender.has_group('clevory_user.hr_group_manager'):
            raise AccessDenied("Unauthorized")
        if amount <= 0:
            raise ValidationError("Transfered amount cannot be negative.")
        
        receiver_wallet = self.env['res.ewallet'].search([('id','=',receiver_wallet_id)])
        

        if sender.company_ref != receiver_wallet.user_id.company_ref:
            raise ValidationError(f"You cannot tranfer credits to employees outside your company.")
        
        if not receiver_wallet.user_id.validate_user():
            raise ValidationError("The receiver is not a valid user.")
        
        sender_wallet = sender.ewallet_id

        if not sender_wallet or not receiver_wallet.exists():
            raise ValidationError("Error: There was a problem retreiving wallets.")
        else:
            if (sender_wallet.balance - amount) < 0 :
                raise ValidationError("Error: Not enough credits. Buy Learning Credits into you account and then re-try.")
            else:
                transfer = self.transfer(sender_wallet,receiver_wallet,amount)
                if transfer:
                    transaction_record,response= self.env['res.transactions'].record_transfer(sender_wallet,
                                                                                                    receiver_wallet,
                                                                                                    amount)
                    if transaction_record:
                        return response
                    else:
                        raise ValidationError("There was an error recording your transaction.")
                    
                    """ return({
                        'response':f"Amount transfered successfully to user {receiver_wallet.user_id.login}",
                        'receiver_id':receiver_wallet.user_id.id,
                        'receiver_wallet_id':receiver_wallet.id,
                        'sender_id':sender.id,
                        'sender_wallet_id':sender_wallet.id,
                        'transfered_amount':amount
                    }) """
                else:
                    raise ValidationError("Error: There was a problem transfering the credits.")
            
    @api.model
    def transfer(self,sender_wallet,receiver_wallet,amount):
        new_balance_receiver = receiver_wallet.balance + amount
        new_balance_sender = sender_wallet.balance - amount
        with self.env.cr.savepoint():
            receiver_wallet.with_user(SUPERUSER_ID).write({'balance':new_balance_receiver})
            sender_wallet.with_user(SUPERUSER_ID).write({'balance':new_balance_sender})
        return True




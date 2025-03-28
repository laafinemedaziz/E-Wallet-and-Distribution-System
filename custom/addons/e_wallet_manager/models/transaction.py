from odoo import models, fields, api
from odoo import SUPERUSER_ID
from odoo.exceptions import ValidationError
from odoo.exceptions import AccessDenied, UserError


#A model to record monetary transactions between users
class transaction(models.Model):
    _name = 'res.transactions'
    _description = "Transactions Records"
    
    sender_wallet_id = fields.Many2one('res.wallet', string='Sender Wallet', required=True)
    receiver_wallet_id = fields.Many2one('res.wallet', string="Receiver Wallet", required=True)
    amount = fields.Monetary(string="Amount", currency_field="currency_id")
    currency_id = fields.Many2one('res.currency',
                                    string='Currency',
                                    required=True,
                                    default=lambda self: self.env.ref('e_wallet_manager.learning_coins'),
                                    readonly=True)

    @api.model
    def record_transaction(self, sender_wallet, receiver_wallet, amount):
        transaction = self.create({
            'sender_wallet_id':sender_wallet.id,
            'receiver_wallet_id':receiver_wallet.id,
            'amount':amount
        })
        if transaction:
            return True, {'response':(f"Amount transfered successfully to user {receiver_wallet.user_id.login}. "
                                      f"Transaction successfully recorded under ID: {transaction.id}"),
                        'receiver_id':receiver_wallet.user_id.id,
                        'receiver_wallet_id':receiver_wallet.id,
                        'sender_id':sender_wallet.user_id.id,
                        'sender_wallet_id':sender_wallet.id,
                        'transfered_amount':amount}
        else:
            return False


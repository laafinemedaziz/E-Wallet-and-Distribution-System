from odoo import models, fields, api
from odoo import SUPERUSER_ID
from odoo.exceptions import ValidationError
from odoo.exceptions import AccessDenied, UserError


#A model to record monetary transactions between users
class transaction(models.Model):
    _name = 'res.transactions'
    _description = "Transactions Records"
    
    user_id = fields.Many2one('res.users', string='User ID', required=True)
    sender_wallet_id = fields.Many2one('res.ewallet', string='Sender Wallet')
    receiver_wallet_id = fields.Many2one('res.ewallet', string="Receiver Wallet")
    amount = fields.Monetary(string="Amount", currency_field="currency_id")
    currency_id = fields.Many2one('res.currency',
                                    string='Currency',
                                    required=True,
                                    default=lambda self: self.env.ref('e_wallet_manager.learning_coins'),
                                    readonly=True)
    category = fields.Selection([('transfer','Transfer'),
                                 ('purchase','Purchase'),
                                 ('payment','Payment')], required=True)
    """
    Transaction categories:
        *Transfer: LC sent from one wallet to another (Only HRs have the right to make this kind of transactions).
        *Purchase: Products bought with LC.
        *Payment: LC bought with real currency.
    """
    @api.model
    def record_transfer(self, sender_wallet, receiver_wallet, amount):
        transaction = self.create({
            'sender_wallet_id':sender_wallet.id,
            'receiver_wallet_id':receiver_wallet.id,
            'user_id':sender_wallet.user_id.id,
            'amount':amount,
            'category':"transfer"
        })
        if transaction:
            return True, {'response':(f"Amount transfered successfully to user {receiver_wallet.user_id.login}. "
                                      f"Transaction successfully recorded under ID: {transaction.id}"),
                        'receiver_id':receiver_wallet.user_id.id,
                        'receiver_wallet_id':receiver_wallet.id,
                        'sender_id':sender_wallet.user_id.id,
                        'sender_wallet_id':sender_wallet.id,
                        'transferred_amount':amount}
        else:
            return False
        
    @api.model
    def record_payment(self,user,amount):
        transaction = self.create({
            'receiver_wallet_id':user.ewallet_id.id,
            'user_id':user.id,
            'amount':amount,
            'category':"payment"
        })
        if transaction:
            return True, {
                            'response':("Payment recorded successfully."
                            f"Transaction successfully recorded under ID: {transaction.id}"),
                            'receiver_id':user.id,
                            'receiver_wallet_id':user.ewallet_id.id,
                            'amount':amount
                            }
        else:
            return False

    @api.model
    def getTransactions(self,user):
        transaction_records = self.search([('user_id','=',user.id)])
        transactions = []
        for record in transaction_records:
            transactions.append({
                'id':record.id,
                'sender_wallet_id':record.sender_wallet_id.id,
                'sender':'Self' if record.sender_wallet_id.user_id.id == record.user_id.id else "System" if not record.sender_wallet_id.user_id.id else record.sender_wallet_id.user_id.name,
                'create_date':str(record.create_date),
                'receiver_wallet_id':record.receiver_wallet_id.id,
                'receiver':'Self' if record.receiver_wallet_id.user_id.id == record.user_id.id else record.receiver_wallet_id.user_id.name,
                'category':record.category,
                'amount':record.amount
            })
        """ transactions = transaction_records.read(['sender_wallet_id','create_date','receiver_wallet_id','category','amount'])
        for record in transactions:
            record['create_date'] = str(record.get('create_date')) """

        return transactions
    
    @api.model
    def getTransfers(self,user):
        transfer_records = self.search([('user_id','=',user.id),('category','=','transfer')])
        transfers = []
        for record in transfer_records:
            transfers.append({
                'id':record.id,
                'sender_wallet_id':record.sender_wallet_id.id,
                'sender':'Self' if record.sender_wallet_id.user_id.id == record.user_id.id else "System" if not record.sender_wallet_id.user_id.id else record.sender_wallet_id.user_id.name,
                'create_date':str(record.create_date),
                'receiver_wallet_id':record.receiver_wallet_id.id,
                'receiver':'Self' if record.receiver_wallet_id.user_id.id == record.user_id.id else record.receiver_wallet_id.user_id.name,
                'category':record.category,
                'amount':record.amount
            })

        return transfers
    
    @api.constrains('category','sender_wallet_id','receiver_wallet_id')
    def _check_constraints(self):
        for record in self:
            if record.category == 'transfer':
                if not record.sender_wallet_id or not record.receiver_wallet_id:
                    raise ValidationError("A transaction of type 'transfer' must have two wallets linked to it.")
            elif record.category == 'purchase':
                if record.receiver_wallet_id or not record.sender_wallet_id:
                    raise ValidationError("A transaction of type 'purchase' must have only the sender wallet linked to it.")
            elif record.category == 'payment':
                if record.sender_wallet_id or not record.receiver_wallet_id:
                    raise ValidationError("A transaction of type 'payment' must have only the receiver wallet linked to it.")
            else:
                raise ValidationError(f"Unknown transaction category: {record.category}")


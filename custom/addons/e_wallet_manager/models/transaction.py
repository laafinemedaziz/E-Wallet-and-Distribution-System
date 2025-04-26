from odoo import models, fields, api
from odoo import SUPERUSER_ID
from odoo.exceptions import ValidationError
from odoo.exceptions import AccessDenied, UserError
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import csv
import io


#A model to record monetary transactions between users
class transaction(models.Model):
    _name = 'res.transactions'
    _description = "Transactions Records"
    #Note: the user_id field purpose is to record the user concerned with the transaction (Can be either the sender or the receiver)
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
        #Record double transaction, one for the sender and one for the receiver
        transaction_sender = self.create({
            'sender_wallet_id':sender_wallet.id,
            'receiver_wallet_id':receiver_wallet.id,
            'user_id':sender_wallet.user_id.id,
            'amount':amount,
            'category':"transfer"
        })
        transaction_receiver = self.create({
            'sender_wallet_id':sender_wallet.id,
            'receiver_wallet_id':receiver_wallet.id,
            'user_id':receiver_wallet.user_id.id,
            'amount':amount,
            'category':"transfer"
        })
        if transaction_sender and transaction_receiver:
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
    

    @api.model
    def getCSVReport(self,user):
        transactions = self.getTransactions(user)
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['Transaction ID', 'Date', 'Type', 'Sender', 'Receiver', 'Amount'])
        for record in transactions:
            writer.writerow([record.get('id'), 
                             record.get('create_date')[:16], 
                             record.get('category'), 
                             record.get('sender'), 
                             record.get('receiver'), 
                             record.get('amount')])
        csv_content = output.getvalue()
        output.close()
        return csv_content
    
    def getPDFReport(self,user):
        pdf_buffer = io.BytesIO()
        pdf = canvas.Canvas(pdf_buffer, pagesize=letter)
        width, height = letter
        transactions = self.getTransactions(user)
        # Title
        pdf.setFont("Helvetica-Bold", 20)
        pdf.drawString(200, 750, "Transactions Report")

        # Column Headers
        pdf.setFont("Helvetica-Bold", 12)
        pdf.drawString(35, 700, "Transaction ID")
        pdf.drawString(135, 700, "Date")
        pdf.drawString(235, 700, "Type")
        pdf.drawString(335, 700, "Sender")
        pdf.drawString(435, 700, "Receiver")
        pdf.drawString(535, 700, "Amount")

        y = 680
        for record in transactions:
            pdf.setFont("Helvetica", 10)
            pdf.drawString(35, y, str(record.get('id')))
            pdf.drawString(135, y, record.get('create_date')[:16])
            pdf.drawString(235, y, record.get('category'))
            pdf.drawString(335, y, record.get('sender'))
            pdf.drawString(435, y, record.get('receiver'))
            pdf.drawString(535, y, f"{str(record.get('amount'))} CT")

            y -= 20 

            if y < 50:
                pdf.showPage()
                y = 750  # Reset y for the new page

        pdf.save()
        pdf_buffer.seek(0)
        return pdf_buffer

        

        


    
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


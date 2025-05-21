from odoo import models, fields, api
from odoo import SUPERUSER_ID
from odoo.exceptions import ValidationError
from odoo.exceptions import AccessDenied, UserError
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.lib import colors
import csv
import io
import os
import logging
from datetime import datetime


_logger = logging.getLogger(__name__)

#A model to record monetary transactions between users
class transaction(models.Model):
    _name = 'res.transactions'
    _description = "Transactions Records"
    #Note: the user_id field purpose is to record the user who made the transaction
    user_id = fields.Many2one('res.users', string='User ID', required=True, ondelete='cascade')
    sender_wallet_id = fields.Many2one('res.ewallet', string='Sender Wallet')
    receiver_wallet_id = fields.Many2one('res.ewallet', string="Receiver Wallet")
    sender_user_name = fields.Char(related='sender_wallet_id.user_id.name', store=True)
    receiver_user_name = fields.Char(related='receiver_wallet_id.user_id.name', store=True)
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

        #For sake of clarity only one transaction is recorded and the user_id field concerns the user who made the transaction
        """ transaction_receiver = self.create({
            'sender_wallet_id':sender_wallet.id,
            'receiver_wallet_id':receiver_wallet.id,
            'user_id':receiver_wallet.user_id.id,
            'amount':amount,
            'category':"transfer"
        }) """
        if transaction_sender:
            self.env['firebase.device.token'].send_notification(
                title="Transfer Recorded!",
                body=f"Your transfer was successfully made. {amount} coins were sent to {receiver_wallet.user_id.name}.",
                user=sender_wallet.user_id
            )

            self.env['firebase.device.token'].send_notification(
                title="Coins Received!",
                body=f"You have received {amount} coins from {sender_wallet.user_id.name}.",
                user=receiver_wallet.user_id
            )
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
            self.env['firebase.device.token'].send_notification(
                title="Payment Recorded!",
                body=f"Thank you for your payment {user.name}. Coins were added to your wallet. Enjoy spending them!",
                user=user
            )
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
    def record_purchase(self,user,course):
        transaction = self.create({
            'sender_wallet_id':user.ewallet_id.id,
            'user_id':user.id,
            'amount':course.price_lc,
            'category':"purchase"
        })
        if transaction:
            self.env['firebase.device.token'].send_notification(
                title="Course Purchased!",
                body=f"Thank you for your purchase {user.name}. You can now access {course.product_tmpl_id.name}. Enjoy learning!",
                user=user
            )
            return True, {
                            'response':("purchase recorded successfully."
                            f"Transaction successfully recorded under ID: {transaction.id}"),
                            'receiver_id':user.id,
                            'receiver_wallet_id':user.ewallet_id.id,
                            'amount':course.price_lc
                            }
        else:
            return False

    @api.model
    def getTransactions(self,user):
        transaction_records = self.search(['|', '|',('user_id','=',user.id),('sender_wallet_id','=',user.ewallet_id.id),('receiver_wallet_id','=',user.ewallet_id.id)])
        transactions = []
        for record in transaction_records:
            transactions.append({
                'id':record.id,
                'sender_wallet_id':record.sender_wallet_id.id,
                'sender':'Self' if record.sender_wallet_id.user_id.id == user.id else "System" if not record.sender_wallet_id else record.sender_wallet_id.user_id.name,
                'create_date':str(record.create_date),
                'receiver_wallet_id':record.receiver_wallet_id.id,
                'receiver':'Self' if record.receiver_wallet_id.user_id.id == user.id else "System" if not record.receiver_wallet_id else record.receiver_wallet_id.user_id.name,
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
    
    @api.model
    def getPDFReport(self, user):
        pdf_buffer = io.BytesIO()
        pdf = canvas.Canvas(pdf_buffer, pagesize=letter)
        width, height = letter
        transactions = self.getTransactions(user)

        current_dir = os.path.dirname(os.path.abspath(__file__))
        logo_path = os.path.join(current_dir, '../data/logo.png')
        logo_path = os.path.normpath(logo_path)
        _logger.info(f"Logo path: {logo_path}")
        try:
            pdf.drawImage(logo_path, 40, 740, width=80, height=35, mask='auto')
        except:
            pass  

        # Title
        pdf.setFont("Helvetica-Bold", 20)
        pdf.drawString(206, 750, "Transactions Report")

        pdf.setFont("Helvetica", 10)
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        pdf.drawRightString(570, 755, f"Generated: {now}")

        # Horizontal line under header
        pdf.setStrokeColor(colors.grey)
        pdf.setLineWidth(1)
        pdf.line(30, 730, width - 30, 730)

        # Column Headers
        pdf.setFont("Helvetica-Bold", 12)
        headers = ["Transaction ID", "Date", "Type", "Sender", "Receiver", "Amount"]
        x_positions = [35, 135, 235, 335, 435, 535]
        y = 710

        for x, header in zip(x_positions, headers):
            pdf.drawString(x, y, header)

        y -= 20
        pdf.setFont("Helvetica", 10)
        for record in transactions:
            values = [
                str(record.get('id')),
                record.get('create_date')[:16],
                record.get('category'),
                record.get('sender'),
                record.get('receiver') or "System",
                f"{str(record.get('amount'))} CT"
            ]
            for x, val in zip(x_positions, values):
                pdf.drawString(x, y, val)

            y -= 20
            if y < 50:
                pdf.showPage()
                y = 750
                # Reprint headers on the new page
                pdf.setFont("Helvetica-Bold", 12)
                for x, header in zip(x_positions, headers):
                    pdf.drawString(x, y, header)
                y -= 20
                pdf.setFont("Helvetica", 10)

        # Footer (optional)
        pdf.setFont("Helvetica-Oblique", 8)
        pdf.drawRightString(width - 30, 20, "Generated by Clevry E-Wallet Manager")

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


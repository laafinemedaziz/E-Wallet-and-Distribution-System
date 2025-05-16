import logging
import secrets
from odoo import models, fields, api
from odoo.exceptions import ValidationError
from odoo.exceptions import AccessDenied, UserError
from odoo import SUPERUSER_ID
import requests
import logging


_logger = logging.getLogger(__name__)

"""
---------------------------------Add Comment------------------------------
"""
class FundWallet (models.Model):
    _inherit = 'account.move'

    @api.model
    def createInvoice(self,lc_quantity,user):
        Currency = self.env.ref('base.TND')
        LC = self.env.ref('fund_wallet.learning_coin_product')
        if not Currency :
            raise ValidationError("There was an error :Currency.")
        if not LC :
            raise ValidationError("There was an error :LC.")

        """ if not Currency or LC :
            raise ValidationError("There was an error fulfilling your request.") """
        invoice_metadata = {
            'partner_id':user.partner_id.id,
            'move_type':"out_invoice",
            'currency_id':Currency.id
        }

        invoice = self.create(invoice_metadata)

        if not invoice:
            raise ValidationError("Invoice creation failed.")
        else:
            invoice_line= self._createInvoiceLine(LC,lc_quantity,invoice,user)
            invoice.action_post()

        return {'response':f"Invoice Was successfully created under id: {invoice.id}",
                                    'invoice_id':invoice.id,
                                    'user':user.login,
                                    'LC_quantity':invoice_line.quantity,
                                    'price':invoice.amount_total_signed,
                                    'currency':invoice.currency_id.name}


    def _createInvoiceLine(self,LC,lc_quantity,invoice,user):
        return self.env['account.move.line'].create({
            'move_id':invoice.id,
            'product_id':LC.id,
            'quantity':lc_quantity,
            'price_unit':1
        })
    
    @api.model
    def getInvoices(self,user):
        invoice_records = self.search([('partner_id','=',user.partner_id.id),('amount_total_signed','>',0),('move_type','=','out_invoice')])
        invoices = []
        for record in invoice_records:
            record.preview_invoice()
            invoices.append(
                {
                    'id':record.id,
                    'ref':record.name,
                    'date':str(record.create_date),
                    'amount':record.amount_total_signed,
                    'currency':record.currency_id.name,
                    'payment_state':record.payment_state,
                    'access_token':record.access_token,
                }
            )
        return invoices
    
    @api.model
    def getInvoiceById(self,user,id):
        invoice_record = self.search([('id','=',id),('partner_id','=',user.partner_id.id),('payment_state','=','not_paid'),('amount_total_signed','>',0),('move_type','=','out_invoice')])
        
        return {
                    'id':invoice_record.id,
                    'ref':invoice_record.name,
                    'date':str(invoice_record.date),
                    'amount':invoice_record.amount_total_signed,
                    'currency':invoice_record.currency_id.name,
                    'payment_state':invoice_record.payment_state
                }
    
    


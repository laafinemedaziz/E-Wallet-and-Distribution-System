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

        invoice = self.with_user(SUPERUSER_ID).create(invoice_metadata)

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
        return self.env['account.move.line'].with_user(SUPERUSER_ID).create({
            'move_id':invoice.id,
            'product_id':LC.id,
            'quantity':lc_quantity,
            'price_unit':1
        })
    
    


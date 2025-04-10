import logging
import secrets
from odoo import models, fields, api
from odoo import SUPERUSER_ID
from odoo.exceptions import ValidationError


class Partner(models.Model):

    _inherit = 'res.partner'

    employees = fields.One2many('res.users','company_ref',String="Employees")
    hr_ref = fields.Many2one('res.users',String="HR Ref",domain="[('type', '=', 'hr')]")

    @api.model
    def add_new_company(self,vals):
        if not vals.get('name') or not vals.get('email') :
            raise ValidationError("Missing important fields")
        
        vals['is_company'] =  True

        company = self.env['res.partner'].with_user(SUPERUSER_ID).create(vals)
        return company
    
    #Assign the correct user_id in the res.partner model on creation
    @api.model
    def _assignUserIDToPartner(self,user):
        self.with_user(SUPERUSER_ID).write({
            'user_id':user.id,
        })
        

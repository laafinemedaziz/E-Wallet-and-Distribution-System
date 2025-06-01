import logging
import secrets
from odoo import models, fields, api
from odoo import SUPERUSER_ID
from odoo.exceptions import ValidationError


class Partner(models.Model):

    _inherit = 'res.partner'

    employees = fields.One2many('res.users','company_ref',String="Employees")
    hr_ref = fields.Many2one('res.users',String="HR Ref",domain="[('type', '=', 'hr')]")
    company_code = fields.Char(String="Company code", store=True)

    @api.model
    def add_new_company(self,vals):
        if not vals.get('name') or not vals.get('email') :
            raise ValidationError("Missing important fields")
        
        if self.search(['|',('email', '=', vals.get('email')),('name', '=', vals.get('name'))]):
            raise ValidationError("Company with this name or/and email already exists. Contact support if you think this is an error.")
        
        vals['is_company'] =  True

        company = self.env['res.partner'].with_user(SUPERUSER_ID).create(vals)
        company.assign_company_code()
        return {
            'id': company.id,
            'name': company.name,
            'email': company.email,
            'company_code': company.company_code,
            'create_date': str(company.create_date),
        }
    
    def assign_company_code(self):
        code = secrets.token_urlsafe(5)
        self.with_user(SUPERUSER_ID).write({
            'company_code':code
        })

    #Assign the correct user_id in the res.partner model on creation
    @api.model
    def _assignUserIDToPartner(self,user):
        self.with_user(SUPERUSER_ID).write({
            'user_id':user.id,
        })

    @api.model
    def getAllCompanies(self):
        companies = self.search([('is_company', '=', True),('company_code', '!=', False)])
        return [{
            'id': company.id,
            'name': company.name,
            'email': company.email,
            'company_code': company.company_code,
            'create_date': str(company.create_date),
        } for company in companies]
        

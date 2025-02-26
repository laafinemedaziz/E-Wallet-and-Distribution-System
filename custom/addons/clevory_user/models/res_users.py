import logging
from queue import Full
import secrets
from odoo import models, fields, api
from odoo import SUPERUSER_ID
from odoo.exceptions import ValidationError



_logger = logging.getLogger(__name__)



class ClevoryUser (models.Model):
    _inherit = 'res.users'

    type = fields.Selection([
        ("hr","HR"),
        ("employee","Employee"),
        ("learner","Learner")],string="User Type")
    
    status = fields.Selection([
        ('invalid', 'Invalid'),
        ('valid', 'Valid')],
        default='invalid')
    
    company_id = fields.Many2one('res.company', string='Company', required=False)

    company_ref = fields.Many2one('res.partner',String="Company",domain="[('is_company', '=', True)]")

    
    
    verification_token = fields.Char()

    
    #Group is a computed field based on type to develop later

    @api.model
    def sign_up_user(self,vals):

        #input validation for basic required fields
        if not vals.get('name') or not vals.get('login') or not vals.get('email') or not vals.get('password') or not vals.get('type') :
            raise ValidationError("Missing important fields")
        
        company = None
        #Validate and retrieve company from res.partner
        if vals.get('type') in ["employee","hr"]:
            if 'company' in vals or 'company_ref' in vals:
                company = self.env['res.partner'].search([("name",'=',vals.get('company'))],limit=1)
                if not company: 
                    raise ValidationError("Company not found")
            else:
                raise ValidationError(f"Users of type {vals.get('type')} should reference their company!")
        else:
            if 'company' in vals or 'company_ref' in vals:
                raise ValidationError("Only users of type Employee or HR can reference their company.")

        if company:
            if vals.get('type') == "hr":
                if company.hr_ref:
                    raise ValidationError("Company already has an HR assigned.")
            else:
                vals['company_ref'] = company.id

            #Deleting the company key from vals as it is not a field in the res.users model
            del vals['company']

        token = secrets.token_urlsafe(16)
        
        vals['verification_token'] = token

        user= self.env['res.users'].sudo().create(vals)

        #Asigning the user to the company if they are of type HR
        if user.type == 'hr':
            company.write({'hr_ref':user.id})

        #self._send_validation_email(user.id)

        return(user)
    
    def _send_validation_email(self,user_id):
        user = self.browse(user_id)
        if not user.exists() :
            raise ValueError("User not found")
        if user.status != 'invalid':
            raise ValueError("User status is not 'invalid'")

        if not user.verification_token:
            raise ValueError("User has no verification token")
        
        validation_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url') + '/auth_signup/confirm?token=' + user.verification_token
        template = self.env.ref('clevory_user.email_template_user_validation')
        template.with_context(validation_url=validation_url, name=user.name, email=user.email).send_mail(user.id, force_send=True)

    def _validate_user(self,token):

        user = self.env['res.users'].search([("verification_token",'=',token),("verification_token",'!=',"False")],limit=1)
    
        if not user :
            return("Unvalid token or an already verified user")
        else :
            user.write({
            "status": "valid",  
            "verification_token": "False"  
        })
            return("User verified successfully")

    # Bypass company check because we won't need it in this model
    @api.constrains('company_id')
    def _check_company(self):
        pass  
    

    #Contrainst for the company_ref field 
    @api.constrains('type', 'company_ref')
    def _check_company_relationship(self):
        for user in self:     
            if user.type == 'employee' :
                if not user.company_ref:
                    raise ValidationError("An employee must be linked to a company.")
                elif user.company_ref.is_company != True:
                    raise ValidationError("Invald company")
            elif user.type == 'learner' and user.company_ref:
                raise ValidationError("A learner should not be linked to a company.")

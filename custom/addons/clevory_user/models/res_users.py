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
        
        
        #Validate and retrieve company from res.partner
        company = None
        if vals.get('type') in ["employee","hr"]:
            if 'company' in vals or 'company_ref' in vals:
                company = self.env['res.partner'].search([("name",'=',vals.get('company')),('is_company','=',True)],limit=1)
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
            
            vals['company_ref'] = company.id

            #Deleting the company key from vals as it is not a field in the res.users model
            del vals['company']

        token = secrets.token_urlsafe(16)
        
        vals['verification_token'] = token

        user= self.env['res.users'].with_user(SUPERUSER_ID).create(vals)

        #Asigning the user to the company if they are of type HR
        if user.type == 'hr':
            company.write({'hr_ref':user.id})

        user._send_validation_email()
        
        if not user :
            raise ValidationError("User creation failed")
        return(user)
    
    def _send_validation_email(self):

        if not self.exists() :
            raise ValueError("User not found")
        if self.status != 'invalid':
            raise ValueError("User status is not 'invalid'")

        if not self.verification_token:
            raise ValueError("User has no verification token")
        

        match self.type:
            case "learner":
                template = self.env.ref('clevory_user.user_registration_learner_mail_template')
            case "employee":
                template = self.env.ref('clevory_user.user_registration_employee_mail_template')
            case "hr":
                template = self.env.ref('clevory_user.user_registration_hr_mail_template')
            case _:
                raise ValueError("User type is not recognized!")



        template.send_mail(self.id, force_send=True)

    def _get_verification_url(self):
        return self.env['ir.config_parameter'].sudo().get_param('web.base.url') + '/api/confirm_user?token=' + self.verification_token
    
    def _get_admin(self):
        admin = self.env['res.users'].search([("id",'=',"2")], limit=1)
        return admin
    @api.model
    def _validate_user(self,token):

        user = self.env['res.users'].search([("verification_token",'=',token),("verification_token",'!=',"False"),("status",'=',"invalid")],limit=1)
    
        if not user :
            raise ValidationError("Error: No user was found!")
        else :
            user.with_user(SUPERUSER_ID).write({
            "status": "valid",  
            "verification_token": "False"  
        })
            return ({"response":f"User with id {user.id} was verified successfully!"})

    # Bypass company check because we won't need it in this model
    @api.constrains('company_id')
    def _check_company(self):
        pass  
    

    #Contrainst for the company_ref field 
    @api.constrains('type', 'company_ref')
    def _check_company_relationship(self):
        for user in self:     
            if user.type in ['employee','hr']:
                if not user.company_ref:
                    raise ValidationError("An Employee or an HR must be linked to a company.")
                elif user.company_ref.is_company != True:
                    raise ValidationError("Invald company")
            elif user.type == 'learner' and user.company_ref:
                raise ValidationError("A learner should not be linked to a company.")

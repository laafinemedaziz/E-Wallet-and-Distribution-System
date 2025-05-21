import logging
import secrets
from odoo import models, fields, api
from odoo import SUPERUSER_ID
from odoo.exceptions import ValidationError
from odoo.exceptions import AccessDenied, UserError


_logger = logging.getLogger(__name__)

"""
* This modele is responsible for managing the users of the application.
* It allows users to sign up, validate their email, and manage their accounts.
"""
class ClevoryUser (models.Model):
    _inherit = 'res.users'

    
    type = fields.Selection([
        ("hr","HR"),
        ("employee","Employee"),
        ("learner","Learner")],string="User Type")
    #Note: User of type Admin is only created manually and not through the app
    
    #Status is used to track email validation and therefore giving the user access to their account
    status = fields.Selection([
        ('invalid', 'Invalid'),
        ('valid', 'Valid')],
        default='invalid')
    
    #active is used to track if the user is active or not (When user is deactivated they lose access to their account)
    active = fields.Boolean(default=False)

    #Wallet field
    ewallet_id = fields.Many2one('res.ewallet',String="E-Wallet id",unique=True,ondelete='cascade')

    #by passing the company restrection
    company_id = fields.Many2one('res.company', string='Company', required=False)

    #Actually referencing the company in res.partner
    company_ref = fields.Many2one('res.partner',String="Company",domain="[('is_company', '=', True)]") 

    #The verification token is used to validate the user by email
    verification_token = fields.Char()

    reset_password_token = fields.Char()

    #Group is a computed field based on type to develop later
#------------------------------------------------------Signup User------------------------------------------------------
    @api.model
    def sign_up_user(self,vals):

        vals = self._validate_signup_vals(vals)
        
        if 'companyCode' in vals:
            vals = self._get_company(vals)
        

        token = secrets.token_urlsafe(16)
        
        vals['verification_token'] = token
        vals['signup_type'] = 'password'
        vals['groups_id'] = [(6, 0, [self.assignGroup(vals.get('type')).id])]
        
        #Create the user
        user= self.env['res.users'].with_context(no_reset_password=True).with_user(SUPERUSER_ID).create(vals)
        if not user :
            raise ValidationError("User creation failed")
        #Assign a new wallet for the user
        user.createWallet()

        #Assign correct user_id in res.partner model
        partner = user.partner_id
        partner._assignUserIDToPartner(user)
        

        user._send_validation_email()
        
        
        return(user.with_user(SUPERUSER_ID).read(['login']))
    
    @api.model
    def _validate_signup_vals(self,vals):
        #input validation for basic required fields
        if not vals.get('name') or not vals.get('login') or not vals.get('email') or not vals.get('password') or not vals.get('type') :
            raise ValidationError("Missing important fields")
        
        if vals.get('type') not in ['hr','employee','learner']:
            raise ValidationError("Invalid user type")

        if vals.get('type') == 'learner':
            if vals.get('companyCode') != "":
                raise ValidationError("User type Learner cannot have a company.")
            del vals['companyCode']

        return vals

    @api.model
    def _get_company(self,vals):
        company = self.env['res.partner'].search([("company_code",'=',vals.get('companyCode')),('is_company','=',True)],limit=1)

        if not company:
            raise ValidationError('No company with given code was not found, Verify company code and try again.')
        
        if vals.get('type') == 'hr' and company.hr_ref:
            raise ValidationError("Company already has an HR assigned.")
        
        vals['company_ref'] = company.id
        #CompanyCode is not needed in the user vals as it is not a field in res.users
        del vals['companyCode']

        return vals


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

    #------------------------------------------------------Validate User------------------------------------------------------
    def _get_verification_url(self):
        return self.env['ir.config_parameter'].sudo().get_param('web.base.url') + '/api/confirm_user?token=' + self.verification_token
    
    def _get_admin(self):
        admin = self.env['res.users'].search([("id",'=',"2")], limit=1)
        return admin
    
    def validate_user(self):
        if self.status != 'valid' or self.active != True:
            return False
        return True
    
    @api.model
    def _validate_user(self,token):

        user = self.env['res.users'].search([
            ("verification_token",'=',token),
            ("verification_token",'!=',"False"),
            ("status",'=',"invalid"),
            ("active",'=',False)],limit=1)
    
        if not user :
            raise ValidationError("Error: No user was found!")
        else :
            if user.type == "hr":
                company = user.company_ref
                company.write({
                    'hr_ref':user.id
                })
            user.write({
            "status": "valid", 
            "active":True, 
            "verification_token": "False"  
        })  
            return ({"response":f"User with id {user.id} was verified successfully!"})
    
    def createWallet(self):
        ewallet = self.env['res.ewallet'].with_user(SUPERUSER_ID).create({
            'user_id':self.id,
            'balance':0
        })
        self.ewallet_id = ewallet.id
    
    @api.model
    def assignGroup(self,user_type):
        match user_type:
            case 'hr': return self.env.ref('clevory_user.hr_group_manager')
            case 'employee':  return self.env.ref('clevory_user.employee_group_manager')
            case 'learner': return self.env.ref('clevory_user.learner_group_manager')
            case default: raise ValueError("User type not recognized")

    
    @api.model
    def getEmps(self, user):
        if not user.has_group('clevory_user.hr_group_manager'):
            raise AccessDenied(f"Prohibited action for user type: {user.type}")
        else:
            emps =  self.search([('company_ref','=',user.company_ref.id),('id','!=',user.id)])
            return emps

    #------------------------------------------------------Reset Password------------------------------------------------------
    @api.model
    def _sendpasswordResetEmail(self,email):
        user = self.with_user(SUPERUSER_ID).search([('email','=',email),('signup_type','=','password')])
        if not user :
            return {
              "success": False,
              "message": f"No user matched this email: {email}. Please double check and try again."
            }

        resetCode = secrets.token_urlsafe(16)
        user.with_user(SUPERUSER_ID).write({
            'reset_password_token':resetCode
        })
        template = self.env.ref('clevory_user.reset_password_mail_template')
        template.send_mail(user.id, force_send=True)
        return {
            "success": True,
            'message':f"Reset password email sent to {email}. Check your inbox."
        }
    
    def _passwordResetLinkFormatter(self):
        return 'http://localhost:4200/updatepassword?token=' + self.reset_password_token
    
    @api.model
    def validateResetToken(self,token):
        if token == None or token == "":
            return {
                'response':False,
                'message':'No token found'
            }

        
        user = self.with_user(SUPERUSER_ID).search([('reset_password_token','=',token)])
        if not user:
            return {
                'response':False,
                'message':'Unvalid or expired token. Try resetting your password again.'
            }
        
        return {
            'response':True
        }
    
    def resetPassword(self,token,newPassword):
        user = self.with_user(SUPERUSER_ID).search([('reset_password_token','=',token)])
        if not user:
            return {
                'response':False,
                'message':'Unvalid or expired token. Try resetting your password again.'
            }
        
        user.with_user(SUPERUSER_ID).write({
            'password':newPassword,
            'reset_password_token':None
        })
        self.env['firebase.device.token'].send_notification(
                title="Password Reset",
                body="Your Password has been changed successfully.",
                user=user,
                status="alert"
            )
        return {
            'response':True,
            'message':"Password changed successfully. You can now log into your account."
        }


    @api.model
    def changeUserInfos(self,user,newUserInfo):
        if not user:
            return {
                'response':False,
                'message':'User not authenticated.'
            }
        user_partner = user.partner_id
        user_partner.write(newUserInfo)
        return {
            'response':True,
            'message':"User info changed successfully."
        }
        
    @api.model
    def getAllUsers(self):
        users_records = self.with_context(active_test=False).search([('type', 'in', ['hr', 'employee', 'learner'])])
        _logger.info(f"Users found: {users_records}")
        users_data = []
        for user in users_records:
            users_data.append({
                'id': user.id,
                'name': user.name,
                'login': user.login,
                'email': user.email,
                'type': user.type,
                'status': user.status,
                'active': user.active,
                'company_ref': user.company_ref.id if user.company_ref else None,
                'create_date': str(user.create_date) if user.create_date else '',
                'write_date': str(user.write_date) if user.write_date else '',
                'balance': user.ewallet_id.balance if user.ewallet_id else 0,
                'active': user.active,
            })
        return users_data


    
    @api.model
    def activateDeactivateUser(self,user_id):
        user = self.with_context(active_test=False).search([('id','=',user_id)])
        _logger.info(f"User found: {user}")
        if not user:
            return {
                'response':False,
                'message':'User not authenticated.'
            }
        user.write({
            'active': not user.active
        })
        _logger.info(f"User {user.name} has been {'activated' if user.active else 'deactivated'}.")
        return {
            'response':True,
            'message':f"User {user.name} has been {'activated' if user.active else 'deactivated'}."
        }
    
    @api.model
    def deleteUser(self,user_id):
        user = self.with_context(active_test=False).search([('id','=',user_id)])
        if not user:
            return {
                'response':False,
                'message':'User not authenticated.'
            }
        
        try:
            user.unlink()
        except Exception as e:
            _logger.error(f"Failed to delete user {user.name}: {e}", exc_info=True)

        _logger.info(f"User {user.name} has been deleted.")
        return {
            'response':True,
            'message':f"User {user.name} has been deleted."
        }



    #------------------------------------------------------Constraints------------------------------------------------------
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
    
    

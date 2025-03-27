from odoo import models, fields, api
from odoo import SUPERUSER_ID
from odoo.exceptions import ValidationError
from odoo.exceptions import AccessDenied, UserError

class transaction(models.Model):
    _name = 'res.transactions'
    _description = "A model to record monetary transactions between users"
    


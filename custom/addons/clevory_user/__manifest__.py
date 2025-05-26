{
    'name':"ClevoryUser",
    'description':"Clevory user model",
    'author':"Med Aziz Laafine",
    'depends':['base','web','mail','account'],
    'controllers':['controllers/user_management_controller.py','controllers/admin_actions_controller.py'],
    'data': [
    'data/learner_mail_template.xml','data/employee_mail_template.xml','data/hr_mail_template.xml','data/access_groups.xml','data/reset_password_mail_template.xml'
    ],
    'application':True,
    'installable':True
}
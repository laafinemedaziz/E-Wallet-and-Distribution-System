{
    'name':"ClevoryUser",
    'description':"Clevory user model",
    'author':"Med Aziz Laafine",
    'depends':['base','web','mail'],
    'controllers':['controllers/clevory_register_controller.py',],
    'data': [
    'data/learner_mail_template.xml','data/employee_mail_template.xml','data/hr_mail_template.xml'
    ],
    'application':True,
    'installable':True
}
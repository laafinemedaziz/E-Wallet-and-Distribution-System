{
    'name':"ClevoryUser",
    'description':"Clevory user model",
    'author':"Med Aziz Laafine",
    'depends':['base','web','mail'],
    'controllers':['controllers/clevory_register_controller.py',],
    'data': [
    'data/email_templates.xml',
    ],
    'application':True,
    'installable':True
}
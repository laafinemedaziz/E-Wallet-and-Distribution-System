{
    'name':"User Authentication Addon",
    'description':"This addon will be responsible for authenticating users after sign up.",
    'author':"Med Aziz Laafine",
    'depends':['base','web','auth_oauth'],
    'controllers':['/controllers/authentication_controller.py'],
    'application':True,
    'installable':True,

}
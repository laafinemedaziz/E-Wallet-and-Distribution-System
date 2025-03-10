{
    'name':"OAuth2 Clevory Authentication",
    'description':"Allow sign in/up with OAuth2 providers",
    'depends':['base','web','auth_oauth'],
    'controllers':['controllers/oauth_controller.py'],
    'application':True,
    'installable':True
}
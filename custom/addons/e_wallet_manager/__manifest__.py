{
    'name':"E-Wallet Management Addon",
    'description':"This addon is responsible for managing e-wallets in the system",
    'author':'Med Aziz Laafine',
    'depends':['base','web'],
    'data':['data/LC_Currency.xml','views/ewallets_view.xml','views/transactions_view.xml'],
    'controllers':['controllers/wallet_controller.py'],
    'application':True,
    'installable':True
}
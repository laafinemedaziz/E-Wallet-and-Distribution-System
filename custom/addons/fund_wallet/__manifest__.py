{
    'name':'Fund Wallet Addon',
    'description':'This addon is responsible for managing funding users wallets',
    'author':'Med Aziz Laafine',
    'depends':['base','web','e_wallet_manager','account', 'payment'],
    'data':["data/LearningCoinProduct.xml"],
    'controllers':["controllers/fund_wallet_controller.py"],
    'installable':True,
    'application':True
}
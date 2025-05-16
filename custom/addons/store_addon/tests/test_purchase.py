import logging
from odoo.tests.common import TransactionCase, tagged
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)

@tagged('-standard', 'test_course_purchase')
class TestCoursePurchase(TransactionCase):

    def setUp(self):
        super().setUp()
        self.CoursePurchase = self.env['course.purchase']
        self.ProductTemplate = self.env['product.template']
        self.ProductProduct = self.env['product.product']
        self.User = self.env['res.users']
        self.Wallet = self.env['res.ewallet']
        self.Currency = self.env.ref('e_wallet_manager.learning_coins')

        self.test_user = self.User.create({
            'name': 'Test Buyer',
            'login': 'buyer_user',
            'email': 'buyer@example.com',
            'active': True,
        })

        # Create wallet
        self.wallet = self.Wallet.create({
            'user_id': self.test_user.id,
            'balance': 1000,
        })
        self.test_user.write({'ewallet_id': self.wallet.id})

        # Create a product template and product
        self.product_template = self.ProductTemplate.create({
            'name': 'Python Course',
            'price_lc': 300.0,
            'list_price': 300.0,
            'category': 'Programming',
            'description': 'A full Python course'
        })
        self.product = self.ProductProduct.search([('product_tmpl_id', '=', self.product_template.id)], limit=1)

    def test_validate_purchase_success(self):
        result = self.CoursePurchase.validatePurchase(
            user_id=self.test_user.id,
            user_wallet=self.wallet,
            price=300.0,
            product_id=self.product.id
        )
        self.assertTrue(result)
        _logger.info("✅ test_validate_purchase_success passed.")

    def test_validate_purchase_insufficient_balance(self):
        self.wallet.write({'balance': 100.0})
        result = self.CoursePurchase.validatePurchase(
            user_id=self.test_user.id,
            user_wallet=self.wallet,
            price=300.0,
            product_id=self.product.id
        )
        self.assertFalse(result)
        _logger.info("✅ test_validate_purchase_insufficient_balance passed.")

    def test_create_product_invoice(self):
        invoice = self.CoursePurchase.createProductInvoice(self.product, self.test_user)
        self.assertTrue(invoice)
        self.assertEqual(invoice.partner_id.id, self.test_user.partner_id.id)
        _logger.info("✅ test_create_product_invoice passed.")

    def test_purchase_course_success(self):
        invoice = self.CoursePurchase.createProductInvoice(self.product, self.test_user)
        invoice = self.CoursePurchase.purchaseCourse(invoice)
        self.assertEqual(invoice.payment_state, 'paid')
        self.wallet._compute_balance()
        self.assertLess(self.wallet.balance, 1000)
        _logger.info("✅ test_purchase_course_success passed.")

    def test_user_purchased_course(self):
        invoice = self.CoursePurchase.createProductInvoice(self.product, self.test_user)
        invoice = self.CoursePurchase.purchaseCourse(invoice)
        purchase = self.CoursePurchase.userPurchasedCourse(invoice, self.product)
        self.assertEqual(purchase.user_id.id, self.test_user.id)
        self.assertEqual(purchase.product_id.id, self.product.id)
        _logger.info("✅ test_user_purchased_course passed.")

    def test_full_purchase_course_flow(self):
        result = self.CoursePurchase.purchaseCourceFlow(self.product_template.id, self.test_user)
        self.assertTrue(result)
        self.assertEqual(result[0]['user_id'][0], self.test_user.id)
        self.assertEqual(result[0]['product_id'][0], self.product.id)
        _logger.info("✅ test_full_purchase_course_flow passed.")

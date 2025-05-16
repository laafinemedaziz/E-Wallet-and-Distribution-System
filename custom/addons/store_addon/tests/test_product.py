import logging
from odoo.tests.common import TransactionCase, tagged
from odoo.exceptions import ValidationError
from odoo.tools import mute_logger

_logger = logging.getLogger(__name__)

@tagged('-standard', 'test_clevory_product')
class TestClevoryProduct(TransactionCase):

    def setUp(self):
        super(TestClevoryProduct, self).setUp()
        self.ProductTemplate = self.env['product.template']
        self.ProductProduct = self.env['product.product']
        self.CoursePurchase = self.env['course.purchase']
        self.test_user = self.env['res.users'].create({
            'name': 'Test User',
            'login': 'test_user',
            'email': 'test@example.com',
            'active': True,
        })

    def test_create_new_product(self):
        product_data = {
            'name': 'Test Course',
            'description': 'Test Description',
            'price_lc': 150.0,
            'category': 'Tech'
        }
        product = self.ProductTemplate.createNewProduct(product_data)
        self.assertEqual(product[0]['name'], 'Test Course')
        created_product = self.ProductTemplate.browse(product[0]['id'])
        self.assertEqual(created_product.price_lc, 150.0)
        self.assertEqual(created_product.category, 'Tech')
        _logger.info("✅ test_create_new_product passed.")

    def test_get_all_products(self):
        product_data = {
            'name': 'Test Course',
            'description': 'Test Description',
            'price_lc': 200.0,
            'category': 'Business'
        }
        created = self.ProductTemplate.createNewProduct(product_data)
        tmpl = self.ProductTemplate.browse(created[0]['id'])
        product = self.ProductProduct.search([('product_tmpl_id', '=', tmpl.id)], limit=1)

        self.CoursePurchase.create({
            'product_id': product.id,
            'user_id': self.test_user.id,
        })

        result = tmpl.getAllProducts(self.test_user)
        found = next((p for p in result if p['id'] == product.id), None)
        self.assertIsNotNone(found)
        self.assertEqual(found['is_purchased'], True)
        self.assertEqual(found['price_lc'], 200.0)
        _logger.info("✅ test_get_all_products passed.")

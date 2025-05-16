from odoo.tests.common import TransactionCase, tagged
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)

@tagged('-standard', 'test_fund_wallet')
class TestFundWallet(TransactionCase):

    def setUp(self):
        super().setUp()
        self.currency = self.env.ref('base.TND')
        self.product = self.env.ref('fund_wallet.learning_coin_product')

        # Create a dummy user with partner
        self.user = self.env['res.users'].create({
            'name': 'Test User',
            'login': 'test_user_wallet',
            'email': 'wallet@example.com',
            'password': 'securepassword',
            'active': True,
        })

    def test_create_invoice_success(self):
        result = self.env['account.move'].createInvoice(100, self.user)
        self.assertIn('invoice_id', result)
        self.assertEqual(result['LC_quantity'], 100)
        self.assertEqual(result['user'], self.user.login)
        self.assertEqual(result['currency'], self.currency.name)
        _logger.info("✅ test_create_invoice_success passed.")


    def test_get_invoices(self):
        self.env['account.move'].createInvoice(100, self.user)
        invoices = self.env['account.move'].getInvoices(self.user)
        self.assertTrue(len(invoices) > 0)
        _logger.info("✅ test_get_invoices passed.")

    def test_get_invoice_by_id_success(self):
        invoice_data = self.env['account.move'].createInvoice(50, self.user)
        invoice_id = invoice_data['invoice_id']
        invoice = self.env['account.move'].getInvoiceById(self.user, invoice_id)
        self.assertEqual(invoice['id'], invoice_id)
        self.assertEqual(invoice['payment_state'], 'not_paid')
        _logger.info("✅ test_get_invoice_by_id_success passed.")

    def test_get_invoice_by_id_invalid(self):
        invalid_id = 999999
        result = self.env['account.move'].getInvoiceById(self.user, invalid_id)
        self.assertEqual(result['id'], False)  # since search returns empty recordset
        _logger.info("✅ test_get_invoice_by_id_invalid passed.")

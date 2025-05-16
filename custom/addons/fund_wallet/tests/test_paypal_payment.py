import json
import logging
from odoo.tests.common import TransactionCase, tagged
from unittest.mock import patch, MagicMock
from odoo.exceptions import ValidationError
from odoo.addons.fund_wallet.models.paypal_payment import PaypalPay

_logger = logging.getLogger(__name__)


@tagged('-standard', 'test_paypal_payment')
class TestPaypalPay(TransactionCase):

    def setUp(self):
        super().setUp()
        self.user = self.env['res.users'].create({
            'name': 'Test User',
            'login': 'testuser',
            'email': 'testuser@example.com',
            'active': True,
            'groups_id': [(6, 0, [self.env.ref('base.group_user').id])],
        })
        self.ewallet = self.env['res.ewallet'].create({
            'user_id': self.user.id,
            'balance': 0.0,
        })
        self.user.write({'ewallet_id': self.ewallet.id})
        self.payment_model = self.env['account.payment']
        self.invoice = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.user.partner_id.id,
            'invoice_line_ids': [(0, 0, {
                'product_id': self.env.ref('fund_wallet.learning_coin_product').id,
                'quantity': 1,
                'price_unit': 100.0,
            })]
        })
        self.invoice.action_post()

    @patch('odoo.addons.fund_wallet.models.paypal_payment.requests.post')
    @patch('odoo.addons.fund_wallet.models.paypal_payment.os.getenv')
    def test_get_access_token(self, mock_getenv, mock_post):
        mock_getenv.return_value = json.dumps({
            'CLIENT_ID': 'test_id',
            'CLIENT_SECRET': 'test_secret'
        })
        mock_post.return_value.json.return_value = {
            'access_token': 'fake-token'
        }
        token = self.payment_model._getAccessToken()
        self.assertEqual(token['access_token'], 'fake-token')
        _logger.info("✅ test_get_access_token passed.")

    @patch('odoo.addons.fund_wallet.models.paypal_payment.requests.post')
    @patch('odoo.addons.fund_wallet.models.paypal_payment.PaypalPay._getAccessToken')
    def test_paypal_create_order(self, mock_token, mock_post):
        mock_token.return_value = {'access_token': 'fake-token'}
        mock_post.return_value.json.return_value = {'id': 'fake-order-id'}
        response = self.payment_model.paypalCreateOrder(self.invoice.id)
        self.assertIn('id', response)
        _logger.info("✅ test_paypal_create_order passed.")

    @patch('odoo.addons.fund_wallet.models.paypal_payment.requests.post')
    @patch('odoo.addons.fund_wallet.models.paypal_payment.PaypalPay._getAccessToken')
    @patch('odoo.addons.e_wallet_manager.models.e_wallet.EWallet.fundWallet')
    def test_capture_payment_paypal(self, mock_fund_wallet, mock_token, mock_post):
        mock_token.return_value = {'access_token': 'fake-token'}
        fake_data = {
            'status': 'COMPLETED',
            'purchase_units': [{
                'payments': {
                    'captures': [{
                        'invoice_id': self.invoice.id,
                        'create_time': '2023-01-01T00:00:00Z',
                        'amount': {'value': '100.00'}
                    }]
                }
            }]
        }
        mock_post.return_value.json.return_value = fake_data
        mock_fund_wallet.return_value = True  
        with patch.object(PaypalPay, 'createPaymentRecord', return_value=(True, self.invoice, self.payment_model)), \
             patch.object(PaypalPay, 'sendReceiptEmail', return_value=True):
            self.invoice.payment_state = 'paid'
            result = self.payment_model.capturePaymentPaypal('fake-order-id')
            self.assertEqual(result['status'], 'COMPLETED')
    
        _logger.info("✅ test_capture_payment_paypal passed.")

    def test_order_request_formatter(self):
        data = self.payment_model._orederRequestFormatter(self.invoice)
        self.assertEqual(data['intent'], 'CAPTURE')
        self.assertIn('purchase_units', data)
        _logger.info("✅ test_order_request_formatter passed.")

    def test_create_payment_record_invalid_invoice(self):
        with self.assertRaises(ValidationError):
            self.payment_model.createPaymentRecord({
                'purchase_units': [{
                    'payments': {
                        'captures': [{
                            'invoice_id': 999999,  # invalid
                            'create_time': '2023-01-01T00:00:00Z',
                            'amount': {'value': '100.00'}
                        }]
                    }
                }]
            })
        _logger.info("✅ test_create_payment_record_invalid_invoice passed.")

    def test_get_payments(self):
        payment = self.payment_model.create({
            'journal_id': self.env['account.journal'].search([('type', '=', 'bank')], limit=1).id,
            'payment_method_id': self.env.ref('account.account_payment_method_manual_in').id,
            'amount': 100.0,
            'partner_id': self.user.partner_id.id,
            'payment_type': 'inbound',
            'partner_type': 'customer',
        })
        payments = self.payment_model.getPayments(self.user)
        self.assertTrue(len(payments) >= 1)
        _logger.info("✅ test_get_payments passed.")

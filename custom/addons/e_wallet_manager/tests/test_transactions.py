from odoo.tests.common import TransactionCase, tagged
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)


@tagged('-standard', 'test_transactions')
class TestTransactionModel(TransactionCase):

    def setUp(self):
        super().setUp()
        self.env = self.env(context=dict(self.env.context, test_queue_job_no_delay=True))
        self.user_sender = self.env['res.users'].create({
            'name': 'Sender User',
            'login': 'sender@example.com',
            'active': True,
        })
        self.user_receiver = self.env['res.users'].create({
            'name': 'Receiver User',
            'login': 'receiver@example.com',
            'active': True,
        })
        self.wallet_model = self.env['res.ewallet']
        self.currency = self.env.ref('e_wallet_manager.learning_coins')
        self.sender_wallet = self.wallet_model.create({'user_id': self.user_sender.id})
        self.user_sender.write({'ewallet_id': self.sender_wallet.id})
        self.receiver_wallet = self.wallet_model.create({'user_id': self.user_receiver.id})
        self.user_receiver.write({'ewallet_id': self.receiver_wallet.id})

    def test_record_transfer_success(self):
        transaction_model = self.env['res.transactions']
        success, result = transaction_model.record_transfer(self.sender_wallet, self.receiver_wallet, 100)

        self.assertTrue(success)
        self.assertIn('response', result)
        self.assertEqual(result['transferred_amount'], 100)

        _logger.info("[TEST] ✅ record_transfer_success passed.")

    def test_record_payment_success(self):
        transaction_model = self.env['res.transactions']
        self.user_sender.ewallet_id = self.sender_wallet

        success, result = transaction_model.record_payment(self.user_sender, 150)

        self.assertTrue(success)
        self.assertEqual(result['amount'], 150)

        _logger.info("[TEST] ✅ record_payment_success passed.")

    def test_record_purchase_success(self):
        course = self.env['product.template'].create({
            'name': 'Test Course',
            'list_price': 0.0
        })
        course_obj = self.env['product.product'].create({
            'product_tmpl_id': course.id
        })
        course.price_lc = 50  # Assuming course object has this attr
        self.user_sender.ewallet_id = self.sender_wallet

        transaction_model = self.env['res.transactions']
        success, result = transaction_model.record_purchase(self.user_sender, course_obj)

        self.assertTrue(success)
        self.assertEqual(result['amount'], 50)

        _logger.info("[TEST] ✅ record_purchase_success passed.")

    def test_getTransactions_returns_data(self):
        transaction_model = self.env['res.transactions']
        self.user_sender.ewallet_id = self.sender_wallet
        transaction_model.record_payment(self.user_sender, 20)

        transactions = transaction_model.getTransactions(self.user_sender)
        self.assertTrue(len(transactions) >= 1)
        self.assertEqual(transactions[0]['amount'], 20)

        _logger.info("[TEST] ✅ getTransactions_returns_data passed.")

    def test_getTransfers_returns_data(self):
        transaction_model = self.env['res.transactions']
        self.user_sender.ewallet_id = self.sender_wallet
        self.user_receiver.ewallet_id = self.receiver_wallet

        transaction_model.record_transfer(self.sender_wallet, self.receiver_wallet, 30)
        transfers = transaction_model.getTransfers(self.user_sender)

        self.assertTrue(len(transfers) >= 1)
        self.assertEqual(transfers[0]['amount'], 30)

        _logger.info("[TEST] ✅ getTransfers_returns_data passed.")

    def test_getCSVReport_structure(self):
        transaction_model = self.env['res.transactions']
        self.user_sender.ewallet_id = self.sender_wallet
        transaction_model.record_payment(self.user_sender, 20)

        csv_data = transaction_model.getCSVReport(self.user_sender)
        self.assertIn("Transaction ID", csv_data)
        self.assertIn("Amount", csv_data)

        _logger.info("[TEST] ✅ getCSVReport_structure passed.")

    def test_getPDFReport_structure(self):
        transaction_model = self.env['res.transactions']
        self.user_sender.ewallet_id = self.sender_wallet
        transaction_model.record_payment(self.user_sender, 20)

        pdf_data = transaction_model.getPDFReport(self.user_sender)
        self.assertTrue(pdf_data.getvalue().startswith(b'%PDF'))

        _logger.info("[TEST] ✅ getPDFReport_structure passed.")

    def test_transfer_constraint_validation_error(self):
        with self.assertRaises(ValidationError):
            self.env['res.transactions'].create({
                'user_id': self.user_sender.id,
                'category': 'transfer',  # missing one or both wallets
                'currency_id': self.currency.id
            })

        _logger.info("[TEST] ✅ transfer_constraint_validation_error passed.")

    def test_purchase_constraint_validation_error(self):
        with self.assertRaises(ValidationError):
            self.env['res.transactions'].create({
                'user_id': self.user_sender.id,
                'category': 'purchase',
                'receiver_wallet_id': self.receiver_wallet.id,  # invalid: should be sender only
                'currency_id': self.currency.id
            })

        _logger.info("[TEST] ✅ purchase_constraint_validation_error passed.")

    def test_payment_constraint_validation_error(self):
        with self.assertRaises(ValidationError):
            self.env['res.transactions'].create({
                'user_id': self.user_sender.id,
                'category': 'payment',
                'sender_wallet_id': self.sender_wallet.id,  # invalid: should be receiver only
                'currency_id': self.currency.id
            })

        _logger.info("[TEST] ✅ payment_constraint_validation_error passed.")

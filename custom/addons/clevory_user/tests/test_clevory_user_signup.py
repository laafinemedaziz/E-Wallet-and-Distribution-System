from odoo.tests.common import TransactionCase, tagged
from odoo.exceptions import ValidationError

@tagged('-standard', 'test_signup')
class TestClevoryUserSignup(TransactionCase):

    def setUp(self):
        super().setUp()
        # Create a dummy company with a unique company_code
        self.company = self.env['res.partner'].create({
            'name': 'Test Company',
            'is_company': True,
            'company_code': 'TEST123',
        })

    def test_successful_learner_signup(self):
        vals = {
            'name': 'John Doe',
            'login': 'john_learner',
            'email': 'john@example.com',
            'password': 'securepassword',
            'type': 'learner',
            'companyCode': ''
        }
        user = self.env['res.users'].sign_up_user(vals)
        self.assertEqual(user[0]['login'], 'john_learner')
        print("✅ test_successful_learner_signup passed")

    def test_successful_employee_signup(self):
        vals = {
            'name': 'Alice Smith',
            'login': 'alice_employee',
            'email': 'alice@example.com',
            'password': 'securepassword',
            'type': 'employee',
            'companyCode': 'TEST123'
        }
        user = self.env['res.users'].sign_up_user(vals)
        self.assertEqual(user[0]['login'], 'alice_employee')
        print("✅ test_successful_employee_signup passed")

    def test_missing_required_fields(self):
        vals = {
            'name': 'Missing Email',
            'login': 'missing_email',
            # 'email' intentionally left out
            'password': 'password',
            'type': 'learner',
            'companyCode': ''
        }
        with self.assertRaises(ValidationError):
            self.env['res.users'].sign_up_user(vals)
        print("✅ test_missing_required_fields passed")

    def test_learner_with_company_should_fail(self):
        vals = {
            'name': 'Learner With Company',
            'login': 'learner_with_company',
            'email': 'learner@company.com',
            'password': 'password',
            'type': 'learner',
            'companyCode': 'TEST123'
        }
        with self.assertRaises(ValidationError):
            self.env['res.users'].sign_up_user(vals)
        print("✅ test_learner_with_company_should_fail passed")

    def test_employee_with_invalid_company_should_fail(self):
        vals = {
            'name': 'Invalid Company',
            'login': 'invalid_company',
            'email': 'invalid@company.com',
            'password': 'password',
            'type': 'employee',
            'companyCode': 'DOESNOTEXIST'
        }
        with self.assertRaises(ValidationError):
            self.env['res.users'].sign_up_user(vals)
        print("✅ test_employee_with_invalid_company_should_fail passed")

    def test_hr_with_existing_hr_should_fail(self):
        # First HR
        self.env['res.users'].sign_up_user({
            'name': 'HR One',
            'login': 'hr1',
            'email': 'hr1@company.com',
            'password': 'password',
            'type': 'hr',
            'companyCode': 'TEST123'
        })
        # Second HR for the same company
        with self.assertRaises(ValidationError):
            self.env['res.users'].sign_up_user({
                'name': 'HR Two',
                'login': 'hr2',
                'email': 'hr2@company.com',
                'password': 'password',
                'type': 'hr',
                'companyCode': 'TEST123'
            })
        print("✅ test_hr_with_existing_hr_should_fail passed")

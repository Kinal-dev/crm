# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo.addons.payment.tests.common import PaymentCommon


class BuckarooCommon(PaymentCommon):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.buckaroo = cls._prepare_acquirer('buckaroo', update_values={
            'buckaroo_website_key': 'dummy',
            'buckaroo_secret_key': 'dummy',
        })

        # Override defaults
        cls.acquirer = cls.buckaroo
        cls.currency = cls.currency_euro

# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging

from odoo import _, fields, models

_logger = logging.getLogger(__name__)


class PaymentAcquirer(models.Model):
    _inherit = 'payment.acquirer'

    provider = fields.Selection(
        selection_add=[('paypal', "Paypal")], ondelete={'paypal': 'set default'})
    paypal_email_account = fields.Char(
        string="Email",
        help="The public business email solely used to identify the account with PayPal",
        required_if_provider='paypal')
    paypal_seller_account = fields.Char(
        string="Merchant Account ID", groups='base.group_system')
    paypal_pdt_token = fields.Char(string="PDT Identity Token", groups='base.group_system')
    paypal_use_ipn = fields.Boolean(
        string="Use IPN", help="Paypal Instant Payment Notification", default=True)

    def _paypal_get_api_url(self):
        """ Return the API URL according to the acquirer state.

        Note: self.ensure_one()

        :return: The API URL
        :rtype: str
        """
        self.ensure_one()

        if self.state == 'enabled':
            return 'https://www.paypal.com/cgi-bin/webscr'
        else:
            return 'https://www.sandbox.paypal.com/cgi-bin/webscr'

    def _paypal_send_configuration_reminder(self):
        template = self.env.ref(
            'payment_paypal.mail_template_paypal_invite_user_to_configure', raise_if_not_found=False
        )
        if template:
            render_template = template._render({'acquirer': self}, engine='ir.qweb')
            mail_body = self.env['mail.render.mixin']._replace_local_links(render_template)
            mail_values = {
                'body_html': mail_body,
                'subject': _("Add your PayPal account to Odoo"),
                'email_to': self.paypal_email_account,
                'email_from': self.create_uid.email_formatted,
                'author_id': self.create_uid.partner_id.id,
            }
            self.env['mail.mail'].sudo().create(mail_values).send()

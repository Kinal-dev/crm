# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import psycopg2

from odoo import api
from odoo.addons.base.models.ir_mail_server import MailDeliveryException
from odoo.addons.test_mail.tests.common import TestMailCommon
from odoo.tests import common
from odoo.tools import mute_logger


class TestMailMail(TestMailCommon):

    @mute_logger('odoo.addons.mail.models.mail_mail')
    def test_mail_message_notify_from_mail_mail(self):
        # Due ot post-commit hooks, store send emails in every step
        mail = self.env['mail.mail'].sudo().create({
            'body_html': '<p>Test</p>',
            'email_to': 'test@example.com',
            'partner_ids': [(4, self.user_employee.partner_id.id)]
        })
        with self.mock_mail_gateway():
            mail.send()
        self.assertSentEmail(mail.env.user.partner_id, ['test@example.com'])
        self.assertEqual(len(self._mails), 1)


class TestMailMailRace(common.TransactionCase):

    @mute_logger('odoo.addons.mail.models.mail_mail')
    def test_mail_bounce_during_send(self):
        self.partner = self.env['res.partner'].create({
            'name': 'Ernest Partner',
        })
        # we need to simulate a mail sent by the cron task, first create mail, message and notification by hand
        mail = self.env['mail.mail'].sudo().create({
            'body_html': '<p>Test</p>',
            'notification': True,
            'state': 'outgoing',
            'recipient_ids': [(4, self.partner.id)]
        })
        message = self.env['mail.message'].create({
            'subject': 'S',
            'body': 'B',
            'subtype_id': self.ref('mail.mt_comment'),
            'notification_ids': [(0, 0, {
                'res_partner_id': self.partner.id,
                'mail_id': mail.id,
                'notification_type': 'email',
                'is_read': True,
                'notification_status': 'ready',
            })],
        })
        notif = self.env['mail.notification'].search([('res_partner_id', '=', self.partner.id)])
        # we need to commit transaction or cr will keep the lock on notif
        self.cr.commit()

        # patch send_email in order to create a concurent update and check the notif is already locked by _send()
        this = self  # coding in javascript ruinned my life
        bounce_deferred = []
        @api.model
        def send_email(self, message, *args, **kwargs):
            with this.registry.cursor() as cr, mute_logger('odoo.sql_db'):
                try:
                    # try ro aquire lock (no wait) on notification (should fail)
                    cr.execute("SELECT notification_status FROM mail_notification WHERE id = %s FOR UPDATE NOWAIT", [notif.id])
                except psycopg2.OperationalError:
                    # record already locked by send, all good
                    bounce_deferred.append(True)
                else:
                    # this should trigger psycopg2.extensions.TransactionRollbackError in send().
                    # Only here to simulate the initial use case
                    # If the record is lock, this line would create a deadlock since we are in the same thread
                    # In practice, the update will wait the end of the send() transaction and set the notif as bounce, as expeced
                    cr.execute("UPDATE mail_notification SET notification_status='bounce' WHERE id = %s", [notif.id])
            return message['Message-Id']
        self.env['ir.mail_server']._patch_method('send_email', send_email)

        mail.send()

        self.assertTrue(bounce_deferred, "The bounce should have been deferred")
        self.assertEqual(notif.notification_status, 'sent')

        # some cleaning since we commited the cr
        self.env['ir.mail_server']._revert_method('send_email')

        notif.unlink()
        message.unlink()
        mail.unlink()
        self.partner.unlink()
        self.env.cr.commit()

        # because we committed the cursor, the savepoint of the test method is
        # gone, and this would break TransactionCase cleanups
        self.cr.execute('SAVEPOINT test_%d' % self._savepoint_id)

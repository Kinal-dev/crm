# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'POS Adyen',
    'version': '1.0',
    'category': 'Sales/Point of Sale',
    'sequence': 6,
    'summary': 'Integrate your POS with an Adyen payment terminal',
    'description': '',
    'data': [
        'security/ir.model.access.csv',
        'views/adyen_account_views.xml',
        'views/pos_config_views.xml',
        'views/pos_payment_method_views.xml',
        'views/res_config_settings_views.xml',
    ],
    'depends': ['adyen_platforms', 'point_of_sale'],
    'installable': True,
    'assets': {
        'point_of_sale.assets': [
            'pos_adyen/static/**/*',
        ],
    }
}

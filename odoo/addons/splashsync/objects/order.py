#
#  This file is part of SplashSync Project.
#
#  Copyright (C) 2015-2020 Splash Sync  <www.splashsync.com>
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
#
#  For the full copyright and license information, please view the LICENSE
#  file that was distributed with this source code.
#

from . import OdooObject
from splashpy import const
from .orders import Orderlines


class Order(OdooObject, Orderlines):
    # ====================================================================#
    # Splash Object Definition
    name = "Order"
    desc = "Odoo Order"
    icon = "fa fa-shopping-cart"

    @staticmethod
    def getDomain():
            return 'sale.order'

    @staticmethod
    def get_listed_fields():
        """Get List of Object Fields to Include in Lists"""
        return ['name', 'display_name', 'client_order_ref', 'id']

    @staticmethod
    def get_required_fields():
        """Get List of Object Fields to Include in Lists"""
        return [
            # 'name', 'date_order', 'currency_id',
            # 'partner_id', 'partner_invoice_id', 'partner_shipping_id',
            # 'pricelist_id', 'warehouse_id', 'picking_policy'
            'company_id', 'currency_id', 'journal_id'
                ]

    @staticmethod
    def get_configuration():
        """Get Hash of Fields Overrides"""
        return {
                "name": {"group": "General", "itemtype": "http://schema.org/Invoice", "itemprop": "name"},
                "state": {"group": "General", "itemtype": "http://schema.org/Invoice", "itemprop": "paymentStatus"},

                "description": {"group": "General", "itemtype": "http://schema.org/Invoice", "itemprop": "description"},
                "date_due": {"group": "General", "itemtype": "http://schema.org/Invoice", "itemprop": "paymentDueDate"},
                "date_invoice": {"group": "General", "itemtype": "http://schema.org/Invoice", "itemprop": "dateCreated"},
                "reference": {"group": "General", "itemtype": "http://schema.org/Invoice", "itemprop": "confirmationNumber"},

                "create_date": {"group": "Meta", "itemtype": "http://schema.org/DataFeedItem", "itemprop": "dateCreated"},
                "__last_update": {"group": "Meta", "itemtype": "http://schema.org/DataFeedItem", "itemprop": "dateModified"},

                # "account.invoice.line[invoice_id]": {"group": "General", "itemtype": "http://schema.org/Invoice", "itemprop": "name"},

                "activity_summary": {"write": False},

                "write_date": {"group": "Meta", "itemtype": "http://schema.org/DataFeedItem", "itemprop": "dateModified"},

         }

    # ====================================================================#
    # Object CRUD
    # ====================================================================#

    def create(self):
        """Create a New Order"""
        # ====================================================================#
        # Init List of required Fields
        reqFields = self.collectRequiredCoreFields()
        if reqFields is False:
            return False

        # ====================================================================#
        # TODO FOR DEV
        reqFields["partner_id"] = 11
        # ====================================================================#
        # Create a New Simple Order
        return self.getModel().create(reqFields)
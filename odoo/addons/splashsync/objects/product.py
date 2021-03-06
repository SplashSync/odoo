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
from .products import ProductsVariants, ProductsAttributes, ProductsPrices, ProductsImages
from .products import ProductsFeatures, ProductsRelations, ProductsSupplier, ProductsInventory


class Product(
    OdooObject,
    ProductsAttributes,
    ProductsVariants,
    ProductsPrices,
    ProductsImages,
    ProductsFeatures,
    ProductsRelations,
    ProductsSupplier,
    ProductsInventory
):
    # ====================================================================#
    # Splash Object Definition
    name = "Product"
    desc = "Odoo Product"
    icon = "fa fa-product-hunt"

    template = None

    @staticmethod
    def getDomain():
        return 'product.product'

    @staticmethod
    def get_listed_fields():
        """Get List of Object Fields to Include in Lists"""
        return ['code', 'name', 'qty_available', 'list_price']

    @staticmethod
    def get_required_fields():
        """Get List of Object Fields to Include in Lists"""
        return ['name']

    @staticmethod
    def get_composite_fields():
        """Get List of Fields NOT To Parse Automaticaly """
        return [
            "id", "valuation", "cost_method", "tracking",
            "image", "image_small", "image_medium", "image_variant",
            "rating_last_image", "rating_last_feedback", "sale_line_warn",
            "message_unread_counter", "purchase_line_warn",
            "price", "lst_price", "list_price", "price_extra", "variant_price_extra", "standard_price",
            "service_to_purchase", "qty_available"
        ]

    @staticmethod
    def get_configuration():
        """Get Hash of Fields Overrides"""
        return {
            "default_code": {"group": "", "itemtype": "http://schema.org/Product", "itemprop": "model"},
            "name": {"group": "", "itemtype": "http://schema.org/Product", "itemprop": "name"},
            "description": {"group": "", "itemtype": "http://schema.org/Product", "itemprop": "description"},

            "active": {"group": "", "itemtype": "http://schema.org/Product", "itemprop": "active", "notest": True},
            "sale_ok": {"group": "", "itemtype": "http://schema.org/Product", "itemprop": "offered"},
            "purchase_ok": {"group": "", "itemtype": "http://schema.org/Product", "itemprop": "ordered"},

            "qty_at_date": {"group": ""},
            "virtual_available": {"group": ""},
            "outgoing_qty	": {"group": ""},
            "incoming_qty": {"group": ""},

            "website_url": {"type": const.__SPL_T_URL__, "itemtype": "http://schema.org/Product", "itemprop": "urlRewrite"},
            "activity_summary": {"write": False},
            "image": {"group": "", "notest": True},

            "type": {"group": "", "required": False, "itemtype": "http://schema.org/Product", "itemprop": "odooType"},

            "create_date": {"group": "Meta", "itemtype": "http://schema.org/DataFeedItem", "itemprop": "dateCreated"},
            "write_date": {"group": "Meta", "itemtype": "http://schema.org/DataFeedItem", "itemprop": "dateModified"},
        }

    # ====================================================================#
    # Object CRUD
    # ====================================================================#

    def create(self):
        """Create a New Product with Variants Detection"""
        # ====================================================================#
        # Order Fields Inputs
        self.order_inputs()
        # ====================================================================#
        # Ensure default type
        if "type" not in self._in:
            self._in['type'] = 'product'
        # ====================================================================#
        # Init List of required Fields
        reqFields = self.collectRequiredCoreFields()
        if reqFields is False:
            return False
        # ====================================================================#
        # Create a New Variable Product
        if self.is_new_variable_product():
            # ====================================================================#
            # Detect Product Variant Template
            template_id = self.detect_variant_template()
            if template_id is not None:
                reqFields["product_tmpl_id"] = template_id
        # ====================================================================#
        # Create Product
        new_product = self.getModel().with_context(create_product_product=True).create(reqFields)
        if new_product is None:
            return False
        # ====================================================================#
        # Load Product Template
        for template in new_product.product_tmpl_id:
            self.template = template.with_context(create_product_product=True)
            break

        return new_product

    def load(self, object_id):
        """Load Odoo Object by Id"""
        from odoo.exceptions import MissingError
        # ====================================================================#
        # Order Fields Inputs
        self.order_inputs()
        try:
            # ====================================================================#
            # Load Product Variant
            model = self.getModel().browse([int(object_id)])
            if len(model) != 1:
                return False
            # ====================================================================#
            # Load Product Template
            for template in model.product_tmpl_id:
                self.template = template
                break
        except Exception:
            from splashpy import Framework
            Framework.log().warn("Unable to Load Odoo Product " + str(object_id))
            return False
        except MissingError:
            return False

        return model

    def delete(self, object_id):
        """Delete Odoo Product with Id"""
        # ====================================================================
        # DEBUG MODE - Delete All Connected Tests Transactions
        from odoo.addons.splashsync.helpers import InventoryHelper
        InventoryHelper.unlink_all_inventory_adjustment(object_id)
        # ====================================================================#
        # Execute Normal Delete
        return super(Product, self).delete(object_id)

# -*- coding: utf-8 -*-
#
#  This file is part of SplashSync Project.
#
#  Copyright (C) 2015-2019 Splash Sync  <www.splashsync.com>
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
#
#  For the full copyright and license information, please view the LICENSE
#  file that was distributed with this source code.
#

from odoo import http
from splashpy.helpers import PricesHelper, ObjectsHelper
from splashpy import Framework


class OrderLinesHelper:
    """Collection of Static Functions to manage Order & Invoices Lines content"""

    __generic_fields = [
        'name', 'state', 'customer_lead', 'discount',
        'product_uom_qty', 'qty_delivered_manual', 'qty_invoiced', 'quantity'
    ]

    __qty_fields = [
        'product_uom_qty', 'qty_delivered_manual', 'qty_invoiced', 'quantity'
    ]

    # ====================================================================#
    # Order & Invoice Line Management
    # ====================================================================#

    @staticmethod
    def get_values(lines, field_id):
        """
        Get List of Lines Values for given Field

        :param lines: recordset
        :param field_id: str
        :return: dict
        """
        values = []
        # ====================================================================#
        # Walk on Lines
        for order_line in lines.filtered(lambda r: r.display_type is False):
            # ====================================================================#
            # Check Line is Not a Comment Line
            if OrderLinesHelper.is_comment(order_line):
                continue
            # ====================================================================#
            # Collect Values
            values += [OrderLinesHelper.__get_raw_values(order_line, field_id)]

        return values

    @staticmethod
    def set_values(line, line_data):
        """
        Set values of Order Line

        :param line: sale.order.line
        :param line_data: dict
        :rtype: bool
        """
        # ====================================================================#
        # Walk on Data to Update
        for field_id, field_data in line_data.items():
            try:
                # ====================================================================#
                # Update Order Line data
                OrderLinesHelper.__set_raw_value(line, field_id, field_data)
            except Exception as ex:
                # ====================================================================#
                # Update Failed => Line may be protected
                return Framework.log().error(ex)

        return True

    @staticmethod
    def complete_values(line_data):
        """
        Complete Order Line values with computed Information
        - Detect Product ID based on Line Name


        :param line_data: dict
        :rtype: dict
        """
        from odoo.addons.splashsync.helpers import M2OHelper

        # ====================================================================#
        # Detect Wrong or Empty Product ID
        # ====================================================================#
        try:
            if not M2OHelper.verify_id(ObjectsHelper.id(line_data["product_id"]), 'product.product'):
                raise Exception("Invalid Product ID")
        except Exception:
            # ====================================================================#
            # Try detection based on Line Description
            try:
                product_id = M2OHelper.verify_name(line_data["name"], 'default_code', 'product.product')
                if int(product_id) > 0:
                    line_data["product_id"] = ObjectsHelper.encode("Product", str(product_id))
            except Exception:
                pass

        return line_data


    # ====================================================================#
    # RAW Order & Invoice Line Management
    # ====================================================================#

    @staticmethod
    def __get_raw_values(line, field_id):
        """
        Line Single Value for given Field

        :param line: sale.order.line
        :param field_id: str
        :return: dict
        """

        from odoo.addons.splashsync.helpers import CurrencyHelper, TaxHelper, SettingsManager, M2MHelper

        # ==================================================================== #
        # [CORE] Order Line Fields
        # ==================================================================== #

        # ==================================================================== #
        # Linked Product ID
        if field_id == "product_id":
            try:
                return ObjectsHelper.encode("Product", str(line.product_id[0].id))
            except:
                return None
        # ==================================================================== #
        # Description
        # Qty Ordered | Qty Shipped/Delivered | Qty Invoiced
        # Delivery Lead Time | Line Status
        # Line Unit Price Reduction (Percent)
        if field_id in OrderLinesHelper.__generic_fields:
            if field_id in OrderLinesHelper.__qty_fields:
                return int(getattr(line, field_id))
            return getattr(line, field_id)
        # ==================================================================== #
        # Line Unit Price (HT)
        if field_id == "price_unit":
            return PricesHelper.encode(
                float(line.price_unit),
                TaxHelper.get_tax_rate(
                    line.tax_id if OrderLinesHelper.is_order_line(line) else line.invoice_line_tax_ids,
                    'sale'
                ),
                None,
                CurrencyHelper.get_main_currency_code()
            )

        # ==================================================================== #
        # Sales Taxes
        if field_id == "tax_name":
            try:
                tax_ids = line.tax_id if OrderLinesHelper.is_order_line(line) else line.invoice_line_tax_ids
                return tax_ids[0].name
            except:
                return None
        if field_id == "tax_names":
            return M2MHelper.get_names(
                line,
                "tax_id" if OrderLinesHelper.is_order_line(line) else "invoice_line_tax_ids"
            )

        # ==================================================================== #
        # [EXTRA] Order Line Fields
        # ==================================================================== #

        # ==================================================================== #
        # Product reference
        if field_id == "product_ref":
            try:
                return str(line.product_id[0].default_code)
            except:
                return None

        return None

    @staticmethod
    def __set_raw_value(line, field_id, field_data):
        """
        Set simple value of Order Line

        :param line: sale.order.line
        :param field_id: str
        :param field_data: mixed
        """

        from odoo.addons.splashsync.helpers import TaxHelper, SettingsManager, M2MHelper
        tax_field_id = "tax_id" if OrderLinesHelper.is_order_line(line) else "invoice_line_tax_ids"

        # ==================================================================== #
        # [CORE] Order Line Fields
        # ==================================================================== #

        # ==================================================================== #
        # Linked Product ID
        if field_id == "product_id" and isinstance(ObjectsHelper.id(field_data), (int, str)):
            line.product_id = int(ObjectsHelper.id(field_data))
        # ==================================================================== #
        # Description
        # Qty Ordered | Qty Shipped/Delivered | Qty Invoiced
        # Delivery Lead Time | Line Status
        # Line Unit Price Reduction (Percent)
        if field_id in OrderLinesHelper.__generic_fields:
            setattr(line, field_id, field_data)
        # ==================================================================== #
        # Line Unit Price (HT)
        if field_id == "price_unit":
            line.price_unit = PricesHelper.extract(field_data, "ht")
            if not SettingsManager.is_sales_adv_taxes():
                setattr(
                    line,
                    tax_field_id,
                    TaxHelper.find_by_rate(PricesHelper.extract(field_data, "vat"), 'sale')
                )
        # ==================================================================== #
        # Sales Taxes
        if field_id == "tax_name" and SettingsManager.is_sales_adv_taxes():
            field_data = '["'+field_data+'"]' if isinstance(field_data, str) else "[]"
            M2MHelper.set_names(
                line, tax_field_id, field_data,
                domain=TaxHelper.tax_domain, filters=[("type_tax_use", "=", 'sale')]
            )
        if field_id == "tax_names" and SettingsManager.is_sales_adv_taxes():
            M2MHelper.set_names(
                line, tax_field_id, field_data,
                domain=TaxHelper.tax_domain, filters=[("type_tax_use", "=", 'sale')]
            )

        # ==================================================================== #
        # [EXTRA] Order Line Fields
        # ==================================================================== #

        return True

    @staticmethod
    def is_comment(line):
        """
        Check if Order Line is Section or Note
        :param line: sale.order.line|account.invoice.line
        :return: bool
        """
        return line.display_type is not False

    @staticmethod
    def is_order_line(order_line):
        """
        Check if Line is Order Line (or Invoice Line)

        :param order_line: sale.order.line|account.invoice.line
        :return: bool
        """
        return getattr(order_line, "_name") == "sale.order.line"

    # ====================================================================#
    # Order Specific Methods
    # ====================================================================#

    @staticmethod
    def add_order_line(order, line_data):
        """
        Add a New Line to an Order
        :param order: sale.order
        :return: sale.order.line
        """
        # ====================================================================#
        # Prepare Minimal Order Line Data
        req_fields = {
            "order_id": order.id,
            "sequence": 10 + len(order.order_line),
            "qty_delivered_method": 'manual',
        }
        # ====================================================================#
        # Link to Product
        try:
            req_fields["product_id"] = int(ObjectsHelper.id(line_data["product_id"]))
        except:
            Framework.log().error("Unable to create Order Line, Product Id is Missing")
            return None
        # ==================================================================== #
        # Description
        # Qty Ordered | Qty Shipped/Delivered | Qty Invoiced
        # Delivery Lead Time | Line Status
        for field_id in OrderLinesHelper.__generic_fields:
            try:
                req_fields[field_id] = line_data[field_id]
            except:
                pass
        # ====================================================================#
        # Unit Price
        try:
            req_fields["price_unit"] = PricesHelper.extract(line_data["price_unit"], "ht")
        except:
            pass
        # ====================================================================#
        # Create Order Line
        try:
            return http.request.env["sale.order.line"].create(req_fields)
        except Exception as exception:
            Framework.log().error("Unable to create Order Line, please check inputs.")
            Framework.log().fromException(exception, False)
            Framework.log().dump(req_fields, "New Order Line")
            return None

    # ====================================================================#
    # Invoice Specific Methods
    # ====================================================================#

    @staticmethod
    def add_invoice_line(invoice, line_data):
        """
        Add a New Line to an Invoice

        :param invoice: account.invoice
        :param line_data: dict
        :return: account.invoice.line
        """
        # ====================================================================#
        # Load Account Id from Configuration
        account_id = OrderLinesHelper.detect_sales_account_id(invoice)
        # ====================================================================#
        # Safety Check
        if account_id is None or int(account_id) <= 0:
            Framework.log().error("Unable to detect Account Id, Add Invoice Line skipped.")
            Framework.log().error("Please check your configuration.")
            return None
        # ====================================================================#
        # Prepare Minimal Order Line Data
        req_fields = {
            "invoice_id": invoice.id,
            "account_id": account_id,
            "sequence": 10 + len(invoice.invoice_line_ids),
        }
        # ====================================================================#
        # Link to Product
        try:
            req_fields["product_id"] = int(ObjectsHelper.id(line_data["product_id"]))
        except:
            pass
        # ==================================================================== #
        # Description
        # Qty Invoiced
        for field_id in OrderLinesHelper.__generic_fields:
            try:
                req_fields[field_id] = line_data[field_id]
            except:
                pass
        # ====================================================================#
        # Unit Price
        try:
            req_fields["price_unit"] = PricesHelper.extract(line_data["price_unit"], "ht")
        except:
            pass
        # ====================================================================#
        # Create Order Line
        try:
            return http.request.env["account.invoice.line"].create(req_fields)
        except Exception as exception:
            Framework.log().error("Unable to create Invoice Line, please check inputs.")
            Framework.log().fromException(exception, False)
            Framework.log().dump(req_fields, "New Invoice Line")
            return None

    @staticmethod
    def detect_sales_account_id(invoice):
        """
        Detect Account id for NEW Invoices Lines

        :param invoice: account.invoice
        :return: account.invoice.line
        """
        from odoo.addons.splashsync.helpers import SettingsManager
        # ====================================================================#
        # Load Account Id from Configuration
        try:
            account_id = SettingsManager.get_sales_account_id()
            # ====================================================================#
            # FallBack to Demo Account Id
            if account_id is None or int(account_id) <= 0:
                account_id = invoice.account_id._name_search("200000 Product Sales")[0][0]
            return account_id
        except:
            return None

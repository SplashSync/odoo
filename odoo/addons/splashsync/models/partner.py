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


from odoo import api, models, fields
from splashpy import const


class Partner(models.Model):
    """Override for Odoo Partners to Make it Work with Splash"""
    _inherit = 'res.partner'

    @api.model
    def create(self, vals):
        res = super(Partner, self).create(vals)

        # ====================================================================#
        # Execute Splash Commit
        self.__do_splash_commit(const.__SPL_A_CREATE__)

        return res

    def write(self, vals):
        res = super(Partner, self).write(vals)

        # ====================================================================#
        # Execute Splash Commit
        self.__do_splash_commit(const.__SPL_A_UPDATE__)

        return res

    def unlink(self):
        # ====================================================================#
        # Execute Splash Commit
        self.__do_splash_commit(const.__SPL_A_DELETE__)

        res = super(Partner, self).unlink()

        return res

    def __do_splash_commit(self, action):
        """
        Execute Splash Commit for this ThirdParty or Address

        :param action: str
        :rtype: void
        """
        # ====================================================================#
        # Check if Splash Commit is Allowed
        from odoo.addons.splashsync.helpers import SettingsManager
        if SettingsManager.is_no_commits():
            return
        # ====================================================================#
        # Import Required Classes
        from odoo.addons.splashsync.helpers.objects.partners import PartnersHelper
        from odoo.addons.splashsync.client import OdooClient
        for partner in self:
            # ====================================================================#
            # Object is a ThirdParty
            if PartnersHelper.is_thirdparty(partner):
                from odoo.addons.splashsync.objects import ThirdParty
                OdooClient.commit(ThirdParty(), action, str(partner.id))
                return
            # ====================================================================#
            # Object is an Address
            if PartnersHelper.is_address(partner):
                from odoo.addons.splashsync.objects import Address
                OdooClient.commit(Address(), action, str(partner.id))
                return
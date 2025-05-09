#
# Copyright (C) 2019  Red Hat, Inc.
#
# This copyrighted material is made available to anyone wishing to use,
# modify, copy, or redistribute it subject to the terms and conditions of
# the GNU General Public License v.2, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY expressed or implied, including the implied warranties of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General
# Public License for more details.  You should have received a copy of the
# GNU General Public License along with this program; if not, write to the
# Free Software Foundation, Inc., 31 Milk Street #960789 Boston, MA
# 02196 USA.  Any Red Hat trademarks that are incorporated in the
# source code or documentation are not subject to the GNU General Public
# License and may only be used or replicated with the express permission of
# Red Hat, Inc.
#
# Red Hat Author(s): Vendula Poncova <vponcova@redhat.com>
#
import unittest
from unittest.mock import Mock, patch

import pytest

from pyanaconda.core.configuration.anaconda import conf
from pyanaconda.modules.common.errors.configuration import StorageDiscoveryError
from pyanaconda.modules.storage.fcoe import FCOEModule
from pyanaconda.modules.storage.fcoe.discover import FCOEDiscoverTask
from pyanaconda.modules.storage.fcoe.fcoe_interface import FCOEInterface
from tests.unit_tests.pyanaconda_tests import (
    check_task_creation,
    patch_dbus_publish_object,
)


class FCOEInterfaceTestCase(unittest.TestCase):
    """Test DBus interface of the FCoE module."""

    def setUp(self):
        """Set up the module."""
        self.fcoe_module = FCOEModule()
        self.fcoe_interface = FCOEInterface(self.fcoe_module)

    @patch("pyanaconda.modules.storage.fcoe.fcoe.has_fcoe", return_value=True)
    def test_is_supported(self, is_supported):
        assert self.fcoe_interface.IsSupported() is True

    def test_get_nics(self):
        """Test the get nics method."""
        assert self.fcoe_interface.GetNics() == []

    @patch('pyanaconda.modules.storage.fcoe.fcoe.fcoe')
    def test_get_dracut_arguments(self, fcoe):
        """Test the get dracut arguments method."""
        # no nics / added FCoE targets
        assert self.fcoe_interface.GetDracutArguments("eth0") == []

        nics_mock = Mock()
        nics_mock.nics = [
            ("eth0", True, True),
            ("eth1", True, True),
            ("eth1", True, False),
            ("eth2", False, True),
        ]
        nics_mock.added_nics = ["eth1", "eth2"]
        fcoe.return_value = nics_mock

        # FCoE added from EDD
        assert self.fcoe_interface.GetDracutArguments("eth0") == \
            ["fcoe=edd:dcb"]
        # FCoE added manually (ks or ui), dcb
        assert self.fcoe_interface.GetDracutArguments("eth1") == \
            ["fcoe=eth1:dcb"]
        # FCoE added manually (ks or ui), dcb, no autovlan
        assert self.fcoe_interface.GetDracutArguments("eth1") == \
            ["fcoe=eth1:dcb"]
        # FCoE added manually (ks or ui), no dcb
        assert self.fcoe_interface.GetDracutArguments("eth2") == \
            ["fcoe=eth2:nodcb"]

    @patch_dbus_publish_object
    def test_discover_with_task(self, publisher):
        """Test the discover task."""
        task_path = self.fcoe_interface.DiscoverWithTask(
            "eth0",  # nic
            False,  # dcb
            True  # auto_vlan
        )

        obj = check_task_creation(task_path, publisher, FCOEDiscoverTask)

        assert obj.implementation._nic == "eth0"
        assert obj.implementation._dcb is False
        assert obj.implementation._auto_vlan is True

    @patch('pyanaconda.modules.storage.fcoe.fcoe.fcoe')
    def test_write_configuration(self, fcoe):
        """Test WriteConfiguration."""
        self.fcoe_interface.WriteConfiguration()
        fcoe.write.assert_called_once_with(conf.target.system_root)


class FCOETasksTestCase(unittest.TestCase):
    """Test FCoE tasks."""

    @patch('pyanaconda.modules.storage.fcoe.discover.fcoe')
    def test_discovery_fails(self, fcoe):
        """Test the failing discovery task."""
        fcoe.add_san.return_value = "Fake error message"

        with pytest.raises(StorageDiscoveryError) as cm:
            FCOEDiscoverTask(nic="eth0", dcb=False, auto_vlan=True).run()

        assert str(cm.value) == "Fake error message"

    @patch('pyanaconda.modules.storage.fcoe.discover.fcoe')
    def test_discovery(self, fcoe):
        """Test the discovery task."""
        fcoe.add_san.return_value = ""

        FCOEDiscoverTask(nic="eth0", dcb=False, auto_vlan=True).run()

        fcoe.add_san.assert_called_once_with("eth0", False, True)
        fcoe.added_nics.append.assert_called_once_with("eth0")

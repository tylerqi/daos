#!/usr/bin/python
"""
(C) Copyright 2018-2022 Intel Corporation.

SPDX-License-Identifier: BSD-2-Clause-Patent
"""

from ior_test_base import IorTestBase


class IorHdf5(IorTestBase):
    # pylint: disable=too-few-public-methods
    # pylint: disable=too-many-ancestors
    """Test class Description: Runs IOR/HDF5 on 2 servers with basic parameters.

    :avocado: recursive
    """

    def test_ior_hdf5(self):
        """Jira ID: DAOS-3657.

        Test Description:
            Verify functionality of IOR with HDF5 API.

        Use case:
            Run IOR write and read + verify with HDF5 using a single shared file

        :avocado: tags=all,full_regression
        :avocado: tags=hw,large
        :avocado: tags=daosio,ior,checksum,hdf5
        :avocado: tags=ior_hdf5
        """
        self.run_ior_with_pool()

    def test_ior_hdf5_vol(self):
        """Jira ID: DAOS-4909.

        Test Description:
            Verify functionality of IOR with HDF5 API using the vol connector.

        Use case:
            Run IOR Write, Read, CheckRead with HDF5 Vol connector using a single shared file

        :avocado: tags=all,full_regression
        :avocado: tags=hw,large
        :avocado: tags=daosio,ior,checksum,hdf5,hdf5_vol
        :avocado: tags=ior_hdf5_vol
        """
        hdf5_plugin_path = self.params.get("plugin_path", '/run/hdf5_vol/*')
        mount_dir = self.params.get("mount_dir", "/run/dfuse/*")
        self.run_ior_with_pool(plugin_path=hdf5_plugin_path, mount_dir=mount_dir)

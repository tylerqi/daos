#!/usr/bin/python3
"""
  (C) Copyright 2018-2022 Intel Corporation.

  SPDX-License-Identifier: BSD-2-Clause-Patent
"""
from ior_test_base import IorTestBase

class IorHard(IorTestBase):
    # pylint: disable=too-many-ancestors
    # pylint: disable=too-few-public-methods
    """Test class Description: Runs IOR Hard with different
                               EC OBject types.

    :avocado: recursive
    """

    def test_ior_hard(self):
        """Jira ID: DAOS-7313.

        Test Description:
            Run IOR Hard with EC Object types.

        Use Cases:
            Run IOR Hard Write, Read CheckRead with EC objects.

        :avocado: tags=all,full_regression
        :avocado: tags=hw,large,ib2
        :avocado: tags=ec,ec_array,ec_ior,ior
        :avocado: tags=ior_hard
        """
        ior_read_flags = self.params.get("read_flags", self.ior_cmd.namespace)
        self.run_ior_with_pool()
        self.ior_cmd.flags.update(ior_read_flags)
        self.ior_cmd.sw_wearout.update(None)
        self.run_ior_with_pool(create_cont=False)

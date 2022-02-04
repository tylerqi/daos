#!/usr/bin/python3
"""
  (C) Copyright 2018-2022 Intel Corporation.

  SPDX-License-Identifier: BSD-2-Clause-Patent
"""
from pool_test_base import PoolTestBase
from command_utils_base import CommandFailure


class PoolCreateAllTest(PoolTestBase):
    # pylint: disable=too-few-public-methods
    """Tests pool create all basics

    :avocado: recursive
    """

    def get_available_bytes(self):
        """Update the available size of the tiers storage."""
        self.log.info("Retrieving available size")

        scm_bytes = 0
        smd_bytes = 0

        self.assertGreater(len(self.server_managers), 0, "No server managers")

        try:
            result = self.server_managers[0].dmg.storage_query_usage()
        except CommandFailure as error:
            self.fail("dmg command failed: {}".format(error))

        for host_storage in result["response"]["HostStorage"].values():
            for scm_devices in host_storage["storage"]["scm_namespaces"]:
                scm_bytes += scm_devices["mount"]["avail_bytes"]
            for nvme_device in host_storage["storage"]["nvme_devices"]:
                for smd_device in nvme_device["smd_devices"]:
                    smd_bytes += smd_device["avail_bytes"]

        self.log.info("Available Bytes: scm=%d, smd=%d", scm_bytes, smd_bytes)

        return (scm_bytes, smd_bytes)

    def test_one_pool(self):
        """Test basic pool creation with full storage

        Test Description:
            Create a pool with all the capacity of all servers. Verify that the pool created
            effectively used all the available storage and there is no more available storage.

        :avocado: tags=all,pr,daily_regression
        :avocado: tags=hw,large
        :avocado: tags=pool
        :avocado: tags=pool_create_tests,pool_create_all,pool_create_all_one
        """

        scm_avail_bytes, smd_avail_bytes = self.get_available_bytes()

        self.log.info("Creating a pool with 100% of the available storage")
        self.add_pool_qty(1, namespace="/run/pool/*", create=False)
        self.pool[0].size.update("100%")
        self.pool[0].create()
        self.assertEqual(self.pool[0].dmg.result.exit_status, 0,
                "Pool could not be created")

        self.log.info("Checking size of the pool")
        self.pool[0].get_info()
        tier_bytes = self.pool[0].info.pi_space.ps_space.s_total
        self.assertEqual(scm_avail_bytes, tier_bytes[0],
                f"Invalid SCM size: want={scm_avail_bytes}, got={tier_bytes[0]}")
        self.assertEqual(smd_avail_bytes, tier_bytes[1],
                f"Invalid SMD size: want={smd_avail_bytes}, got={tier_bytes[1]}")

        self.log.info("Checking size of available storage")
        tier_bytes = self.get_available_bytes()
        self.assertEqual(0, tier_bytes[0],
                f"Invalid SCM size: want=0, got={tier_bytes[0]}")
        self.assertEqual(0, tier_bytes[1],
                f"Invalid SMD size: want=0, got={tier_bytes[1]}")

    def test_two_pools(self):
        """Test pool creation of two pools with 50% and 100% of the available storage

        Test Description:
            Create a first pool with 50% of all the capacity of all servers. Verify that the pool
            created effectively used 50% of the available storage and there still is more or less
            50% available storage. Create a second pool with all the remaining storage. Verify that
            the pool created effectively used all the available storage and there is no more
            available storage.

        :avocado: tags=all,pr,daily_regression
        :avocado: tags=hw,large
        :avocado: tags=pool
        :avocado: tags=pool_create_tests,pool_create_all,pool_create_all_two
        """

        epsilon_bytes = 1 << 20 # 1MiB
        max_metadata_bytes = 1 << 34 # 16GiB
        scm_avail_bytes, smd_avail_bytes = self.get_available_bytes()

        self.add_pool_qty(2, namespace="/run/pool/*", create=False)
        self.pool[0].size.update("50%")
        self.pool[1].size.update("100%")

        self.log.info("Creating a first pool with 50% of the available storage")
        self.pool[0].create()
        self.pool[0].get_info()
        self.assertEqual(self.pool[0].dmg.result.exit_status, 0,
                "First pool 0 could not be created")

        self.log.info("Checking size of the first pool")
        self.pool[0].get_info()
        tier_bytes = self.pool[0].info.pi_space.ps_space.s_total
        self.assertLessEqual(abs(scm_avail_bytes-2*tier_bytes[0]), epsilon_bytes,
                f"Invalid SCM size: want={scm_avail_bytes/2}, got={tier_bytes[0]}, "
                 "epsilon={epsilon_bytes}")
        self.assertLessEqual(abs(smd_avail_bytes-2*tier_bytes[1]), epsilon_bytes,
                f"Invalid SMD size: want={smd_avail_bytes/2}, got={tier_bytes[1]}, "
                 "epsilon={epsilon_bytes}")

        # NOTE The size of the available bytes is different from he size of the first pool: size
        # used by the metadata are removed from the available size returned.
        self.log.info("Checking size of available storage after the creation of the first pool")
        tier_bytes = self.get_available_bytes()
        self.assertLessEqual(abs(scm_avail_bytes-2*tier_bytes[0]), max_metadata_bytes,
                f"Invalid SCM size: want={scm_avail_bytes/2}, got={tier_bytes[0]}")
        self.assertLessEqual(abs(smd_avail_bytes-2*tier_bytes[1]), max_metadata_bytes,
                f"Invalid SMD size: want={smd_avail_bytes/2}, got={tier_bytes[1]}")
        scm_avail_bytes, smd_avail_bytes = tier_bytes

        self.log.info("Creating a second pool with 100% of the available storage")
        self.pool[1].create()
        self.pool[1].get_info()
        self.assertEqual(self.pool[1].dmg.result.exit_status, 0,
                "Second pool could not be created")

        self.log.info("Checking size of the second pool")
        self.pool[1].get_info()
        tier_bytes = self.pool[1].info.pi_space.ps_space.s_total
        self.assertLessEqual(abs(scm_avail_bytes-tier_bytes[0]), epsilon_bytes,
                f"Invalid SCM size: want={scm_avail_bytes}, got={tier_bytes[0]}, "
                 "epsilon={epsilon_bytes}")
        self.assertLessEqual(abs(smd_avail_bytes-tier_bytes[1]), epsilon_bytes,
                f"Invalid SMD size: want={smd_avail_bytes/2}, got={tier_bytes[1]}, "
                 "epsilon={epsilon_bytes}")

        self.log.info("Checking size of available storage after the creation of the second pool")
        tier_bytes = self.get_available_bytes()
        self.assertEqual(0, tier_bytes[0],
                f"Invalid SCM size: want=0, got={tier_bytes[0]}")
        self.assertEqual(0, tier_bytes[1],
                f"Invalid SMD size: want=0, got={tier_bytes[1]}")

    def test_recycle_pools(self):
        """Test pool creation and destruction

        Test Description:
            Create a pool with all the capacity of all servers. Verify that the pool created
            effectively used all the available storage. Destroy the pool and repeat these steps 100
            times. For each iteration, check that the size of the created pool is always the same.

        :avocado: tags=all,pr,daily_regression
        :avocado: tags=hw,large
        :avocado: tags=pool
        :avocado: tags=pool_create_tests,pool_create_all,pool_create_all_recycle
        """

        scm_delta_bytes = 1 << 20 # 1MiB
        scm_avail_bytes, smd_avail_bytes = self.get_available_bytes()

        for index in range(10):
            self.log.info("Creating pool %d with 100% of the available storage", index)
            self.add_pool_qty(1, namespace="/run/pool/*", create=False)
            self.pool[0].size.update("100%")
            self.pool[0].create()
            self.assertEqual(self.pool[0].dmg.result.exit_status, 0,
                    f"Pool {index} could not be created")

            self.log.info("Checking size of pool %d", index)
            self.pool[0].get_info()
            tier_bytes = self.pool[0].info.pi_space.ps_space.s_total
            self.assertLessEqual(abs(scm_avail_bytes-tier_bytes[0]), scm_delta_bytes,
                    f"Invalid SCM size: want={scm_avail_bytes}, got={tier_bytes[0]}")
            self.assertEqual(smd_avail_bytes, tier_bytes[1],
                    f"Invalid SMD size: want={smd_avail_bytes}, got={tier_bytes[1]}")

            self.log.info("Destroying pool %d", index)
            self.pool[0].destroy()
            self.assertEqual(self.pool[0].dmg.result.exit_status, 0,
                    f"Pool {index} could not be destroyed")

            self.log.info("Checking size of available storage at iteration %d", index)
            tier_bytes = self.get_available_bytes()
            self.assertLessEqual(abs(scm_avail_bytes-tier_bytes[0]), scm_delta_bytes,
                    f"Invalid SCM size: want={scm_avail_bytes}, got={tier_bytes[0]}")
            self.assertEqual(smd_avail_bytes, tier_bytes[1],
                    f"Invalid SMD size: want={smd_avail_bytes}, got={tier_bytes[1]}")

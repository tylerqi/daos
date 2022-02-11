#!/usr/bin/python
"""
  (C) Copyright 2019-2022 Intel Corporation.

  SPDX-License-Identifier: BSD-2-Clause-Patent
"""
import os
from dfuse_test_base import DfuseTestBase
from ior_utils import IorCommand, run_ior
from job_manager_utils import Mpirun
from thread_manager import ThreadManager


class IorInterceptVerifyDataIntegrity(DfuseTestBase):
    # pylint: disable=too-many-ancestors
    """Test class Description: Runs IOR with mix of dfuse and
       interception library on a multi server and multi client
       settings and verify read/write.

    :avocado: recursive
    """

    def __init__(self, *args, **kwargs):
        """Initialize a IorTestBase object."""
        super().__init__(*args, **kwargs)
        self.processes = None

    def setUp(self):
        """Set up each test case."""
        # obtain separate logs
        self.update_log_file_names()
        # Start the servers and agents
        super().setUp()

        # Get the parameters for IOR
        self.processes = self.params.get("np", '/run/ior/*')

    def test_ior_intercept_verify_data(self):
        """Jira ID: DAOS-3502.

        Test Description:
            Purpose of this test is to run ior through dfuse with
            interception library on 5 clients and without interception
            library on 1 client for at least 30 minutes and verify the
            data integrity using ior's Read Verify and Write Verify
            options.

        Use case:
            Run ior with read, write, fpp, read verify
            write verify for 30 minutes
            Run ior with read, write, read verify
            write verify for 30 minutes

        :avocado: tags=all,full_regression
        :avocado: tags=hw,large
        :avocado: tags=daosio,ior_intercept_verify_data
        """
        self.add_pool()
        self.add_container(self.pool)

        # Start dfuse for POSIX api. This is specific to interception library test requirements.
        self.start_dfuse(self.hostlist_clients, self.pool, self.container)

        # Setup the thread manager
        thread_manager = ThreadManager(run_ior, self.timeout - 30)
        ior_clients_intercept = {
            self.hostlist_clients[0:-1]: os.path.join(self.prefix, 'lib64', 'libioil.so'),
            [self.hostlist_clients[-1]]: None,
        }
        self.job_manager = []
        for index, clients in enumerate(ior_clients_intercept):
            # Add a job manager for each ior command
            self.job_manager.append(Mpirun(None, False, mpitype="mpich"))
            self.job_manager[-1].timeout = self.timeout - 35
            self.job_manager[-1].tmpdir_base.update(self.test_dir, "tmpdir_base")

            # Create a unique ior test file for each thread
            test_file_items = ["testfile", str(index)]
            if ior_clients_intercept[clients]:
                test_file_items.append("intercept")
            test_file = os.path.join(self.dfuse.mount_dir.value, "_".join(test_file_items))

            # Define the paramaters that will be used to run an ior command in this thread
            thread_manager.add(
                test=self,
                manager=self.job_manager[-1],
                log=self.client_log,
                hosts=clients,
                path=self.workdir,
                slots=self.hostfile_clients_slots,
                group=self.server_group,
                pool=self.pool,
                container=self.container,
                processes=(self.processes // len(self.hostlist_clients)) * len(clients),
                intercept=ior_clients_intercept[clients],
                ior_params={"test_file": test_file})
            self.log.info(
                "Created thread %s for %s with intercept: %s",
                index, clients, str(ior_clients_intercept[clients]))

        # Launch the IOR threads
        self.log.info("Launching %d IOR threads", thread_manager.qty)
        results = thread_manager.run()

        # Stop dfuse
        self.stop_dfuse()

        # Check the ior thread results
        failed_thread_count = thread_manager.check(results)
        if failed_thread_count > 0:
            msg = "{} FAILED IOR Thread(s)".format(failed_thread_count)
            self.d_log.error(msg)
            self.fail(msg)

        for index, clients in enumerate(ior_clients_intercept):
            intercept_lib = "without" if ior_clients_intercept[clients] is None else "with"
            IorCommand.log_metrics(
                self.log, "{} clients {} interception library".format(len(clients), intercept_lib),
                results[index]
            )

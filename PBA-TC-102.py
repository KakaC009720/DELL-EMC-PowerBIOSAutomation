#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script Name :PBA-TC-102.py
Author      :Zoran Zhan
Email       :zoran_zhan@wistron.com
TestCase    :[PBA-TC-102] Collect UEFI Version

Description  :
    1. Display Test Configurations
    2. Build ssh connection
    3. Power on SUT
    4. Boot to BIOS settings menu
    5. Collect UEFI Version using racadm
    


Config      :
    [CommonData]
    idrac_ip = <iDRAC IP>
    idrac_user = <iDRAC Username, default=root>
    idrac_pwd = <iDRAC Password, default=calvin>
    os_ip = <OS ip, default=None, Optional>
    os_user = <OS Username, default=root>
    os_pwd = <OS Password, default=iamroot (Notice that this should be
        changed to 'Administrator' for this test case)>

    [WinBoot]
    check_SEL = <Perform SEL verification, default=True>
    check_LC = <Perform LC log verification, default=True>

    [UEFIVersion]
    expected_uefi_version = <expected uefi version>
"""

from libs.product import BaseClass
from libs.product import BIOSLibWrapper
from libs.product.commons import fnkey
from libs.product.commons import util
from os import getcwd as osgetcwd
from sys import path as syspath
import difflib
import logging
import os
import re
import time
syspath.append(osgetcwd())
tc_id = util.get_tc_data(__file__)


class Testcase(BIOSLibWrapper.TestBase):
    """
    Error injection + RLM

    """
    _group_ = "Testcase"
   
    def __init__(self, *args, **kwargs):

        desc = "<Collect UEFI Version>"
        BIOSLibWrapper.TestBase.__init__(self, desc, tc_id, *args, **kwargs)
        self.logger = logging.getLogger(tc_id)

    @BaseClass.TestBase.func_exec
    
    def test_functionality(self):
        """
        Start collect uefi version

        """

        # ---------- Step 1 - Display Test Configurations  ---------- #
        stepName = "Display Test Config"

        # Common data
        self.logger.info("Common data - \n  idrac_ip=%s\n  idrac_user=%s\n"
                         "  idrac_pwd=%s\n  os_ip=%s\n  os_user=%s\n"
                         "  os_pwd=%s\n" % (self.commonData['idrac_ip'],
                                            self.commonData['idrac_user'],
                                            self.commonData['idrac_pwd'],
                                            self.commonData['os_ip'],
                                            self.commonData['os_user'],
                                            self.commonData['os_pwd']))

        # Testcase data
        self.TCData = self.read_testCaseConfig('WinBoot')
        if not self.TCData:
            self.failure(stepName, "Unable to read valid test case data",
                         raise_exc=True)

        self.logger.info("Test case data - \n  check_SEL=%s\n  "
                         "check_LC=%s\n" % (self.TCData['check_SEL'],
                                            self.TCData['check_LC']))

        self.succeed(stepName, "Succeed to display all test case data "
                     "on console")
        # ---------- Step 1 - Display Test Configurations  ---------- #

        # ---------- Step 2 - Build ssh connection ---------- #
        stepName = "SSH Connection"
        self.logger.info("Build connection to SUT")

        rc = self.init_sut()
        if rc != 0:
            self.logger.error("Failed to build SSH connection to SUT")
            self.failure(stepName, "Failed to build SSH connection to SUT",
                         raise_exc=True)

        self.logger.info("Succeed to build SSH connection to SUT")
        self.succeed(stepName, "Succeed to build SSH connection to SUT")
        # ---------- Step 2 - Build ssh connection ---------- #

        # ---------- Step 3 - Power on SUT ------------- #
        stepName = "Pre-Test"
        # 1. Power on SUT if the SUT is offline

        # Check the SUT power status
        self.logger.info("Check the SUT power status")
        rc, response = self.sut.serverAction('powerstatus')
        if not re.search(r'power status:\s+ON', response):
            self.logger.info("SUT is power down right now, power up the SUT")

            # Power on SUT
            rc, response = self.sut.serverAction('powerup')
            if rc != 0:
                self.logger.error("Failed to power on the SUT")
                self.failure(stepName, "Failed to power on the SUT",
                             raise_exc=True)

            # Wait POST readiness
            self.logger.info("SUT power on command sent, "
                             "wait for system boot ...")
            time.sleep(30)
            self.sut.waitPOSTReady()

            self.logger.info("POST exited, wait for 20 secs then start "
                             "OS type check")
            time.sleep(20)

        else:
            self.logger.info("SUT is power up right now")

        # Setup log folders
        self.sut.initLogFolder("captureSEL")    # Name is TBD, should be modified later
        SUTLogDir = self.sut.getLogFolder()

        # Capture and verify SEL log
        self.logger.info("Capturing the SEL log ...")
        rc = self.sut.captureSEL("sel_before.log")
        if rc != 0:
            self.logger.error("Failed to capture the SEL log")
            self.failure(stepName, "Failed to capture the SEL log",
                         raise_exc=True)

        self.logger.info("Succeed to capture the SEL log")
        with open(os.path.join(SUTLogDir, "sel_before.log")) as fin:
            SELStr = fin.read()

        if self.TCData['check_SEL']:
            if not self.sut.verifySEL(SELStr):
                self.logger.error("SEL pre-check -- FAIL")
                self.failure(stepName, "SEL pre-check -- FAIL",
                             raise_exc=True)
            self.logger.info("SEL pre-check -- PASS")
        else:
            self.logger.info("SEL pre-check -- BYPASS")

        self.logger.info("Succeed to power on SUT")
        self.succeed(stepName, "Succeed to power on SUT")

        # ----------- Step 3 - Power on SUT ------------- #

	# ----------- Step 4 - Boot to BIOS settings menu ------------- #

        # Boot to BIOS settings menu
        self.logger.info("Boot to BIOS settings menu")
        rc = self.sut.HIIBootToBIOSSettingsMenu()
        if rc != 0:
            self.logger.error("Unable to boot to BIOS settings menu")
            self.failure(stepName, "Unable to boot to BIOS settings menu",
                         raise_exc=True)

        self.logger.info("Succeed to boot to BIOS settings menu")
        self.succeed(stepName, "Succeed to boot to BIOS settings menu")

        # ----------- Step 4 - Boot to BIOS settings menu ------------- #
        
	# ----------- Step 5 - Collect UEFI Version using racadm ---------- #
        step_name = "Collect UEFI Version using racadm"
        self.logger.info("Collecting UEFI Version using racadm")
        rc, response = self.sut.runRacadm("get BIOS.SysInformation.UefiComplianceVersion")
        if rc != 0:
            msg = "Fails to collect UEFI Version using racadm"
            self.logger.error(msg)
            self.failure(step_name, msg, raise_exc=True)

        self.logger.info("Try racadm comand: 'get BIOS.SysInformation.UefiComplianceVersion', response: \n%s" %
                         response)
        self.UData = self.read_testCaseConfig('UEFIVersion')
        self.logger.info("Expected UEFI Version - \nUefiComplianceVersion=%s\n "
                          % (self.UData['expected_uefi_version']))


        if self.UData['expected_uefi_version'] not in response:
            self.logger.error("UEFI Version is not expected")
            self.failure(step_name, "UEFI Version is not expected",
                         raise_exc=True)
        else:
            self.logger.info("UEFI Version is expected")

        self.logger.info("Succeed to collect UEFI version using racadm")
        self.succeed(step_name, "Succeed to collect UEFI version using racadm")

        # ---------- Step 5 - Collect UEFI Version using racadm ---------- #


        # Always put these two lines as final commands to make sure ssh session closed properly
        self.logger.info("Closing ssh session ...")
        self.sut.close()
        # ----------- Step N - <TBD, Step name> ------------- #

#!/usr/bin/python2
"""
Created on Feb 18, 2020

@author: Vijay Kumar
"""
import os
import sys
import time
import logging
import json
RUN_DIR = os.path.abspath(os.path.dirname(__file__))
CURRENT_DIR = os.getcwd()

if __name__ == '__main__':
    os.chdir(RUN_DIR)


# several of the modules in core expect to be able to import themselves... :(
sys.path.insert(1, os.path.abspath('libs/core'))

# Path updates for third party packages that expect to import packages
sys.path.append(os.path.abspath('libs/thirdparty'))

sys.path.append(os.path.abspath('libs'))

import dellunit
from libs.product.commons import util
from dellunit import build_report_json, report
LOGTIME = time.strftime("%Y%m%d_%H%M%S")
DIRLIST = [sys.path.append(x[0].replace("\\", "/")) for x in os.walk('tests') if not x[0].endswith("__")]

logtime = time.strftime("%Y%m%d_%H%M%S")
def main(execution_type = "Native", qmetry_data = {}):
    """
    Start method of execution
    """
    try:
        prog = dellunit.TestProgram(LOGTIME, execution_type, qmetry_data)
        jsonfile = ('report_%s.json'%logtime if (prog.timestamp_report == 1) else 'report.json')
        htmlfile = ('report_%s.html'%logtime if (prog.timestamp_report == 1) else 'report.html')
        JSON_FILE = os.path.abspath(os.path.join('logs', jsonfile))
        REPORT_FILE = os.path.abspath(os.path.join('logs', htmlfile))

        invalid_tests_json = []
        for test in prog.invalid_tests:
            test_json = {}
            test_json["testcase"] = test
            test_json["invalid"] = True
            test_json["status"] = "error"
            test_json["description"] = util.getTestcaseInformation(test)["Testcase Name"]
            invalid_tests_json.append(test_json)

    except:
        sys.stdout == sys.__stdout__
        sys.stderr == sys.__stderr__
        logging.exception('Fatal error during test, skipping report generation')
        os.chdir(CURRENT_DIR)
        sys.exit(1)

    with open(JSON_FILE, 'r') as outfile_read:
        data = json.load(outfile_read)
        with open(JSON_FILE, 'w') as outfile_write:
            data["results"][0]["tests"].extend(invalid_tests_json)
            json.dump(data, outfile_write)
    logging.info('Creating the report.html file')
    report.render_report(JSON_FILE, REPORT_FILE)
    os.chdir(CURRENT_DIR)

if __name__ == '__main__':
    main()

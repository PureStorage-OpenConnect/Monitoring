#!/usr/bin/env python3
# Copyright (c) 2019 Pure Storage, Inc.
#
# *Overview
#
# This short Zabbix external check code shows how to monitor Pure Storage FlashBlade systems.
# The Pure Storage Python REST Client is used to query the FlashBlade occupancy and performcnce indicators.
# A simplistic use of generators is introduced in the attempt to keep code a bit more cleaner and condensed, athough not
# strictly required.
#
# *Installation
#
# The script should be copied to the Zabbix external check scripts directory on the
# Change the execution rights of the program to allow the execution to 'zabbix' (usually chmod 0755).
#
# *Dependencies
#
# purity_fb         Pure Storage Python REST Client for FlashBlade (https://github.com/purestorage/purity_fb_python_client)

__author__ = "Eugenio Grosso"
__copyright__ = "Copyright 2019, Pure Storage Inc."
__license__ = "Apache v2.0"
__version__ = "1.1"
__maintainer__ = "Eugenio Grosso"
__email__ = "geneg@purestorage.com"
__status__ = "Production"

"""Pure Storage FlashBlade occupancy and performance indicators

   Zabbix external check utility to retrieve  from a Pure Storage FlashBlade.

   The utility has the following mandatory arguments:

       -e/--endpoint ENDPOINT         the FB hostname or ip address

       -t/--apitoken APITOKEN         the api_token to autenticate with FB

       -z/--zabbix ZABBIX             the Zabbix server hostname or ip address

       -m/--metric {aperf,aspace,bspace,fspace}      array metrics type to be returned:
                                      specify 'aperf' to collect array global performance metrics,
                                              'aspace' to collect array global used space metrics,
                                              'bspace' to collect space used per bucket,
                                              'fspace' to collect space used per filesystem

   and the following optional arguments control the connection timeouts and retry to the target FlashBlade

       --ctimeo CTIMEO                FB connection timeout. Defines the timeout in seconds to connect to the FB REST server

       --rtimeo RTIMEO                FB request timeout. Defines the timeout in seconds for a request to the FB REST server 

       --retries RETRIES              FB request retries. Defines the number of retries after which a request to the FB REST
                                      server is considered lost.


   The -d/--debug flag controls whether the metrics should be printed to standard output or delivered to the Zabbix
   server.

   Zabbix LLD discovery is performed in case of buckets and filesystem metrics, as those are inherentlt dynamic elements.

"""


import argparse
import logging
import logging.handlers
import sys
import urllib3
import json
from purity_fb import PurityFb, rest
from pyzabbix import ZabbixMetric, ZabbixSender


PURE_ZBX_LOGFILE = '/var/log/pure_fb_check.log'


"""Pure Storage FlashBlade Zabbix collector

Retrieves occupancy and perfromance metrics from FlashBlade and send everything to Zabbix server
"""


class PureZabbixFBChecker:

    """ Class that instantiate the checker methods to collect Zabbix metrix and LLD data
    from Puretorage FlashBlade.
    to work
    Parameters:
        fb: the authenticated API session to the Purestorage FlashBlade
    """

    def __init__(self, fb):
        self.fb = fb
        self._name = None

    @property
    def name(self):
        """(Self) -> str
        Return the FlashBlade name
        """
        if self._name is None:
            fbinfo = self.fb.arrays.list_arrays()
            self._name = fbinfo.items[0].name
        return self._name

    def array_space(self):
        """Get overall array occupancy info from FlashBlade.
        """

        host = self.name
        fbinfo = self.fb.arrays.list_arrays_space()
        metrics = []        # metrics for Zabbix trapper
        a = fbinfo.items[0]
        metrics.append(ZabbixMetric(
            host, "purestorage.fb.array.total", a.space.total_physical))
        metrics.append(ZabbixMetric(
            host, "purestorage.fb.array.unique", a.space.unique))
        metrics.append(ZabbixMetric(
            host, "purestorage.fb.array.virtual", a.space.virtual))
        metrics.append(ZabbixMetric(
            host, "purestorage.fb.array.datareduction", a.space.data_reduction))
        metrics.append(ZabbixMetric(
            host, "purestorage.fb.array.snapshots", a.space.snapshots))
        yield metrics

    def buckets_space(self):
        """Get buckets occupancy info from FlashBlade.
        Performs LLD of current FlashBlade buckets and gathers buckets counters at the same time,
        optimizing into a single query to FlashBlade.
        """

        host = self.name
        fbinfo = self.fb.buckets.list_buckets()
        zbx_lld_data = {"data": []}  # Zabbix LLD data
        metrics = []  # metrics for Zabbix trapper

        for b in fbinfo.items:
            zbx_lld_data["data"].append(
                {"{#ACCOUNT}":  b.account.name, "{#BUCKET}": b.name})
            metrics.append(ZabbixMetric(
                host, "purestorage.fb.buckets[" + b.account.name + "," + b.name + ",total]", b.space.total_physical))
            metrics.append(ZabbixMetric(
                host, "purestorage.fb.buckets[" + b.account.name + "," + b.name + ",unique]", b.space.unique))
            metrics.append(ZabbixMetric(
                host, "purestorage.fb.buckets[" + b.account.name + "," + b.name + ",virtual]", b.space.virtual))
            metrics.append(ZabbixMetric(
                host, "purestorage.fb.buckets[" + b.account.name + "," + b.name + ",objects]", b.object_count))
            metrics.append(ZabbixMetric(
                host, "purestorage.fb.buckets[" + b.account.name + "," + b.name + ",snapshots]", b.space.snapshots))
            if b.space.data_reduction is None:
                b.space.data_reduction = 0
            metrics.append(ZabbixMetric(
                host, "purestorage.fb.buckets[" + b.account.name + "," + b.name + ",data_reduction]", b.space.data_reduction))

        yield zbx_lld_data
        yield metrics

    def filesystems_space(self):
        """Get filesystems occupancy info from FlashBlade.
        This generator performs LLD of current FlashBlade filesystems and gathers filesystems counters at the same time,
        optimizing into a single query to FlashBlade.
        """

        host = self.name
        fbinfo = self.fb.file_systems.list_file_systems()

        zbx_lld_data = {"data": []}  # Zabbix LLD data
        metrics = []  # metrics for Zabbix trapper
        for f in fbinfo.items:
            zbx_lld_data["data"].append({"{#FILESYSTEM}": f.name})
            metrics.append(ZabbixMetric(
                host, "purestorage.fb.filesystems[" + f.name + ",total]", f.space.total_physical))
            metrics.append(ZabbixMetric(
                host, "purestorage.fb.filesystems[" + f.name + ",unique]", f.space.unique))
            metrics.append(ZabbixMetric(
                host, "purestorage.fb.filesystems[" + f.name + ",virtual]", f.space.virtual))
            metrics.append(ZabbixMetric(
                host, "purestorage.fb.filesystems[" + f.name + ",snapshots]", f.space.snapshots))
            if f.space.data_reduction is None:
                f.space.data_reduction = 0
            metrics.append(ZabbixMetric(
                host, "purestorage.fb.filesystems[" + f.name + ",data_reduction]", f.space.data_reduction))

        yield zbx_lld_data
        yield metrics

    def array_perf(self):
        """Get performance metrics from FlashBlade."""

        host = self.name
        fbinfo = self.fb.arrays.list_arrays_performance()
        pinfo = fbinfo.items[0]
        metrics = []
        metrics.append(ZabbixMetric(
            host, "purestorage.fb.array.bytes_per_op", pinfo.bytes_per_op))
        metrics.append(ZabbixMetric(
            host, "purestorage.fb.array.bytes_per_read", pinfo.bytes_per_read))
        metrics.append(ZabbixMetric(
            host, "purestorage.fb.array.bytes_per_write", pinfo.bytes_per_write))
        metrics.append(ZabbixMetric(
            host, "purestorage.fb.array.input_per_sec", pinfo.input_per_sec))
        metrics.append(ZabbixMetric(
            host, "purestorage.fb.array.others_per_sec", pinfo.others_per_sec))
        metrics.append(ZabbixMetric(
            host, "purestorage.fb.array.output_per_sec", pinfo.output_per_sec))
        metrics.append(ZabbixMetric(
            host, "purestorage.fb.array.read_bytes_per_sec", pinfo.read_bytes_per_sec))
        metrics.append(ZabbixMetric(
            host, "purestorage.fb.array.reads_per_sec", pinfo.reads_per_sec))
        metrics.append(ZabbixMetric(
            host, "purestorage.fb.array.usec_per_other_op", pinfo.usec_per_other_op))
        metrics.append(ZabbixMetric(
            host, "purestorage.fb.array.usec_per_read_op", pinfo.usec_per_read_op))
        metrics.append(ZabbixMetric(
            host, "purestorage.fb.array.usec_per_write_op", pinfo.usec_per_write_op))
        metrics.append(ZabbixMetric(
            host, "purestorage.fb.array.write_bytes_per_sec", pinfo.write_bytes_per_sec))
        metrics.append(ZabbixMetric(
            host, "purestorage.fb.array.writes_per_sec", pinfo.writes_per_sec))

        for proto in ['http', 'nfs', 's3', 'smb']:
            fbinfo = self.fb.arrays.list_arrays_performance(protocol=proto)
            pinfo = fbinfo.items[0]
            metrics.append(ZabbixMetric(host, "purestorage.fb." +
                                        proto + ".bytes_per_op", pinfo.bytes_per_op))
            metrics.append(ZabbixMetric(host, "purestorage.fb." +
                                        proto + ".bytes_per_read", pinfo.bytes_per_read))
            metrics.append(ZabbixMetric(host, "purestorage.fb." +
                                        proto + ".bytes_per_write", pinfo.bytes_per_write))
            metrics.append(ZabbixMetric(host, "purestorage.fb." +
                                        proto + ".input_per_sec", pinfo.input_per_sec))
            metrics.append(ZabbixMetric(host, "purestorage.fb." +
                                        proto + ".others_per_sec", pinfo.others_per_sec))
            metrics.append(ZabbixMetric(host, "purestorage.fb." +
                                        proto + ".output_per_sec", pinfo.output_per_sec))
            metrics.append(ZabbixMetric(host, "purestorage.fb." +
                                        proto + ".read_bytes_per_sec", pinfo.read_bytes_per_sec))
            metrics.append(ZabbixMetric(host, "purestorage.fb." +
                                        proto + ".reads_per_sec", pinfo.reads_per_sec))
            metrics.append(ZabbixMetric(host, "purestorage.fb." +
                                        proto + ".usec_per_other_op", pinfo.usec_per_other_op))
            metrics.append(ZabbixMetric(host, "purestorage.fb." +
                                        proto + ".usec_per_read_op", pinfo.usec_per_read_op))
            metrics.append(ZabbixMetric(host, "purestorage.fb." +
                                        proto + ".usec_per_write_op", pinfo.usec_per_write_op))
            metrics.append(ZabbixMetric(host, "purestorage.fb." +
                                        proto + ".write_bytes_per_sec", pinfo.write_bytes_per_sec))
            metrics.append(ZabbixMetric(host, "purestorage.fb." +
                                        proto + ".writes_per_sec", pinfo.writes_per_sec))
        yield metrics


def init_logger():

    # set up logging to file
    logging.basicConfig(filename=PURE_ZBX_LOGFILE,
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    # disable urllib3.connectionpool annoying warnings
    log_cpool = logging.getLogger('urllib3.connectionpool')
    log_cpool.setLevel(logging.ERROR)

    logger = logging.getLogger('pure-fb-probe')
    h = logging.handlers.SysLogHandler()
    h.setLevel(logging.ERROR)

    logger.addHandler(h)
    return logger


def connect_fb(endpoint, apitoken, ctimeo=2.0, rtimeo=5.0, retries=3):
    """Establish connection with FlashBlade."""
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    fb = PurityFb(endpoint, conn_timeo=ctimeo, read_timeo=rtimeo, retries=retries)
    fb.disable_verify_ssl()
    fb.login(apitoken)
    return fb


def disconnect_fb(fb):
    fb.logout()


def parse_args():
    argp = argparse.ArgumentParser()
    argp.add_argument('-e', '--endpoint',
                      required=True,
                      action='store',
                      help="FB hostname or ip address")
    argp.add_argument('-t', '--apitoken',
                      required=True,
                      action='store',
                      help="FB api_token")
    argp.add_argument('-z', '--zabbix',
                      required=True,
                      action='store',
                      help="Zabbix server hostname or ip address")
    argp.add_argument('-m', '--metric', choices=['aperf', 'aspace', 'bspace', 'fspace'],
                      required=True,
                      action='store',
                      help="array metrics type to be returned")
    argp.add_argument('-d', '--debug',
                      required=False,
                      action='store_true',
                      help="Print return values to standard output instead than actually send them to Zabbix server")
    argp.add_argument('--ctimeo',
                      type=float,
                      required=False,
                      action='store',
                      default=10.0,
                      help="FlashBlade REST server connection timeo")
    argp.add_argument('--rtimeo',
                      type=float,
                      required=False,
                      action='store',
                      default=30.0,
                      help="FlashBlade REST server response timeout")
    argp.add_argument('--retries',
                      type=int,
                      required=False,
                      action='store',
                      default=3,
                      help="FlashBlade REST server request retries")
    return argp.parse_args()


def main():

    logger = init_logger()
    args = parse_args()

    try:
        flashblade = connect_fb(args.endpoint, args.apitoken, args.ctimeo, args.rtimeo, args.retries)
        if flashblade is None:
            print("Error")
            return

        zbx_checker = PureZabbixFBChecker(flashblade)

        zbx_lld_data = None

        if (args.metric == 'aperf'):
            z = zbx_checker.array_perf()
            zbx_metrics = next(z)
        elif (args.metric == 'aspace'):
            z = zbx_checker.array_space()
            zbx_metrics = next(z)
        elif (args.metric == 'bspace'):
            z = zbx_checker.buckets_space()
            zbx_lld_data = next(z)
            zbx_metrics = next(z)
        elif (args.metric == 'fspace'):
            z = zbx_checker.filesystems_space()
            zbx_lld_data = next(z)
            zbx_metrics = next(z)

        if zbx_lld_data is not None:
            # Return JSON formatted LLD buckets data to Zabbix external check
            print(json.dumps(zbx_lld_data, sort_keys=True, indent=4))
        else:
            # Remember, need to return a string to Zabbix as we are in an external checker
            print("Done!")

        if (args.debug):
            for zm in zbx_metrics:
                print(zm)
        else:
            sender = ZabbixSender(args.zabbix)
            sender.send(zbx_metrics)
        disconnect_fb(flashblade)

    except Exception as e:
        logger.exception("Exception occurred")
        print("Error") # Remember, need to return a string to Zabbix as we are in an external checker


if __name__ == '__main__':
    main()

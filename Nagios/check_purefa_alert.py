#!/usr/bin/env python
# Copyright (c) 2018 Pure Storage, Inc.
#
# * Overview
#
# This short Nagios/Icinga plugin code shows  how to build a simple plugin to monitor Pure Storage FlashArrays.
# The Pure Storage Python REST Client is used to query the FlashArray alert messages.
# Plugin leverages the remarkably helpful nagiosplugin library by Christian Kauhaus.
#
# * Installation
#
# The script should be copied to the Nagios plugins directory on the machine hosting the Nagios server or the NRPE
# for example the /usr/lib/nagios/plugins folder.
# Change the execution rights of the program to allow the execution to 'all' (usually chmod 0755).
#
# * Dependencies
#
#  nagiosplugin      helper Python class library for Nagios plugins by Christian Kauhaus (http://pythonhosted.org/nagiosplugin)
#  purestorage       Pure Storage Python REST Client (https://github.com/purestorage/rest-client)

__author__ = "Eugenio Grosso"
__copyright__ = "Copyright 2018, Pure Storage Inc."
__credits__ = "Christian Kauhaus"
__license__ = "Apache v2.0"
__version__ = "1.2"
__maintainer__ = "Eugenio Grosso"
__email__ = "geneg@purestorage.com"
__status__ = "Production"

"""Pure Storage FlashArray alert messages status
   Nagios plugin to check the general state of a Pure Storage FlashArray from the internal alert messages.
   The plugin has two mandatory arguments:  'endpoint', which specifies the target FA, 'apitoken', which
   specifies the autentication token for the REST call session. The FlashArray is considered unhealty if
   there is any pending message that reports a warning or critical status of one or more components
"""

import argparse
import logging
import nagiosplugin
import purestorage
import urllib3


_log = logging.getLogger('nagiosplugin')

class PureFAalert(nagiosplugin.Resource):
    """Pure Storage FlashArray overall occupancy
    Calculates the overall FA storage occupancy
    """

    def __init__(self, endpoint, apitoken):
        self.endpoint = endpoint
        self.apitoken = apitoken

    @property
    def name(self):
        return 'PURE_ALERT'

    def get_alerts(self):
        """Gets active alerts from FlashArray."""
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        fa = purestorage.FlashArray(self.endpoint, api_token=self.apitoken)
        fainfo = fa.list_messages(open = True)
        fa.invalidate_cookie()
        return(fainfo)

    def probe(self):

        fainfo = self.get_alerts()
        _log.debug('FA REST call returned "%s" ', fainfo)
        if len(fainfo) == 0:
            metric = nagiosplugin.Metric('FA_ALERTS', 0, context='default' )
        else:
            metric = nagiosplugin.Metric('FA_ALERTS', 1, context='default')
        return metric


def parse_args():
    argp = argparse.ArgumentParser()
    argp.add_argument('endpoint', help="FA hostname or ip address")
    argp.add_argument('apitoken', help="FA api_token")
    argp.add_argument('-v', '--verbose', action='count', default=0,
                      help='increase output verbosity (use up to 3 times)')
    argp.add_argument('-t', '--timeout', default=30,
                      help='abort execution after TIMEOUT seconds')
    return argp.parse_args()


@nagiosplugin.guarded
def main():
    args = parse_args()
    check = nagiosplugin.Check( PureFAalert(args.endpoint, args.apitoken) )
    check.add(nagiosplugin.ScalarContext('default', '', '@1:1'))
    check.main(args.verbose, args.timeout)

if __name__ == '__main__':
    main()

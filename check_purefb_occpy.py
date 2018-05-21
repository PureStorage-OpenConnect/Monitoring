#!/usr/bin/env python
# Copyright (c) 2018 Pure Storage, Inc.
#
## Overview
#
# This short Nagios/Icinga plugin code shows  how to build a simple plugin to monitor Pure Storage FlashBlade systems.
# The Pure Storage Python REST Client is used to query the FlashBlade occupancy indicators.
# Plugin leverages the remarkably helpful nagiosplugin library by Christian Kauhaus.
#
## Installation
#
# The script should be copied to the Nagios plugins directory on the machine hosting the Nagios server or the NRPE
# for example the /usr/lib/nagios/plugins folder.
# Change the execution rights of the program to allow the execution to 'all' (usually chmod 0755).
#
## Dependencies
#
#  nagiosplugin      helper Python class library for Nagios plugins by Christian Kauhaus (http://pythonhosted.org/nagiosplugin)
#  purity_fb         Pure Storage Python REST Client for FlashBlade v1.2 (https://github.com/purestorage/purity_fb_python_client/archive/v1.2.tar.gz)

__author__ = "Eugenio Grosso"
__copyright__ = "Copyright 2018, Pure Storage Inc."
__credits__ = "Christian Kauhaus"
__license__ = "Apache v2.0"
__version__ = "1.0"
__maintainer__ = "Eugenio Grosso"
__email__ = "geneg@purestorage.com"
__status__ = "Production"

"""Pure Storage FlashBlade occupancy status

   Nagios plugin to retrieve the overall occupancy from a Pure Storage FlashBlade, or from a single volume, or from the object store.
   Storage occupancy indicators are collected from the target FB using the REST call.
   The plugin has two mandatory arguments:  'endpoint', which specifies the target FB and 'apitoken', which
   specifies the autentication token for the REST call session. A third optional parameter, 'volname' can
   be used to check a specific named value. The optional values for the warning and critical thresholds have
   different meausure units: they must be expressed as percentages in the case of checkig the whole flasharray
   occupancy, while they must be integer byte units if checking a single volume.

"""

import argparse
import logging
import nagiosplugin
import urllib3
from purity_fb import PurityFb, rest


_log = logging.getLogger('nagiosplugin')

class PureFBoccpy(nagiosplugin.Resource):
    """Pure Storage FlashBlade  occupancy

    Calculates the overall FB storage occupancy or a single volume capacity.

    """

    def __init__(self, endpoint, apitoken, type, volname):
        self.endpoint = endpoint
        self.apitoken = apitoken
        if (type == 'filesystem'):
            self.type = 'filesystem'
            self.volname = volname
        elif (type == 'objectstore'):
            self.type = 'objectstore'
            self.volname = None
        else:
            self.type = None
            self.volname = None

    @property
    def name(self):
        if (self.type == 'filesystem'):
            return 'PURE_FB_VOL_OCCUPANCY'
        elif (self.type == 'objectstore' ):
            return 'PURE_FB_OBJSTOR_OCCUPANCY'
        else:
            return 'PURE_FB_OCCUPANCY'


    def get_occupancy(self):
        """Gets occupancy values from FlasgBlade ."""
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        fb = PurityFb(self.endpoint)
        fb.disable_verify_ssl()
        fb.login(self.apitoken)


        if (self.type == 'filesystem'):
            fbinfo = fb.file_systems.list_file_systems(names=[self.volname])
        elif (self.type == 'objectstore' ):
            fbinfo = fb.arrays.list_arrays_space(type='object-store')
        else:
            fbinfo = fb.arrays.list_arrays_space()

        fb.logout()
        return(fbinfo)

    def probe(self):

        fbinfo = self.get_occupancy()
        _log.debug('FA REST call returned "%s" ', fbinfo)
        if (self.type == 'filesystem'):
            occupancy = int(fbinfo.items[0].space.virtual)
            metric = nagiosplugin.Metric(self.volname + ' occupancy', occupancy, 'B', min=0, context='occupancy')
        elif (self.type == 'objectstore' ):
            occupancy = round(float(fbinfo.items[0].space.total_physical) / float(fbinfo.items[0].capacity), 2) * 100
            metric = nagiosplugin.Metric('FB occupancy', occupancy, '%', min=0, max=100, context='occupancy')
        else:
            occupancy = round(float(fbinfo.items[0].space.total_physical) / float(fbinfo.items[0].capacity), 2) * 100
            metric = nagiosplugin.Metric('FB occupancy', occupancy, '%', min=0, max=100, context='occupancy')
        return metric


def parse_args():
    argp = argparse.ArgumentParser()
    argp.add_argument('endpoint', help="FB hostname or ip address")
    argp.add_argument('apitoken', help="FB api_token")
    group = argp.add_mutually_exclusive_group()
    group.add_argument("--vol", type=str, help="FB volume name.")
    group.add_argument("--objstore", action="store_true")
    argp.add_argument('-w', '--warning', metavar='RANGE', default='',
                      help='return warning if occupancy is outside RANGE. Value has to be expressed in percentage for the FB, while in bytes for the single volume')
    argp.add_argument('-c', '--critical', metavar='RANGE', default='',
                      help='return critical if occupancy is outside RANGE. Value has to be expressed in percentage for the FB, while in bytes for the single volume')
    argp.add_argument('-v', '--verbose', action='count', default=0,
                      help='increase output verbosity (use up to 3 times)')
    argp.add_argument('-t', '--timeout', default=30,
                      help='abort execution after TIMEOUT seconds')
    return argp.parse_args()


@nagiosplugin.guarded
def main():
    args = parse_args()
    if (args.objstore):
        check = nagiosplugin.Check( PureFBoccpy(args.endpoint, args.apitoken, 'objectstore', None) )
    elif (args.vol is not None):
        check = nagiosplugin.Check( PureFBoccpy(args.endpoint, args.apitoken, 'filesystem', args.vol) )
    else:
        check = nagiosplugin.Check( PureFBoccpy(args.endpoint, args.apitoken, None, None) )
    check.add(nagiosplugin.ScalarContext('occupancy', args.warning, args.critical))
    check.main(args.verbose, args.timeout)

if __name__ == '__main__':
    main()

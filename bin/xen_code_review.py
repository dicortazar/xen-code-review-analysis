#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.
#
# Authors:
#     Daniel Izquierdo <dizquierdo@bitergia.com>
#

import os
import MySQLdb
from ConfigParser import ConfigParser


SETTINGS = "./settings" # arguments file


def parse_file_args():
    config = ConfigParser()
    config.read("settings")

    args = {}
    # There are two sections: mysql and elasticsearch
    if config.has_section("mysql"):
        if config.has_option("mysql", "user") and \
            config.has_option("mysql", "password") and \
            config.has_option("mysql", "mlstats_db") and \
            config.has_option("mysql", "cvsanaly_db") and \
            config.has_option("mysql", "code_review_db"):
                args["mysql"] = dict(config.items("mysql"))
    else:
        raise Exception("Section 'mysql' not found in the 'settings' file")

    if config.has_section("elasticsearch"):
        args["elasticsearch"] = dict(config.items("elasticsearch"))
    else:
        raise Exception("Section 'elasticsearch' not found in the 'settings' file")

    return args


def connect(args):
    user = args["mysql"]["user"]
    password = args["mysql"]["password"]

    db = args["mysql"]["code_review_db"]
    try:
        db = MySQLdb.connect(user = user, passwd = password, db = db, charset='utf8')
        return db, db.cursor()
    except:
        raise Exception("Database connection error")


def execute_query(connector, query):
    results = int (connector.execute(query))

    if results > 0:
        result1 = connector.fetchall()
        return result1
    else:
        return []


def update_tables(args):

    _, cursor = connect(args)
    # Update tables to produce UTC dates needed for the analysis.
    query = "alter table patches add column date_utc DATETIME;"
    execute_query(cursor, query)
    query = "alter table patch_series_version add column date_utc DATETIME;"
    execute_query(cursor, query)
    query = "alter table comments add column date_utc DATETIME;"
    execute_query(cursor, query)
    query = "alter table flags add column date_utc DATETIME;"
    execute_query(cursor, query)
    query = "alter table commits add column author_date_utc DATETIME;"
    execute_query(cursor, query)
    query = "alter table commits add column committer_date_utc DATETIME;"
    execute_query(cursor, query)

    query = "update patches set date_utc=TIMESTAMPADD(SECOND, -date_tz, date)"
    execute_query(cursor, query)
    query = "update patch_series_version set date_utc=TIMESTAMPADD(SECOND, -date_tz, date);"
    execute_query(cursor, query)
    query = "update comments set date_utc=TIMESTAMPADD(SECOND, -date_tz, date);"
    execute_query(cursor, query)
    query = "update flags set date_utc=TIMESTAMPADD(SECOND, -date_tz, date);"
    execute_query(cursor, query)
    query = "update commits set author_date_utc=TIMESTAMPADD(SECOND, -author_date_tz, author_date);"
    execute_query(cursor, query)
    query = "update commits set committer_date_utc=TIMESTAMPADD(SECOND, -committer_date_tz, committer_date);"
    execute_query(cursor, query)


def main():
    args = parse_file_args()

    # Running the database for code review actions
    run_codereviews = ("python ../data-retrieval/xen_patches.py -u='%s' -p='%s' -d='%s' %s %s") % \
                      (args["mysql"]["user"], args["mysql"]["password"], args["mysql"]["code_review_db"],
                      args["mysql"]["mlstats_db"], args["mysql"]["cvsanaly_db"])
    os.system(run_codereviews)

    # Updating the database code_review_db with UTC dates.
    update_tables(args)

    # Running the analysis to produce patch series information
    run_patchseries = ("python ../data-analysis/xen_analysis_ps.py -c='%s' -i='%s'") % \
                        (SETTINGS, args['elasticsearch']['xen_reviewers'])
    os.system(run_patchseries)

    # Running the analysis to produce patch_series timing information
    run_patchseries_ts = ("python ../data-analysis/xen_analysis_ps_datetime.py -c='%s' -i='%s'") % \
                            (SETTINGS, args['elasticsearch']['xen_timefocused'])
    os.system(run_patchseries_ts)


if __name__ == '__main__':
    main()

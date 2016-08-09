#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2015-2016 Bitergia
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
#     Santiago Dueñas <sduenas@bitergia.com>
#
"""
Xen Code Review Kibana-dashboard builder

This script aims at building a Kibana dashboard focused on the
several aspects of interest for the Xen community.

This builds the following panels:

  * Time-focused panel at the level of patch series
  * People/Organizations panel at the level of patches/comments/reviews
  * Backlog/commits panel at the level of patch series

The time focused panel plays with the following data:
  * Filters:
  * Patches per patch serie
  * Loops per patch serie
  * Evolutionary charts:
  * Time to merge
  * Time to commit
  * Time to re-work a patch serie
  * Cycle time
  * Time to first review
"""

import argparse

import pandas

from queries import (QUERY_PATCH_SERIE,
                     QUERY_TIME2MERGE,
                     QUERY_TIME2COMMIT)
from utils import (create_mysql_connection,
                   create_elasticsearch_connection,
                   execute_mysql_query,
                   read_config_file,
                   to_dict)


XEN_INDEX = 'xen-patchseries-timefocused'

DF_PATCH_COLUMNS = ["patchserie_id", "message_id", "subject", "sender",
                    "sender_domain", "sent_date", "num_patches",
                    "num_versions", "num_comments", "num_commenters"]
DF_TIME2MERGE_COLUMNS = ["patchserie_id", "time2merge", "sent_date", "mergetime"]
DF_TIME2COMMIT_COLUMNS = ["patchserie_id", "time2commit",
                          "lastcommentdate", "committime"]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--config', dest='config_file',
                        default='./settings')
    args = parser.parse_args()

    config = read_config_file(args.config_file)

    cursor = connect_to_mysql(**config['mysql'])

    dfs = load_dataframes(cursor)
    data = calculate(dfs)

    es_conn = connect_to_elasticsearch(**config['elasticsearch'])
    write_to_elasticsearch(es_conn, data)


def load_dataframes(cursor):
    data_patchserie = list(execute_mysql_query(cursor, QUERY_PATCH_SERIE))
    data_time2merge = list(execute_mysql_query(cursor, QUERY_TIME2MERGE))
    data_time2commit = list(execute_mysql_query(cursor, QUERY_TIME2COMMIT))

    dfs = {
        'patchseries' : pandas.DataFrame(data_patchserie, columns=DF_PATCH_COLUMNS),
        'time2merge' : pandas.DataFrame(data_time2merge, columns=DF_TIME2MERGE_COLUMNS),
        'time2commit' : pandas.DataFrame(data_time2commit, columns=DF_TIME2COMMIT_COLUMNS)
    }

    return dfs


def calculate(dfs):
    patchseries = dfs['patchseries']
    time2merge = dfs['time2merge']
    time2commit = dfs['time2commit']

    patchseries_df = pandas.merge(patchseries, time2merge,
                                  on='patchserie_id', how='left')
    patchseries_df = pandas.merge(patchseries_df, time2commit,
                                  on='patchserie_id', how='left')
    patchseries_df = patchseries_df.fillna(-1)
    patchseries_df['time2commit'] = (patchseries_df['time2commit'] / 3600.0) / 24.0
    patchseries_df['time2merge'] = (patchseries_df['time2merge'] / 3600.0) / 24.0

    return patchseries_df


def connect_to_mysql(**params):
    user = params['user']
    password = params['password']
    host = params['host']
    db = params['code_review_db']

    cursor = create_mysql_connection(user, password, host, db)

    return cursor


def connect_to_elasticsearch(**params):
    user = params['user']
    password = params['password']
    url = params['url']

    conn = create_elasticsearch_connection(url, user, password)

    return conn


def write_to_elasticsearch(conn, data):
    columns = data.columns.values.tolist()

    for row in data.itertuples():
        uniq_id = row[0]
        doc = to_dict(row, columns)
        _ = conn.index(index=XEN_INDEX,
                       doc_type='patchserie',
                       id=uniq_id, body=doc)


if __name__ == '__main__':
    main()

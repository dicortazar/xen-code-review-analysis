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
Case of study: Developers

This will provide an index full of information for each developer.

The goal is to have a full idea of how developers and organizations (per domain
initially) deal with the concept of review, to award top ones if required, to
avoid not that useful noise after an ack and to notice those more focused on
reviewing activities or in development of new functionalities.

Each row is based on the following fields:
  * EmailType: 'patch serie', 'patch', 'review' or 'comment'.
  * Developer: email of the developer.
  * Domain: domain of the developer.
  * Time: time when the email was sent.
  * Balance: this contains a -1 if this is patch and a +1 if this is a review.
    Any other 'EmailTYpe' contains a 0.
  * Subject: subject of the email.
  * Flag: for 'review' or 'comment' 'EmailType', this contains the specific
    flag used by the developer if so: eg-'Reviewed-by', etc.
  * Merged: this contains a +1 if this was merged. 0 In any other case.
  * MergeTime: this contains info if the field 'Merged' is +1.
  * PostAck: this contains a +1 if the 'EmailType' is 'comment' or 'review',
    that patch was merged and this comment or review was done after a previous
    review with the flag 'acked-by'.

This is intended to build the following tables:
  * Top reviewers by developer and top reviewers by domain:
       No. reviews, No. patches, No. patch series.
  * Imbalances by developer and by domain: this is an integer providing
    negative or positive values. The more the negative, the more patches
    sent vs reviews done.
  * Post ack by developer and by reviewer.

Also the following charts:
  * Patch evolution
  * Reviews evolution
  * Comments evolution
  * Patch series evolution

And the following tables (searches in Kibana nomenclature) at the very end:
  * Patches
  * Comments
  * Reviews
"""

import argparse

import pandas

from elasticsearch import helpers

from mappings import PS_REVIEWERS_MAPPING
from queries import (QUERY_PATCHSERIES,
                     QUERY_PATCHES,
                     QUERY_FLAGS,
                     QUERY_COMMENTS,
                     QUERY_POST_ACK,
                     QUERY_SELF_COMMENT,
                     QUERY_ACKED_PATCHES)
from utils import (create_mysql_connection,
                   create_elasticsearch_connection,
                   execute_mysql_query,
                   read_config_file,
                   to_dict)


XEN_INDEX = 'xen-patchseries-reviewers'

DF_COMMON_COLUMNS = ["patchserie_id", "patch_id", "comment_id", "subject",
                     "message_id", "sender", "sender_domain", "sent_date",
                     "balance", "flag", "merged", "emailtype", "num_flag_review",
                     "num_flag_ack", "num_patch", "is_acked", "post_ack_comment",
                     "patchserie_numpatches", "patchserie_numackedpatches",
                     "patchserie_percentage_ackedpatches"]
DF_POST_ACK_COLUMNS = ["comment_id", "post_ack_comment"]
DF_COMMNENTS_COLUMNS = ["comment_id", "emailtype"]
DF_ACK_PATCHES_COLUMNS = ["patchserie_id", "patchserie_numackedpatches",
                          "patchserie_numpatches", "patchserie_percentage_ackedpatches"]


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
    data_patchseries = list(execute_mysql_query(cursor, QUERY_PATCHSERIES))
    data_patches = list(execute_mysql_query(cursor, QUERY_PATCHES))
    data_flags = list(execute_mysql_query(cursor, QUERY_FLAGS))
    data_comments = list(execute_mysql_query(cursor, QUERY_COMMENTS))
    data_post_ack = list(execute_mysql_query(cursor, QUERY_POST_ACK))
    data_self_comment = list(execute_mysql_query(cursor, QUERY_SELF_COMMENT))
    data_acked_patches = list(execute_mysql_query(cursor, QUERY_ACKED_PATCHES))

    dfs = {
        'patchseries' : pandas.DataFrame(data_patchseries, columns= DF_COMMON_COLUMNS),
        'patches' : pandas.DataFrame(data_patches, columns=DF_COMMON_COLUMNS),
        'flags' : pandas.DataFrame(data_flags, columns=DF_COMMON_COLUMNS),
        'comments' : pandas.DataFrame(data_comments, columns=DF_COMMON_COLUMNS),
        'post_ack' : pandas.DataFrame(data_post_ack, columns=DF_POST_ACK_COLUMNS),
        'self_comments' : pandas.DataFrame(data_self_comment, columns=DF_COMMNENTS_COLUMNS),
        'acked_patches' : pandas.DataFrame(data_acked_patches, columns=DF_ACK_PATCHES_COLUMNS)
    }

    return dfs


def calculate(dfs):
    # 1. Update values for the post_ack_comments

    # Set index to comment_id
    res_comments = dfs['comments'].set_index("comment_id")
    res_post_ack = dfs['post_ack'].set_index("comment_id")
    res_self_comments = dfs['self_comments'].set_index("comment_id")

    # Let's update the comments index with the post_ack comments
    res_comments.update(res_post_ack)
    # Let's update the comments index with the self_comments data
    res_comments.update(res_self_comments)

    # Reset index and order columns as expected prior the concat action
    reseted_index_comments = res_comments.reset_index()

    # Then I need to move two columns the comments_id column.
    reseted_index_comments = reseted_index_comments[DF_COMMON_COLUMNS]

    # 3. Update values for the acked_patches analysis
    res_patchseries = dfs['patchseries'].set_index("patchserie_id")
    res_acked_patches = dfs['acked_patches'].set_index("patchserie_id")

    # mix  both dataframes
    res_patchseries.update(res_acked_patches)

    # reset index to a generic one
    reseted_index_patchseries = res_patchseries.reset_index()
    # order again the columns
    reseted_index_patchseries = reseted_index_patchseries[DF_COMMON_COLUMNS]

    all_data = pandas.concat([reseted_index_patchseries, dfs['patches'], dfs['flags'], reseted_index_comments])

    return all_data


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
    conn.indices.create(index=XEN_INDEX, body=PS_REVIEWERS_MAPPING,
                        ignore=400)

    columns = data.columns.values.tolist()

    uniq_id = 0
    bulk_doc = []

    for row in data.itertuples():
        uniq_id = uniq_id + 1
        doc = to_dict(row, columns)

        header = {
            "_index": XEN_INDEX,
            "_type": "patchserie",
            "_id": uniq_id,
            "_source": doc
        }

        bulk_doc.append(header)
        if uniq_id % 5000 == 0:
            helpers.bulk(conn, bulk_doc)
            bulk_doc = []

    helpers.bulk(conn, bulk_doc)


if __name__ == '__main__':
    main()

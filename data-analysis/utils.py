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

from __future__ import absolute_import

try:
    import configparser
except ImportError:
    import ConfigParser as configparser

import elasticsearch
import numpy

try:
    import pymysql as mysql
except ImportError:
    import MySQLdb as mysql


def read_config_file(filepath):
    """Read configuration file"""

    cfg_parser = configparser.SafeConfigParser()
    cfg_parser.read(filepath)

    config = {}

    for section in ['mysql', 'elasticsearch']:
        if section not in cfg_parser.sections():
            cause = "Section %s not found in the %s file" % (section, filepath)
            raise KeyError(cause)

        config[section] = dict(cfg_parser.items(section))

    return config


def to_dict(row, columns):
    """Translates from tuple to a dict"""

    d = {}

    for column in columns:
        value = row[columns.index(column) + 1]

        if isinstance(value, numpy.int64):
            value = int(value)
        elif isinstance(value, numpy.float64):
            value = float(value)

        d[column] = value

    return d


def create_mysql_connection(user, password, host, db):
    """Connect to a MySQL server"""

    db = mysql.connect(host=host, user=user, passwd=password, db=db,
                       charset='utf8')
    return db.cursor()


def execute_mysql_query(conn, query):
    """Execute a MySQL query"""

    n = int(conn.execute(query))
    results = conn.fetchall() if n else []
    return results


def create_elasticsearch_connection(url, user, password):
    """Connect to a ES server"""

    conn = elasticsearch.Elasticsearch([url], http_auth=(user, password))
    return conn

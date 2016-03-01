#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2014-2015 Bitergia
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
#     Santiago Dueñas <sduenas@bitergia.com>
#     Daniel Izquierdo <dizquierdo@bitergia.com>
#

import re

import MySQLdb
import MySQLdb.cursors

from argparse import ArgumentParser

from sqlalchemy import Column, DateTime, Integer, String, Text, \
    ForeignKey, create_engine
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.engine.url import URL
from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.pool import NullPool



class Thread(object):

    def __init__(self, root):
        self.root = root

    def __str__(self):
        return self.__pretty_print(self.root)

    def __pretty_print(self, msg, indent=0):
        s = ' ' * indent + str(msg) + '\n'

        for r in msg.responses:
            s += self.__pretty_print(r, indent + 2)
        return s


class Message(object):

    def __init__(self, msg_id):
        self.msg_id = msg_id
        self.subject = None
        self.body = None
        self.date = None
        self.date_tz = None
        self.sender = None
        self.mailing_list = None
        self.responses = []

    def __repr__(self):
        return '<Email %(subject)s - (%(date)s)>' % {'date': str(self.date),
                                                     'subject' : self.subject}


class SCMLog(object):

    def __init__(self, commit_id):
        self.commit_id = commit_id
        self.rev = None
        self.author = None
        self.committer = None
        self.author_date = None
        self.author_date_tz = None
        self.commit_date = None
        self.commit_date_tz = None
        self.message = None

    def __repr__(self):
        return '<SCMLog %(rev)s - (%(date)s)' % {'rev' : self.rev,
                                                 'date' : self.commit_date}


def retrieve_patch_threads(conn, from_date, to_date):
    """Returns a list of threads."""

    def clean_subject(s):
        s = s.replace('\n', ' ')
        s = s.replace('\t', '')
        s = re.sub('\[Xen-devel\].*\[[Pp][aA][tT][cC][hH]', '[PATCH', s)

        return s

    query = """
            SELECT DISTINCT m.message_ID AS msg_id, m.subject AS subject,
                m.message_body AS body, m.first_date AS date, m.first_date_tz as date_tz,
                mp.email_address AS sender,
                m.is_response_of AS is_response_of, m.mailing_list_url AS url
            FROM messages m, messages_people mp
            WHERE m.message_ID = mp.message_id
                AND mp.type_of_recipient = 'From'
                AND first_date >= %s and first_date < %s
                AND subject LIKE '%%[PATCH%%'
            ORDER BY first_date
            """

    cursor = conn.cursor(cursorclass=MySQLdb.cursors.DictCursor)
    cursor.execute(query, [from_date, to_date])
    raw_messages =  cursor.fetchall()

    threads = []
    messages = {}

    for raw_msg in raw_messages:
        msg_id = raw_msg['msg_id']
        is_response_of = raw_msg['is_response_of']

        if msg_id not in messages:
            m = Message(msg_id)
            messages[msg_id] = m
        else:
            m = messages[msg_id]

        m.msg_id = raw_msg["msg_id"]
        m.subject = clean_subject(raw_msg['subject'])
        m.body = raw_msg['body']
        m.date = raw_msg['date']
        m.date_tz = raw_msg['date_tz']
        m.sender = raw_msg['sender']
        m.mailing_list = raw_msg['url']

        # New thread
        if is_response_of is None:
            thread = Thread(m)
            threads.append(thread)
        else:
            if is_response_of not in messages:
                p = Message(is_response_of)
                messages[is_response_of] = p
            else:
                p = messages[is_response_of]

            p.responses.append(m)

    return threads


def retrieve_commits(conn, from_date, to_date):
    """Returns a dict of commits by subject"""

    query = """
            SELECT id AS id, rev AS rev, date AS commit_date, author_date AS author_date,
                date_tz as commit_date_tz, author_date_tz as author_date_tz,
                message AS message, author_id AS author_id, committer_id AS committer_id
            FROM scmlog s
            WHERE date >= %s and date < %s
                AND s.id IN (SELECT DISTINCT(commit_id) FROM actions)
            ORDER BY date
            """

    query_people = """
                   SELECT id, email
                   FROM people
                   """

    cursor = conn.cursor(cursorclass=MySQLdb.cursors.DictCursor)
    cursor.execute(query_people)
    raw_people =  cursor.fetchall()

    people = {rp['id'] : rp['email'] for rp in raw_people}

    cursor.execute(query, [from_date, to_date])
    raw_scmlog = cursor.fetchall()

    scm_logs = []

    for rs in raw_scmlog:
        log = SCMLog(rs['id'])
        log.rev = rs['rev']
        log.author = people[rs['author_id']]
        log.committer = people[rs['committer_id']]
        log.author_date = rs['author_date']
        log.author_date_tz = rs['author_date_tz']
        log.commit_date = rs['commit_date']
        log.commit_date_tz = rs['commit_date_tz']
        log.message = rs['message']

        scm_logs.append(log)

    return scm_logs


# Database model

Base = declarative_base()


class PatchSeries(Base):

    __tablename__ = 'patch_series'
    __table_args__ = ({'mysql_charset': 'utf8'})

    id = Column(Integer, primary_key=True)
    message_id = Column(String(256))
    subject = Column(String(256))
    versions = relationship('PatchSeriesVersion',
                            cascade="save-update, merge, delete")


class PatchSeriesVersion(Base):

    __tablename__ = 'patch_series_version'
    __table_args__ = ({'mysql_charset': 'utf8'})

    id = Column(Integer, primary_key=True)
    version = Column(Integer)
    subject = Column(String(256))
    body = Column(Text)
    date = Column(DateTime)
    date_tz = Column(Integer)
    ps_id = Column(Integer,
                   ForeignKey('patch_series.id', ondelete='CASCADE'),)

    patch_series = relationship('PatchSeries', foreign_keys=[ps_id])
    patches = relationship('Patch',
                            cascade="save-update, merge, delete")


class Patch(Base):

    __tablename__ = 'patches'
    __table_args__ = ({'mysql_charset': 'utf8'})

    id = Column(Integer, primary_key=True)
    message_id = Column(String(256))
    subject = Column(String(256))
    body = Column(Text)
    series = Column(Integer)
    total = Column(Integer)
    date = Column(DateTime)
    date_tz = Column(Integer)
    ps_version_id = Column(Integer,
                           ForeignKey('patch_series_version.id', ondelete='CASCADE'),)
    submitter_id = Column(Integer,
                          ForeignKey('people.id', ondelete='CASCADE'),)
    commit_id = Column(Integer,
                       ForeignKey('commits.id', ondelete='CASCADE'),)

    patch_series = relationship('PatchSeriesVersion', foreign_keys=[ps_version_id])
    submitter = relationship('Member', foreign_keys=[submitter_id])
    commit = relationship('Commit', foreign_keys=[commit_id])
    comments = relationship('Comment',
                            cascade="save-update, merge, delete")
    flags = relationship('Flag',
                         cascade="save-update, merge, delete")


class Comment(Base):
    __tablename__ = 'comments'
    __table_args__ = ({'mysql_charset': 'utf8'})

    id = Column(Integer, primary_key=True)
    message_id = Column(String(256))
    subject = Column(String(256))
    body = Column(Text)
    date = Column(DateTime)
    date_tz = Column(Integer)
    patch_id = Column(Integer,
                      ForeignKey('patches.id', ondelete='CASCADE'),)
    submitter_id = Column(Integer,
                          ForeignKey('people.id', ondelete='CASCADE'),)

    patch = relationship('Patch', foreign_keys=[patch_id])
    submitter = relationship('Member', foreign_keys=[submitter_id])


class Flag(Base):
    __tablename__ = 'flags'
    __table_args__ = ({'mysql_charset': 'utf8'})

    id = Column(Integer, primary_key=True)
    flag = Column(String(64))
    value = Column(String(256))
    date = Column(DateTime)
    date_tz = Column(Integer)

    patch_id = Column(Integer,
                      ForeignKey('patches.id', ondelete='CASCADE'),)

    #member_id = Column(Integer,
    #                   ForeignKey('people.id', ondelete='CASCADE'),)

    patch = relationship('Patch', foreign_keys=[patch_id])
    #member = relationship('Member', foreign_keys=[member_id])


class Commit(Base):
    __tablename__ = 'commits'
    __table_args__ = ({'mysql_charset': 'utf8'})

    id = Column(Integer, primary_key=True)
    rev = Column(String(256))
    subject = Column(String(256))
    author_date = Column(DateTime)
    author_date_tz = Column(Integer)
    committer_date = Column(DateTime)
    committer_date_tz = Column(Integer)

    author_id = Column(Integer,
                       ForeignKey('people.id', ondelete='CASCADE'),)
    committer_id = Column(Integer,
                          ForeignKey('people.id', ondelete='CASCADE'),)

    author = relationship('Member', foreign_keys=[author_id])
    committer = relationship('Member', foreign_keys=[committer_id])
    patches = relationship('Patch',
                           cascade="save-update, merge, delete")


class Member(Base):
    __tablename__ = 'people'
    __table_args__ = ({'mysql_charset': 'utf8'})

    id = Column(Integer, primary_key=True)
    email = Column(String(256))


# Database management

class Database(object):

    def __init__(self, user, password, database, host='localhost', port='3306'):
        # Create an engine
        self.url = URL('mysql', user, password, host, port, database,
                       query={'charset' : 'utf8'})
        self._engine = create_engine(self.url, poolclass=NullPool, echo=False)
        self._Session = sessionmaker(bind=self._engine)

        # Create the schema on the database.
        # It won't replace any existing schema
        try:
            Base.metadata.create_all(self._engine)
        except OperationalError, e:
            raise DatabaseError(error=e.orig[1], code=e.orig[0])

    def connect(self):
        return self._Session()

    def store(self, session, obj):
        try:
            session.add(obj)
            session.commit()
        except:
            session.rollback()
            raise

    def clear(self):
        session = self._Session()

        for table in reversed(Base.metadata.sorted_tables):
            session.execute(table.delete())
            session.commit()
        session.close()


class DatabaseError(Exception):
    """Database error exception"""

    def __init__(self, error, code):
        super(DatabaseError, self).__init__()
        self.error = error
        self.code = code

    def __str__(self):
        return "%(error)s (err: %(code)s)" % {'error' : self.error,
                                              'code' : self.code}



class PatchesParser(object):

    THREAD_REGEX = '^\[PATCH.*].+$'
    #PATCH_REGEX = '^.*\[PATCH\s*(?:\s+for[\-\s]\d+\.\d+)?\s*(?:[vV](?P<version>\d+))?\s*(?:(?P<num>\d+)/(?P<total>\d+))?\]\s*(?P<subject>.+)$'
    TYPE = '(OSSTEST|MINI-OS|raisin|iommu|OPW|ARM)*'
    PATCH_REGEX = '^.*\[\s*'+TYPE+'\s*PATCH\s*'+TYPE+'\s*(?:\s+for[\-\s]\d+\.\d+)?\s*(?:[vV](?P<version>\d+))?\s*(?:(?P<num>\d+)/(?P<total>\d+))?\]\s*(?P<subject>.+)$'
    FLAGS_REGEX = {
                   'Acked-by' : '^Acked-by:(?P<value>.+)$',
                   'Cc' : '^Cc:(?P<value>.+)',
                   'Fixes' : '^Fixes:(?P<value>.+)$',
                   'From' : '^[Ff]rom:(?P<value>.+)$',
                   'Reported-by' : '^Reported-by:(?P<value>.+)$',
                   'Tested-by' : '^Tested-by:(?P<value>.+)$',
                   'Reviewed-by' : '^Reviewed-by:(?P<value>.+)$',
                   'Release-Acked-by' : '^Release-Acked-by:(?P<value>.+)$',
                   'Signed-off-by' : '^Signed-off-by:(?P<value>.+)$',
                   'Suggested-by' : '^Suggested-by:(?P<value>.+)$',
                   }

    def __init__(self):
        self.members = {}
        self.commits = {}

    def parse(self, threads, commits):
        """Parse a list of threads"""

        patches_series = []

        self.commits = self.__parse_commits(commits)

        for th in threads:
            root = th.root

            m = re.match(self.THREAD_REGEX, root.subject)

            if not m:
                print "ERROR: not valid thread - %s" % root.subject
                continue

            try:
                parts = self.__parse_patch_subject(root)
            except Exception, e:
                print "Thread error", e
                continue

            patches = []

            if parts['num'] == 0:
                for msg in root.responses:
                    try:
                        patch = self.__parse_patch(msg)
                        patches.append(patch)
                    except Exception, e:
                        print e
                        continue
            else:
                try:
                    patch = self.__parse_patch(root)
                    patches.append(patch)
                except Exception, e:
                    print e
                    continue

            # New patch series
            psv = PatchSeriesVersion(version=parts['version'],
                                     subject=root.subject,
                                     body=root.body,
                                     date=root.date,
                                     date_tz=root.date_tz)

            for p in patches:
                psv.patches.append(p)

            # Find the patch series
            ps = None

            if parts['version'] > 1:
                for o in patches_series:
                    if o.subject == parts['subject']:
                        ps = o
                        break

            # Not found, so create a new one
            if ps is None:
                # root message_id
                root_message_id = root.msg_id
                ps = PatchSeries(message_id=root_message_id,
                                 subject=parts['subject'])

            ps.versions.append(psv)

            patches_series.append(ps)

        return self.commits, patches_series

    def __parse_patch_subject(self, patch):
        """Parse and split patch subject"""

        m = re.match(self.PATCH_REGEX, patch.subject)

        if not m:
            raise Exception("Error parsing header: %s" % patch.subject)

        to_int = lambda x, y: int(x) if x else y

        return {'subject' : m.group('subject'),
                'version' : to_int(m.group('version'), 1),
                'num'     : to_int(m.group('num'), None),
                'total'   : to_int(m.group('total'), None)}

    def __parse_patch(self, msg):
        """Get the patch from a message"""

        parts = self.__parse_patch_subject(msg)

        patch = Patch(message_id = msg.msg_id, subject=msg.subject,
                      body=msg.body, series=parts['num'],
                      total=parts['total'], date=msg.date,
                      date_tz=msg.date_tz)

        member = self.members.get(msg.sender, None)

        if not member:
            member = Member(email=msg.sender)
            self.members[member.email] = member

        patch.submitter = member

        flags = self.__parse_flags(msg)
        for f in flags:
            patch.flags.append(f)

        comments, flags = self.__parse_responses(msg)

        for c in comments:
            patch.comments.append(c)
        for f in flags:
            patch.flags.append(f)

        key = to_key(parts['subject'])

        commit = self.commits.get(key, None)

        if commit:
            commit.patches.append(patch)

        return patch

    def __parse_responses(self, root):
        """Parse responses from a list of nested messages"""

        comments = []
        flags = []
        to_parse = root.responses[:]

        while to_parse:
            m = to_parse.pop(0)
            to_parse.extend(m.responses[:])

            comment = Comment(message_id=m.msg_id, subject=m.subject,
                              body=m.body, date=m.date, date_tz=m.date_tz)
            member = self.members.get(m.sender, None)

            if not member:
                member = Member(email=m.sender)
                self.members[member.email] = member

            comment.submitter = member

            comments.append(comment)

            fgs = self.__parse_flags(m)
            flags.extend(fgs)

        return comments, flags

    def __parse_flags(self, msg):
        """Parse flags from a messages"""

        flags = []
        lines = msg.body.split('\n')

        for l in lines:
            for name in self.FLAGS_REGEX:
                m = re.match(self.FLAGS_REGEX[name], l)

                if m:
                    flag = Flag(flag=name, value=m.group('value'), date=msg.date, date_tz =msg.date_tz)
                    flags.append(flag)

        return flags

    def __parse_commits(self, scm_logs):
        commits = {}

        for log in scm_logs:
            subject = log.message.split('\n')[0].strip()

            commit = Commit(rev=log.rev, subject=subject,
                            author_date=log.author_date,
                            committer_date=log.commit_date,
                            author_date_tz=log.author_date_tz,
                            committer_date_tz=log.commit_date_tz)

            author = self.members.get(log.author, None)

            if not author:
                author = Member(email=log.author)
                self.members[author.email] = author

            committer = self.members.get(log.committer, None)

            if not committer:
                committer = Member(email=log.committer)
                self.members[committer.email] = committer

            commit.author = author
            commit.committer = committer

            key = to_key(subject)

            commits[key] = commit

        return commits

def to_key(s):
    import nltk
    import string

    key = s.lower()
    key = key.replace('"', "'")
    key = key[:-1] if key.endswith('.') else key
    key = key[key.rfind(': ') + 2:]
    key = key.replace('/', "")
    key = key.replace(" ", "")
    key = key.replace('\n', "")
    key = key.replace('\t', "")
    key = key.replace('.', "")
    key = key.replace("_", "")
    key = key.lstrip()
    key = key.rstrip()

    #punctuations = list(string.punctuation)
    #for punctuation in punctuations:
    #    key = key.replace(punctuation, "")

    return key

def parse_args():
    parser = ArgumentParser(usage="Usage: '%(prog)s [options] <threads_db>")

    # Database options
    group = parser.add_argument_group('Database options')
    group.add_argument('-u', '--user', dest='db_user',
                       help='Database user name',
                       default='root')
    group.add_argument('-p', '--password', dest='db_password',
                       help='Database user password',
                       default='')
    group.add_argument('-d', dest='db_name', required=True,
                       help='Name of the database where data will be stored')
    group.add_argument('--host', dest='db_hostname',
                       help='Name of the host where the database server is running',
                       default='localhost')
    group.add_argument('--port', dest='db_port',
                       help='Port of the host where the database server is running',
                       default='3306')

    # Positional arguments
    parser.add_argument('threads_db', help='Threads database')
    parser.add_argument('commits_db', help='Commits database')

    # Parse arguments
    args = parser.parse_args()

    return args


def main():
    args = parse_args()

    try:
        db = Database(args.db_user, args.db_password, args.db_name,
                      args.db_hostname, args.db_port)
    except DatabaseError, e:
        raise RuntimeError(str(e))

    conn = MySQLdb.connect(user=args.db_user, passwd=args.db_password,
                           db=args.threads_db)
    threads = retrieve_patch_threads(conn, "2010-01-01", "2100-01-01")

    conn = MySQLdb.connect(user=args.db_user, passwd=args.db_password,
                           db=args.commits_db)
    commits = retrieve_commits(conn, "2010-01-01", "2100-01-01")

    parser = PatchesParser()
    commits, patches_series = parser.parse(threads, commits)

    db.clear()
    session = db.connect()

    for ps in patches_series:
        db.store(session, ps)
    for c in commits.values():
        db.store(session, c)


if __name__ == '__main__':
    main()


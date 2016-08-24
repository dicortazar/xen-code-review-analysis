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

QUERY_PATCHSERIES = """SELECT ps.id as patchserie_id,
                              -1 as patch_id,
                              -1 as comment_id,
                              ps.subject as subject,
                              ps.message_id as message_id,
                              pe.email as sender,
                              SUBSTRING_INDEX(pe.email, '@', -1) as sender_domain,
                              MIN(psv.date_utc) as sent_date,
                              0 as balance,
                              'na' as flag,
                              IF(p.commit_id IS NULL, 0, 1) as merged,
                              'patchserie' as emailtype,
                              0 as num_flag_review,
                              0 as num_flag_ack,
                              0 as num_patches,
                              -1 as is_acked,
                              -1 as post_ack_comment,
                              0 as patchserie_numpatches,
                              0 as patchserie_numackedpatches,
                              0 as patchserie_percentage_ackedpatches
                       FROM  patch_series ps,
                             patch_series_version psv,
                             patches p,
                             people pe
                       WHERE pe.id = p.submitter_id AND
                             p.ps_version_id = psv.id AND
                             psv.ps_id = ps.id
                       GROUP BY ps.id"""


QUERY_PATCH_SERIE = """SELECT ps.id as patchserie_id,
                              ps.message_id as message_id,
                              ps.subject as patchserie_subject,
                              pe.email as patchserie_sender,
                              SUBSTRING_INDEX(pe.email, '@', -1) as sender_domain,
                              MIN(psv.date_utc) as patchserie_sent_date,
                              MAX(t1.patches) as patchserie_numpatches,
                              COUNT(DISTINCT(version)) as patchserie_versions,
                              COUNT(DISTINCT(c.id)) as patchserie_comments,
                              COUNT(DISTINCT(c.submitter_id)) as patchserie_commenters
                       FROM patch_series ps,
                            patch_series_version psv,
                            patches p,
                            people pe,
                            comments c,
                            (SELECT psv.ps_id,
                                    p.ps_version_id,
                                    COUNT(DISTINCT(p.id)) as patches
                             FROM patch_series_version psv,
                                  patches p
                             WHERE psv.id = p.ps_version_id
                             GROUP BY psv.ps_id,
                                   p.ps_version_id) t1
                       WHERE ps.id = psv.ps_id AND
                             psv.id = p.ps_version_id AND
                             p.ps_version_id = t1.ps_version_id AND
                             p.id = c.patch_id AND
                             p.submitter_id = pe.id
                       GROUP BY ps.id"""


QUERY_PATCHES = """SELECT psv.ps_id as patchserie_id,
                          p.id as patch_id,
                          -1 as comment_id,
                          p.subject as subject,
                          p.message_id as message_id,
                          pe.email as sender,
                          SUBSTRING_INDEX(pe.email, '@', -1) as sender_domain,
                          p.date_utc as sent_date,
                          -1 as balance,
                          'na' as flag,
                          IF(p.commit_id IS NULL, 0, 1) as merged,
                          'patch' as emailtype,
                          0 as num_flag_review,
                          0 as num_flag_ack,
                          1 as num_patch,
                          IF(t.flag='Acked-by', 1, 0) as is_acked,
                          0 as post_ack_comment,
                          -1 as patchserie_numpatches,
                          -1 as patchserie_numackedpatches,
                          -1 as patchserie_percentage_ackedpatches
                   FROM patch_series_version psv,
                        patches p,
                        people pe,
                        (SELECT p.id as patch_id,
                                f.flag as flag
                         FROM patches p
                         LEFT JOIN flags f
                             ON p.id = f.patch_id AND
                                f.flag = 'Acked-by') t
                   WHERE p.submitter_id = pe.id AND
                         psv.id = p.ps_version_id AND
                         p.id = t.patch_id"""


QUERY_FLAGS = """SELECT psv.ps_id as patchserie_id,
                        patch_id as patch_id,
                        -1 as comment_id,
                        p.subject as subject,
                        'na' as message_id,
                        SUBSTRING_INDEX(SUBSTRING_INDEX(value, '<', -1), '>', 1) as sender,
                        SUBSTRING_INDEX(SUBSTRING_INDEX(SUBSTRING_INDEX(value, '<', -1), '>', 1), '@', -1) as sender_domain,
                        f.date_utc as sent_date,
                        IF(flag = 'Reviewed-by', 1, 0) as balance,
                        flag as flag,
                        -1 as merged,
                        'flag' as emailtype,
                        IF(flag = 'Reviewed-by', 1, 0) as num_flag_review,
                        IF(flag = 'Acked-by', 1, 0) as num_flag_ack,
                        0 as num_patch,
                        -1 as is_acked,
                        -1 as post_ack_comment,
                        -1 as patchserie_numpatches,
                        -1 as patchserie_numackedpatches,
                        -1 as patchserie_percentage_ackedpatches
                 FROM patch_series_version psv,
                      patches p,
                      flags f
                 WHERE psv.id = p.ps_version_id AND
                       p.id = f.patch_id"""


QUERY_COMMENTS = """SELECT psv.ps_id as patchserie_id,
                           c.patch_id as patch_id,
                           c.id as comment_id,
                           c.subject as subject,
                           c.message_id as message_id,
                           pe.email as sender,
                           SUBSTRING_INDEX(pe.email, '@', -1) as sender_domain,
                           c.date_utc as sent_date,
                           0 as balance,
                           'na' as flag,
                           -1 as merged,
                           'comment' as emailtype,
                           0 as num_flag_review,
                           0 as num_flag_ack,
                           0 as num_patch,
                           -1 as is_acked,
                           0 as post_ack_comment,
                           -1 as patchserie_numpatches,
                           -1 as patchserie_numackedpatches,
                           -1 as patchserie_percentage_ackedpatches
                    FROM patch_series_version psv,
                         patches p,
                         people pe,
                         comments c
                    WHERE psv.id = p.ps_version_id AND
                          p.id = c.patch_id AND
                          c.submitter_id = pe.id"""


QUERY_POST_ACK = """SELECT comments.id as comment_id,
                           1 as post_ack_comment
                    FROM comments left join
                        (SELECT patch_id,
                                MIN(date) as first_ack_date
                         FROM flags
                         WHERE flag='Acked-by'
                         GROUP BY patch_id) t
                    ON t.patch_id=comments.patch_id
                    WHERE date > t.first_ack_date"""


"""
Query to detect those comments that are sent by the same
developer that sent the original patch.
"""
QUERY_SELF_COMMENT = """SELECT c.id as comment_id,
                               'self-comment' as emailtype
                        FROM comments c,
                             patches p
                        WHERE c.submitter_id = p.submitter_id AND
                              p.id = c.patch_id
                        ORDER BY comment_id"""


"""
Query to detect the number of ack-ed patches from a patchserie
"""
QUERY_ACKED_PATCHES = """SELECT psv.ps_id as patchserie_id,
                                IF(count(distinct(p.series)) = 0, 1, count(distinct(p.series))) as acked_patches,
                                t1.total_num_patches as total_num_patches,
                                IFNULL(TRUNCATE(((IF(count(distinct(p.series)) = 0, 1, count(distinct(p.series)))/t1.total_num_patches)*100), 0), 0) as percentage_acked_patches
                         FROM patch_series_version psv,
                              patches p,
                              flags f,
                              (SELECT psv.ps_id,
                                      IF(count(distinct(p.series))=0, 1, count(distinct(p.series)))  as total_num_patches
                               FROM patch_series_version psv,
                                    patches p
                               WHERE psv.id=p.ps_version_id
                               GROUP BY psv.ps_id) t1
                         WHERE f.patch_id=p.id AND
                               f.flag='Acked-by' AND
                               psv.id=p.ps_version_id AND
                               psv.ps_id=t1.ps_id
                         GROUP BY psv.ps_id"""


QUERY_TIME2MERGE = """SELECT psv.ps_id as patch_serie,
                             TIMESTAMPDIFF(SECOND, MIN(psv.date_utc), MAX(c.committer_date_utc)) as time2merge,
                             MIN(psv.date_utc) as first_patch_date,
                             MAX(c.committer_date_utc) as merge_time
                      FROM patch_series_version psv,
                           patches p,
                           commits c
                      WHERE psv.id=p.ps_version_id AND
                            p.commit_id = c.id
                      GROUP BY psv.ps_id"""


QUERY_TIME2COMMIT = """SELECT psv.ps_id as patch_serie,
                              TIMESTAMPDIFF(SECOND, MAX(c.date_utc), MAX(commits.committer_date_utc)) as time2commit,
                              MAX(c.date_utc) as last_comment_date,
                              MAX(commits.committer_date_utc) as commit_time
                       FROM patch_series_version psv,
                            patches p,
                            comments c,
                            commits
                       WHERE psv.id = p.ps_version_id AND
                             p.commit_id = commits.id AND
                             p.id=c.patch_id
                       GROUP BY psv.ps_id
                       HAVING time2commit >= 0 and time2commit < 2000*3600*24"""


QUERY_PEOPLE = """SELECT p.subject as patch_subject,
                         p.message_id as message_id,
                         p.date_utc as patch_sent_date,
                         pe.email as patch_sender,
                         SUBSTRING_INDEX(pe.email, '@', -1) as patch_sender_domain,
                         ps.id as patchserie_id,
                         ps.subject as patchserie_subject,
                         MIN(psv.date_utc) as patchserie_sent_date,
                         t1.email as patch_comment_sender,
                         t1.domain as patch_comment_domain,
                         t1.comment_date as patch_comment_date,
                         TIMESTAMPDIFF(SECOND, p.date_utc, t1.comment_date) as patch_time2comment
                  FROM patch_series ps,
                       patch_series_version psv,
                       patches p,
                       people pe,
                       (SELECT p.id as patch_id,
                               pe.email as email,
                               SUBSTRING_INDEX(pe.email, '@', -1) as domain,
                               c.date_utc as comment_date
                        FROM patches p,
                             comments c,
                             people pe
                        WHERE c.patch_id = p.id and
                              c.submitter_id = pe.id) t1
                  WHERE ps.id = psv.ps_id AND
                        psv.id = p.ps_version_id AND
                        p.submitter_id = pe.id AND
                        p.id = t1.patch_id
                  GROUP BY p.id"""

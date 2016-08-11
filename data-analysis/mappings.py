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

PS_REVIEWERS_MAPPING = {
    "mappings" : {
        "patchserie" : {
            "properties" : {
                "balance" : {
                        "type": "long"
                },
                "comment_id": {
                    "type": "long"
                },
                "emailtype": {
                    "index": "not_analyzed",
                    "type": "string"
                },
                "flag": {
                    "index": "not_analyzed",
                    "type": "string"
                },
                "is_acked": {
                    "type": "long"
                },
                "merged": {
                    "type": "long"
                },
                "message_id": {
                    "index": "not_analyzed",
                    "type": "string"
                },
                "num_flag_ack": {
                    "type": "long"
                },
                "num_flag_review": {
                    "type": "long"
                },
                "num_patch": {
                    "type": "long"
                },
                "patch_id": {
                    "type": "long"
                },
                "patchserie_id": {
                    "type": "long"
                },
                "patchserie_numackedpatches": {
                    "type": "double"
                },
                "patchserie_numpatches": {
                    "type": "double"
                },
                "patchserie_percentage_ackedpatches": {
                    "type": "long"
                },
                "post_ack_comment": {
                    "type": "double"
                },
                "sender": {
                    "index": "not_analyzed",
                    "type": "string"
                },
                "sender_domain": {
                    "index": "not_analyzed",
                    "type": "string"
                },
                "sent_date": {
                    "format": "strict_date_optional_time||epoch_millis",
                    "type": "date"
                },
                "subject": {
                    "index": "not_analyzed",
                    "type": "string"
                }
            }
        }
    }
}
{
    "xen-patchseries-timefocused": {
        "mappings": {
            "patchserie": {
                "properties": {
                    "committime": {
                        "format": "strict_date_optional_time||epoch_millis",
                        "type": "date"
                    },
                    "lastcommentdate": {
                        "format": "strict_date_optional_time||epoch_millis",
                        "type": "date"
                    },
                    "mergetime": {
                        "format": "strict_date_optional_time||epoch_millis",
                        "type": "date"
                    },
                    "message_id": {
                        "index": "not_analyzed",
                        "type": "string"
                    },
                    "num_commenters": {
                        "type": "long"
                    },
                    "num_comments": {
                        "type": "long"
                    },
                    "num_patches": {
                        "type": "long"
                    },
                    "num_versions": {
                        "type": "long"
                    },
                    "patchserie_id": {
                        "type": "long"
                    },
                    "sender": {
                        "index": "not_analyzed",
                        "type": "string"
                    },
                    "sender_domain": {
                        "index": "not_analyzed",
                        "type": "string"
                    },
                    "sent_date_x": {
                        "format": "strict_date_optional_time||epoch_millis",
                        "type": "date"
                    },
                    "sent_date_y": {
                        "format": "strict_date_optional_time||epoch_millis",
                        "type": "date"
                    },
                    "subject": {
                        "index": "not_analyzed",
                        "type": "string"
                    },
                    "time2commit": {
                        "type": "double"
                    },
                    "time2merge": {
                        "type": "double"
                    }
                }
            }
        }
    }
}

PS_TIMEFOCUSED_MAPPING = {
    "mappings": {
        "patchserie": {
            "properties": {
                "committime": {
                    "format": "strict_date_optional_time||epoch_millis",
                    "type": "date"
                },
                "lastcommentdate": {
                    "format": "strict_date_optional_time||epoch_millis",
                    "type": "date"
                },
                "mergetime": {
                    "format": "strict_date_optional_time||epoch_millis",
                    "type": "date"
                },
                "message_id": {
                    "index": "not_analyzed",
                    "type": "string"
                },
                "num_commenters": {
                    "type": "long"
                },
                "num_comments": {
                    "type": "long"
                },
                "num_patches": {
                    "type": "long"
                },
                "num_versions": {
                    "type": "long"
                },
                "patchserie_id": {
                    "type": "long"
                },
                "sender": {
                    "index": "not_analyzed",
                    "type": "string"
                },
                "sender_domain": {
                    "index": "not_analyzed",
                    "type": "string"
                },
                "sent_date_x": {
                    "format": "strict_date_optional_time||epoch_millis",
                    "type": "date"
                },
                "sent_date_y": {
                    "format": "strict_date_optional_time||epoch_millis",
                    "type": "date"
                },
                "subject": {
                    "index": "not_analyzed",
                    "type": "string"
                },
                "time2commit": {
                    "type": "double"
                },
                "time2merge": {
                    "type": "double"
                }
            }
        }
    }
}

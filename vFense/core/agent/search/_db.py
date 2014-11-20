from vFense.db.client import db_create_close, r
from vFense.core.agent._constants import AgentCommonKeys
from vFense.core.agent._db_model import (
    AgentKeys, AgentCollections,
    HardwarePerAgentIndexes, HardwarePerAgentKeys
)
from vFense.core.tag._db_model import (
    TagCollections, TagKeys, TagsPerAgentKeys, TagsPerAgentIndexes
)
from vFense.plugins.patching._db_model import (
    AppCollections, AppsKey, AppsPerAgentIndexes
)
from vFense.plugins.patching._db_model import *
from vFense.plugins.patching._constants import CommonAppKeys
from vFense.core.decorators import time_it, catch_it
from vFense.search._db_base import FetchBase


class FetchAgents(FetchBase):
    """Agent database queries"""
    def __init__(self, **kwargs):
        super(FetchAgents, self).__init__(**kwargs)

        self.keys_to_pluck = [
            AgentKeys.ComputerName, AgentKeys.HostName,
            AgentKeys.DisplayName, AgentKeys.OsCode, AgentKeys.Tags,
            AgentKeys.OsString, AgentKeys.AgentId, AgentKeys.AgentStatus,
            AgentKeys.NeedsReboot, AgentKeys.Environment,
            AgentCommonKeys.AVAIL_UPDATES, AgentCommonKeys.AVAIL_VULN,
            AgentKeys.LastAgentUpdate, AgentKeys.DateAdded
        ]

    @time_it
    @catch_it((0, []))
    @db_create_close
    def by_id(self, agent_id, conn=None):
        """Retrieve an agent by its id and all of its properties.
        Args:
            agent_id (str): 36 character UUID of the agent.

        Basic Usage:
            >>> from vFense.agent.search._db import FetchAgents
            >>> agent = FetchAgents()
            >>> agent.by_id('96f02bcf-2ada-465c-b175-0e5163b36e1c')

        Returns:
            Tuple
            (count, group_data)
        >>>
        """
        base_filter = (
            r
            .table(AgentCollections.Agents)
        )
        merge_query = self._set_merge_query()
        agent_merge_query = self._set_agent_merge_query()

        count = (
            base_filter
            .get_all(agent_id)
            .count()
            .run(conn)
        )

        data = list(
            base_filter
            .get_all(agent_id)
            .merge(merge_query)
            .merge(agent_merge_query)
            .run(conn)
        )

        return(count, data)

    @time_it
    @catch_it((0, []))
    @db_create_close
    def by_name(self, name, conn=None):
        """Query agents by computer or display name.
        Args:
            name (str): The regex you are searching by

        Basic Usage:
            >>> from vFense.core.agent.search._db import FetchAgents
            >>> view_name = 'default'
            >>> search_agents = FetchAgents(view_name='default')
            >>> search_agents.by_name('ubu')

        Returns:
            List of dictionairies.
            [
                {
                    "display_name": null,
                    "environment": "Production",
                    "tags": [
                        {
                            "tag_name": "Foo Bar",
                            "tag_id": "6ef12d9d-a5a0-49c8-9890-206a7b362ce4"
                        }
                    ],
                    "available_vulnerabilities": 8,
                    "os_code": "linux",
                    "available_updates": 17,
                    "agent_status": "up",
                    "agent_id": "d4119b36-fe3c-4973-84c7-e8e3d72a3e02",
                    "computer_name": "ubuntu",
                    "os_string": "Ubuntu 12.04",
                    "needs_reboot": "no",
                    "host_name": ""
                }
            ]
        """
        merge_query = self._set_merge_query()
        base_filter = self._set_agent_base_query()
        count = (
            base_filter
            .filter(
                (r.row[AgentKeys.ComputerName].match("(?i)^"+name))
                |
                (r.row[AgentKeys.DisplayName].match("(?i)^"+name))
            )
            .count()
            .run(conn)
        )

        data = list(
            base_filter
            .filter(
                (r.row[AgentKeys.ComputerName].match("(?i)^"+name))
                |
                (r.row[AgentKeys.DisplayName].match("(?i)^"+name))
            )
            .order_by(self.sort(self.sort_key))
            .skip(self.offset)
            .limit(self.count)
            .merge(merge_query)
            .pluck(self.keys_to_pluck)
            .run(conn)
        )

        return(count, data)

    @time_it
    @catch_it((0, []))
    @db_create_close
    def all(self, conn=None):
        """Retrieve all agents.
        Basic Usage:
            >>> from vFense.core.agent.search._db import FetchAgents
            >>> view_name = 'default'
            >>> search_agents = FetchAgents(view_name='default')
            >>> search_agents.all()

        Returns:
            List of dictionairies.
            [
                {
                    "display_name": null,
                    "environment": "Production",
                    "tags": [
                        {
                            "tag_name": "Foo Bar",
                            "tag_id": "6ef12d9d-a5a0-49c8-9890-206a7b362ce4"
                        }
                    ],
                    "available_vulnerabilities": 8,
                    "os_code": "linux",
                    "available_updates": 17,
                    "agent_status": "up",
                    "agent_id": "d4119b36-fe3c-4973-84c7-e8e3d72a3e02",
                    "computer_name": "ubuntu",
                    "os_string": "Ubuntu 12.04",
                    "needs_reboot": "no",
                    "host_name": ""
                }
            ]

        """
        base_filter = self._set_agent_base_query()
        query_merge = self._set_merge_query()
        count = (
            base_filter
            .count()
            .run(conn)
        )

        data = list(
            base_filter
            .merge(query_merge)
            .order_by(AgentKeys.ComputerName)
            .pluck(self.keys_to_pluck)
            .order_by(self.sort(self.sort_key))
            .skip(self.offset)
            .limit(self.count)
            .run(conn)
        )

        return(count, data)

    @time_it
    @catch_it((0, []))
    @db_create_close
    def by_key_and_val(self, fkey, fval, conn=None):
        """Filter agents by a key and value.
        Args:
            fkey (str): The key you are filtering on.
            fval (str): The value for the key you are filtering on.

        Basic Usage:
            >>> from vFense.core.agent.search._db import FetchAgents
            >>> view_name = 'default'
            >>> fkey = 'os_code'
            >>> fval = 'linux'
            >>> search_agents = FetchAgents(view_name='default')
            >>> search_agents.by_key_and_val(fkey, fval)

        Returns:
            List of dictionairies.
            [
                {
                    "display_name": null,
                    "environment": "Production",
                    "tags": [
                        {
                            "tag_name": "Foo Bar",
                            "tag_id": "6ef12d9d-a5a0-49c8-9890-206a7b362ce4"
                        }
                    ],
                    "available_vulnerabilities": 8,
                    "os_code": "linux",
                    "available_updates": 17,
                    "agent_status": "up",
                    "agent_id": "d4119b36-fe3c-4973-84c7-e8e3d72a3e02",
                    "computer_name": "ubuntu",
                    "os_string": "Ubuntu 12.04",
                    "needs_reboot": "no",
                    "host_name": ""
                }
            ]
        """
        base_filter = self._set_agent_base_query()
        query_merge = self._set_merge_query()
        count = (
            base_filter
            .filter({fkey: fval})
            .count()
            .run(conn)
        )

        data = list(
            base_filter
            .filter({fkey: fval})
            .merge(query_merge)
            .pluck(self.keys_to_pluck)
            .order_by(self.sort(self.sort_key))
            .skip(self.offset)
            .limit(self.count)
            .run(conn)
        )

        return(count, data)

    @time_it
    @catch_it((0, []))
    @db_create_close
    def by_key_and_value_and_query(self, fkey, fval, query, conn=None):
        """Filter agents based on a key and value, while
            searching by computer and display name.
        Args:
            fkey (str): The key you are filtering on.
            fval (str): The value for the key you are filtering on.

        Basic Usage:
            >>> from vFense.core.agent.search._db import FetchAgents
            >>> view_name = 'default'
            >>> fkey = 'os_code'
            >>> fval = 'linux'
            >>> query = 'ubu'
            >>> search_agents = FetchAgents(view_name='default')
            >>> search_agents.by_key_and_value_and_query(fkey, fval, query)

        Returns:
            List of dictionairies.
            [
                {
                    "display_name": null,
                    "environment": "Production",
                    "tags": [
                        {
                            "tag_name": "Foo Bar",
                            "tag_id": "6ef12d9d-a5a0-49c8-9890-206a7b362ce4"
                        }
                    ],
                    "available_vulnerabilities": 8,
                    "os_code": "linux",
                    "available_updates": 17,
                    "agent_status": "up",
                    "agent_id": "d4119b36-fe3c-4973-84c7-e8e3d72a3e02",
                    "computer_name": "ubuntu",
                    "os_string": "Ubuntu 12.04",
                    "needs_reboot": "no",
                    "host_name": ""
                }
            ]
        """
        base_filter = self._set_agent_base_query()
        query_merge = self._set_merge_query()
        count = (
            base_filter
            .filter({fkey: fval})
            .filter(
                (r.row[AgentKeys.ComputerName].match("(?i)^"+query))
                |
                (r.row[AgentKeys.DisplayName].match("(?i)^"+query))
            )
            .count()
            .run(conn)
        )

        data = list(
            base_filter
            .filter({fkey: fval})
            .filter(
                (r.row[AgentKeys.ComputerName].match("(?i)^"+query))
                |
                (r.row[AgentKeys.DisplayName].match("(?i)^"+query))
            )
            .merge(query_merge)
            .pluck(self.keys_to_pluck)
            .order_by(self.sort(self.sort_key))
            .skip(self.offset)
            .limit(self.count)
            .run(conn)
        )

        return(count, data)

    @time_it
    @catch_it((0, []))
    @db_create_close
    def by_ip(self, ip, conn=None):
        """Search agents based on an ip address.
        Args:
            ip (str): The ip address you are searching for.

        Basic Usage:
            >>> from vFense.core.agent.search._db import FetchAgents
            >>> view_name = 'default'
            >>> ip = '192.168.0.101'
            >>> search_agents = FetchAgents(view_name='default')
            >>> search_agents.by_ip(ip)

        Returns:
            List of dictionairies.
            [
                {
                    "display_name": null,
                    "environment": "Production",
                    "tags": [
                        {
                            "tag_name": "Foo Bar",
                            "tag_id": "6ef12d9d-a5a0-49c8-9890-206a7b362ce4"
                        }
                    ],
                    "available_vulnerabilities": 8,
                    "os_code": "linux",
                    "available_updates": 17,
                    "agent_status": "up",
                    "agent_id": "d4119b36-fe3c-4973-84c7-e8e3d72a3e02",
                    "computer_name": "ubuntu",
                    "os_string": "Ubuntu 12.04",
                    "needs_reboot": "no",
                    "host_name": ""
                }
            ]
        """
        base_count, base_filter = self._set_hw_base_query_by_nic()
        query_merge = self._set_merge_query()
        count = (
            base_count
            .filter(r.row[HardwarePerAgentKeys.IpAddress].match("(?i)^"+ip))
            .pluck(self.keys_to_pluck)
            .distinct()
            .count()
            .run(conn)
        )

        data = list(
            base_filter
            .filter(r.row[HardwarePerAgentKeys.IpAddress].match("(?i)^"+ip))
            .merge(query_merge)
            .pluck(self.keys_to_pluck)
            .distinct()
            .order_by(self.sort(self.sort_key))
            .skip(self.offset)
            .limit(self.count)
            .run(conn)
        )

        return(count, data)

    @time_it
    @catch_it((0, []))
    @db_create_close
    def by_ip_and_filter(self, ip, fkey, fval, conn=None):
        """Search agents by ip address while filtering
            based on a key and value.
        Args:
            ip (str): The ip address you are searching for.
            fkey (str): The key you are filtering on.
            fval (str): The value for the key you are filtering on.

        Basic Usage:
            >>> from vFense.core.agent.search._db import FetchAgents
            >>> view_name = 'default'
            >>> ip = '192.168'
            >>> fkey = 'os_code'
            >>> fval = 'linux'
            >>> search_agents = FetchAgents(view_name='default')
            >>> search_agents.by_ip_and_filter(ip, fkey, fval)

        Returns:
            List of dictionairies.
            [
                {
                    "display_name": null,
                    "environment": "Production",
                    "tags": [
                        {
                            "tag_name": "Foo Bar",
                            "tag_id": "6ef12d9d-a5a0-49c8-9890-206a7b362ce4"
                        }
                    ],
                    "available_vulnerabilities": 8,
                    "os_code": "linux",
                    "available_updates": 17,
                    "agent_status": "up",
                    "agent_id": "d4119b36-fe3c-4973-84c7-e8e3d72a3e02",
                    "computer_name": "ubuntu",
                    "os_string": "Ubuntu 12.04",
                    "needs_reboot": "no",
                    "host_name": ""
                }
            ]
        """
        base_count, base_filter = self._set_hw_base_query_by_nic()
        query_merge = self._set_merge_query()
        count = (
            base_count
            .filter({fkey: fval})
            .filter(r.row[HardwarePerAgentKeys.IpAddress].match("(?i)^"+ip))
            .pluck(self.keys_to_pluck)
            .distinct()
            .count()
            .run(conn)
        )

        data = list(
            base_filter
            .filter({fkey: fval})
            .filter(r.row[HardwarePerAgentKeys.IpAddress].match("(?i)^"+ip))
            .merge(query_merge)
            .pluck(self.keys_to_pluck)
            .distinct()
            .order_by(self.sort(self.sort_key))
            .skip(self.offset)
            .limit(self.count)
            .run(conn)
        )

        return(count, data)

    @time_it
    @catch_it((0, []))
    @db_create_close
    def by_mac(self, mac, conn=None):
        """Search agents based on an mac address.
        Args:
            mac (str): The mac address you are searching for.

        Basic Usage:
            >>> from vFense.core.agent.search._db import FetchAgents
            >>> view_name = 'default'
            >>> mac = '000c292672d6'
            >>> search_agents = FetchAgents(view_name='default')
            >>> search_agents.by_mac(mac)

        Returns:
            List of dictionairies.
            [
                {
                    "display_name": null,
                    "environment": "Production",
                    "tags": [
                        {
                            "tag_name": "Foo Bar",
                            "tag_id": "6ef12d9d-a5a0-49c8-9890-206a7b362ce4"
                        }
                    ],
                    "available_vulnerabilities": 8,
                    "os_code": "linux",
                    "available_updates": 17,
                    "agent_status": "up",
                    "agent_id": "d4119b36-fe3c-4973-84c7-e8e3d72a3e02",
                    "computer_name": "ubuntu",
                    "os_string": "Ubuntu 12.04",
                    "needs_reboot": "no",
                    "host_name": ""
                }
            ]
        """
        base_count, base_filter = self._set_hw_base_query_by_nic()
        query_merge = self._set_merge_query()
        count = (
            base_count
            .filter(r.row[HardwarePerAgentKeys.Mac].match("(?i)^"+mac))
            .pluck(self.keys_to_pluck)
            .distinct()
            .count()
            .run(conn)
        )

        data = list(
            base_filter
            .filter(r.row[HardwarePerAgentKeys.Mac].match("(?i)^"+mac))
            .merge(query_merge)
            .pluck(self.keys_to_pluck)
            .distinct()
            .order_by(self.sort(self.sort_key))
            .skip(self.offset)
            .limit(self.count)
            .run(conn)
        )

        return(count, data)

    @time_it
    @catch_it((0, []))
    @db_create_close
    def by_mac_and_filter(self, mac, fkey, fval, conn=None):
        """Search agents by mac address while filtering
            based on a key and value.
        Args:
            mac (str): The mac address you are searching for.
            fkey (str): The key you are filtering on.
            fval (str): The value for the key you are filtering on.

        Basic Usage:
            >>> from vFense.core.agent.search._db import FetchAgents
            >>> view_name = 'default'
            >>> mac = '000c292672d6'
            >>> fkey = 'os_code'
            >>> fval = 'linux'
            >>> search_agents = FetchAgents(view_name='default')
            >>> search_agents.by_mac_and_filter(mac, fkey, fval)

        Returns:
            List of dictionairies.
            [
                {
                    "display_name": null,
                    "environment": "Production",
                    "tags": [
                        {
                            "tag_name": "Foo Bar",
                            "tag_id": "6ef12d9d-a5a0-49c8-9890-206a7b362ce4"
                        }
                    ],
                    "available_vulnerabilities": 8,
                    "os_code": "linux",
                    "available_updates": 17,
                    "agent_status": "up",
                    "agent_id": "d4119b36-fe3c-4973-84c7-e8e3d72a3e02",
                    "computer_name": "ubuntu",
                    "os_string": "Ubuntu 12.04",
                    "needs_reboot": "no",
                    "host_name": ""
                }
            ]
        """
        base_count, base_filter = self._set_hw_base_query_by_nic()
        query_merge = self._set_merge_query()
        count = (
            base_count
            .filter({fkey: fval})
            .filter(r.row[HardwarePerAgentKeys.Mac].match("(?i)^"+mac))
            .pluck(self.keys_to_pluck)
            .distinct()
            .count()
            .run(conn)
        )

        data = list(
            base_filter
            .filter({fkey: fval})
            .filter(r.row[HardwarePerAgentKeys.Mac].match("(?i)^"+mac))
            .merge(query_merge)
            .pluck(self.keys_to_pluck)
            .distinct()
            .order_by(self.sort(self.sort_key))
            .skip(self.offset)
            .limit(self.count)
            .run(conn)
        )

        return(count, data)

    def _set_agent_merge_query(self):
        merge_query = (
            lambda x:
            {
                CommonAppKeys.APP_STATS: (
                    [
                        {
                            CommonAppKeys.COUNT: (
                                r
                                .table(AppCollections.AppsPerAgent)
                                .get_all(
                                    [
                                        CommonAppKeys.INSTALLED,
                                        x[AgentKeys.AgentId]
                                    ],
                                    index=AppsPerAgentIndexes.StatusAndAgentId
                                )
                                .count()
                            ),
                            CommonAppKeys.STATUS: CommonAppKeys.INSTALLED,
                            CommonAppKeys.NAME: CommonAppKeys.SOFTWAREINVENTORY
                        },
                        {
                            CommonAppKeys.COUNT: (
                                r
                                .table(AppCollections.AppsPerAgent)
                                .get_all(
                                    [
                                        CommonAppKeys.AVAILABLE,
                                        x[AgentKeys.AgentId]
                                    ],
                                    index=AppsPerAgentIndexes.StatusAndAgentId
                                )
                                .count()
                            ),
                            CommonAppKeys.STATUS: CommonAppKeys.AVAILABLE,
                            CommonAppKeys.NAME: CommonAppKeys.OS
                        },
                        {
                            CommonAppKeys.COUNT: (
                                r
                                .table(AppCollections.CustomAppsPerAgent)
                                .get_all(
                                    [
                                        CommonAppKeys.AVAILABLE,
                                        x[AgentKeys.AgentId]
                                    ],
                                    index=AppsPerAgentIndexes.StatusAndAgentId
                                )
                                .count()
                            ),
                            CommonAppKeys.STATUS: CommonAppKeys.AVAILABLE,
                            CommonAppKeys.NAME: CommonAppKeys.CUSTOM
                        },
                        {
                            CommonAppKeys.COUNT: (
                                r
                                .table(AppCollections.vFenseAppsPerAgent)
                                .get_all(
                                    [
                                        CommonAppKeys.AVAILABLE,
                                        x[AgentKeys.AgentId]
                                    ],
                                    index=AppsPerAgentIndexes.StatusAndAgentId
                                )
                                .count()
                            ),
                            CommonAppKeys.STATUS: CommonAppKeys.AVAILABLE,
                            CommonAppKeys.NAME: CommonAppKeys.AGENT_UPDATES
                        },
                    ]
                ),
            }
        )

        return merge_query

    def _set_merge_query(self):
        merge_query = (
            lambda x:
            {
                TagCollections.Tags: (
                    r
                    .table(TagCollections.TagsPerAgent)
                    .get_all(
                        x[TagsPerAgentKeys.AgentId],
                        index=TagsPerAgentIndexes.AgentId
                    )
                    .eq_join(
                        TagKeys.TagId,
                        r.table(TagCollections.Tags)
                    )
                    .zip()
                    .pluck(
                        TagsPerAgentKeys.TagId,
                        TagsPerAgentKeys.TagName
                    )
                    .coerce_to('array')
                ),
                AgentCommonKeys.AVAIL_UPDATES: (
                    r
                    .table(AppCollections.AppsPerAgent)
                    .get_all(
                        [
                            CommonAppKeys.AVAILABLE,
                            x[AgentKeys.AgentId]
                        ],
                        index=AppsPerAgentIndexes.StatusAndAgentId
                    )
                    .count()
                ),
                AgentCommonKeys.AVAIL_VULN: (
                    r
                    .table(AppCollections.AppsPerAgent)
                    .get_all(
                        [
                            CommonAppKeys.AVAILABLE,
                            x[AgentKeys.AgentId]
                        ],
                        index=AppsPerAgentIndexes.StatusAndAgentId
                    )
                    .eq_join(
                        lambda y:
                        y[AppsKey.AppId],
                        r.table(AppCollections.UniqueApplications)
                    )
                    .zip()
                    .filter(
                        lambda z:
                        z[AppsKey.VulnerabilityId] != ''
                    )
                    .count()
                ),
                AgentKeys.LastAgentUpdate: (
                    x[AgentKeys.LastAgentUpdate].to_epoch_time()
                ),
                AgentKeys.DateAdded: (
                    x[AgentKeys.DateAdded].to_epoch_time()
                )
            }
        )

        return merge_query

    def _set_agent_base_query(self):
        base_filter = (
            r
            .table(AgentCollections.Agents)
        )
        if self.view_name:
            base_filter = (
                r
                .table(AgentCollections.Agents)
                .get_all(
                    self.view_name,
                    index=AgentKeys.Views
                )
            )

        return base_filter

    def _set_hw_base_query_by_nic(self):
        if self.view_name:
            base_filter = (
                r
                .table(AgentCollections.Agents)
                .get_all(self.view_name, index=AgentIndexes.Views)
                .eq_join(
                    lambda x: [
                        x[AgentKeys.AgentId],
                        HardwarePerAgentKeys.Nic
                    ],
                    r.table(AgentCollections.Hardware),
                    index=HardwarePerAgentIndexes.AgentIdAndType
                )
                .zip()
            )
            base_count = base_filter
        else:
            base_filter = (
                r
                .table(AgentCollections.Agents)
                .eq_join(
                    lambda x: [
                        x[AgentKeys.AgentId],
                        HardwarePerAgentKeys.Nic
                    ],
                    r.table(AgentCollections.Hardware),
                    index=HardwarePerAgentIndexes.AgentIdAndType
                )
                .zip()
            )
            base_count = base_filter

        return(base_count, base_filter)

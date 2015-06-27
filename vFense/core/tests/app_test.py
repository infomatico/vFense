import unittest
from json import dumps

from vFense.core.agent._db_model import AgentKeys
from vFense.core.tag import Tag
from vFense.core.tag._db_model import TagKeys
from vFense.core.tag._db import fetch_tag_by_name_and_view
from vFense.core.agent._db import fetch_agent_ids
from vFense.core.tag.manager import TagManager
from vFense.core.agent import Agent
from vFense.core.agent.manager import AgentManager
from vFense.core.agent.status_codes import AgentCodes
from vFense.core.receiver.status_codes import AgentResultCodes
from vFense.core.tag.status_codes import TagCodes
from vFense.core.view.status_codes import ViewCodes
from vFense.core.tests.app_data import app_data
from vFense.core.tests.agent_and_tag_data import agent_data
from vFense.core.tests.app_data import app_data
from vFense.core.view import View
from vFense.core.view.manager import ViewManager
from vFense.plugins.patch.apps.manager import incoming_applications_from_agent

class AgentsAndTagsTests(unittest.TestCase):

    def test_a_create_view1(self):
        view = View(
            'Test View 1', package_download_url_base='http://localhost/packages'
        )
        manager = ViewManager(view.view_name)
        results = manager.create(view)
        print dumps(results.to_dict(), indent=4)
        status_code = results.vfense_status_code
        self.failUnless(status_code == ViewCodes.ViewCreated)


    def test_b_create_tag1(self):
        tag = (
            Tag(
                tag_name='Global Test Tag 1', view_name='Test View 1',
                is_global=True
            )
        )
        manager = TagManager()
        results = manager.create(tag)
        print dumps(results.to_dict(), indent=4)
        status_code = results.vfense_status_code
        self.failUnless(status_code == TagCodes.TagCreated)

    def test_c_create_agent1(self):
        system_info = agent_data["system_info"]
        system_info[AgentKeys.Views] = agent_data[AgentKeys.Views]
        system_info[AgentKeys.Hardware] = agent_data[AgentKeys.Hardware]
        agent = Agent(**system_info)
        tag = (
            fetch_tag_by_name_and_view(
                'Global Test Tag 1', 'Test View 1'
            )
        )
        manager = AgentManager()
        results = manager.create(agent, tags=[tag[TagKeys.TagId]])
        print dumps(results.to_dict(), indent=4)
        status_code = results.vfense_status_code
        self.failUnless(status_code == AgentResultCodes.NewAgentSucceeded)

    def test_d_load_apps(self):
        apps = app_data
        agent_id = fetch_agent_ids('Test View 1')[-1]
        incoming_applications_from_agent(agent_id, apps)


def main():
    unittest.main()

if __name__ == '__main__':
    main()

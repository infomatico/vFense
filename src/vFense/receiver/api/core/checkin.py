import logging
from json import dumps

from vFense import VFENSE_LOGGING_CONFIG
from vFense.core.agent.manager import AgentManager
from vFense.errorz.error_messages import (
    GenericResults, AgentResults
)
from vFense.errorz._constants import ApiResultKeys
from vFense.errorz.results import Results
from vFense.core.api.base import BaseHandler
from vFense.core.decorators import agent_authenticated_request, results_message

from vFense.receiver.corehandler import process_queue_data

from vFense.core.api.decorators import authenticate_agent

logging.config.fileConfig(VFENSE_LOGGING_CONFIG)
logger = logging.getLogger('rvlistener')


class CheckInV1(BaseHandler):
    @agent_authenticated_request
    def get(self, agent_id):
        username = self.get_current_user()
        uri = self.request.uri
        method = self.request.method
        try:
            agent_queue = process_queue_data(agent_id)
            status = (
                AgentResults(
                    username, uri, method
                ).check_in(agent_id, agent_queue)
            )
            self.update_agent_status(agent_id)
            self.set_status(status['http_status'])
            self.set_header('Content-Type', 'application/json')
            self.write(dumps(status))

        except Exception as e:
            status = (
                GenericResults(
                    username, uri, method
                ).something_broke(agent_id, 'check_in', e)
            )
            logger.exception(e)
            self.set_status(status['http_status'])
            self.set_header('Content-Type', 'application/json')
            self.write(dumps(status))


    @results_message
    def update_agent_status(self, agent_id):
        manager = AgentManager(agent_id)
        results = manager.update_last_checkin_time()
        return results


class CheckInV2(BaseHandler):
    @authenticate_agent
    def get(self, agent_id):
        username = self.get_current_user()
        uri = self.request.uri
        http_method = self.request.method
        try:
            results = (
                self.update_agent_status(
                    agent_id, username, uri, http_method
                )
            )
            self.set_status(results['http_status'])
            self.set_header('Content-Type', 'application/json')
            self.write(dumps(results))

        except Exception as e:
            status = (
                GenericResults(
                    username, uri, http_method
                ).something_broke(agent_id, 'check_in', e)
            )
            logger.exception(e)
            self.set_status(status['http_status'])
            self.set_header('Content-Type', 'application/json')
            self.write(dumps(status))


    def update_agent_status(self, agent_id, username, uri, http_method):
        manager = AgentManager(agent_id)
        manager.update_last_checkin_time()
        agent_queue = process_queue_data(agent_id)
        data = {ApiResultKeys.OPERATIONS: agent_queue}
        status = (
            Results(username, uri, http_method).check_in(**data)
        )
        return status

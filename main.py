from typing import List, Union
import configparser
import asyncio
import aiohttp
import i18n
import re

from gitlabAPI import get_private_projects, UnauthorizedException, UnavailableServiceException, Project
from limoo import LimooDriver


i18n.load_path.append('translates')
i18n.set('locale', 'fa')

config = configparser.ConfigParser()
config.read('config.ini')


class _Command:
    def __init__(self, method: callable, *args):
        self.method = method
        self.args = args

    async def run(self, *args):
        return await self.method(*args, *self.args)


async def _help(*args):
    return i18n.t('response.help_message')


async def _projects_to_md(projects: List[Project]):
    md_s = []
    for project in projects:
        formatted_desc = re.sub('[\r\n]+', '', project.description) if project.description else None
        md_s.append(
            f"__{project.name}__" +
            (f"\n* {formatted_desc}" if formatted_desc else "") +
            f"\n* [{project.url}]({project.url})"
        )
    return "\n".join(md_s)


async def _get_private_projects(session: aiohttp.ClientSession, private_token: str = None, *args) -> str:
    if isinstance(private_token, str) and private_token != i18n.t('commands.help'):
        response_text: str = ""
        try:
            projects = await get_private_projects(session, private_token)
            response_text += await _projects_to_md(projects)
        except UnauthorizedException as err:
            response_text += f"__{i18n.t('response.unauth')}__"
        except UnavailableServiceException as err:
            response_text += f"__{i18n.t('response.unavailable')}__"

        return response_text
    else:
        return i18n.t('response.get_project.help_message')


async def _process_event(event) -> Union[None, _Command]:
    command = None
    if (event['event'] == 'message_created' and
            not (event['data']['message']['type'] or
                 event['data']['message']['user_id'] == self['id'])):
        msg_parts = event['data']['message']['text'].split(' ')
        if len(msg_parts) > 0 and msg_parts[0] == i18n.t('commands.gitlab'):
            if len(msg_parts) < 2:
                command = _Command(_COMMANDS[i18n.t('commands.help')])
            else:
                if msg_parts[1] in _COMMANDS:
                    command = _Command(_COMMANDS[msg_parts[1]], *msg_parts[2:])
                else:
                    command = _Command(_COMMANDS[i18n.t('commands.help')])
        elif event['data']['conversation_type'] == 'direct':
            command = _Command(_COMMANDS[i18n.t('commands.help')])

    return command


async def respond(event: dict, session: aiohttp.ClientSession):
    command = await _process_event(event)
    if command:
        response_text = await command.run(session)

        await ld.messages.create(
            event['data']['workspace_id'],
            event['data']['message']['conversation_id'],
            response_text,
        )


async def main():
    global ld, self
    ld = LimooDriver('web.limoo.im', config['BOT']['Username'], config['BOT']['Password'])
    try:
        self = await ld.users.get()
        forever = asyncio.get_running_loop().create_future()
        async with aiohttp.ClientSession() as session:
            ld.set_event_handler(lambda event: asyncio.create_task(respond(event, session)))
            await forever
    finally:
        await ld.close()


_COMMANDS = {
    i18n.t('commands.project'): _get_private_projects,
    i18n.t('commands.help'): _help,
}

asyncio.run(main())

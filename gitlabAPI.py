import asyncio
from typing import List
import aiohttp


_base_url = 'https://gitlab.com/api/v4'
_project_dir = 'projects'

_project_types_map = {
    'pr': 'private',
    'pu': 'public',
    'in': 'internal'
}


class UnauthorizedException(Exception):
    pass


class UnavailableServiceException(Exception):
    pass


class ProjectType:
    PRIVATE = 'pr'
    PUBLIC = 'pu'
    INTERNAL = 'in'


class Project:
    API_MAP = {
        'id': 'id',
        'name': 'name',
        'namespace': 'name_with_namespace',
        'url': 'web_url',
        'desc': 'description',
        'avatar': 'avatar_url'
    }

    def __init__(self, id_num: int, name: str, name_with_namespace: str, url: str, description: str, avatar: str) -> None:
        self.id = id_num
        self.name = name
        self.name_with_namespace = name_with_namespace
        self.url = url
        self.description = description
        self.avatar = avatar


async def project_to_object(project: dict) -> Project:
    return Project(
        project.get(Project.API_MAP['id']),
        project.get(Project.API_MAP['name']),
        project.get(Project.API_MAP['namespace']),
        project.get(Project.API_MAP['url']),
        project.get(Project.API_MAP['desc']),
        project.get(Project.API_MAP['avatar']),
    )


async def _get_projects(session: aiohttp.ClientSession, private_token: str, visibility: str) -> List[Project]:
    try:
        async with session.get(
            f"{_base_url}/{_project_dir}",
            params={
                'private_token': private_token,
                'visibility': _project_types_map.get(visibility)
            }
        ) as resp:
            resp.raise_for_status()
            projects_json = await resp.json()
            convert_project_tasks = [project_to_object(project) for project in projects_json]
            return await asyncio.gather(*convert_project_tasks)
    except aiohttp.ClientResponseError as err:
        if err.status == 401:
            raise UnauthorizedException(err.message)
        else:
            raise UnavailableServiceException(err.message)
    except Exception as err:
        raise UnavailableServiceException(err)


async def get_private_projects(session: aiohttp.ClientSession, private_token: str) -> List[Project]:
    return await _get_projects(session, private_token, ProjectType.PRIVATE)

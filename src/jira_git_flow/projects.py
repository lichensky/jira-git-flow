import questionary
from marshmallow import Schema, fields, post_load
from prompt_toolkit import prompt
from tinydb import TinyDB

from jira_git_flow import config
from jira_git_flow.cli import print_simple_collection
from jira_git_flow.db import EntityRepository
from jira_git_flow.validators import UniqueID


class Project():
    def __init__(self, id, key, instance, workflow):
        self.id = id
        self.key = key
        self.instance = instance
        self.workflow = workflow


class ProjectSchema(Schema):
    id = fields.Str()
    key = fields.Str()
    instance = fields.Str()
    workflow = fields.Str()

    @post_load
    def deserialize(self, data, **kwargs):
        return Project(**data)


class ProjectRepository(EntityRepository):
    def __init__(self):
        super().__init__(Project, ProjectSchema(), "projects.json")


class ProjectCLI:
    def __init__(self, project_repository, instance_repository, workflow_repository):
        self.projects = project_repository
        self.instances = instance_repository
        self.workflows = workflow_repository

    def new(self):
        id = prompt(
            "Project ID: ", validator=UniqueID("Project", self.projects)
        )
        key = questionary.text("Project key:").ask()
        instance = questionary.select(
            "Project instance:", choices=self.instances.ids()
        ).ask()
        workflow = questionary.select(
            "Project workflow:", choices=self.workflows.ids()
        ).ask()

        project = Project(id, key, instance, workflow)
        self.projects.save(project)

    def list(self):
        print_simple_collection(ProjectSchema(), self.projects.all(), "id")

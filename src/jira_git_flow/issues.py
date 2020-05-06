import questionary

from jira_git_flow import config
from jira_git_flow.db import Model, Repository
from jira_git_flow.cli import (
    get_pointer_index,
    convert_stories_to_choices,
    select_issue,
)


class Issue(Model):
    """Jira simplified issue"""

    def __init__(self, key, summary, type, status):
        self.key = key
        self.summary = summary
        self.type = type
        self.status = status
        self.subtasks = []
        self.full_name = self.__repr__()

    def __hash__(self):
        return self.key.split("-")[1]

    def __eq__(self, obj):
        return self.key == obj.key

    def __repr__(self):
        return "{}: {}".format(self.key, self.summary)

    @classmethod
    def from_jira(cls, issue):
        if isinstance(issue, cls):
            return issue
        i = cls(issue.key, issue.fields.summary, _get_type(issue), _get_status(issue),)
        i.subtasks = _get_subtasks(issue)
        return i

    def add_subtask(self, subtask):
        if subtask not in self.subtasks:
            self.subtasks.append(subtask)

    # custom from_db method
    @classmethod
    def from_db(cls, db):
        def issue_from_db(db):
            return cls(db["key"], db["summary"], db["type"], db["status"])

        issue = issue_from_db(db)
        issue.subtasks = [issue_from_db(subtask) for subtask in db["subtasks"]]
        return issue


def _get_subtasks(jira_issue):
    try:
        return [Issue.from_jira(subtask) for subtask in jira_issue.fields.subtasks]
    except AttributeError as e:
        return []


def _get_type(jira_issue):
    jira_type = jira_issue.fields.issuetype.name
    for key, value in config.ISSUE_TYPES.items():
        if jira_type == value["name"]:
            return key
    raise Exception(f"Unable to map issue type: {jira_type}")


def _get_status(jira_issue):
    jira_status = jira_issue.fields.status.name
    for key, value in config.STATUSES.items():
        if jira_status in value:
            return key
    raise Exception(f"Unable to map issue status: {jira_status}")


class IssueRepository(Repository):
    def __init__(self):
        super().__init__(Issue, "issues.json")


class IssuesCLI:
    def __init__(self, repository):
        self.repository = repository

    def choose_issue(self):
        issues = self.choose_interactive()
        if issues:
            return issues[0]

    def choose_by_types(self, types):
        return self.choose_interactive(lambda issue: issue.type in types)

    def choose_by_status(self, status):
        return self.choose_interactive(lambda issue: issue.status == status)

    def choose_interactive(self, filter_function=lambda issue: True):
        issues = self.repository.all()

        if not issues:
            return []

        pointer_index = get_pointer_index(issues)
        choices = convert_stories_to_choices(issues, filter_function)

        if choices[pointer_index].get("disabled"):
            pointer_index = 0

        selected = select_issue(pointer_index=pointer_index, choices=choices)

        return selected

    def choose_issues_from_simple_view(self, issues):
        if not issues:
            exit('No issues.')
        print('Matching issues')
        for idx, issue in enumerate(issues):
            issue_model = Issue.from_jira(issue)
            print('{}: {} {}'.format(idx, issue_model.key, issue_model.summary))
        issue_id = int(questionary.text('Choose issue').ask())
        return issues[issue_id]
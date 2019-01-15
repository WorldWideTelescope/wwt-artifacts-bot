import pprint

from flask import current_app

from baldrick.github.github_api import PullRequestHandler
from baldrick.blueprints.github import github_webhook_handler


@github_webhook_handler
def handle_pull_requests(repo_handler, payload, headers):

    event = headers['X-GitHub-Event']

    pprint.pprint(payload)

    print(event, payload['action'])

    if event == 'pull_request':
        number = payload['pull_request']['number']
    elif event == 'issues':
        number = payload['issue']['number']
    else:
        return "Not an issue or pull request"

    pr_handler = PullRequestHandler(repo_handler.repo, number, repo_handler.installation)

    pr_handler.submit_comment('Testing')

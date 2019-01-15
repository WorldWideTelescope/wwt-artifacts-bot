import requests
from flask import current_app

from baldrick.github.github_api import PullRequestHandler
from baldrick.blueprints.github import github_webhook_handler


@github_webhook_handler
def handle_pull_requests(repo_handler, payload, headers):

    pr_handler = PullRequestHandler(repo_handler.repo, number, repo_handler.installation)

    event = headers['X-GitHub-Event']

    # We are only intersted in checks that are completed
    if event != 'check_run':
        return

    # We are only interested in checks that have been completed by Azure
    if payload['check_run']['app']['name'] != 'Azure Pipelines':
        return

    if payload['check_run']['conclusion'] != 'success':
        return

    details_url = payload['check_run']['details_url']

    # details_url is a URL of the form:
    # https://dev.azure.com/thomasrobitaille/<pipeline>/_build/results?buildId=<build_id>
    if '?buildID=' not in details_url or '/_build/' not in details_url:
        print('ERROR: URL did not match pattern: ' + details_url)
        return

    build_id = details_url.split('buildId=')[1]
    base_url = details_url.split('_build')[0]
    artifacts_url = f'{base_url}/_apis/build/builds/{build_id}/artifacts'

    artifacts = requests.get(artifacts_url).json()

    if artifacts['count'] > 0:

        message = 'The Azure Pipelines build produced the following artifacts:\n\n'

        for artifact in artifacts['value']:
            download_url = artifacts_url + '?artifactName={name}&fileId={data}&fileName={name}&api-version=5.0-preview.5'.format(name=artifact['name'], data=artifact['resource']['name'])
            message += '* [{name}]({url})\n'.format(name=artifact['name'], url=download_url)

        pr_handler.submit_comment(message)

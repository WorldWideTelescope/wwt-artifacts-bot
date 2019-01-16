import requests

from baldrick.blueprints.github import github_webhook_handler

from flask import Blueprint, request


azure_artifacts_blueprint = Blueprint('azure_artifacts', __name__)


ARTIFACTS_ROOT_URL = ("https://dev.azure.com/thomasrobitaille/{pipeline_id}"
                      "/_apis/build/builds/{build_id}/artifacts")


@azure_artifacts_blueprint.route('/azure_list_artifacts', methods=['GET'])
def azure_list_artifacts():

    pipeline_id = request.args.get('pipeline_id')
    build_id = request.args.get('build_id')

    if pipeline_id is None:
        return "Pipeline ID missing"

    if build_id is None:
        return "Build ID missing"

    artifacts_url = ARTIFACTS_ROOT_URL.format(pipeline_id=pipeline_id, build_id=build_id)

    artifacts = requests.get(artifacts_url).json()

    result = "<html><body>Build {build_id} produced the following artifacts:<ul>".format(build_id=build_id)

    for artifact in artifacts['value']:
        artifact_url = f'/azure_get_artifact?pipeline_id={pipeline_id}&build_id={build_id}&filename={artifact["name"]}&file_id={artifact["resource"]["data"]}'
        result += '<li><a href="{artifact_url}">{name}</a>'.format(artifact_url=artifact_url, name=artifact['name'])

    return result


@azure_artifacts_blueprint.route('/azure_get_artifact', methods=['GET'])
def azure_get_artifact():

    pipeline_id = request.args.get('pipeline_id')
    build_id = request.args.get('build_id')
    filename = request.args.get('filename')
    file_id = request.args.get('file_id')

    artifact_url = ARTIFACTS_ROOT_URL.format(pipeline_id=pipeline_id, build_id=build_id)

    params = {'artifactName': filename,
              'fileName': filename,
              'fileId': file_id,
              'api-version': '5.0-preview.5'}

    artifact = requests.get(artifact_url, params).json()
    params['fileId'] = artifact['items'][0]['blob']['id']

    artifact = requests.get(artifact_url, params)

    return artifact.content


@github_webhook_handler
def handle_pull_requests(repo_handler, payload, headers):

    event = headers['X-GitHub-Event']

    # We are only intersted in checks that are completed
    if event != 'check_run':
        return

    # We are only interested in checks that have been completed by Azure
    if payload['check_run']['app']['name'] != 'Azure Pipelines':
        return

    head_sha = payload['check_run']['head_sha']

    if payload['check_run']['status'] != 'completed':
        repo_handler.set_status('pending', 'Waiting for artifacts', 'wwt-artifacts-bot', head_sha)
    elif payload['check_run']['conclusion'] != 'success':
        repo_handler.set_status('error', 'No artifacts produced', 'wwt-artifacts-bot', head_sha)
        return

    details_url = payload['check_run']['details_url']

    # details_url is a URL of the form:
    # https://dev.azure.com/thomasrobitaille/<pipeline>/_build/results?buildId=<build_id>
    if '?buildId=' not in details_url or '/_build/' not in details_url:
        repo_handler.set_status('error', 'Could not parse Azure details URL', 'wwt-artifacts-bot', head_sha, target_url=details_url)
        return

    build_id = details_url.split('buildId=')[1]
    pipeline_id = details_url.split('/dev.azure.com/')[1].split('/')[1]

    artifacts_url = request.base_url + f'/azure_list_artifacts?pipeline_id={pipeline_id}&build_id={build_id}'

    repo_handler.set_status('error', 'Click Details to see artifacts produced by Azure Pipelines', 'wwt-artifacts-bot', head_sha, target_url=artifacts_url)

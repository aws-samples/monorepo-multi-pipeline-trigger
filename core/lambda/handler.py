import logging
import base64
import boto3
import botocore
from functools import reduce
import json

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

codecommit = boto3.client('codecommit')
ssm = boto3.client('ssm')


def main(event, context):
    """
    This AWS Lambda is triggered by AWS CodeCommit event.
    It starts AWS CodePipelines according to modifications in toplevel folders of the monorepo.
    Each toplevel folder can be associate with a different AWS CodePipeline.
    Must be run without concurrency - once at time for each monorepo (to avoid race condition while updating last commit parameter in SSM ParameterStore)
    """

    logger.info('event: %s', event)
    commit_id = get_commit_id(event)
    branch_name = get_branch_name(event)

    # logger.info('references: %s', references)

    repository = event['Records'][0]['eventSourceARN'].split(':')[5]

    paths = get_modified_files_since_last_run(
        repositoryName=repository, afterCommitSpecifier=commit_id, branch_name=branch_name)

    logger.info('paths: %s', paths)
    print(paths)
    toplevel_dirs = get_unique_toplevel_dirs(paths)
    print("unique toplevl dirs:", toplevel_dirs)
    pipeline_names = resolve_pipeline_names(toplevel_dirs, repository, branch_name)
    print("pipeline_names:", pipeline_names)
    print(start_codepipelines(pipeline_names))

    update_last_commit(repository, commit_id, branch_name)


def get_commit_id(event):
    return event['Records'][0]['codecommit']['references'][0]['commit']


def get_branch_name(event):
    branch_ref = event['Records'][0]['codecommit']['references'][0]['ref']
    return branch_ref.split('/')[-1]


def resolve_pipeline_names(toplevel_dirs, repository, branch_name):
    """
    Look up for pipeline names according to the toplevel dir names. 
    File name with the mapping (folder -> codepipeline-name) must be in the root level of the repo.
    Returns CodePipeline names that need to be triggered.
    """
    pipeline_map = codecommit.get_file(repositoryName=repository,
                                       commitSpecifier=f'refs/heads/{branch_name}', filePath=f'monorepo-{branch_name}.json')['fileContent']
    pipeline_map = json.loads(pipeline_map)
    pipeline_names = []
    for dir in toplevel_dirs:
        if dir in pipeline_map:
            pipeline_names.append(pipeline_map[dir])
    return pipeline_names


def get_unique_toplevel_dirs(modified_files):
    """
    Returns toplevel folders that were modified by the last commit(s)
    """
    toplevel_dirs = set(
        [splitted[0] for splitted in (file.split('/') for file in modified_files)
         if len(splitted) > 1]
    )

    logger.info('toplevel dirs: %s', toplevel_dirs)
    return toplevel_dirs


def start_codepipelines(codepipeline_names: list) -> dict:
    """
    start CodePipeline (s)
    Returns a tupple with 2 list: (success_started_pipelines, failed_to_start_pipelines)
    """
    codepipeline_client = boto3.Session().client('codepipeline')

    failed_codepipelines = []
    started_codepipelines = []
    for codepipeline_name in codepipeline_names:
        try:
            codepipeline_client.start_pipeline_execution(
                name=codepipeline_name
            )
            logger.info(f'Started CodePipeline {codepipeline_name}.')
            started_codepipelines.append(codepipeline_name)
        except codepipeline_client.exceptions.PipelineNotFoundException:
            logger.info(f'Could not find CodePipeline {codepipeline_name}.')
            failed_codepipelines.append(codepipeline_name)

    return (started_codepipelines, failed_codepipelines)


def build_parameter_name(repository, branch_name):
    """
    Create the name of SSM ParameterStore LastCommit
    """
    # TODO must have the branch name in the parameter?
    return f'/MonoRepoTrigger/{repository}/{branch_name}/LastCommit'


def get_last_commit(repository, commit_id, branch_name):
    """
    Get last triggered commit id. 
    Strategy: try to find the last commit id in SSM Parameter Store '/MonoRepoTrigger/{repository}/LastCommit', 
              if does not exist, get the parent commit from the commit that triggers this lambda
    Return last triggered commit hash
    """
    param_name = build_parameter_name(repository, branch_name)
    try:
        return ssm.get_parameter(Name=param_name)['Parameter']['Value']
    except botocore.exceptions.ClientError:
        logger.info('not found ssm parameter %s', param_name)
        commit = codecommit.get_commit(
            repositoryName=repository, commitId=commit_id)['commit']
        parent = None
        if commit['parents']:
            parent = commit['parents'][0]
        return parent


def update_last_commit(repository, commit_id, branch_name):
    """
    Update '/MonoRepoTrigger/{repository}/LastCommit' SSM Parameter Store with the current commit that triggered the lambda
    """
    ssm.put_parameter(Name=build_parameter_name(repository, branch_name),
                      Description='Keep track of the last commit already triggered',
                      Value=commit_id,
                      Type='String',
                      Overwrite=True)


def get_modified_files_since_last_run(repositoryName, afterCommitSpecifier, branch_name):
    """
    Get all modified files since last time the lambda was triggered. Developer can push several commit at once, 
    so the number of commits between beforeCommit and afterCommit can be greater than one.
    """

    last_commit = get_last_commit(repositoryName, afterCommitSpecifier, branch_name)
    print("last_commit: ", last_commit)
    print("commit_id: ", afterCommitSpecifier)
    # TODO working with next_token to paginate
    diff = None
    if last_commit:
        diff = codecommit.get_differences(repositoryName=repositoryName, beforeCommitSpecifier=last_commit,
                                          afterCommitSpecifier=afterCommitSpecifier)['differences']
    else:
        diff = codecommit.get_differences(repositoryName=repositoryName,
                                          afterCommitSpecifier=afterCommitSpecifier)['differences']

    logger.info('diff: %s', diff)

    before_blob_paths = {d.get('beforeBlob', {}).get('path') for d in diff}
    after_blob_paths = {d.get('afterBlob', {}).get('path') for d in diff}

    all_modifications = before_blob_paths.union(after_blob_paths)
    return filter(lambda f: f is not None, all_modifications)


if __name__ == '__main__':
    main({'Records': [{'codecommit': {'references': [{'commit': 'a6528d2dd877288e7c0ebdf9860d356e6d4bd073',
                                                      }]}, 'eventSourceARN': ':::::repo-test-trigger-lambda'}]}, {})

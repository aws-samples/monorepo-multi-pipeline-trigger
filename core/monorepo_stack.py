from aws_cdk import (core as cdk,
                     aws_lambda as lambda_,
                     aws_codecommit as codecommit,
                     aws_iam as iam,
                     aws_s3 as s3,
                     aws_s3_deployment as s3_deployment)
import os
import zipfile
import tempfile
import json


class MonorepoStack(cdk.Stack):
    exported_monorepo: codecommit.Repository

    def __init__(self, scope: cdk.Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        ### Stack Parameters ###
        monorepo_name = cdk.CfnParameter(self, 'MonorepoName',
                                         type='String',
                                         description='CodeCommit Monorepo name',
                                         default='monorepo-sample')

        branch_for_trigger = 'main'

        function_name = f'{monorepo_name.value_as_string}-codecommit-handler'
        repository_name = monorepo_name.value_as_string
        region = cdk.Stack.of(self).region
        account = cdk.Stack.of(self).account


        monorepo = self.create_codecommit_repo(repository_name, branch_for_trigger)

        monorepo_lambda = self.create_lambda(region, account, repository_name, function_name)
        
        monorepo.grant_read(monorepo_lambda)
        monorepo.notify(f"arn:aws:lambda:{region}:{account}:function:{function_name}",
                        name="lambda-codecommit-event", branches=[branch_for_trigger])
        self.exported_monorepo = monorepo


    def create_lambda(self, region, account, repository_name, function_name):
        # Lambda function which triggers code pipeline according
        # Function must run with concurrency = 1 -- to avoid race condition
        monorepo_lambda = lambda_.Function(self, "CodeCommitEventHandler",
                                           function_name=function_name,
                                           runtime=lambda_.Runtime.PYTHON_3_8,
                                           code=lambda_.Code.from_asset("core/lambda/"),
                                           handler="handler.main",
                                           timeout=cdk.Duration.seconds(60),
                                           dead_letter_queue_enabled=True,
                                           reserved_concurrent_executions=1)
        monorepo_lambda.add_permission("codecommit-permission",
                                       principal=iam.ServicePrincipal("codecommit.amazonaws.com"),
                                       action="lambda:InvokeFunction",
                                       source_arn=f"arn:aws:codecommit:{region}:{account}:{repository_name}")
        monorepo_lambda.add_to_role_policy(
            iam.PolicyStatement(resources=[f'arn:aws:ssm:{region}:{account}:parameter/MonoRepoTrigger/*'],
                                actions=['ssm:GetParameter', 'ssm:GetParameters', 'ssm:PutParameter']))
        monorepo_lambda.add_to_role_policy(
            iam.PolicyStatement(resources=[f'arn:aws:codepipeline:{region}:{account}:*'],
                                actions=['codepipeline:GetPipeline', 'codepipeline:ListPipelines',
                                'codepipeline:StartPipelineExecution', 'codepipeline:StopPipelineExecution']))
        return monorepo_lambda


    def create_codecommit_repo(self, repository_name, branch_for_trigger):
        tmp_dir = zip_sample()
        sample_bucket = s3.Bucket(self, 'MonoRepoSample',
                                  removal_policy=cdk.RemovalPolicy.DESTROY,
                                  auto_delete_objects=True)
        sample_deployment = s3_deployment.BucketDeployment(self, 'DeployMonoRepoSample',
                                                           sources=[s3_deployment.Source.asset(tmp_dir)],
                                                           destination_bucket=sample_bucket)
        monorepo = codecommit.Repository(self, "monorepo", repository_name=repository_name)
        cfn_repo = monorepo.node.find_child('Resource')
        cfn_repo.code = codecommit.CfnRepository.CodeProperty(s3={'bucket': sample_bucket.bucket_name, 'key': 'sample.zip'},
                                                              branch_name=branch_for_trigger)
        monorepo.node.add_dependency(sample_deployment)
        return monorepo


def zip_sample():
    # codepipeline_map = {}
    # for dir_name, service_pipeline in monorepo_config.service_map.items():
    #     codepipeline_map[dir_name] = service_pipeline.pipeline_name()
    tempdir = tempfile.mkdtemp('bucket-sample')
    with zipfile.ZipFile(os.path.join(tempdir, 'sample.zip'), 'w') as zf:
        # zf.writestr(f'monorepo-{branch_name}.json', json.dumps(codepipeline_map))
        for dirname, subdirs, files in os.walk("./monorepo-sample/"):
            for filename in files:
                relativepath = os.path.join(dirname.replace("./monorepo-sample/", ""), filename)
                zf.write(os.path.join(dirname, filename), arcname=relativepath)
    return tempdir

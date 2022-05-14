from core.abstract_service_pipeline import ServicePipeline
from aws_cdk import (RemovalPolicy, CfnOutput, 
                     aws_iam as iam,
                     aws_codebuild as codebuild,
                     aws_codepipeline as codepipeline,
                     aws_codepipeline_actions as codepipeline_actions,
                     aws_codecommit as codecommit,
                     aws_s3 as s3,
                     aws_cloudfront as cloudfront)
from constructs import Construct


class HotsitePipeline(ServicePipeline):

    def pipeline_name(self) -> str:
        return 'codepipeline-hotsite-main'

    def build_pipeline(self, scope: Construct, code_commit: codecommit.Repository, pipeline_name: str, service_name: str):
        select_artifact_build = codebuild.PipelineProject(scope, f'SelectArtifactBuild-{pipeline_name}',
                                                          build_spec=codebuild.BuildSpec.from_object(dict(
                                                              version='0.2',
                                                              phases=dict(
                                                                  build=dict(
                                                                      commands=[
                                                                          f'echo selecting directory for {service_name}...'])),
                                                              artifacts={
                                                                  'base-directory': service_name,
                                                                  'files': ['**/*']})),
                                                          environment=dict(build_image=codebuild.LinuxBuildImage.STANDARD_5_0))
        source_output = codepipeline.Artifact()
        service_artifact = codepipeline.Artifact()

        bucket = s3.Bucket(
            scope,
            f'Bucket-{pipeline_name}-{service_name}',
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            website_index_document='index.html',
            website_error_document='error.html',
            auto_delete_objects=True,
            removal_policy=RemovalPolicy.DESTROY)

        cloudfront_oai = cloudfront.OriginAccessIdentity(scope, f"Cloudfront OAI for {service_name}")

        bucket.add_to_resource_policy(iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            actions=["s3:GetObject"],
            principals=[iam.CanonicalUserPrincipal(
                cloudfront_oai.cloud_front_origin_access_identity_s3_canonical_user_id)],
            resources=[bucket.arn_for_objects("*")]
        ))

        s3_origin_source = cloudfront.S3OriginConfig(s3_bucket_source=bucket, origin_access_identity=cloudfront_oai)
        source_config = cloudfront.SourceConfiguration(s3_origin_source=s3_origin_source, behaviors=[
            cloudfront.Behavior(is_default_behavior=True)])

        dist = cloudfront.CloudFrontWebDistribution(scope,
                                                    service_name,
                                                    origin_configs=[source_config],
                                                    comment='CDK created',
                                                    default_root_object="index.html")

        CfnOutput(scope, f'{service_name}_url', value=dist.distribution_domain_name,
                      export_name=f'{service_name}-url')

        return codepipeline.Pipeline(scope, pipeline_name,
                                     pipeline_name=pipeline_name,
                                     stages=[
                                         codepipeline.StageProps(stage_name="Source",
                                                                 actions=[
                                                                     codepipeline_actions.CodeCommitSourceAction(
                                                                         action_name="CodeCommit_Source",
                                                                         branch="main",
                                                                         repository=code_commit,
                                                                         output=source_output,
                                                                         trigger=codepipeline_actions.CodeCommitTrigger.NONE)]),
                                         codepipeline.StageProps(stage_name="Build",
                                                                 actions=[
                                                                     codepipeline_actions.CodeBuildAction(
                                                                         action_name="SelectServiceArtifact",
                                                                         project=select_artifact_build,
                                                                         input=source_output,
                                                                         outputs=[service_artifact])]),
                                         codepipeline.StageProps(stage_name="Deploy",
                                                                 actions=[codepipeline_actions.S3DeployAction(action_name="DeployS3", bucket=bucket, input=service_artifact)]), ])

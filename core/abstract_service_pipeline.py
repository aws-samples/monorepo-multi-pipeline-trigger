from abc import ABC, abstractmethod
from aws_cdk import (core as cdk,
                     aws_codecommit as codecommit,)


class ServicePipeline(ABC):

    @abstractmethod
    def pipeline_name(self) -> str:
        pass

    @abstractmethod
    def build_pipeline(self, scope: cdk.Construct, code_commit: codecommit.Repository, pipeline_name: str, service_name: str):
        pass
from abc import ABC, abstractmethod
from aws_cdk import (aws_codecommit as codecommit)
from constructs import Construct


class ServicePipeline(ABC):

    @abstractmethod
    def pipeline_name(self) -> str:
        pass

    @abstractmethod
    def build_pipeline(self, scope: Construct, code_commit: codecommit.Repository, pipeline_name: str, service_name: str):
        pass
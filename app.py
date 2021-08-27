#!/usr/bin/env python3

from aws_cdk import (core as cdk)
from core.monorepo_stack import MonorepoStack
from core.pipelines_stack import PipelineStack

app = cdk.App()
core = MonorepoStack(app, "MonoRepoStack")
PipelineStack(app, "PipelinesStack", core.exported_monorepo)

app.synth()

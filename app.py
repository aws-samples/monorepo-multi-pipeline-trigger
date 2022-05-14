#!/usr/bin/env python3

from aws_cdk import App
from core.monorepo_stack import MonorepoStack
from core.pipelines_stack import PipelineStack

app = App()
core = MonorepoStack(app, "MonoRepoStack")
PipelineStack(app, "PipelinesStack", core.exported_monorepo)

app.synth()

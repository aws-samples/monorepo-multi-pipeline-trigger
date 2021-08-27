# This is a configuration file is used by PipelineStack to determine which pipelines should be constructed

from core.abstract_service_pipeline import ServicePipeline
from typing import Dict


# Pipeline definition imports
from pipelines.pipeline_demo import DemoPipeline
from pipelines.pipeline_hotsite import HotsitePipeline

### Add your pipeline configuration here
service_map: Dict[str, ServicePipeline]  = {
    # folder-name -> pipeline-class
    'demo': DemoPipeline(),
    'hotsite': HotsitePipeline()
}
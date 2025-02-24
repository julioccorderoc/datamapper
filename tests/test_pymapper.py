from pymapper.pymapper import ModelMapper
from tests.models import *
from tests.sources import source_order

mapper = ModelMapper(log_level_name="DEBUG")

test = mapper.map_models(source_order, TargetOrderForAccounting)

import json
try:
    print(json.dumps(test.model_dump(), indent=4))
except:
    print(json.dumps(test, indent=4))
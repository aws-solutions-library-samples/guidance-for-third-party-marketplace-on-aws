#!/usr/bin/env python3
import os

import aws_cdk as cdk

from cdk.guidance_for_third_party_marketplace_on_aws import ThirdPartyMarketplaceStack
from cdk.front_end_stack import FrontEndStack

app = cdk.App()
ThirdPartyMarketplaceStack(app, "ThirdPartyMarketplaceStack", 
    env=cdk.Environment(account=os.getenv('CDK_DEFAULT_ACCOUNT'), region=os.getenv('CDK_DEFAULT_REGION')),
    )

FrontEndStack(app, "FrontEndStack")
app.synth()
#api_end_point = cdk.Fn.import_value("suppliersapiEndpointDFE6BD04")


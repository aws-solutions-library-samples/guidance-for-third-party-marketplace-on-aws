#!/usr/bin/env python3
import os

import aws_cdk as cdk

from cdk.guidance_for_third_party_marketplace_on_aws import ThirdPartyMarketplaceStack
from cdk.front_end_stack import FrontEndStack

from aws_cdk import Aspects
from cdk_nag import AwsSolutionsChecks
from cdk_nag import NagSuppressions

app = cdk.App()
description = "Guidance for building Third Party Marketplace on AWS (S09XXX)"
third_party_marketplace_stack = ThirdPartyMarketplaceStack(app, "ThirdPartyMarketplaceStack", 
    description=description,
    env=cdk.Environment(account=os.getenv('CDK_DEFAULT_ACCOUNT'), region=os.getenv('CDK_DEFAULT_REGION')),
    )

description = "User Interface - Guidance for building Third Party Marketplace on AWS (S09XXX)"
front_end_stack = FrontEndStack(app, "FrontEndStack",
              description=description)

Aspects.of(app).add(AwsSolutionsChecks(verbose=True))

NagSuppressions.add_stack_suppressions(
    stack=front_end_stack, 
    suppressions=[
        {"id":"AwsSolutions-IAM4", "reason":"Sample Code"},
        {"id":"AwsSolutions-IAM5", "reason":"Sample Code"},
        #{"id":"AwsSolutions-CFR4", "reason":"Sample Code"},
        # Suppress warnings
        {"id":"AwsSolutions-CFR2", "reason":"AWS Gateway is already protected by WAF so not protecting CloudFront UI distribution with WAF in the sample code"},
    ]
)

NagSuppressions.add_stack_suppressions(
    stack=third_party_marketplace_stack, 
    suppressions=[
        {"id":"AwsSolutions-APIG4", "reason":"API has to be publicly accessible and doesn't need Cognito authorization in this use case"},
        {"id":"AwsSolutions-COG4", "reason":"Using Lambda Authorizer and not Cognito user pool authorizer"},
        {"id":"AwsSolutions-IAM4", "reason":"Sample Code"},
        {"id":"AwsSolutions-IAM5", "reason":"Sample Code"},
        {"id":"AwsSolutions-SF2", "reason":"Avoiding complexity of integration Step Function with X-ray because of complexity introduced to the proof of concept"},
        {"id":"AwsSolutions-SQS3", "reason":"The resource is already a dead-letter queue"},
        {"id":"AwsSolutions-SQS4", "reason":"Need to add queue policy with condition aws:SecureTransport true"},

        #
        #  Suppress warnings
        #{"id":"AwsSolutions-APIG3", "reason":"Not using WAF in this guidance but recommended for real-world use"},
    ]
)

app.synth()
#api_end_point = cdk.Fn.import_value("suppliersapiEndpointDFE6BD04")


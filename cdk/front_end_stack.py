from aws_cdk import (
    # Duration,
    Stack,
    CfnOutput,
    aws_dynamodb as ddb,
    aws_lambda as lambda1,
    aws_s3 as s3,
    aws_s3_deployment as s3deploy,
    aws_apigateway as api,
    aws_wafv2 as wafv2,
    aws_lambda_event_sources as lambda_event_sources,
    aws_iam as iam,
    aws_stepfunctions as step_functions,
    aws_codepipeline as code_pipelines, 
    aws_pipes as pipes,
    aws_cloudfront as cloudfront,
    aws_cloudfront_origins as cloudfront_origins,
    aws_sns as sns,
    aws_sqs as sqs,
    RemovalPolicy,
)
from constructs import Construct

import json


  
class FrontEndStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        api_end_point = self.node.try_get_context("api_end_point")        

        ## Step 1 - static s3 website to enroll new suppliers
        mys3 = s3.Bucket(self, "third-party-marketplace-bucket",
        removal_policy=RemovalPolicy.DESTROY)

        ## Step 2 - Insert api_end_point variable in website-template and create deployable webpage
        web_content = open('./cdk/website/index-template.html').read()
        web_content = web_content.replace('$$API_URL$$', '"{0}"'.format(api_end_point))

        website_deploy_file = open("./cdk/website/website-deploy/index.html",mode='w')
        website_deploy_file.write(web_content)

        ## Step 3 - deploy website
        mydep = s3deploy.BucketDeployment(self, "deployThirdParty",
            sources=[s3deploy.Source.asset("./cdk/website/website-deploy")],
            destination_bucket=mys3
            #destination_key_prefix="web/static"
            )

        origin_access_identity_1 = cloudfront.OriginAccessIdentity(self,'OriginAccessIdentity')
        
        mys3.grant_read(origin_access_identity_1)

        cloudfront_distribution = cloudfront.Distribution(self, 'Suppliers_Distribution',
            default_root_object='index.html',     
            enable_logging=True,
            default_behavior=cloudfront.BehaviorOptions
            (origin= cloudfront_origins.S3Origin(bucket=mys3,
            origin_access_identity=origin_access_identity_1),
            allowed_methods=cloudfront.AllowedMethods.ALLOW_ALL,
            viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS))
        
        CfnOutput(self, "CloudFront URL", export_name="cloudfront-url",
                  value=cloudfront_distribution.distribution_domain_name
                  )
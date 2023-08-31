from aws_cdk import (
    # Duration,
    Stack,
    CfnOutput,
    aws_s3 as s3,
    aws_s3_deployment as s3deploy,
    aws_iam as iam,
    aws_cloudfront as cloudfront,
    aws_cloudfront_origins as cloudfront_origins,
    RemovalPolicy,
)
from constructs import Construct

  
class FrontEndStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        api_end_point = self.node.try_get_context("api-end-point")        

        ## Step 0 - following cdk nag best practices
        
        ## Step 1 - static s3 website to enroll new suppliers
        mys3 = s3.Bucket(self, "third-party-marketplace-bucket",
        removal_policy=RemovalPolicy.DESTROY,
        enforce_ssl=True,
        block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
        access_control=s3.BucketAccessControl.LOG_DELIVERY_WRITE,
        object_ownership=s3.ObjectOwnership.OBJECT_WRITER,
        server_access_logs_prefix="web-access-logs")

        ## Step 2 - Insert api_end_point variable in website-template and create deployable webpage
        web_content = open('./cdk/website/index-template.html').read()
        web_content = web_content.replace('$$API_URL$$', '"{0}"'.format(api_end_point))

        website_deploy_file = open("./cdk/website/website-deploy/index.html",mode='w')
        website_deploy_file.write(web_content)
        website_deploy_file.close()

        ## Step 3 - deploy website
        mydep = s3deploy.BucketDeployment(self, "deployThirdParty",
            sources=[s3deploy.Source.asset("./cdk/website/website-deploy")],
            destination_bucket=mys3
            )

        origin_access_identity_1 = cloudfront.OriginAccessIdentity(self,'OriginAccessIdentity')
        
        mys3.grant_read(origin_access_identity_1)

        ## Creating a bucket for cloud front logs - cdk nag requirement
        cloudfront_log_s3 = s3.Bucket(self, "suppliers-distribution-cloudfront-log-bucket",
        enforce_ssl=True,
        block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
        access_control=s3.BucketAccessControl.LOG_DELIVERY_WRITE,
        object_ownership=s3.ObjectOwnership.OBJECT_WRITER,
        server_access_logs_prefix="cloudfront-access-logs")
        
        cloudfront_distribution = cloudfront.Distribution(self, 'Suppliers_Distribution',
            default_root_object='index.html',
            log_bucket=cloudfront_log_s3,
            log_file_prefix="cloudfront-log",
            geo_restriction=cloudfront.GeoRestriction.allowlist("US","GB"),
            #certificate=acm.Certificate,  - Best practice for production systems
            #minimum_protocol_version=cloudfront.SecurityPolicyProtocol.TLS_V1_2_2018, - Best practice for production systems          
            default_behavior=cloudfront.BehaviorOptions
            (origin= cloudfront_origins.S3Origin(bucket=mys3,
            origin_access_identity=origin_access_identity_1),
            allowed_methods=cloudfront.AllowedMethods.ALLOW_ALL,
            viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS))
        
        CfnOutput(self, "CloudFront URL", export_name="cloudfront-url",
                  value=cloudfront_distribution.distribution_domain_name
                  )
from aws_cdk import (
    # Duration,
    Stack,
    aws_dynamodb as ddb,
    aws_lambda as lambda1,
    aws_s3 as s3,
    aws_s3_deployment as s3deploy,
    aws_apigateway as api,
    aws_wafv2 as wafv2,
    aws_lambda_event_sources as lambda_events,
    aws_iam as iam,
    aws_stepfunctions as step_function,
    aws_pipes as pipes,
    aws_cloudfront as cloudfront,
    aws_cloudfront_origins as cloudfront_origins,
    RemovalPolicy,
)
from constructs import Construct

import json

class ThirdPartyMarketPlaceStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # The code that defines your stack goes here
        supplier_table = ddb.Table(
             self, "Supplier",
             partition_key = ddb.Attribute(name="Brand", type = ddb.AttributeType.STRING),
             stream = ddb.StreamViewType.NEW_IMAGE,
             removal_policy=RemovalPolicy.RETAIN
        )

        #Name of the registrant is the secondary/sort key
        supplier_table.add_global_secondary_index(index_name="Name", 
              partition_key=ddb.Attribute(name="Name", type = ddb.AttributeType.STRING))
        
        ### STEP 2 - Lambda funtion that inserts values in SupplierTable ###
        
        my_lambda = lambda1.Function(self, "EnrollNewSupplier",
            code=lambda1.Code.from_asset("./cdk/lambda"),
            handler="index.lambda_handler",
            runtime= lambda1.Runtime.PYTHON_3_9,
            environment={"SUPPLIERS_TABLE_NAME":supplier_table.table_name})

        # my_lambda.add_event_source(lambda_events.DynamoEventSource(supplier_table, 
         #starting_position= lambda.StartingPosition.TRIM_HORIZON))
        
        #supplier_table.grant_full_access(my_lambda)
        supplier_table.grant_read_write_data(my_lambda)
        
        ### Step 3 - API Gateway
        api_role = iam.Role(self, "api_role",
            assumed_by=iam.ServicePrincipal("apigateway.amazonaws.com"),
            description="api_role"
        )

        ## API - Gateway
        third_party_api = api.LambdaRestApi(self, "suppliers-api", 
            handler=my_lambda,
            default_cors_preflight_options=api.CorsOptions(
                 allow_origins=api.Cors.ALL_ORIGINS,
                 allow_methods=api.Cors.ALL_METHODS,
                 allow_headers=api.Cors.DEFAULT_HEADERS
            ))
        
        ## Enabling web access firewall to protect API Gateway
        web_acl = wafv2.CfnWebACL(self, "suppliers-webacl", default_action=wafv2.CfnWebACL.DefaultActionProperty(allow={}),
                                  scope="REGIONAL", 
                                  visibility_config=wafv2.CfnWebACL.VisibilityConfigProperty(cloud_watch_metrics_enabled=True, 
                                        metric_name="suppliers-web-acl",sampled_requests_enabled=False))                                                                                                        

#                                         ,wafv2.CfnWebACL.ManagedRuleGroupStatementProperty.name = "AWSManagedRulesCommonRuleSet"
#                                         ,wafv2.CfnWebACL.RuleProperty.statement = ; ,wafv2.CfnWebACL.RuleProperty.name="CRSRule"
#                                  rules=[wafv2.CfnWebACL.AWSManagedRulesBotControlRuleSetProperty]

        web_acl_association = wafv2.CfnWebACLAssociation(self,'bot-waf-association',
                                resource_arn=third_party_api.deployment_stage.stage_arn,
                                web_acl_arn=web_acl.attr_arn)

        ## Step 4 - website to enroll new suppliers
        mys3 = s3.Bucket(self, "third-party-marketplace-bucket",
        removal_policy=RemovalPolicy.DESTROY)

        mydep = s3deploy.BucketDeployment(self, "deployThirdParty",
            sources=[s3deploy.Source.asset("./cdk/website")],
            destination_bucket=mys3
            #destination_key_prefix="web/static"
            )

        origin_access_identity_1 = cloudfront.OriginAccessIdentity(self,'OriginAccessIdentity')
        
        mys3.grant_read(origin_access_identity_1)

        #cloudfront_distribution = cloudfront.Distribution(self, 'Suppliers_Distribution',
         #   default_root_object='index.html',
         #   default_behavior={'origin': cloudfront_origins.HttpOrigin(
          #      domain_name= mydep.deployed_bucket.bucket_website_domain_name)})

        cloudfront_distribution = cloudfront.Distribution(self, 'Suppliers_Distribution',
            default_root_object='index.html',
            default_behavior=cloudfront.BehaviorOptions
            (origin= cloudfront_origins.S3Origin(bucket=mys3,
            origin_access_identity=origin_access_identity_1),
            allowed_methods=cloudfront.AllowedMethods.ALLOW_ALL,
            viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS))
        
        ## Step 4 - Step function which gets triggered on dynamodb stream

        # 5.a. IAM role for step function
        step_role = iam.Role(self, "step_role",
            assumed_by=iam.ServicePrincipal("states.amazonaws.com"),
            description="step_role"
        )

        # 5.b. reading step function definition
        with open('./cdk/step/step_definition.json') as f:
            definition = json.load(f)
        definition = json.dumps(definition, indent = 4)

        my_step = step_function.CfnStateMachine(self, "validate_data", definition_string=definition,role_arn=step_role.role_arn)

        # 5.c. IAM role for eventbridge pipes
        pipe_role = iam.Role(self, "pipe_role",
            assumed_by=iam.ServicePrincipal("pipes.amazonaws.com"),
            description="pipe_role"
        )

        pipe_role.add_to_policy(iam.PolicyStatement(effect=iam.Effect.ALLOW, actions=["states:*"], resources=[my_step.ref]))

        supplier_table.grant_stream_read(pipe_role)

        # 5. d. connect dynamodb stream to pipe
        my_pipe = pipes.CfnPipe(self, "supplier_pipe", role_arn=pipe_role.role_arn, source=supplier_table.table_stream_arn, 
            source_parameters=pipes.CfnPipe.PipeSourceParametersProperty(dynamo_db_stream_parameters=
            pipes.CfnPipe.PipeSourceDynamoDBStreamParametersProperty(starting_position="TRIM_HORIZON")),
            target=my_step.ref, 
            target_parameters=pipes.CfnPipe.PipeTargetParametersProperty(step_function_state_machine_parameters=
            pipes.CfnPipe.PipeTargetStateMachineParametersProperty(invocation_type="FIRE_AND_FORGET")))


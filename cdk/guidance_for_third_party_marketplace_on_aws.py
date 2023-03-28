from aws_cdk import (
    # Duration,
    Stack,
    CfnOutput,
    Aws,
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
    aws_route53 as route53,
    aws_route53_targets as route53_targets,
    aws_certificatemanager as acm,
    aws_sns as sns,
    aws_sqs as sqs,
    RemovalPolicy,
)
from constructs import Construct

import json
import os

class ThirdPartyMarketplaceStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)        

        # DynamoDB table
        supplier_table = ddb.Table(
             self, "Supplier",
             partition_key = ddb.Attribute(name="BrandId", type = ddb.AttributeType.STRING),
             stream = ddb.StreamViewType.NEW_IMAGE,
             removal_policy=RemovalPolicy.RETAIN
        )

        #Name of the registrant is the secondary/sort key
        supplier_table.add_global_secondary_index(index_name="SupplierStatus", 
              partition_key=ddb.Attribute(name="SupplierStatus", type = ddb.AttributeType.STRING))
        
        ### STEP 2 - Lambda funtion that inserts values in SupplierTable ###
        
        my_lambda = lambda1.Function(self, "EnrollNewSupplier",
            code=lambda1.Code.from_asset("./cdk/lambda/registration"),
            handler="index.lambda_handler",
            runtime= lambda1.Runtime.PYTHON_3_9,
            environment={"SUPPLIERS_TABLE_NAME":supplier_table.table_name})

        supplier_table.grant_read_write_data(my_lambda)
        
        ### Step 3 - API Gateway
        api_role = iam.Role(self, "api_role",
            assumed_by=iam.ServicePrincipal("apigateway.amazonaws.com"),
            description="api_role"
        )

         ## Creating a stable API endpoint proxy for UI to access

        #root_domain = 'thirdpartymarketplace.com'
        #sub_domain='supplier-registration-api'

        #hosted_zone = route53.HostedZone(self,id='ThirdPartyHostedZone', zone_name=root_domain)
        
        #cert = acm.Certificate(self,id='cert',domain_name=sub_domain+"."+root_domain,
        #                       validation=acm.CertificateValidation.from_dns(hosted_zone))
        
        #domain = api.DomainName(self,'ThirdPartyDomainName',
        #                        certificate=cert,
        #                        domain_name=sub_domain+"."+root_domain)
        
        ## API - Gateway
        third_party_api = api.LambdaRestApi(
            self, "suppliers-api", 
            handler=my_lambda,
            #domain_name=api.DomainNameOptions(
            #    domain_name=root_domain,
            #    certificate=cert),
            endpoint_types=[api.EndpointType.REGIONAL],
            default_cors_preflight_options=api.CorsOptions(
                 allow_origins=api.Cors.ALL_ORIGINS,
                 allow_methods=api.Cors.ALL_METHODS,
                 allow_headers=api.Cors.DEFAULT_HEADERS
            ))
        

        #route53_record = route53.ARecord(self, 'ThirdPartyDNS', 
        #                                 zone= hosted_zone,
        #                                 record_name=sub_domain,
        #                                 target=route53.RecordTarget.from_alias(route53_targets.ApiGateway(third_party_api)))

        
        ## Step 4 - Enabling web access firewall to protect API Gateway
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
        
        
        # Saving the api end point as an output that will be used by the front end stack
        CfnOutput(self, "Suppliers API Endpoint", export_name="api-end-point",
                  value=f"https://{third_party_api.rest_api_id}.execute-api.{Aws.REGION}.amazonaws.com/prod/"
                )
        
        ## Step 5 - Creating supporting resources for Step function

        ## 5.a SNS topic for all notifications regarding subscriber registration
        supplier_sns = sns.Topic(self, "supplier_notifications")

        ## 5.b SQS for queueing manual tasks
        manual_queue = sqs.Queue(self, "needs_manual_verification",
                                 queue_name="ThirdParty-Manual-Verification")

        ## 5.c Lambda function that automatically checks if the business info is valid

        lambda_role = iam.Role(self, "verify_supplier_role",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            description="verify_supplier_role"
        )

        lambda_role.add_to_policy(statement=iam.PolicyStatement(                    
                    actions=['states:SendTaskSuccess'],
                        effect= iam.Effect.ALLOW,
                        resources=["*"]
                )
        )

        lambda_role.add_to_policy(statement=iam.PolicyStatement(                    
                    actions=['logs:CreateLogGroup',
                             'logs:CreateLogStream',
                             'logs:PutLogEvents'],
                        effect= iam.Effect.ALLOW,
                        resources=["*"]
                )
        )
        

        supplier_verification_lambda = lambda1.Function(self, "VerifySupplier",
            function_name="VerifySupplier",
            role=lambda_role,
            code=lambda1.Code.from_asset("./cdk/lambda/verification"),
            handler="validate_brand.lambda_handler",
            runtime= lambda1.Runtime.PYTHON_3_9,
            environment={"SUPPLIERS_TABLE_NAME":supplier_table.table_name})

        supplier_table.grant_read_write_data(supplier_verification_lambda) 

        ## Step 6 - Step function which gets triggered on dynamodb stream

        # 6.a. IAM role for step function
        step_role = iam.Role(self, "step_role",
            assumed_by=iam.ServicePrincipal("states.amazonaws.com"),
            description="step_role"
        )

        
        # 6.b. reading step function definition
        content_str = open('./cdk/step/step_definition.json').read()
        content_str = content_str.replace("$$$ACCOUNT_ID$$$",self.account)
        #with open('./cdk/step/step_definition.json') as f:
        definition = json.loads(content_str)
        definition = json.dumps(definition, indent = 4)

        my_step = step_functions.CfnStateMachine(self, "validate_data", 
                                                 definition_string=definition,role_arn=step_role.role_arn)


        #supplier_verification_lambda.add_permission("PermitStepFunctionInvocation",
        ##                                            principal= iam.ServicePrincipal("states.amazonaws.com"),
        #                                            source_arn=my_step.ref)
        
        step_role.add_to_policy(statement=iam.PolicyStatement(                    
                    actions=['lambda:InvokeAsync', 'lambda:InvokeFunction'],
                        effect= iam.Effect.ALLOW,
                        resources=[supplier_verification_lambda.function_arn]
                )
        )

        step_role.add_to_policy(statement=iam.PolicyStatement(                    
                    actions=['sqs:*'],
                        effect= iam.Effect.ALLOW,
                        resources=["*"]
                )
        )

        # supplier_verification_lambda will be triggered by SQS events
        verify_lambda_source_sqs = lambda_event_sources.SqsEventSource(manual_queue)
        supplier_verification_lambda.add_event_source(verify_lambda_source_sqs)
    
    #todo fix the star above to the actual resource arn

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


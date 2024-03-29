# Guidance for Third-Party Marketplace on AWS

This repository has a CDK app to demonstrate how to establish a Third-Party Marketplace. The Third-Party Marketplace stack will use Lambda, Step Functions, DynamoDB, API Gateway and EventBridge to establish a backend for hosting Third-Party information. The Front-end stack, which calls the API Gateway established, presents a simple form that allows new Third-Party sellers to register. 


## Table of Contents
- [Introduction](#introduction)
- [Pre-requisites](#pre-requisites)
- [Deployment Steps](#deployment-steps)
- [Deployment Validation](#deployment-validation)
- [Running the Guidance](#running-the-guidance)
  - [Registering New Suppliers to the Third Party Marketplace](#registering-new-suppliers-to-the-third-party-marketplace)
- [Cleanup](#cleanup)
- [Usage Note](#usage-note)
- [Security](#security)
- [License](#license)


## Introduction

Retailers want to offer a wide range of products to their customers but can't necessarily take on the cost of holding the inventory. For many, creating an online marketplace for thrid-party sellers addresses this problem and creates an additional revenue stream through listing fees. Customers, in turn, find more products they want and tend to spend more, creating a virtuous cycle that benefits the retailer, the third-party sellers, and the customers. 

### Reference Architecture

![Reference Architecture Image](/assets/images/third-party-marketplace-RA.png)

## Pre-requisites

- python3 v3.9.x with venv package
- Node
- AWS CLI
- AWS Account with CLI access
- curl 7.82.0 or greater.
  - A REST client like insomnia or postman can be used instead of curl

More details about the pre-requisites to run the CDK app can be found in https://docs.aws.amazon.com/cdk/v2/guide/getting_started.html#getting_started_prerequisites

## Deployment Steps

This repository has a CDK app with Python that generates the AWS stacks that correspond to the Third Party Marketplace guidance. 

1. Clone the `main` repository
```
git clone git@github.com:aws-solutions-library-samples/guidance-for-third-party-marketplace-on-aws.git
cd guidance-for-third-party-marketplace-on-aws
```
2. Create a virtualenv on MacOS and Linux
```
python3 -m venv .venv
```

3. After the virtualenv is created, you can use the following step to activate your virtualenv.
```
source .venv/bin/activate
```
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;If you are a Windows platform, you would activate the virtualenv like this:
```
.venv\Scripts\activate.bat
```
4. Once the virtualenv is activated, you can install the required dependencies.
```
python3 -m pip install -r requirements.txt
```
5. At this point you can view the available stacks to deploy using the command

```
cdk ls
```
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;You should see 2 stacks `ThirdPartyMarketplaceStack` and `FrontEndStack` 

6. You will first need to deploy the `ThirdpartyMarketPlaceStack`. This ThirdPartyMarketplaceStack creates an Amazon DynamoDB database that stores third party suppliers information, an AWS Step Function that validates the suppliers' information, and an Amazon API gateway that exposes APIs that allow for new suppliers to be registered. 

```
cdk deploy ThirdPartyMarketplaceStack
```
The output displayed should include the API gateway end point. 

7. You will deploy the `FrontEndStack` stack using the below command which needs the API gateway end point from last step's output. The FrontEndStack creates a static S3 website that is served through an Amazon CloudFront endpoint.   

```
cdk deploy FrontEndStack -c api-end-point=<API-GATEWAY-END-POINT>
```

Capture the cloudfront end point displayed in the output

## Deployment Validation

This repository has a CDK app with Python that generates two AWS stacks 1. ThirdPartyMarketplaceStack and 2. FrontEndStack which can be verified by visiting AWS CloudFormation Console. 

## Running the Guidance

### Registering New Suppliers to the Third Party Marketplace

1. Visit cloudfront end point

![Supplier Registration Image](/assets/images/supplierregistration_website.png)

2. Enter supplier details in the form shown above

3. Check DynamoDB table to see the new entry is reflected there

4. The new DynamoDB table entry creates a DynamoDB stream entry, that triggers the following step function.

![Step Function Image](/assets/images/stepfunctions_graph.svg)

5. Manually change the status of entry from "register_new_supplier" to "Supplier" which causes the step function to sucessfully verify the entry


## Cleanup
After testing the guidance, you will be able to clean up the AWS resources using the below commands
```
cdk destroy FrontEndStack
cdk destroy ThirdPartyMarketplaceStack
```

Note: Cloudwatch logs and S3 buckets may need to be removed manually from the AWS console. 

## Usage Note

The Authorization header set to "allow" is an authentication bypass mechanism used in sample code. This should be replaced with a secure API authentication method. More details can be found at https://docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-control-access-to-api.html

For information regarding securely handling Personal Identifiable Inforamtion (PII) see https://docs.aws.amazon.com/whitepapers/latest/logical-separation/encrypting-data-at-rest-and--in-transit.html, https://docs.aws.amazon.com/sns/latest/dg/sns-message-data-protection-sensitive-data-types-pii.html and https://docs.aws.amazon.com/AmazonS3/latest/userguide/security-best-practices.html

## Security

See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.

## License

This library is licensed under the MIT-0 License. See the LICENSE file.
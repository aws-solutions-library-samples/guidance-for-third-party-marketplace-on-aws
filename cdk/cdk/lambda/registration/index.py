# import the json utility package since we will be working with a JSON object
import json
# import the AWS SDK (for Python the package name is boto3)
import boto3
# import two packages to help us with dates and date formatting
import os

from time import gmtime, strftime

import logging 

#create Logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# create a DynamoDB object using the AWS SDK
dynamodb = boto3.resource('dynamodb')
# use the DynamoDB object to select our table

table_name = os.environ["SUPPLIERS_TABLE_NAME"]

table = dynamodb.Table(table_name)
# store the current time in a human readable format in a variable
now = strftime("%a, %d %b %Y %H:%M:%S +0000", gmtime())

# define the handler function that the Lambda service will use as an entry point
def lambda_handler(event, context):
# extract values from the event object we got from the Lambda service and store in a variable
    logger.info(event)
    logger.info(context)

    body = json.loads(event['body'])
    
    #print(body)
    #body=event
    name = body['registrantName'] 
  
    brand_id = body['brandId']
    brand_legal_name = body['legalName']
    brand_dba_name = body['dbaName']
    brand_url = body['brandUrl']
    email = body['email']
    phone_number = body['phoneNumber']
    role_name = body['roleName']
    image_standard = body['imageStandard']

# check if another entry with the same brandname already exists
# if so throw error saying - conflicting brand name
    read_brand = table.get_item(Key={
        'BrandId' : brand_id
    }, ProjectionExpression = "SupplierStatus")

    logger.info("### Dynamodb result for Brand: " + brand_id + " - " + brand_legal_name)
    logger.info(read_brand)

    try:
        item = read_brand['Item']
        logger.error(" Brand - " + brand_id + " - is already " + item["SupplierStatus"])

        return {
            'statusCode': 400,
            'body': json.dumps('Hello ' + name + ', ' + brand_id +' is already registered')
        }
        
    except KeyError as k:
    # No values already present, so go a head and insert value
    # write name and time to the DynamoDB table using the object we instantiated and save response in a variable
        response = table.put_item(
            Item={
                'BrandId': brand_id,
                'SupplierStatus': "register_new_supplier",                
                'BrandLegalName': brand_legal_name ,
                'BrandDbaName': brand_dba_name,                
                'BrandURL': brand_url,
                'RegistrantName':name,
                'RegistrantRole':role_name,
                'RegistrantPhoneNumber':phone_number,
                'RegistrantEmail':email,
                'ImageStandard':image_standard,
                'RegistrationTime':now
                })
    # return a properly formatted JSON object
        return {
            'statusCode': 200,
            'body': json.dumps('Hello from Lambda, ' + name)
        }
    
    
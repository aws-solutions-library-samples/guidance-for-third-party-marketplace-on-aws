# import the json utility package since we will be working with a JSON object
import json
# import the AWS SDK (for Python the package name is boto3)
import boto3
# import two packages to help us with dates and date formatting
import os

from time import gmtime, strftime
#import logging 
#import json_logger

#create Logger
#LOGGER = json_logger.setup_logger()
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
    print(event)
    print(context)

    body = json.loads(event['body'])
    
    #print(body)
    #body=event
    name = body['firstName'] 
  
    brand = body['brandName']
    brandUrl = body['brandUrl']
    email = body['email']
    phoneNumber = body['phoneNumber']
    roleName = body['roleName']
    imageStandard = body['imageStandard']

# write name and time to the DynamoDB table using the object we instantiated and save response in a variable
    response = table.put_item(
        Item={
            'Brand': brand,
            'LatestGreetingTime':now,
            'BrandURL': brandUrl,
            'Name':name,
            'Role':roleName,
            'PhoneNumber':phoneNumber,
            'Email':email,
            'ImageStandard':imageStandard
            })
# return a properly formatted JSON object
    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda, ' + name)
    }
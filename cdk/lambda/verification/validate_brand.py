# import the json utility package since we will be working with a JSON object
import json
# import the AWS SDK (for Python the package name is boto3)
import boto3
# import two packages to help us with dates and date formatting
import os
import time

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
start_time = gmtime()


# define the handler function that the Lambda service will use as an entry point
def lambda_handler(event, context):
# extract values from the event object we got from the Lambda service and store in a variable
    logger.info(event)
    records = event['Records']
    logger.info(records)
    
    body_str = records[0]['body']
    body = json.loads(body_str)
    
    task_token = body['TaskToken']
    brand_id = body['BrandId']['S']
    brand_legal_name = body['BrandLegalName']['S']

    step_functions = boto3.client('stepfunctions')
    

    if(does_match_brand_id_name(brand_id,brand_legal_name)):
        # update dynamodb table with status - Supplier
        table.update_item(
            Key={},
            
        )

        #return task token to 
        step_functions.send_task_success(
            taskToken = task_token,
            output =  "\"brand is automatically verified to be valid\""
        )
    else: 

        # Manually update the dynamodb table with status (Supplier - for verified brands and failed_manual_verification for others) 
        new_status = "register_new_supplier"
        
        while new_status == "register_new_supplier" :
            #Be in a loop till the entry is changed from status (to_be_verified_manually)
            read_brand_status = table.get_item(Key={
                'BrandId' : brand_id
                }, ProjectionExpression = "SupplierStatus")
            item = read_brand_status['Item']
            #logger.info(item)
            new_status = item["SupplierStatus"]            
            time.sleep(2)
        
        logger.info('status of '+ brand_id + ' is ' + new_status)
        #then send the new status as the message
        if new_status == 'Supplier' :
            step_functions.send_task_success(
                taskToken = task_token,
                output = "\"brand is manually verified to be valid\""
            )
        else:
            logger.info("new status is " + new_status)
            step_functions.send_task_success(
                taskToken = task_token,
                output = "\"brand failed manual verification\""
            )
    

def does_match_brand_id_name(idval,name):
    # Production system can verify this information by calling independent sources
    brand_dict = {'911646860':'amazon com inc',
                  '611767919':'alphabet inc',
                  '12345':'our inc'
                  }
    try:
        if brand_dict[idval] == name:
            return True
    finally:
        return False
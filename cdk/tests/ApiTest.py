# importing the requests library
import requests
  
# defining the api-endpoint 
# "https://t1yn6z4gs7.execute-api.us-west-2.amazonaws.com/dev"
API_ENDPOINT = "https://ygem2y7z6j.execute-api.us-east-1.amazonaws.com/prod"
  
# your API key here
#API_KEY = "XXXXXXXXXXXXXXXXX"
  
# your source code here
source_code = '''
print("Hello, world!")
a = 1
b = 2
print(a + b)
'''
  
# data to be sent to api
data = {"body":{
  "firstName": "Ada",
  "lastName": "Lovelace",
  "brandName": "binary",
  "brandUrl": "https://binary.com",
  "email": "onesnzeros@binary.com",
  "phoneNumber": "1110001010",
  "roleName": "Chief Scientist",
  "imageStandard": true
}
}
# sending post request and saving response as response object
r = requests.post(url = API_ENDPOINT, json = data)
  
# extracting response text 
response_text = r.text
print("The response is " + response_text)
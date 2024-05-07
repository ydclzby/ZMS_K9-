import os
from ibm_watson import AssistantV2
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator

api_key = 'MD6EtN06mXxtG-cncRkrZCT0Ckt3Hj3rX91FjnbNj4G6'
service_url = 'https://api.us-south.assistant.watson.cloud.ibm.com/instances/a556627a-309f-4fed-aad4-23962294f55a'
assistant_id = 'a6973f24-9444-446a-bdb1-647949cdf540'

authenticator = IAMAuthenticator(api_key)
assistant = AssistantV2(
    version='2024-05-03',  # Specify the version you are working with
    authenticator=authenticator
)

print("assistance created")

# Set the service URL
assistant.set_service_url(service_url)

# Create a new session
response = assistant.create_session(assistant_id=assistant_id).get_result()
session_id = response['session_id']

print(session_id)

# Send a message to the chatbot
message_input = {
    'message_type': 'text',
    'text': 'hello'
}

response = assistant.message(
    assistant_id=assistant_id,
    session_id=session_id,
    input=message_input
).get_result()

# Print the chatbot's response
print(response['output']['generic'][0]['text'])



message_input = {
    'message_type': 'text',
    'text': 'a'
}

response = assistant.message(
    assistant_id=assistant_id,
    session_id=session_id,
    input=message_input
).get_result()

# Print the chatbot's response
print(response['output']['generic'][0]['text'])



# Close the session
assistant.delete_session(assistant_id=assistant_id, session_id=session_id)
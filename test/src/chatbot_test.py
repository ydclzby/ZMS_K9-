import os
from ibm_watson import AssistantV2
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator

api_key = 'pi8pPj2tKQ21SjXaWZhRH5QJHemD1VUh9OCNk4_mxZll'
service_url = 'https://api.us-south.assistant.watson.cloud.ibm.com/instances/331ce7d9-5f6f-4f18-ae44-6418b93a1753'
assistant_id = '7d57aa96-2f2f-472a-8427-85181a6f5768'

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
while True:
    input_text = input(":")
    message_input = {
        'message_type': 'text',
        'text': input_text
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
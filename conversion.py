import boto3

sqs = boto3.resource('sqs')

# Get the queue
queue = sqs.get_queue_by_name(QueueName='sm1552_pwtc')

for message in queue.receive_messages(MessageAttributeNames=['Insertion']):
    # Get the custom author message attribute if it was set
    author_text = ''
    if message.message_attributes is not None:
        author_name = message.message_attributes.get('Insertion').get('StringValue')
        if author_name:
            author_text = ' ({0})'.format(author_name)

    # Print out the body and author (if set)
    print('{0}'.format(author_text))
print("Nearest Five Locations are : \n")
# Process messages by printing out body and optional author name
for message in queue.receive_messages(MessageAttributeNames=['Locations']):
    # Get the custom author message attribute if it was set
    author_text = ''
    if message.message_attributes is not None:
        author_name = message.message_attributes.get('Locations').get('StringValue')
        if author_name:
            author_text = ' ({0})'.format(author_name)

    # Print out the body and author (if set)
    print('{0}'.format(author_text))

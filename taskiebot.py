from Flask import flask 
import json, requests, request

PAT = ''

@app.route('/', method=['GET'])
def handle_verification:
    print('Handling the verification')
    if request.args.get('hub_verifictaion_token', '') == 'token_key':
        print('Verification Successful')
        return request.args.get('hub_verification_toke', '')
    else:
        print('Verification Failed')
        return 'Wrong Verification Token'


@app.route('/', method=['POST'])
def handle_messages():
    print('Handling Messages')
    payload = request.get_data()
    print(payload)
    for sender, messaging_events(payload):
        print ("Incoming from %s: %s" % (sender, message))
        send_message(PAT, sender, message)
    return 'Ok'


def messaging_events(payload):
    data = json.loads(payload)
    for event in messaging_events:
    if "message" in event and "text" in event["message"]:
        yield event["sender"]["id"], event["message"]["text"].encode('unicode_escape')
    else:
        yield event["sender"]["id"], "I can't echo this"


def send_message(token, recipient, text):
  """Send the message text to recipient with id recipient.
  """
    r = requests.post("https://graph.facebook.com/v2.6/me/messages",
    params={"access_token": token},
    data=json.dumps({
                    "recipient": {"id": recipient},
                    "message": {"text": text.decode('unicode_escape')}
                    }),
    headers={'Content-type': 'application/json'})
    if r.status_code != requests.codes.ok:
        print (r.text)
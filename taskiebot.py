from flask import Flask, request # pylint: disable=W0611
import json, requests
app = Flask(__name__)
PAT = 'EAAejjCE6jRIBAInnEJorcRRZCbPQavMB9b1xb2Kpqvy5MJY5A8T4N7SdVOWNgQsvihSvdS0ecgQjTZAW8zWUnWcGbATez04Xx4bq1iKRiBordhOWsYa59lwV0QZBaqN6nm8d1nLlqHnbJUUh7yI2kR1xgCHWRNPuAhlgec4IQZDZD'

@app.route('/webhook', methods=['GET']) # pylint: disable=W0611
def handle_verification():
    print('Handling the verification')
    if request.args.get('hub_verification_token', '') == 'token_key':
        print('Verification Successful')
        return request.args.get('hub_verification_token', '')
    else:
        print('Verification Failed')
        return 'Wrong Verification Token'


@app.route('/webhook', methods=['POST'])
def handle_messages():
    print('Handling Messages')
    payload = request.get_data()
    print(payload)
    for sender, message in messaging_events(payload):
        print ("Incoming from %s: %s" % (sender, message))
        send_message(PAT, sender, message)
    return 'Ok'


def messaging_events(payload):
    data = json.loads(payload)
    for event in data:
        if "message" in event and "text" in event["message"]:
            yield event["sender"]["id"], event["message"]["text"].encode('unicode_escape')
        else:
            yield event["sender"]["id"], "I can't echo this"


def send_message(token, recipient, text):
    """hello world"""
    req = requests.post("https://graph.facebook.com/v2.6/me/messages",
    params={"access_token": token},
    data=json.dumps({
                    "recipient": {"id": recipient},
                    "message": {"text": text.decode('unicode_escape')}
                    }),
    headers={'Content-type': 'application/json'})
    if req.status_code != requests.codes['ok']:
        print (req.text)

if __name__ == '__main__':
    app.run()
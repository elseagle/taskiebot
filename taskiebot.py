from flask import Flask, request
import json, requests, apiai, threading, time

app = Flask(__name__)
datetime_dict = {}

PAT = ''
VERIFICATION_TOKEN = ""

@app.route('/webhook', methods=['GET'])
def handle_verification():
    print('Handling the verification')
    if ((request.args.get('hub.verify_token', '') == VERIFICATION_TOKEN)):
        print('Verification Successful')
        
        return request.args.get('hub.challenge', '')
    else:
        print('Verification Failed')
        print(request.args.get('hub.challenge', ''))
        print(equest.get_data())
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


def parse_user_message(sender, user_text):
    '''
    Send the message to API AI which invokes an intent
    and sends the response accordingly
    The bot response is checked for the date and time entities.
    If one is missing, the obtained entity is saved, then the
    missing one is requested for by sending a response asking for
    the data to be supplied. The two entites are popped from the
    storage location once the two entities are obtained.
    '''
    ai = apiai.ApiAI(CLIENT_ACCESS_TOKEN)
    r = ai.text_request()
    r.query = user_text.decode('utf-8')
    # r.getresponse()

    response = json.loads(r.getresponse().read().decode('utf-8'))
    responseStatus = response['status']['code']

    if (responseStatus == 200):
        print("API AI response", response['result']['fulfillment']['speech'])
        api_response = response['result']
        # quotes = None
        # attractions = None
        # print(response['result'])
        
        try:
            if api_response['metadata']['intentName'] == 'what_to_do':
                if sender not in datetime_dict: datetime_dict[sender] = {}
                if 'date' not in datetime_dict[sender]:
                    try:
                        datetime_dict[sender]['date'] = api_response['parameters']['date']
                    except KeyError:
                        pass
                if 'time' not in datetime_dict[sender]:
                    try:
                        datetime_dict[sender]['time'] = api_response['parameters']['time']
                    except KeyError:
                        pass
                if 'date' in datetime_dict[sender] and 'time' in datetime_dict[sender]:
                    date = datetime_dict[sender].pop('date')
                    time = datetime_dict[sender].pop('time')
                    myThread(sender, date, time).run()
        except KeyError:
            pass
        return api_response['fulfillment']['speech']


class myThread(threading.Thread):
   def __init__(self, sender, date_and_time):
      threading.Thread.__init__(self)
      self.sender = sender
      self.date_and_time = date_and_time
   def run(self):
      print "Starting thread for " + self.sender
      time.sleep(10)
      task_alert_message = 'Your task is starting in 10 minutes time. Get ready yo!'
      send_message(PAT, sender, task_alert_message)
      print "Exiting thread for " + self.sender


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
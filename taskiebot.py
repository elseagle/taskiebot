from flask import Flask, request
import json, requests, apiai, threading, time, pprint

app = Flask(__name__)
datetime_dict = {}

PAT = 'EAAIEBfGH3bIBAN2xaZBy7dW7kAxvfCQSz7K6o3ejZAJDP8QCUQRTZCkKl1iTm74qAFxVP94FNb1O4YCaPPGIW827tw5lZBJJIn7MCv2KQOUvUlZAgXI3E6CeZBFsESz3bfS8Foq4ixha7myyeFbLtEkSbe8wSNGFJQtBpqIfWtFgZDZD'
VERIFICATION_TOKEN = "token_key"
CLIENT_ACCESS_TOKEN = "176fc731ea3e46ff9f5154981eb5eeed"

@app.route('/webhook', methods=['GET'])
def handle_verification():
    print('Handling the verification')
    if ((request.args.get('hub.verify_token', '') == VERIFICATION_TOKEN)):
        print('Verification Successful')
        return request.args.get('hub.challenge', '')
    else:
        print('Verification Failed')
        print(request.args.get('hub.challenge', ''))
        print(request.get_data())
        return 'Wrong Verification Token'


@app.route('/webhook', methods=['POST'])
def handle_messages():
    print('Handling Messages')
    payload = request.get_data()
    print(payload)
    for sender, message in messaging_events(payload):
        print ("Incoming from %s: %s" % (sender, message))
        message = parse_user_message(sender, message)
        print('Message ready to be returned.')
        send_message(PAT, sender, message)
        print('Message sent.')
    return 'Ok'


def messaging_events(payload):
    data = json.loads(payload)
    pprint.pprint(data)
    messaging_events = data["entry"][0]["messaging"]
    print('Obtaining sender, msg pair from payload.')
    print([key for key in data])
    for event in messaging_events:
        print([key for key in event])
        if "message" in event and "text" in event["message"]:
            print('If condition true')
            yield event["sender"]["id"], event["message"]["text"].encode('unicode_escape')


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
    r.session_id = sender[-11:]
    print("Session ID: {}".format(sender[-11:]))
    # r.getresponse()

    response = json.loads(r.getresponse().read().decode('utf-8'))
    print('Api response obtained.')
    responseStatus = response['status']['code']

    if (responseStatus == 200):
        print("API AI response", response['result']['fulfillment']['speech'])
        api_response = response['result']
        pprint.pprint(response)
        
        try:
            if api_response['metadata']['intentName'] == 'task':
                print('Intent is "task".')
                if sender not in datetime_dict: datetime_dict[sender] = {}
                if 'date' not in datetime_dict[sender] and api_response['parameters']['date'] != '':
                    try:
                        datetime_dict[sender]['date'] = api_response['parameters']['date']
                        print('Date entity obtained.')
                    except KeyError:
                        pass
                if 'time' not in datetime_dict[sender] and api_response['parameters']['time'] != '':
                    try:
                        datetime_dict[sender]['time'] = api_response['parameters']['time']
                        print('Time entity obtained.')
                    except KeyError:
                        pass
                if datetime_dict[sender]['date'] != '' and datetime_dict[sender]['time'] != '':
                    date = datetime_dict[sender].pop('date')
                    times = datetime_dict[sender].pop('time')
                    datetime_dict.pop(sender)
                    print('About to start thread')
                    time_in_seconds, info = parse_datetime_from(date, times)
                    myThread(sender, time_in_seconds, info).start()
        except KeyError:
            pass
        return api_response['fulfillment']['speech']


class myThread(threading.Thread):
    def __init__(self, sender, date_and_time, info):
        threading.Thread.__init__(self)
        self.sender = sender
        self.date_and_time = date_and_time
        self.info = info
    def run(self):
        print("Starting thread for " + self.sender)
        time.sleep(self.date_and_time)
        task_alert_message = 'Your task is starting in {} minute(s). Get ready yo!'.format(self.info)
        send_message(PAT, self.sender, task_alert_message)
        print("Exiting thread for " + self.sender)


def parse_datetime_from(date, times):
	t1 = date[:10] + 'T' + times[11:19]
	t1 = time.strptime(t1, '%Y-%m-%dT%H:%M:%S')
	time_now = time.time()
	time_set = time.mktime(t1)
	if time_set - time_now <= 600: return (time_set - time_now - 60, 'one')
	return (time_set - time_now - 600, 'ten')


def send_message(token, recipient, text):
    """hello world"""
    req = requests.post("https://graph.facebook.com/v2.8/me/messages",
    params={"access_token": token},
    data=json.dumps({
                    "recipient": {"id": recipient},
                    "message": {"text": text}
                    }),
    headers={'Content-type': 'application/json'})
    if req.status_code != requests.codes['ok']:
        print (req.text)

if __name__ == '__main__':
    app.run()
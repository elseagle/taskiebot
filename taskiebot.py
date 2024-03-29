from flask import Flask, request
import json, requests, apiai, threading, time, pprint

app = Flask(__name__)
datetime_dict = {}

PAT = ""
VERIFICATION_TOKEN = ""
CLIENT_ACCESS_TOKEN = ""

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
    '''Docstring for myThread class'''

    def __init__(self, sender, date_and_time, info, kind='alerts'):
        threading.Thread.__init__(self)
        self.sender = sender
        self.date_and_time = date_and_time
        self.info = info
        self.kind = kind

    def run(self):
        if self.kind != 'alerts':
            self.pingServer()
            return
        print("Starting thread for " + self.sender)
        time.sleep(self.date_and_time)
        task_alert_message = 'Your task is starting in {} minute(s). Get ready yo!'.format(self.info)
        send_message(PAT, self.sender, task_alert_message)
        time.sleep(598 if self.info == 'ten' else 58)
        task_alert_message = 'Heyo! You scheduled a task, and it starts now.'
        send_message(PAT, self.sender, task_alert_message)
        print("Exiting thread for " + self.sender)

    def pingServer(self):
        requests.post('https://taskiebot.herokuapp.com/webhook')
        print('Server pinged.')
        time.sleep(28*60)
        self.pingServer()


def parse_datetime_from(date, times):
	t1 = str(date) + str(times)
	print(t1)
	t1 = time.strptime(t1, '%Y-%m-%d%H:%M:%S')
	time_now = time.time()
	time_set = time.mktime(t1)
	print("Time now: {}, time then: {}".format(time_now, time_set))
	if time_set - time_now -3600 <= 600: return (time_set - time_now - 3660, 'one')
	return (time_set - time_now - 4200, 'ten')


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


# class 
#     def permission_response():
#         permissions =  permission_response.permisssions()
#         isGranted = permission_response.isGranted()
        
#         if isGranted:
#             print("Permision is granted")
#         else:
#             print("Error Occurred")


if __name__ == '__main__':
    app.run()
    myThread(None,None,None,kind='onStart').start()

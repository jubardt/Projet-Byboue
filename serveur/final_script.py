#!/usr/bin/env python3
import ssl
import smtplib
import bluetooth
import socket 
import time
import nxppy
import json
import threading
import asyncio


from pynotifier import NotificationClient, Notification
from pynotifier.backends import platform, smtp

import logging
import json, os

from flask import request, Response, render_template, jsonify, Flask
from pywebpush import webpush, WebPushException


hostMACAddress = 'b8:27:eb:64:62:de' #The MAC address of a Bluetooth adapter on the server. The server might have multiple Bluetooth adapters.
port = 3
backlog = 1
size = 1024
s = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
binded = False

HAPPY = "happy"
MEH = "meh"
SAD = "sad"
VERY_SAD = "very_sad"

#10 minutes
VISIT_TIMEOUT = 10*60
#1 semaine
DOWNGRADE_TIME = 7*24*60*60

# API requirements
app = Flask(__name__)
app.config['SECRET_KEY'] = '9OLWxND4o83j4K4iuopO'

DER_BASE64_ENCODED_PRIVATE_KEY_FILE_PATH = os.path.join(os.getcwd(),"private_key.txt")
DER_BASE64_ENCODED_PUBLIC_KEY_FILE_PATH = os.path.join(os.getcwd(),"public_key.txt")

VAPID_PRIVATE_KEY = open(DER_BASE64_ENCODED_PRIVATE_KEY_FILE_PATH, "r+").readline().strip("\n")
VAPID_PUBLIC_KEY = open(DER_BASE64_ENCODED_PUBLIC_KEY_FILE_PATH, "r+").read().strip("\n")

VAPID_CLAIMS = {
"sub": "mailto:develop@raturi.in"
}


class Chieng:
	def __init__(self):
		self.state = SAD
		self.in_activity = False
		self.last_update = time.time()
		
	def set_activity(self, activity):
		self.in_activity = activity
		if activity:
			self.last_update = time.time()
		
	def get_activity(self):
		return self.in_activity
	
	def get_last_update(self):
		return self.last_update
		
	def upgrade_state(self):
		if not self.in_activity:
			if self.state == MEH:
				self.state = HAPPY
			elif self.state == SAD:
				self.state = MEH
			elif self.state == VERY_SAD:
				self.state = SAD
			self.last_update = time.time()
			self.notifyUser()
	def downgrade_state(self):
		if self.state == HAPPY:
			self.state = MEH
		elif self.state == MEH:
			self.state = SAD
		elif self.state == SAD:
			self.state = VERY_SAD
		self.last_update = time.time()
		self.notifyUser()
			
	def get_state(self):
		return self.state
		
	def notifyUser(self):
		push_v1(self.get_state(),self.get_last_update())
		print("Je notifie")

data = ""
data_sem = threading.Semaphore()

chieng_sem = threading.Semaphore()
chieng = Chieng()

peoples_sem = threading.Semaphore()
peoples = {}

subcribers_sem = threading.Semaphore()
subcribers = {}

def backend_thread(name):	
	print("backend start")
	while True:
		peoples_sem.acquire()
		# clean up different visits 
		ts = time.time()
		to_remove = []
		for people in peoples:
			diff = ts - peoples[people][1]
			if diff > VISIT_TIMEOUT:
				to_remove.append(people)
		for rm in to_remove:
			peoples.pop(rm)
		chieng_sem.acquire()
		# check for updating the visit mood
		if len(peoples) >= 1:
			chieng.upgrade_state()
			chieng.set_activity(True)
		elif len(peoples) == 0:
			chieng.set_activity(False)
		print("chieng : ", chieng.get_activity(), " ", chieng.get_state())
		# check for timeout mood update
		if ts - chieng.get_last_update() > DOWNGRADE_TIME:
			chieng.downgrade_state()
		chieng_sem.release()
		peoples_sem.release()
		time.sleep(10)
	print("backend_stop")

def bluetooth_thread(name):
	i = 0
	s = None
	try:
		subprocess.run("bluetoothctl pair 00:0E:0B:0E:AB:35",shell=True)
		subprocess.run("bluetoothctl trust 00:0E:0B:0E:AB:35",shell=True)
		s = socket.socket(socket.AF_BLUETOOTH,socket.SOCK_STREAM,socket.BTPROTO_RFCOMM)
		s.connect(("00:0E:0B:0E:AB:35",1))
		retry = False
	except Exception as e: 
		retry = True
		print(e)
	print("pairing")
	while True:
		try:
			print("try : ", i)
			bytedata = s.recv(2048)
			print("data: ", bytedata)
			myjson = bytedata.decode('utf8').replace("'",'"')
			myjson = json.loads(myjson)
			i += 1
			print("i : ", i)
		except Exception as e:
			print(e)
			retry = True
		print("retry")
		if(i%5==0 or retry):
			retry = True
			print("retry")
			while retry:
				print("retry")
				try:
					if s is not None:
						s.close()
					print("Reconnection")
					time.sleep(0.5)
					s = socket.socket(socket.AF_BLUETOOTH,socket.SOCK_STREAM,socket.BTPROTO_RFCOMM)
					s.connect(("00:0E:0B:0E:AB:35",1))
					print("Connected")
					retry = False
				except Exception as e:
					print(e)
					retry = True

def nfc_thread(name):
	print("nfc thread start")
	mifare = nxppy.Mifare()
	while True:
		try:
			uid = mifare.select()
			ndef_data = mifare.read_ndef()
			print("data :", ndef_data[7:])
			user_id = int(ndef_data[10:])
			
			peoples_sem.acquire()
			if peoples.get(user_id) is not None:
				peoples[user_id][1] = time.time()
			else:
				# time of first arrival, time of last connection
				ts = time.time() 
				peoples[user_id] = [ts, ts]
				
			peoples_sem.release()
		except nxppy.SelectError:
			pass
		except MemoryError:
			print('Could not read chip')
			pass
		except ValueError:
			print('Could not parse data from JSON')
			pass
	print("nfc thread stop")

def send_web_push(subscription_information, message_body):
    return webpush(
        subscription_info=subscription_information,
        data=message_body,
        vapid_private_key=VAPID_PRIVATE_KEY,
        vapid_claims=VAPID_CLAIMS
    )

@app.route('/')
def index():
    return render_template('index.html')

@app.route("/subscription/", methods=["GET", "POST"])
def subscription():
    """
        POST creates a subscription
        GET returns vapid public key which clients uses to send around push notification
    """

    if request.method == "GET":
        print("======================= GET ================== ",VAPID_PUBLIC_KEY)
        return Response(response=json.dumps({"public_key": VAPID_PUBLIC_KEY}),headers={"Access-Control-Allow-Origin": "*"}, content_type="application/json")

    subscription_token = request.get_json("subscription_token")
    print("subscription_token ==================> ",subscription_token)
    return Response(status=201, mimetype="application/json")

@app.route("/push_token/",methods=['POST'])
def romain():
    print("JE SUIS DANS ROMAIN")
    message = "{\"etat\":state,\"derniere_maj\":last_update}"
    print("message : ",message)

    if not request.json or not request.json.get('sub_token'):
        return jsonify({'failed':1})

    print("request.json",request.json)

    token = request.json.get('sub_token')
    
    try:
        token = json.loads(token)
        subcribers_sem.acquire()
        subcribers[str(token)] = ""
        subcribers_sem.release()
        subcribers_sem.acquire()
        for key in subcribers.keys():
            print("Cle ==================> ",key)
            send_web_push(key, message)
        subcribers_sem.release()
        return jsonify({'success':1})
    except Exception as e:
        print("error",e)
        return jsonify({'failed':str(e)})

@app.route("/push_v1/",methods=['POST'])
def push_v1(state="Init",last_update="now"):
    #message = str(jsonify({"etat":state,"derniere_maj":last_update}))
    message = "{\"etat\":state,\"derniere_maj\":last_update}"
    print("message : ",message)
    #print(len(message))
    #print(message.is_json)
    #print("is_json",request.is_json)

    if not request.json or not request.json.get('sub_token'):
        return jsonify({'failed':1})

    print("request.json",request.json)

    token = request.json.get('sub_token')
    print("token ============= >",token)
    
    try:
        token = json.loads(token)
        send_web_push(token, message)
        return jsonify({'success':1})
    except Exception as e:
        print("error",e)
        return jsonify({'failed':str(e)})

if (__name__ == "__main__"):	
	b_thread = threading.Thread(target=bluetooth_thread, args=(1,))
	n_thread = threading.Thread(target=nfc_thread, args=(1,))
	bc_thread = threading.Thread(target=backend_thread, args=(1,))
	b_thread.start()
	n_thread.start()
	bc_thread.start()
	app.run(host="0.0.0.0",port=8080)
	bc_thread.join()
	n_thread.join()
	b_thread.join()
	


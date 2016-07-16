#!/bin/python

# standard imports:
from threading import Thread
from time import sleep
from random import randint
import socket,sys, select
import json
from pprint import *
import bitcoin
# own imports:
import jsonConn, hpUtils, txUtils


# Parameters to be, later on, inputed to the program (rather than harcoded)

class connManager(Thread):

	def __init__(self,_c, info):
		Thread.__init__(self)
		self.c = _c
		self.balance = 0 
		self.usage = 0
		self.ipClient = info
		self.privS ='KxF9VktMWSdZV72ZMaB4bQM3D25bGEinwqrwW8t2kh73MnJZ2ajp'
	
	def controlSpin(self):		
		while True:
			sleep(0.1)
			print 'Current balance: %d' %self.balance
			print 'Current usage: ',hpUtils.retrieveUsage(self.ipClient)	
			if hpUtils.retrieveUsage(self.ipClient) > self.balance:
				print 'Usage exceeds balance > deny Fwd'
				self.cashier.signal=False
				hpUtils.denyFwd(self.ipClient)
			
	def run(self):
		print 'Initialisation of MPC...'

		# exchange public keys
		pubKeyClient = txUtils.exchangePubKey(bitcoin.privtopub(self.privS), self.c)
		
		#print 'On to dtx'
		signedDtx = self.c.jrecv()
		print signedDtx
		scriptDtx = self.c.jrecv()
		
		# broadcast D 
		try:
			bitcoin.pushtx(signedDtx)
		except :
			print sys.exc_info()[0]
			raise Exception('pb with the Dtx received')
		print 'MPC initialised'
		self.balance += 500000
		
		# authorize use of the internet:
		hpUtils.allowFwd(self.ipClient)	
	
		# set up Cashier (observed)
		self.cashier = cashier(self.c)
		self.cashier.addObserver(self)    # obviously not the right way
		#self.cashier.start()	
		
		# start control spin
		self.controlSpin()
			
		print 'Terminating'
	        self.cashier.join()

class cashier(Thread):
        def __init__(self, _c):
                Thread.__init__(self)
                self.c = _c
		self.signal = True
		self.observers = []
		self.payment = 0
	def addObserver(self, obs):
		self.observers.append(obs)

	def extractAmount(self, payment):
		d = bitcoin.deserialize(payment)
		return d['outs'][0]['value']

	def notifyObservers(self, payment):
		amnt = extractAmount(payment)
		print amnt
		for obs in self.observers:obs.notify(amnt)  
	
	def verifyPayment(self, payment, amount):
		# deserialized payment:
		#desPay = bitcoin.deserialize(payment)
		# verify amount
	 	#if desPay['outs'][0]['value'] < amount:
		#	print 'Wrong Amount'	
		#	return False
		# verify beneficiary
		#if desPay['outs'][0]['script']
		#	return False 
		return True             

        def run(self):
		print 'Cashier running'
		self.amount = 0
		while self.signal:
			print 'cashier spinning'
			
			self.rlist =[]
			self.wlist =[]
			self.xlist =[]	
			self.toread=[self.c.socket]
			self.rlist, self.wlist, self.xlist = select.select(self.toread, [], [], 2)
			if self.rlist != []: self.payment = self.c.jrecv()
			print self.payment	
			self.rlist, self.wlist, self.xlist = select.select(self.toread, [], [], 2)
			if self.rlist != []: self.signature= self.c.jrecv()

			if self.verifyPayment(self.payment, 12):
				print 'Notifying payment'
                                self.notifyObservers(self.payment)
			sleep(.2)
		self.c.close()
		print 'Cashier stopping'


	
##############################################################################
# This is the code of the dispatcher
if __name__ == "__main__":
	
	serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	port = 7878                
	serversocket.bind(('', port))
	serversocket.listen(5)

	# First, forbid all forwarding
	# set default policy of FORWARD to drop 
	hpUtils.setChainPolicy('FORWARD','DROP')
	# flush FORWARD
	hpUtils.flushChain('FORWARD')
	# authorize interaction with blockchain.info
        hpUtils.allowSpecificWebsite('104.16.54.3')	
        hpUtils.allowSpecificWebsite('104.16.55.3')	
	
	print('Done with Iptables setup')

	# Second, connect with clients
	while True:
		c, addr = serversocket.accept()
		print 'Got connected by: ', addr
		cm = connManager(jsonConn.JsonConn(c), addr[0])
		cm.start()










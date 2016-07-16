#!/bin/python

# standard imports:
import socket
from random import randint
from time import sleep
import bitcoin, pprint, sys
# own imports:
import jsonConn, txUtils




def paymentSpin(redeemScript, conn, privkeyC, pubkeyS, increment):
	amount = 0
	i = 0
	print 'inpaymentspin'
	while i<10:
		print 'Sppinnning'
		amount += increment
		i+=1
		# make a payment transaction with amount += increment
		Ptx = txUtils.makePtx(redeemScript, bitcoin.privtopub(privkeyC), pubkeyS, amount)
		# partially sign it
		clientSig = bitcoin.multisign(Ptx, 0, redeemScript, privkeyC) 
		clientSig = 'clientSig in pspin'
		# send Ptx 
		conn.jsend(Ptx)
		# send client signature
		conn.jsend(clientSig)
		sleep(.5)
	print 'Total spent this time: %d' %amount 
	return amount 


if __name__ == "__main__":
	
	if len(sys.argv) > 1:
		host = str(sys.argv[1])
	else:
		host = '192.168.12.1'
		
	# Parameters to be, later on inputed to the program 
	privC = 'L4hhTgFtTkLc5rWW7M2iHb1J6nc9o5bNw3vhuyxWNzpKLqTUkhdC'
	dep = 150000
	increment = 5000

	# Create socket and connect                                 
	s = jsonConn.JsonConn(socket.socket(socket.AF_INET, socket.SOCK_STREAM))                         
	s.connect((host, 7878))
	print 'Let s surf!'

	# exchange public keys
	pubKeyServer = txUtils.exchangePubKey(bitcoin.privtopub(privC), s)
	# Deposit Tx
	print 'Now on to the Dtx'
	# build and sign Dtx
	[unsignedDtx, scriptDtx] = txUtils.makeDtx(privC, pubKeyServer, dep)
	print 'On to signing'
	signedDtx = bitcoin.sign(unsignedDtx, 0, privC)
	#send Dtx
	print 'done with tx'
	s.jsend('signedDtx')
	s.jsend('scriptDtx')
	print 'Script: ', scriptDtx
	#paymentSpin
	paymentSpin(scriptDtx, s, privC, pubKeyServer, increment)

	# close the channel
	s.close()
	print 'Internet is overrated'







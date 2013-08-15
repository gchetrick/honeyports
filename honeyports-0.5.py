#!/usr/bin/python           

# Author: Paul Asadoorian, PaulDotCom/Black Hills Information Security
# Contributors: Benjamin Donnelly, BHIS;Greg Hetrick, PaulDotCom

# Date: 7/28/13

# Description: This script listens on a port. When a full connection is made to that port
# Honeyports will create a firewall rule blocking the source IP address.
# Currently works on Windows, Linux and OS X with the built-in firewalls.
# You no longer need Netcat on your system!

# TODO:
# Create own chain for easy management in linux
# Fix menuing system
# Add Daemon option
# List all interfaces and define the interface to listen on
# Listen on multiple ports
# Add ability for a whilelist - Listening port and localhost or file input
# Syslog blocks in daemon mode
# Set/config a lifetime for the FW rule that is created
# Add options for protocol specific banners or taunting messages.

# Change Log v0.5
# Added support for multi-threading
# fix options section to actually catch a miss and improper port


# Import the stuff we need

import threading
import thread
import SocketServer
import socket               # Import socket module
import platform          # Import platform module to determine the os
from subprocess import call # Import module for making OS commands (os.system is deprecated)
import sys, getopt       # Import sys and getopt to grab some cmd options like port number
import os          # Import os because on Linux to run commands I had to use popen

class ThreadingTCPServer (SocketServer.ThreadingMixIn, SocketServer.TCPServer):
   pass

class ServerHandler (SocketServer.StreamRequestHandler):

  def handle(self):
    print "Got Connection from: ", self.client_address
    print "Blocking the address: ", self.client_address[0]
    hostname = self.client_address[0]
    thread = threading.current_thread()
    self.request.sendall(nasty_msg)
    
    # If there is a full connection, create a firewall rule
    # Run the command associated with the platform being run:
    if platform == "Windows":
      print "Creating a Windows Firewall Rule\n"
      fw_result = call('netsh advfirewall firewall add rule name="honeyports" dir=in remoteip= ' + hostname + ' localport=any protocol=TCP action=block > NUL', shell=True)   
    elif platform == "Linux":
      print "Creating a Linux Firewall Rule\n"
      command = '/sbin/iptables -A INPUT -s ' + hostname + ' -j ACCEPT'
      fw_result = os.popen(command)
      if fw_result:
        fw_result=0
      else:
        fw_result=1
    elif platform == "Darwin":
      print "Creating a Mac OS X Firewall Rule\n"
      fw_result = call(['ipfw', '-q add deny src-ip ' + hostname])
    if fw_result:
      print 'Crapper, firewall rule not added'
    else:
      print 'I just blocked: ', hostname
    return

  def finish(self):
    print self.client_address, 'disconnected!'
    self.request.send('bye ' + str(self.client_address) + '\n')

# Declare some useless variables to display info about this script
def StartServer (threadName, host, port):
  
  server = SocketServer.ThreadingTCPServer((host,port) , ServerHandler)
  ip,port = server.server_address
  serverthread =  threading.Thread(target=server.serve_forever())
  serverthread.daemon = True
  serverthread.start()

def MenuInteraction (threadName):
  # Listen for user to type something then give options to
  # Flush all firewall rules, quit or print the rules
  while True:
    mydata = raw_input('Enter Commands (q=quit f=flush rules p=print rules): ')

    if mydata == "f":
      print "Flushing firewall rules..."
      print 'Flush command is: ', str(flush)
      call(flush[0] + ' ' + flush[1], shell=True)
    elif mydata == "p":
      print 'Here is what your rules look like:'
      call(fwlist[0] + ' ' +  fwlist[1], shell=True)
    elif mydata == "q":
      print "Goodbye."
      sys.exit()
    else:
      print "What?"

port=''                # Reserve a port for your service, user must use -p to specify port.
version="0.5"
name="Honeyports"

USAGE="""
USAGE %s -p <port>

-p, --port      Required <port>, port to start the listner on (1-65535)
-h, --host      Required <host>, host/IP address to run the listner on
-D, --daemon    Optionally run in daemon mode (supresses interactive mode)
""" % sys.argv[0]

# Message to send via TCP to connected addresses
# Can be used to mimic a banner
            
nasty_msg = "\n***** This Fuck you provided by the fine folks at PaulDotCom, Hack Naked!*****\n" 

try:
        myopts, args = getopt.gnu_getopt(sys.argv[1:], "h:p:D", ["host", "port", "daemon"])
except getopt.GetoptError as error:
        print (str(error))
        print USAGE
        sys.exit(2)
#initial check to verify we have any options since port num is required.
if not myopts:
      print USAGE
      sys.exit(2)

for o, a in myopts:
   if o == '-p' and int(a) < 65536:
      port=int(a)
   else:
      print("Not a valid port number")
      print USAGE
      sys.exit(2)
		
print name, 'Version:', version
print 'I will listen on TCP port number: ', port 

# Determine which platform we are running on

platform = platform.system()
print 'Honeyports detected you are running on: ', platform

if platform == "Darwin":
	#host = socket.gethostname() # Get local IP on OS X
  flush = 'ipfw', '-q flush'
  fwlist = 'ipfw', 'list'
  print "Setting sockets up for OS X"
elif platform == "Linux":
	#host = s.getsockname()[0] # Get local IP on Linux
  flush = 'iptables', '-F'
  fwlist = 'iptables', '-nL'
  print "Setting sockets up for Linux"
else:
  flush = 'netsh', 'advfirewall reset'
  fwlist = "netsh", """ advfirewall firewall show rule name=honeyports | find "RemoteIP" """
  host = ''
host = '172.16.67.228'

#try:
thread.start_new_thread( StartServer, ("Thread1", host, port))
thread.start_new_thread( MenuInteraction, ("Thread2",))
#StartServer("Thread1",host, port)
#except:
 #  print "Error: unable to start thread"
while 1: 
  pass

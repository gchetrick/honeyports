#!/usr/bin/python           

# Author: Paul Asadoorian, PaulDotCom/Black Hills Information Security
# Contributors: Benjamin Donnelly, BHIS

# Date: 7/28/13

# Description: This script listens on a port. When a full connection is made to that port
# Honeyports will create a firewall rule blocking the source IP address.
# Currently works on Windows, Linux and OS X with the built-in firewalls.
# You no longer need Netcat on your system!

# TODO:
# Needs to have multi-threaded stuff added

# Import the stuff we need

import socket               # Import socket module
import platform		    # Import platform module to determine the os
from subprocess import call # Import module for making OS commands (os.system is deprecated)
import sys, getopt	    # Import sys and getopt to grab some cmd options like port number
import os		    # Import os because on Linux to run commands I had to use popen

# Declare some useless variables to display info about this script

port=''                # Reserve a port for your service, user must use -p to specify port.
version="0.04a"
name="Honeyports"

# Message to send via TCP to connected addresses
# Can be used to mimic a banner
nasty_msg = "\n\n***** Fuck You For Connecting *****\n\n" 

# Debug
DEBUG = None

# Whitelist: Source (Client) IP addresses that should never be blocked
# 
#whitelist=127.0.0.1

# Command line options!

try:
   myopts, args = getopt.getopt(sys.argv[1:],"dp:")
   #print 'Options: ', myopts, args
except getopt.GetoptError:
   print("Usage: %s -p port " % sys.argv[0])
   sys.exit(2)

for o, a in myopts:
   if o == '-p':
      try:
         port=int(a)
      except:
         print("Not a valid port")
         sys.exit(2)
		 
   elif o == '-d':
      DEBUG = True
      print("Debugging Enabled.")

   elif o == '':
      print("Usage: %s -p port (Required)" % sys.argv[0])
      sys.exit(2)
   else:
      print("Usage: %s -p port " % sys.argv[0])

   if DEBUG:
      print name, 'Version:', version
      print 'I will listen on TCP port number: ', port 

# Determine which platform we are running on

platform = platform.system()
if DEBUG: print 'Honeyports detected you are running on: ', platform

# Start Listener

s = socket.socket()         # Create a socket object

# Doesn't hog the port on termination
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) 


# God, sockets are a nightmare on different platforms!
# May have to let the user pick from a list
# Which interface to listen on

if platform == "Darwin":
	host = socket.gethostname() # Get local IP on OS X
	if DEBUG: print "Setting sockets up for OS X"
elif platform == "Linux":
	host = s.getsockname()[0] # Get local IP on Linux
	if DEBUG: print "Setting sockets up for Linux"
else:
	host = ''
	
if port >= 1 and port <= 65535:
   try:
      s.bind((host, port))        # Bind to the port
   except socket.error, e:
      print("Unable to bind to port with error: {0} -- {1} ".format( e[0], e[1]))
      sys.exit(2)
else:
   print("Usage: %s -p port " % sys.argv[0])
   print 'Please specify a valid port range (1-65535) using the -p option'
   sys.exit(2)

s.listen(5)                 # Now wait for client connection.
host_ip = s.getsockname()[0]
print 'Listening on ', host, 'IP: ', host_ip, ' : ', port

while True:
   c, addr = s.accept()     # Establish connection with client.
   hostname = str(addr[0])
   print 'Got connection from', hostname

   # If connecting IP is the same as the listening IP, abort

   if hostname == host_ip:
      print 'Source and Destination IP addresses match, aborting'
      abort = True
      c.close()
   else:
      c.send(nasty_msg)
      print 'Blocking the address: ', hostname

      # If there is a full connection, create a firewall rule
      # Run the command associated with the platform being run:

      if platform == "Windows":
         print "Creating a Windows Firewall Rule\n"
         fw_result = call('netsh advfirewall firewall add rule name="honeyports" dir=in remoteip= ' + hostname + ' localport=any protocol=TCP action=block > NUL', shell=True)
         flush = 'netsh', 'advfirewall reset'
         fwlist = "netsh", """ advfirewall firewall show rule name=honeyports | find "RemoteIP" """
	
      elif platform == "Linux":
         print "Creating a Linux Firewall Rule\n"
         fw_result = os.popen( '/sbin/iptables -A INPUT -s ' + hostname + ' -j REJECT' )
         if fw_result:
            fw_result=0
         else:
            fw_result=1

         flush = 'iptables', '-F'
         fwlist = 'iptables', '-nL'

      elif platform == "Darwin":
         print "Creating a Mac OS X Firewall Rule\n"
         fw_result = call(['ipfw', '-q add deny src-ip ' + hostname])
         flush = 'ipfw', '-q flush'
         fwlist = 'ipfw', 'list'

      if fw_result:
         print 'Crapper, firewall rule not added'
      else:
         print 'I just blocked: ', hostname

      c.close()                # Close the connection

# Listen for user to type something then give options to
# Flush all firewall rules, quit or print the rules

   if abort:
      print 'No firewall rules created.'
   else: 
      mydata = raw_input('Enter Commands: q=quit f=flush rules p=print rules.')

      if mydata == "f":
         print "Flushing firewall rules..."
         print 'Flush command is: ', str(flush)
         call(flush[0] + ' ' + flush[1], shell=True)
      elif mydata == "p":
         print 'Here is what your rules look like:'
         call(fwlist[0] + ' ' +  fwlist[1], shell=True)
      elif mydata == "q":
         if platform == "Linux":
            s.shutdown(1)
         s.close()
         print "Goodbye."
         exit()

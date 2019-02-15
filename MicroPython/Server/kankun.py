#!/usr/bin/python
import socket
import fcntl
import struct
import urllib2
import csv
import sys
import argparse
import os

# Author: Yahya Khaled
parser = argparse.ArgumentParser(description='Kankun automation')
parser.add_argument('-l','--list', help='List Kankun devices on the network',required=False)
parser.add_argument('-s','--switch',help='Issue switch command followed by on or off', required=False)
parser.add_argument('-d','--device',help='Specify the device name specified in the relay.cgi script per device', required=False)
args = parser.parse_args()


def get_ip_address(ifname):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    return socket.inet_ntoa(fcntl.ioctl(
        s.fileno(),
        0x8915,  # SIOCGIFADDR
        struct.pack('256s', ifname[:15])
    )[20:24])



def get_kankun_list():
  local_ip = get_ip_address('eth0')
  local_ip = local_ip.split('.')
  kankun_list = []

  for i in range(1,254):
    socket.setdefaulttimeout(0.1)
    s = socket.socket()
    address = local_ip[0]+"."+local_ip[1]+"."+local_ip[2]+"."+str(i)
    port = 80 # port number is a number, not string
    try:
        s.connect((address, port))
        response =  address, urllib2.urlopen("http://"+address+"/cgi-bin/relay.cgi?").read()
        print response
        kankun_list.append(("ip="+response[0], response[1].rstrip()))
    except Exception, e:
       # alert('something\'s wrong with %s:%d. Exception type is %s' % (address, port, `e`))
       pass


  with open(os.path.expanduser('~')+"/.kankun-devices.list",'w') as out:
    csv_out=csv.writer(out)
    for row in kankun_list:
      csv_out.writerow(row)

def switch_kankun():

  kankun_device_ip = []
  kankun_device_response = []
  kankun_csv = csv.reader(open(os.path.expanduser('~')+"/.kankun-devices.list"))
  devicesCounter = 0
  for row in kankun_csv:
    kankun_device_ip.append(row[0])
    kankun_device_response.append(row[1])
    devicesCounter = devicesCounter + 1

  if devicesCounter == 0:
    print "Please try \"kankun -l list\" first"
    exit(0)
  if args.switch.lower() != "on" and args.switch.lower() != "off":
    print "-s option can only be on or off."
  else:
    for index in range(len(kankun_device_response)):
      if args.device.lower() in kankun_device_response[index].lower():
         port = 80 # port number is a number, not string
         socket.setdefaulttimeout(5)
         s = socket.socket()
         try:
             s.connect((kankun_device_ip[index].split('ip=')[1], port))
             response = urllib2.urlopen("http://"+kankun_device_ip[index].split('ip=')[1]+"/cgi-bin/relay.cgi?"+args.switch.lower()).read()
             print response
         except Exception, e:
            #alert('something\'s wrong with %s:%d. Exception type is %s' % (kankun_device_ip[index].split('ip=')[1], port, `e`))
            print "http Error, please update your list or check your spelling"

def status_kankun():

  kankun_device_ip = []
  kankun_device_response = []
  kankun_csv = csv.reader(open(os.path.expanduser('~')+"/.kankun-devices.list"))
  devicesCounter = 0
  for row in kankun_csv:
    kankun_device_ip.append(row[0])
    kankun_device_response.append(row[1])
    devicesCounter = devicesCounter + 1

  if devicesCounter == 0:
    print "Please try \"kankun -l list\" first"
    exit(0)
  for index in range(len(kankun_device_response)):
    if args.device.lower() in kankun_device_response[index].lower():
       port = 80 # port number is a number, not string
       socket.setdefaulttimeout(5)
       s = socket.socket()
       try:
           s.connect((kankun_device_ip[index].split('ip=')[1], port))
           response = urllib2.urlopen("http://"+kankun_device_ip[index].split('ip=')[1]+"/cgi-bin/relay.cgi?").read()
           print response
       except Exception, e:
          #alert('something\'s wrong with %s:%d. Exception type is %s' % (kankun_device_ip[index].split('ip=')[1], port, `e`))
          print "http Error, please update your list or check your spelling"

if args.list is not None:
  get_kankun_list()
elif args.device is not None and args.switch is not None:
  switch_kankun()
elif args.device is not None:
  status_kankun()

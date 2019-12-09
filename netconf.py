import paramiko
import xmltodict
import xml
import pprint
import sys
from helpers import *
from time import sleep
from functools import partial
from bs4 import BeautifulSoup
from itertools import cycle

class SSH():
	client = None
	session = None
	read_interval = .6
	connect_params = {"hostname":"192.168.0.201", "username":"goon", "password":"goon","port":22,"look_for_keys":False, "allow_agent":False}
	def read(self):
		blocks = []
		chunk_size = 900000
		while True:
			sleep(self.read_interval)
			block = self.session.recv(chunk_size)
			#DEBUG
			# print(block.decode(),end="")
			# file_add_contents("add.xml",block.decode())
			#end debug
			blocks.append(block.decode())
			if len(block) < chunk_size:
				break
		text = ''.join(blocks).strip()
		return text
	def start(self, *args,**kwargs):
		self.client = paramiko.SSHClient()
		#overrides the default above
		self.connect_params.update(kwargs)
		hostname = self.connect_params.get("hostname")
		del self.connect_params['hostname']
		#debug
		print("LOGGING INTO:")
		print(hostname,self.connect_params)
		self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
		self.client.connect(hostname,**self.connect_params)
		self.session = self.client.get_transport().open_session()
		# Only uncomment if sending command line arguments. Separate into separate class or function if expands.
	def s(self, *args,**kwargs):
		'''console shorthand'''
		self.start(*args,**kwargs)
	def close(self):
		self.client.close()
		print("SSH Session Closed")

class CommandLine(SSH):
	'''Command Line Specific'''
	#port 22
	connect_params = {'hostname': '10.10.20.48', 'username': 'cisco', 'password': 'cisco_1234!', 'port': 22, 'look_for_keys': False, 'allow_agent': False}
	def __init__(self, *args,**kwargs):
		self.start(*args,**kwargs)
		#invoke shell is specific to Command Lines (not netconf)
		self.session.invoke_shell()
	def send(self,command):
		command = command + "\n"
		self.session.send(command.encode())
		response = self.read()
		return response

class Netconf(SSH):
	'''Class & Functions & Values specific to NETCONF'''
	#
	#Cisco DevNet Params
	#port 830
	#
	cisco_namespace_prefix = 'http://cisco.com/ns/yang/'
	ietf_namespace_prefix = 'urn:ietf:params:xml:ns:yang:'
	connect_params = {'hostname': '10.10.20.48', 'username': 'cisco', 'password': 'cisco_1234!', 'port': 830, 'look_for_keys': False, 'allow_agent': False}
	terminator = ']]>]]>'
	def __init__(self, *args,**kwargs):
		#Cisco Devnet Params
		self.start(*args,**kwargs)
		self.netconf_hello()
	def n(self):
		'''console restart socket & netflow shorthand'''
		self.start()
		self.netconf_hello()
	def send(self,command):
		command = command + self.terminator + "/n"
		self.session.send(command.encode())
		response = self.read()
		return response
	def netconf_hello(self):
		self.session.invoke_subsystem('netconf')
		hello_rpc = '<?xml version="1.0" encoding="UTF-8"?><hello xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"><capabilities><capability>urn:ietf:params:netconf:base:1.0</capability></capabilities></hello>'
		return self.send(hello_rpc)
	def change_hostname(self,hostname):
		self.send(f'<?xml version="1.0" encoding="UTF-8"?> <rpc message-id="101" xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"> <edit-config> <target> <running/> </target> <config> <cli-config-data> <cmd>hostname {hostname}</cmd> </cli-config-data> </config> </edit-config> </rpc>')
	def print_netconf_graph(self,xml_response):
		xml_response = xml_response.replace(self.terminator,'')
		try:
			print_structure(xmltodict.parse(xml_response))
		except xml.parsers.expat.ExpatError:
			print("Your XML is structured wrong")
	def console_send(self,xml_filepath="payload.txt"):
		'''meant for consoles. filename with XML to send must be in payload.txt'''
		self.print_netconf_graph(n.send(file_get_contents(xml_filepath)))
	def get(self,filter):
		rpc_get = '<?xml version="1.0" encoding="UTF-8"?><rpc message-id="101" xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"><get><filter>' + filter + '</filter></get></rpc>'
		return self.send(rpc_get)
	def edit_config(self,filter):
		rpc_edit_config = '<?xml version="1.0" encoding="UTF-8"?><rpc xmlns="urn:ietf:params:xml:ns:netconf:base:1.0" message-id="111"><edit-config><target><running/></target><config>' + filter + '</config></edit-config></rpc>'
		return self.send(rpc_edit_config)
	def pretty_print_xml(self,ugly_xml):
		bs = BeautifulSoup(ugly_xml, 'xml')
		print(bs.prettify())


if __name__ == '__main__':
	try:
		#cisco_namespace_prefix = "http://cisco.com/ns/yang/"
		#ietf_namespace_prefix = "urn:ietf:params:xml:ns:yang:"
		#CISCO DEVNET! CISCO ANYCONNECT MUST BE ACTIVATED
		cs = Netconf()
		client = cs.client
		rpc_fragment = '''<interfaces xmlns="http://cisco.com/ns/yang/Cisco-IOS-XE-interfaces-oper">
		<interface>
		<name>GigabitEthernet2</name>
		
		</interface>
		</interfaces>'''
		
		for octet_4 in cycle(range(4,255)):
		rpc_fragment = f'
			<interfaces xmlns="urn:ietf:params:xml:ns:yang:ietf-interfaces">
			  <interface operation="replace">
				<name>
				  GigabitEthernet2
				</name>
			  <description>
				GOON
			  </description>
			  <type xmlns:ianaift="urn:ietf:params:xml:ns:yang:iana-if-type">
				ianaift:ethernetCsmacd
			  </type>
			  <enabled>
				true
			  </enabled>
			  <ipv4 xmlns="urn:ietf:params:xml:ns:yang:ietf-ip">
				<address>
				  <ip>
					10.10.50.{octet_4}
				  </ip>
				  <netmask>
					255.255.255.0
				  </netmask>
				</address>
			  </ipv4>
			  </interface>
			</interfaces>
		  '
	  xml_response = cs.edit_config(rpc_fragment)
		xml_response = cs.get(rpc_fragment)
		print(xml_response)
	finally:
		sleep(1)
		client.close()

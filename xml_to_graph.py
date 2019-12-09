import xml
import xmltodict
from helpers import *
import pprint
import os

def dict_to_graph(structure,filename=None):
	depth = 0
	path = []
	text = ''
	def recurse(structure,filename=None):
		nonlocal depth
		nonlocal path
		nonlocal text
		if isinstance(structure, dict) or isinstance(structure, OrderedDict):
			for k, value in structure.items():
				depth += 1
				#Only done for YANG key identification
				if structure.get("@name") is not None:
					k = structure.get("@name")
				path.append(str(k))
				recurse(value)
				path.pop()
				depth -= 1
		elif isinstance(structure, list):
			for i, value in enumerate(structure):
				depth += 1
				recurse(value)
				depth -= 1
		else:
			#You Are now in a leaf of the structure, which can be an INT or a STRING
			keys = "|".join(path)
			value_string = str(structure).replace("\n"," ").strip()
			text += "{:100} {:20} \n".format(keys, value_string)
	recurse(structure)
	return text



yang_directory_name = "cisco_xe_yang_1681"
filenames = os.listdir(yang_directory_name)
#only filenames with yang
filenames = list(filter(lambda x: ".xml" in x, filenames))
file_with_graph = "graph.txt"

for filename in filenames:
	text = ''
	try:
		text += f"\n\n\n{filename}\n\n\n"
		text += dict_to_graph(xmltodict.parse(file_get_contents(yang_directory_name + "/" + filename)))
		print(text)
		file_add_contents(file_with_graph,text)
	except xml.parsers.expat.ExpatError:
		text += f"{filename} Can't Parse\n"
		print(text)
		file_add_contents(file_with_graph,text)
	except:
		text += f"{filename} has general exception\n"
		print(text)
		file_add_contents(file_with_graph,text)

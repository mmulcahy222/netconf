import os
import subprocess
import shlex

def run_command(command):
	process = subprocess.call(command, stdout=subprocess.PIPE, shell=True)
	while True:
		output = process.stdout.readline()
		if output == '' or process.poll() is not None:	
			break
		if output:
			pass
	rc = process.poll()
	return rc

yang_directory_name = "cisco_xe_yang_1681"
directory = os.getcwd() + "/" + yang_directory_name
directory = directory.replace("\\","/")
filenames = os.listdir(directory)
#only filenames with yang
filenames = list(filter(lambda x: ".yang" in x, filenames))
for filename in filenames:
	try:
		#SOMEHOW IT WORKS, DON'T WORRY!!!
		yang_name = os.path.splitext(filename)[0]
		command = f"pyang -f yin {directory}/{yang_name}.yang > {directory}/{yang_name}.xml"
		print(command)
		run_command(command)
		print(f"{yang_name} has XML")
	except KeyboardInterrupt:
		exit(0)
	except:
		print("NO XML")

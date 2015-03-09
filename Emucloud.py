import os,sys,cherrypy,logging,json,importlib,base64,zipfile,shutil


#My Imports
import gd_auth,gd_ops



class EmuCloud(object):
	#Make sure we're logged in and have what we need.
	def __init__(self,gdsvc=None,emucloud_db=None):
		self.app_root = os.getcwd()
		#Set up environment.
		if(not os.path.exists("emulators")):
			os.makedirs("emulators")
		if(not os.path.exists("data")):
			os.makedirs("data")
		if(not os.path.exists("databases")):
			os.makedirs("databases")
			os.system("python emucloud_dbgen.py")
		
		if(not os.path.exists(os.path.join("emulators","__init__.py"))):
				f = open(os.path.join("emulators","__init__.py"),"wb")
				f.close()
		if(not os.path.exists("tmp")):
			os.makedirs("tmp")
		#End Setting up Environment.
		if(gdsvc == None):
			logging.debug("Logging into GDrive...")
			gdsvc = gd_auth.drive_login()
		if(gdsvc == None):
			logging.critical("Unable to Sign into GDrive!")
			exit(1)
		self.dsvc = gdsvc
		#Find out if we delete the rom afterward - defaults to true, can be set in the web interface.
		self.d_after = True
		#State that monitors if the rom loaded is local or cloud.
		self.cloud_rom = False
		self.emucloud_db = emucloud_db
		if(emucloud_db == None):
			self.refresh_emucloud_database()
		if(self.emucloud_db == None):
			logging.critical("Unable to DB")
			exit(1)
		if(self.emucloud_db == []):
			logging.warning("No entries")
		self.emulator_db = {} 
		self.refresh_emulator_database()
		self.current_system=None
	
	#Refresh Emulator Database.
	def refresh_emulator_database(self):
		self.emulator_db = {}
		for root, dirs, files in os.walk("emulators"):
			for d in dirs:
				module_path = os.path.join(root,d,"__init__.py")
				
				if(os.path.exists(module_path)):
					self.emulator_db[d] = "%s.%s" % (root,d)
					
		
	#Refresh Database.
	def refresh_emucloud_database(self):
		self.emucloud_db = {}
		logging.info("Refreshing EmuCloud Database from Local...\r")

		for root, dirs, files in os.walk("databases"):
			for f in files:
				if(f.endswith(".json")):
					fl = open(os.path.join(root,f),"rb")
					data = fl.read()
					fl.close()
					flr,fext = os.path.splitext(f)
					self.emucloud_db[flr] = json.loads(data)
					#Make Rom Directory If not exists.
					if(not os.path.exists(os.path.join("Data",flr))):
						os.makedirs(os.path.join("Data",flr))

	def find_rom(self,system,game_name,extensions):
		cgame = self.emucloud_db[system][game_name]
		rom_files = []
		for ex in extensions:
			tp = os.path.join("data",system,"%s.%s" % (game_name,ex))
			if(os.path.exists(tp)):
				self.cloud_rom = False
				print("Local File Found at %s" % tp)
				return [tp]
		#If we can't find it locally, time to hit the cloud.
		cidr = os.getcwd()
		#We'll put the game in the tmp directory if we aren't keeping it.
		if(self.d_after == True):
			os.chdir("tmp")
		if(not os.path.exists(os.path.join("data",system))):
			os.makedirs(os.path.join("data",system))
		os.chdir(os.path.join("data",system))
		for fid in cgame["file_id"]:
			rom_file_obj = gd_ops.get_file_by_id(self.dsvc,fid)
			
			if(rom_file_obj == None):
				return None
			gd_ops.download_file(self.dsvc,rom_file_obj)
			out_path = ""
			
			if(self.d_after == True):
				out_path = os.path.join("tmp","data",system,"%s" % (rom_file_obj['title']))
				print(out_path)
			else:
				out_path = os.path.join("data",system,"%s" % (rom_file_obj['title']))
				print(out_path)
			rom_files.append(out_path)
			
		os.chdir(cidr)
		self.cloud_rom = True
		
		return rom_files
	
	def get_emulator(self,emulator_name,out_path):
		cidr = os.getcwd()
		
		os.chdir("tmp")
		
		emu_file_obj = gd_ops.get_file_meta(self.dsvc,"fullText contains 'EmuCloud_Emulator' and fullText contains '%s' and fullText contains '%s'" % (
		emulator_name,os.name))

		if(emu_file_obj == []):
			os.chdir(cidr)
			return None
		#Hack - only get the first one
		emu_file_obj = emu_file_obj[0]		
		gd_ops.download_file(self.dsvc,emu_file_obj)
		#Unzip file to directory.
		
		fh = open(emu_file_obj['title'], 'rb')
		z = zipfile.ZipFile(fh)
		for name in z.namelist():
			z.extract(name,out_path)
		fh.close()
		os.remove(emu_file_obj['title'])
		os.chdir(cidr)
		self.refresh_emulator_database()
	
	def sizeof_fmt(self,num, suffix='B'):
		for unit in [' ',' K',' M',' G',' T',' P',' E',' Z']:
			if abs(num) < 1024.0:
				return "%3.1f%s%s" % (num, unit, suffix)
			num /= 1024.0
		return "%.1f%s%s" % (num, ' Y', suffix)
	
	@cherrypy.expose
	def index(self):
		os.chdir(self.app_root)
		response = ""
		
		response +="<input type='button' name='refresh_rdb' value='ReGenerate Cloud Database' onclick=\"location.href='regen'\">"
		if(self.d_after == True):
			response +="<input type='button' name='toggle_keep' value='Keep Downloaded: OFF' onclick=\"location.href='toggle_keep'\">"
		else:
			response +="<input type='button' name='toggle_keep' value='Keep Downloaded: ON' onclick=\"location.href='toggle_keep'\">"
		response +="<style>icon {width: 10%;height: auto;}</style>"
		
		response +="<table>"
		for system in self.emucloud_db.keys():
			#response += "<h4>%s</h4>" % system
			for game in self.emucloud_db[system].keys():
				response+="<tr><td>"
				if(self.emucloud_db[system][game]['artwork_video'] == []):
					response += "<a href='run?req=%s'><img id='icon' src='https://googledrive.com/host/%s'/></a>" % (base64.b64encode("%s|%s" % (system,game)),self.emucloud_db[system][game]['icon'])
				else:
					response += "<a href='run?req=%s'><video id='preview_video' loop='loop' onclick='this.pause()'  onmouseover='this.play()' onmouseout='this.pause();this.src=\"\";this.src=\"https://googledrive.com/host/%s\"' poster='https://googledrive.com/host/%s' width='360' height='240' source src='https://googledrive.com/host/%s'/></video></a>" % (base64.b64encode("%s|%s" % (system,game)),self.emucloud_db[system][game]['artwork_video'][0],self.emucloud_db[system][game]['icon'],self.emucloud_db[system][game]['artwork_video'][0])
				response+="</td><td>"
		
				cg = self.emucloud_db[system][game]
				if(cg['year'] == ""):
					title_text = "%s" % cg['name']
				else:
					title_text = "%s  (%s)" % (cg['name'],cg['year'])
				response+="""
				%s<br/>
				System: %s<br/>
				Region: %s<br/>
				Manufacturer: %s<br/>
				Genre: %s<br/>
				Rating: %s<br/>
				Players: %s<br/>
				File Size: %s <br/>
				Description: <p><i>%s</i></p>
				""" % (title_text,cg['system'],cg['region'],cg['manufacturer'],cg['genre'],cg['rating'],cg['players'],self.sizeof_fmt(int(cg['file_sz'])),cg['description'])
				response+="</td></tr>"
		response+="</table>"
		#response += "<iframe type='text/html' width='125' height='100' src='http://www.youtube.com/embed/YbEsoI1_eiY?autoplay=1' frameborder='0'></iframe>"
		
		return response
	
	@cherrypy.expose
	def regen(self):
		os.system("python emucloud_dbgen.py")
		self.refresh_emucloud_database()
		raise cherrypy.HTTPRedirect("/")
	@cherrypy.expose
	def toggle_keep(self):
		if(self.d_after == True):
			self.d_after = False
		else:
			self.d_after = True
		raise cherrypy.HTTPRedirect("/")		
		
	@cherrypy.expose
	def run(self,req):
		req = base64.b64decode(req)
		system,game_name = req.split("|")
		cgame = self.emucloud_db[system][game_name]
		emulator_name = cgame['emulator']
		#Get the emulator if we don't have it.
		if(not os.path.exists(os.path.join("emulators",emulator_name))):
			os.makedirs(os.path.join("emulators",emulator_name))
			out_path = os.path.join("..","emulators",emulator_name)
			self.get_emulator(emulator_name,out_path)
		
		try:
			emu = importlib.import_module(self.emulator_db[cgame["emulator"]])
		except:
			return "Error getting emulator module inserted %s" % self.emulator_db[cgame["emulator"]]
		rom_files = self.find_rom(system,game_name,emu.get_extensions())
		
		if(rom_files != None):
			emu.run(rom_files)
			
		else:
			os.system("python emucloud_dbgen.py")
			self.refresh_emucloud_database()
			return "Error - %s Rom not found. Regenerating Database..." % game_name
			
		#Clean up tmp folder.
		os.chdir(self.app_root)
		if(self.d_after == True):
			shutil.rmtree("tmp")
			#HAAAAAAX - TEH HAAAAAAXXX
			os.makedirs("tmp")
		raise cherrypy.HTTPRedirect("/")
if(__name__=="__main__"):
	cherrypy.config.update({'server.socket_host': '0.0.0.0'})
	cherrypy.config.update({'response.timeout':1000000000})
	cherrypy.quickstart(EmuCloud())
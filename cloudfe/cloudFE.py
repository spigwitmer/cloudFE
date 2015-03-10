import os,sys,cherrypy,json,base64,zipfile,importlib,shutil,subprocess
try:
	from cloudfe import cs, cfe_dbgen
except:
	import cs


class CloudFE(object):
	required_dirs = ['databases','loaders','data','tmp']
	supported_svcs = ['gdrive','onedrive']
	cfe_database = {}
	loaderdb = {}
	def __init__(self):
		self.app_root = os.getcwd()
		for d in self.required_dirs:
			if(not os.path.exists(d)):
				os.makedirs(d)
				if(d == 'loaders'):
					f = open(os.path.join('loaders','__init__.py'),'wb')
					f.close()
					
				if(d == 'databases'):
					self.reload_db()
		#Log into all your cloud services.
		self.cloud_services = {}
		for svc in self.supported_svcs:
			asvc = cs.CloudService(svc)
			if(asvc.svc_active == True):
				if(not svc in self.cloud_services.keys()):
					self.cloud_services[svc] = asvc
		
		if(not os.path.exists(os.path.join("databases","Loaders.json"))):
			self.reload_db()
		
		
		self.get_loader_db()
		self.reload_db(True)
		self.d_after = True
		self.local_entry = False
		self.selected_system = None		
		self.cache_system_list = None

		
	def reload_db(self,first_run=False):
		self.cfe_database = {}
		if(first_run == False):
			cfe_dbgen.run()
			self.get_loader_db()
		#Load Any local databases.
		for root,dirs,files in os.walk("databases"):
			for f in files:
				if(f.endswith(".json") and f != "Loaders.json"):
					fb,fe = os.path.splitext(f)
					if(not fb in self.cfe_database.keys()):
						self.cfe_database[fb] = {}
					json_data=open(os.path.join(root,f))
					jd = json.load(json_data)
					json_data.close()
					for j in jd.keys():
						if('loader' in jd[j]):
							req_emu = jd[j]['loader']
						else:
							req_emu = jd[j]['emulator']
						
						if(os.name in self.loaderdb[fb] and req_emu in self.loaderdb[fb][os.name]):
							jd[j]['has_loader'] = True
						else:
							jd[j]['has_loader'] = False
						self.cfe_database[fb][j] = jd[j]		
		
	def get_loader_db(self):
		#Loader Tree: System->Native->Emulator_Name
		self.loaderdb = {}
		
		json_data=open(os.path.join("databases","Loaders.json"))
		self.loaderdb = json.load(json_data)["Loader"]
		json_data.close()
	def sizeof_fmt(self,num, suffix='B'):
		for unit in [' ',' K',' M',' G',' T',' P',' E',' Z']:
			if abs(num) < 1024.0:
				return "%3.1f%s%s" % (num, unit, suffix)
			num /= 1024.0
		return "%.1f%s%s" % (num, ' Y', suffix)
		
		
	def gen_entries(self,selected_system):
		response = ""
		elist = []
		#Sort Titles
		for ek in self.cfe_database[selected_system].keys():
			elist.append((self.cfe_database[selected_system][ek]['name'],ek))
		elist = sorted(elist)
		for ek in elist:
			ek = ek[1]
			entry = self.cfe_database[selected_system][ek]
			if(entry['has_loader']):
				run_req = base64.b64encode("%s|%s" % (selected_system,ek))
			else:
				run_req = ""
			video_entry = ""
			for vk in entry['Artwork']:
				if('video' in vk['type']):
					video_entry = vk['url']
			
			response += "<tr>"
			response += "<td><a href='run?req=%s'><video id='preview_video' loop='loop' onclick=\"this.pause()\"  onmouseover=\"this.play()\" onmouseout=\"this.pause();this.src='';this.src='%s'\" poster='%s' width='360' height='240' source src='%s'/></video></a></td>" % (run_req,video_entry,entry['Icon'][0]['url'],video_entry)
			#Metadata for now.
			
			#response +="<td>Entry_ID: %s</br>" % ek
			response+="<td>"
			if(entry['year'] == ""):
				response+="%s<br/>" % entry['name']
			else:
				response+="%s (%s)<br/>" % (entry['name'],entry['year'])
			response+= "Publisher: %s<br/>" % entry['publisher']
			response+= "Developer: %s<br/>" % entry['developer']
			response+= "Region: %s<br/>" % entry['region']
			response+= "Genre: %s<br/>" % entry['genre']
			response+= "Players: %s<br/>" % entry['players']
			response+= "Size: %s<br/>" % self.sizeof_fmt(int(entry['data_sz']))
			response+= "Description: <p><i>%s</i></p>" % entry['description']
			
			
			'''DEBUG = Show ALL 
			for ei in entry.keys():
				response +="%s: %s<br/>" % (ei,entry[ei])	
			'''
			
			response +="</td>"
			response += "</tr>"
		
		return response
		
	@cherrypy.expose
	def index(self,selected_system=None):
		response = "<html>"
		if(selected_system == None):
			selected_system = self.cfe_database.keys()[0]
			
			
		response +="<form action=\"index\" method=\"get\">"
		response +="<select name='selected_system' onchange=\"this.form.submit()\">"
		response +="<option value=''>Select System...</option>"
		for dr in self.cfe_database.keys():
			response +="<option value='%s'>%s</option>" % (dr,dr)
		response +="</select>"
		response +="</form>"
		 
			
		
		
		os.chdir(self.app_root)

			

			
	
		if(not selected_system in self.cfe_database.keys()):
			return "No Games for %s" % selected_system
		
		#Get List for System:
		
		response +="<input type='button' name='refresh_rdb' value='ReGenerate Cloud Database' onclick=\"location.href='regen'\"/>"
		response += "<h4>%s</h4>" % selected_system
		response += "<table>"
		if(self.selected_system!=selected_system or self.cache_system_list==""):
			self.cache_system_list = self.gen_entries(selected_system)
			self.selected_system = selected_system
			
		response+=self.cache_system_list
		response += "</table>"

		response +="</html>"
		return response
	@cherrypy.expose
	def regen(self):
		cfe_dbgen.run()
		self.get_loader_db()
		self.reload_db(True)
		self.cache_system_list=""
		raise cherrypy.HTTPRedirect("/")
		
		
	@cherrypy.expose
	def reset(self):
		os.chdir(self.app_root)
		if(self.local_entry == False):
			if(self.d_after == True):
				shutil.rmtree("tmp")
				#HAAAAAAX - TEH HAAAAAAXXX
				os.makedirs("tmp")
		raise cherrypy.HTTPRedirect("/?selected_system=%s" % self.selected_system)	

	def find_data_dir(self,entry_id):
		tp = os.path.join("data",self.selected_system,"%s" % entry_id)
		if(os.path.exists(tp)):
			self.cloud_rom = False
			print("Local Path Found at %s" % tp)
			return tp
		if(self.d_after == True):
			tp = os.path.join("tmp","data",self.selected_system,"%s" % entry_id)	
		else:
			tp = os.path.join("data",self.selected_system,"%s" % entry_id)
		os.makedirs(tp)
		os.chdir(tp)
		#We need to hit the cloud now.
		entry = self.cfe_database[self.selected_system][entry_id]
		
		for svc in self.cloud_services.keys():
			file_lst = []
			
			for fls in entry["Data"]:
				if(fls['svc'] == svc):
					op = self.cloud_services[svc].get_file(fls['id'])
					if(op != None):
						file_lst.append(op)
			break
		#Go back to root.
		os.chdir(self.app_root)
		return tp
			
				
	@cherrypy.expose
	def run(self,req):
		req = base64.b64decode(req)
		system,entry_id = req.split("|")
		entry = self.cfe_database[system][entry_id]
		#See if we have the emulator already.
		
		if(not os.path.exists(os.path.join("loaders",entry['loader']))):
			os.makedirs(os.path.join("loaders",entry['loader']))
			out_path = os.path.join(self.app_root,"loaders",entry['loader'])
			#Get the emulator if we can't find it locally.
			os.chdir("tmp")
			
			fls = self.loaderdb[self.selected_system][os.name][entry['loader']]
			
			for svc in self.cloud_services.keys():
				file_lst = []
				if(fls['svc'] == svc):
					for fl in fls['id']:
						op = self.cloud_services[svc].get_file(fl)
						if(op != None):
							file_lst.append(op)
					break
			
			os.chdir(self.app_root)
			file_lst = sorted(file_lst)
			for fl in file_lst:
				fh = open(fl, 'rb')
				z = zipfile.ZipFile(fh)
				for name in z.namelist():
					z.extract(name,out_path)
				fh.close()
				os.remove(fl)

		try:
			ldr = importlib.import_module("loaders.%s" % entry['loader'])
		except:
			return "Error getting emulator module inserted loaders.%s"% entry['loader']	
		#Get all the data files.
				
		data_path = self.find_data_dir(entry_id)
		
		if(data_path != None):
			
			ldr.run(data_path)
			
		else:
			cfe_dbgen.run()
			self.refresh_emucloud_database()
			return "Error - %s Rom not found. Regenerating Database..." % game_name
		#Execute and Cleanup.
		return "<input type='button' name='reset_menu' value='Back to Menu' onclick=\"location.href='reset'\">"

def main():
	cherrypy.config.update({'server.socket_host': '0.0.0.0'})
	cherrypy.config.update({'server.socket_port': 1337})
	cherrypy.config.update({'response.timeout':1000000000})
	cherrypy.quickstart(CloudFE())

if(__name__=="__main__"):
	sys.exit(main())

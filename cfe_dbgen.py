'''
	cloudFE Database Generator
'''
import os,sys,json
import cs

#Lists in case we need to add more than one tag for each type (different naming from friends, services, etc).
file_identifiers = {
	"Entry":['cFE_ETRY'],
	"Loader":['cFE_LODR'],
	"Artwork":['cFE_ARTW'],
	"Icon":['cFE_ICON'],
	"Data":['cFE_DATA']
}

WORKING_DB = {
"Entry":{},
"Loader":{},
"Artwork":{},
"Icon":{},
"Data":{}
}
ldr_database = {"Loader":{}}

	
'''	
Rebuild the database procedure:
	Query all files with descriptions containing cFE_ETRY
	for each:
		- Build URLs to their icon,artwork,video
		- Build total file size of data.
		- Sort final by emulated system to make shit easier to find later.
		- build out metadata based on whats in the file.
'''

def gen_dbfiles(cfe_database):
	print("Writing DB Files...")
	if(not os.path.exists("databases")):
		os.makedirs("databases")
	system_list = {}
	for c in cfe_database.keys():
		system_list[cfe_database[c]['system']] = {}
	for c in cfe_database.keys():
		c_sys = cfe_database[c]['system']
		system_list[c_sys][c] = cfe_database[c]
		
	for system in system_list.keys():
		f = open(os.path.join("databases","%s.json" % system),"wb")
		f.write(json.dumps(system_list[system]))
		f.close()
	#Write the Loader DB to Disk.
	f = open(os.path.join("databases","Loaders.json"),"wb")
	f.write(json.dumps(ldr_database))
	f.close()
	

def proc_services(cloud_services):
	cfe_database = {}
	for svc in cloud_services:
		#This will Get all of our game entries.
		for fi in file_identifiers["Entry"]:
			e_list = svc.ls([fi])
			for e in e_list:
				entry_data = svc.get_data(e)
				
				try:
					entry_data = json.loads(entry_data)
				except:
					print("Warning - %s has corrupt entry data." % e['title'])
					continue
				
				for entry_key in entry_data.keys():
					cfe_database[entry_key] = entry_data[entry_key]
		print("%d Entries Loaded." % len(cfe_database))
		#This will get all of our Artwork.
		artwork_counter = 0
		for fi in file_identifiers["Artwork"]:
			e_list = svc.ls([fi])
			for e in e_list:
				if(svc.svc_type == "gdrive"):
					
					file_meta = e['mimeType']
					file_desc = e['description']
					file_url = "https://googledrive.com/host/%s" % e['id']
					file_desc = file_desc.replace("%s:" % fi,"")
					#all that should remain are the ids now.
					eid_list = file_desc.split(",")
					for eid in eid_list:
						if(not "Artwork" in cfe_database[eid].keys()):
							cfe_database[eid]["Artwork"] = []
						cfe_database[eid]["Artwork"].append({'type':e['mimeType'],'url':file_url})
						artwork_counter+=1
		print("%d Artwork Assets Loaded." % artwork_counter)
		#This will get all of our Icons.	
		icon_counter = 0
		for fi in file_identifiers["Icon"]:
			e_list = svc.ls([fi])
			for e in e_list:
				if(svc.svc_type == "gdrive"):
					file_meta = e['mimeType']
					file_desc = e['description']
					file_url = "https://googledrive.com/host/%s" % e['id']
					file_desc = file_desc.replace("%s:" % fi,"")
					#all that should remain are the ids now.
					eid_list = file_desc.split(",")
					for eid in eid_list:
						if(not "Icon" in cfe_database[eid].keys()):
							cfe_database[eid]["Icon"] = []
						cfe_database[eid]["Icon"].append({'type':e['mimeType'],'url':file_url})
						icon_counter+=1
						
		data_counter = 0
		data_sz_counter = 0
		for fi in file_identifiers["Data"]:
			e_list = svc.ls([fi])
			for e in e_list:
				if(svc.svc_type == "gdrive"):
					file_desc = e['description']
					file_desc = file_desc.replace("%s:" % fi,"")
					file_id = e['id']
					file_sz = e['fileSize']
					eid_list = file_desc.split(",")
					for eid in eid_list:
						
						if(not "Data" in cfe_database[eid].keys()):
							cfe_database[eid]["Data"] = []
						cfe_database[eid]["Data"].append({'id':file_id,'svc':svc.svc_type})
						data_counter+=1
						if(not "data_sz" in cfe_database[eid].keys()):
							cfe_database[eid]["data_sz"] = 0
						cfe_database[eid]["data_sz"]+=int(file_sz)
						data_sz_counter+=int(file_sz)
		print("%d Data Assets Loaded." % data_counter)
		
		loader_counter = 0
		for fi in file_identifiers["Loader"]:
			e_list = svc.ls([fi])
			for e in e_list:
				if(svc.svc_type == "gdrive"):
					
					file_desc = e['description']
					file_desc = file_desc.replace("%s:" % fi,"")
					
					eid_list = file_desc.split(",")
					for eid in eid_list:
						system,native,ldr_name = eid.split("|")
						
						if(not system in ldr_database["Loader"].keys()):
							ldr_database["Loader"][system] = {}
						if(not native in ldr_database["Loader"][system].keys()):
							ldr_database["Loader"][system][native] = {}
						if(not ldr_name in ldr_database["Loader"][system][native].keys()):
							ldr_database["Loader"][system][native][ldr_name] = {'svc':'gdrive','id':[]}
						ldr_database["Loader"][system][native][ldr_name]['id'].append(e['id'])
						loader_counter+=1		
						
		print("%d Loaders Loaded." % loader_counter)
	return cfe_database
def run():
	cloud_services = []
	#Firstly, we're going to attempt a login to Google Drive.
	gdrive = cs.CloudService("gdrive")
	
	if(gdrive.svc_active == True):
		cloud_services.append(gdrive)
	cfe_database = proc_services(cloud_services)
	gen_dbfiles(cfe_database)
	
	print("Done!")
if(__name__=="__main__"):
	run()

	
	
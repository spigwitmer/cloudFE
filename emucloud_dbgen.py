import os,sys,json
import gd_ops,gd_auth

EMUCLOUD_KEY = "EmuCloud_Entry"
EMUCARTW_KEY = "EmuCloud_Artwork"
EMUCICON_KEY = "EmuCloud_Icon"
ROM = {}
ARTWORK = {}
ICON = {}


def gen_json(system,system_name):
	if(not os.path.exists("Databases")):
		os.makedirs("Databases")
	output_path = "%s.json" % os.path.join("Databases",system_name)
	jsonarray = json.dumps(system)
	f = open(output_path,"wb")
	f.write(jsonarray)
	f.close()

	
def gen_artwork_entry(f):
	e= {}
	e["type"] = f['mimeType']
	e["id"] = f['id']
	return e
def gen_icon_entry(f):
	e= {}
	e["type"] = f['mimeType']
	e["id"] = f['id']
	return e

def get_eset_target(db,system_name,game_name,media_type):
	
	if(system_name in db.keys()):
		
		if(game_name in db[system_name].keys()):
			rs = []
			
			for en in db[system_name][game_name]: 
				if(en['type'] in media_type):
					rs.append(en['id'])
			return rs
	if(game_name in db["Unsorted"].keys()):
		rs = []
		for en in db["Unsorted"][game_name]: 
			if(en['type'] in media_type):
				rs.append(en['id'])
		return rs
	else:
		return []	
		
def get_eset(db,system_name,game_name):
	
	if(system_name in db.keys()):
		if(game_name in db[system_name].keys()):
			return db[system_name][game_name]['id']
	if(game_name in db["Unsorted"].keys()):
		return db["Unsorted"][game_name]['id']
	else:
		return []

def append_rom_entry(f,entry):
	e = gen_rom_entry(f)
	for ek in e.keys():
		if(e[ek] != "" and entry[ek]==""):
			entry[ek] = e[ek]
			
	entry['file_id'].append(f['id'])
	new_sz = int(entry['file_sz']) + int(f['fileSize'])
	entry['file_sz'] = new_sz
	
	return entry
		
def gen_rom_entry(f):
	e = {}
	
	e['region']= get_field(f,"game_region")
	e['emu_status']= get_field(f,"emu_status")
	
	e['file_id']= [f['id']]
	e['file_sz']= f['fileSize']
	e['md5']= f['md5Checksum']
	e['name']= get_field(f,"game_name")
	
	e['emulator']= get_field(f,"emulator")
	if(e['name'] == ""):
		e['name'] = f['title']
	e['description']= get_field(f,"description")
	e['system']= get_field(f,"game_system")
	e['artwork_image']= get_eset_target(ARTWORK,e['system'],e['name'],['image/png','image/jpeg'])
	e['artwork_video']= get_eset_target(ARTWORK,e['system'],e['name'],['video/mp4'])

	e['cloneof']= get_field(f,"cloneof")
	e['sha1']= get_field(f,"sha1")
	e['manufacturer']= get_field(f,"manufacturer")
	e['year']= get_field(f,"year")
	e['genre']= get_field(f,"genre")
	e['players']= get_field(f,"players")
	e['rating']= get_field(f,"rating")
	e['enabled']= get_field(f,"enabled")
	e['icon'] = get_eset(ICON,e['system'],e['name'])
	return e
		
def get_field(f,key):
	opening_tag = "<%s>" % key
	closing_tag = "</%s>" % key
	try:
		start_point = f['description'].find(opening_tag)
		end_point = f['description'].find(closing_tag)
		if(start_point == -1 or end_point == -1):
			return ""
		result = f["description"][start_point+len(opening_tag):end_point]
	except:
		print("WARNING: Tag %s Mismatch or not found on rom %s" % (key,f['title']))
		#Maybe a bit too harsh
		#exit(1)
		return ""
	return result
	
#Refresh Database Logic.
def refresh_db(dsvc,system_name=None):
	
	global ROM
	global ICON
	global ARTWORK

	print("Refreshing ICON DB - Please Wait...")
	ICON = {}
	ICON["Unsorted"] = {}
	
	game_list = gd_ops.get_file_meta(dsvc,"fullText contains '%s'" % EMUCICON_KEY)

	for g in game_list:

		fl,ext = os.path.splitext(g['title'])
		if("<game_system>" in g['description']):
			game_system = get_field(g,"game_system")
			game_name = get_field(g,"game_name")
			if(game_name == ""):
				game_name = fl			
			if(game_system in ICON.keys()):
				ICON[game_system][game_name] = gen_icon_entry(g)
			else:
				ICON[game_system] = {}
				ICON[game_system][game_name] = gen_icon_entry(g)
		else:
			ICON["Unsorted"][game_name] = gen_icon_entry(g)

	print("Refreshing ARTWORK DB - Please Wait...")
	ARTWORK = {}
	ARTWORK["Unsorted"] = {}
	game_list = gd_ops.get_file_meta(dsvc,"fullText contains '%s'" % EMUCARTW_KEY)
	
	
	for g in game_list:
		'''
		if(g['mimeType'] == "video/mp4"):
			print(g)
			fuckyou = open("out.txt","wb")
			fuckyou.write(str(g))
			fuckyou.close()
			exit(1)
		'''
		fl,ext = os.path.splitext(g['title'])
		if("<game_system>" in g['description']):
			game_system = get_field(g,"game_system")
			game_name = get_field(g,"game_name")
			if(game_name == ""):
				game_name = fl
			if(game_system in ARTWORK.keys()):
				if(not game_name in ARTWORK[game_system].keys()):
					ARTWORK[game_system][game_name] = []
				ARTWORK[game_system][game_name].append(gen_artwork_entry(g))
			else:
				ARTWORK[game_system] = {}
				if(not game_name in ARTWORK[game_system].keys()):
					ARTWORK[game_system][game_name] = []
				ARTWORK[game_system][game_name].append(gen_artwork_entry(g))
		else:
			if(not game_name in ARTWORK["Unsorted"].keys()):
				ARTWORK[game_system][game_name] = []
			
			ARTWORK["Unsorted"][game_name].append(gen_artwork_entry(g))	
	
	
	print("Refreshing ROM DB - Please Wait...")
	ROM = {}
	if(system_name == None):
		game_list = gd_ops.get_file_meta(dsvc,"fullText contains '%s'" % EMUCLOUD_KEY)
	else:
		game_list = gd_ops.get_file_meta(dsvc,"fullText contains '%s' and fullText contains '%s'" % (EMUCLOUD_KEY,system_name))	
		 
	
	
	for g in game_list:
		if("<game_system>"in g['description']):
			game_system = get_field(g,"game_system")
			game_name = get_field(g,"game_name")
		else:
			continue
		if(not game_system in ROM.keys()):
				ROM[game_system] = {}
				
		if(game_name in ROM[game_system].keys()):
			ROM[game_system][game_name] = append_rom_entry(g,ROM[game_system][game_name])
		else:
			
			ROM[game_system][game_name] = gen_rom_entry(g)

	
		
if(__name__=="__main__"):
	
	#Might as well leave it logged in.
	dsvc = gd_auth.drive_login()
	if(len(sys.argv) > 1):
		#Get metadata of all Emucloud roms.
		refresh_db(dsvc,sys.argv[1])
	else:
		refresh_db(dsvc)
	#Print New XML Files.
	for sys in ROM.keys():
		if(sys == "Unsorted" or sys == []):
			continue
		
		#gen_xml(ROM[sys],sys)
		gen_json(ROM[sys],sys)
		
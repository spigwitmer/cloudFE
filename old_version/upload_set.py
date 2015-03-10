import sys,os,hashlib
import gd_auth,gd_ops
from xml.dom import minidom

EMULATOR = 'desmume'
SUPPORTED_EXTENSIONS = ['smc','sfc','zip','7z','rar']
ROM_DB = {}

#upload_file(dsvc, file, "", cur_parent_id, "", os.path.join(root_path,file))
'''
<game image="" index="" name="Hisshou 777 Fighter III - Kokuryuu Ou no Fukkatsu (Japan)">
<description>Hisshou 777 Fighter III - Kokuryuu Ou no Fukkatsu (Japan)</description>
<cloneof />
<manufacturer /><crc>C386FC22</crc>
<genre />
<year />
<enabled>Yes</enabled>
</game>


EmuCloud_Entry
<game_system>Super Nintendo</game_system>
<emulator>zsnes</emulator>
<game_name>Super Mario All-Stars + Super Mario World (USA)</game_name><description>Sweetest fucking platformer orgasm basically ever.</description>
<cloneof></cloneof>
<sha1>b073ee0624ccfb8b3d78db9d26deae693329aaca</sha1>
<manufacturer>Nintendo</manufacturer>
<year>1994</year>
<genre>Platform</genre>
<game_region>USA</game_region>
<rating>Other - NR (Not Rated)</rating>
<players>1-2</players>
<enabled>Yes</enabled>
'''

def sha1_for_file(f, block_size=2**25):
    sha1 = hashlib.sha1()
    while True:
        data = f.read(block_size)
        if not data:
            break
        sha1.update(data)
    return sha1.hexdigest()
	
def get_sha1sum(infile):
	ff = open(infile,"rb")
	result = sha1_for_file(ff)
	ff.close()
	return result 
	
def usage():
	print("Usage: %s [system_name]" % sys.argv[0])
	sys.exit(1)

def gen_description(file_key,game_info):
	rslt = file_key
	for g in game_info.keys():
		rslt +="<%s>%s</%s>" % (g,game_info[g],g)
	return rslt
	
def proc_rom(dsvc,parent_id,inpath):
	upload_list = []
	base,romfile = os.path.split(inpath)
	base_romname,ext = os.path.splitext(romfile)
	if(ext.startswith(".")):
		ext = ext[1:]
	if(ext not in SUPPORTED_EXTENSIONS):
		return
	print("Processing: %s " % inpath)
	if(base_romname in ROM_DB):
		game_info = ROM_DB[base_romname]
	else:
		game_info = {}
		game_info['game_system'] = system_name
		game_info['game_name'] = base_romname
		game_info['emulator'] = EMULATOR
		game_info['players'] = ""
		game_info['cloneof'] = ""
		game_info['year'] = ""
		game_info['manufacturer'] = ""
		game_info['genre'] = ""
		game_info['game_region'] = ""
		game_info['rating'] = ""
		game_info['enabled'] = "Yes"
	#Get hash.
	game_info['sha1'] = get_sha1sum(inpath)
	desc = gen_description("EmuCloud_Entry",game_info)
	#Add rom to our upload list.
	upload_list.append([inpath,desc])
	
	#Add icon to our upload list.
	for root,dirs,files in os.walk("icon"):
		for f in files:
			if f.startswith(base_romname):
				print("Found Icon %s" % os.path.join(root,f))
				rt,parent = os.path.split(root)
				basef,ext = os.path.splitext(f)
				if(not basef.endswith("_%s" % parent)):
					fixed_name = os.path.join(root,"%s_%s%s" % (basef,parent,ext))
					os.rename(os.path.join(root,f),fixed_name)
				else:
					fixed_name = os.path.join(root,f)
				upload_list.append([fixed_name,"EmuCloud_Icon <game_system>%s</game_system><game_name>%s</game_name>" % (system_name,base_romname)])
	
	#Add any artwork to our upload list.
	for root,dirs,files in os.walk("artwork"):
		for f in files:
			if f.startswith(base_romname):
				print("Found Artwork %s" % os.path.join(root,f))
				rt,parent = os.path.split(root)
				basef,ext = os.path.splitext(f)
				if(not basef.endswith("_%s" % parent)):
					fixed_name = os.path.join(root,"%s_%s%s" % (basef,parent,ext))
					os.rename(os.path.join(root,f),fixed_name)
				else:
					fixed_name = os.path.join(root,f)
				upload_list.append([fixed_name,"EmuCloud_Artwork <game_system>%s</game_system><game_name>%s</game_name>" % (system_name,base_romname)])
	

	
	for item in upload_list:
		#Check to make sure we aren't uploading a duplicate.
		baspth,name = os.path.split(item[0])
		emu_file_obj = gd_ops.get_file_meta(dsvc,"title='%s' and fullText contains '%s' and fullText contains '%s'" % (name.replace("'","\\'"),system_name,base_romname.replace("'","\\'")))
		
		if(emu_file_obj != []):
			print("Skipping %s" % name)
			continue
			
		print("Uploading %s" % name)
		gd_ops.upload_file(dsvc, name, item[1], parent_id, "", item[0])
		
	
if(__name__=="__main__"):
	if(len(sys.argv) < 2):
		usage()
	system_name = sys.argv[1]
	#open xml database (if exist)
	if(os.path.exists("%s.xml" % system_name)):
		xmldoc = minidom.parse("%s.xml" % system_name)
		itemlist = xmldoc.getElementsByTagName('game')
		for item in itemlist:
			game_info = {}
			game_info['game_system'] = system_name
			game_info['game_name'] = item.attributes['name'].value
			
			game_info['emulator'] = EMULATOR
			game_info['players'] = ""
			game_info['cloneof'] = ""
			game_info['year'] = ""
			game_info['manufacturer'] = ""
			game_info['genre'] = ""
			game_info['game_region'] = ""
			game_info['rating'] = ""
			game_info['enabled'] = "Yes"
			game_info['sha1'] = ""
			
			for c in item.childNodes:
				#Skip Text Nodes because fuck them.
				if(c.nodeType == 3):
					continue
				tag_name  = c.tagName
				
				itm = item.getElementsByTagName(tag_name)
				
				for a in itm:
					try:
						game_info[tag_name] = a.firstChild.nodeValue
					except:
						pass
	
			ROM_DB[game_info['game_name']] = game_info
	#Time to start going through all the roms.
	#Log in.
	dsvc = gd_auth.drive_login()
	if(len(sys.argv) < 3):
		parent_id = gd_ops.get_root_id(dsvc)
	else:
		parent_id = sys.argv[2]
	for root,dirs,files in os.walk("roms"):
		for f in files:
			proc_rom(dsvc,parent_id,os.path.join(root,f))
			
			
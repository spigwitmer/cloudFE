'''
	Cloud Services Abstraction Layer
'''

import os,importlib




class CloudService(object):
	driver_db = {
	"gdrive":"cloudstorage.gdrive",
	"onedrive":"cloudstorage.onedrive"
	}
	def __init__(self,svc_type):
		self.svc_type = svc_type
		try:
			self.svc_driver = importlib.import_module(self.driver_db[self.svc_type])
		except:
			self.svc_driver = importlib.import_module("cloudfe.%s" % self.driver_db[self.svc_type])
			
		
		svc = self.svc_driver.login()
		if(svc == None):
			self.svc_active = False
		else:
			self.svc_active = True
			self.svc_handle = svc
			
	def ls(self,qe=[]):
		if(qe == []):
			q = None
		else:
			q = "fullText contains '%s'" % qe[0]
			if(len(qe) > 1):
				for i in range(1,len(qe)):
					q+=" and fullText contains '%s'" % qe[i]
		
		result = self.svc_driver.get_fe(self.svc_handle,q)
		return result
	
	#Get data - used for small files.
	def get_data(self,file_entry):
		result = self.svc_driver.get_data(self.svc_handle,file_entry)
		return result
		
	def get_file(self,file_id):
		file = self.svc_driver.get_file_by_id(self.svc_handle,file_id)
		self.svc_driver.download_file(self.svc_handle,file,f0=0)
		out_path = os.path.join(os.getcwd(),file['title'])
		return out_path

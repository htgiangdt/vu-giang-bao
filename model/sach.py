# -*- encoding: utf-8 -*-
from osv import fields,osv
from tools.translate import _
import time
from datetime import datetime, date
import os
import base64,os,re
import sys
reload(sys)
sys.setdefaultencoding("utf8")


class yhoc_sach(osv.osv):
    _name = "yhoc_sach"    
    _columns = {
                'name':fields.char("Tên sách",size=500, required='1'),
                'tacgia':fields.char("Tên tác giả",size=500, required='1'),
                'nguoihieudinh':fields.many2one('hr.employee', 'Người hiệu đính', required="1"),
                'mota': fields.text('Mô tả'),
                'noidung': fields.text('Mô tả'),
                'file': fields.binary('File'),
                'datas_fname': fields.char('Filename',size=256),
                'link': fields.char("Link",size=200),
                }
    _defaults={
               }
    
    def test_ss(self, cr, uid, ids, contxt=None):
        import pyslideshare
        
        # Have all the secure keys in a file called localsettings.py
        #try:
        #    from localsettings import username, password, api_key, secret_key, proxy
        #except:
        #    pass
        
        # Use proxy if available
        vals = {
        'api_key':'bQFCVV7X',
        'secret_key':'SCmYTgrI'
            }
        obj = pyslideshare.pyslideshare(vals, verbose=False, proxy=None)
        json = obj.upload_slideshow(username='yenbao1340@gmail.com', password='tuongvi', upload_url='http://yhoccongdong.com/Documents/128_hoi-phuc-suc-khoe-sau-mo-tim-ho.pdf',
                                       slideshow_title='pyslideshare works!')
        if not json:
            import sys
            print >> sys.stderr, 'No response. Perhaps slideshare down?'
            sys.exit(1)
            
        showId = json.SlideShowUploaded.SlideShowID
        print 'Uploaded successfully. Id is %s.'%showId
        return True
yhoc_sach()

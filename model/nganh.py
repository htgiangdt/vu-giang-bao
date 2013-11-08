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


class yhoc_nganh(osv.osv):
    _name = "yhoc_nganh"    
    _columns = {
                'name':fields.char("Tên ngành",size=500, required='1'),
                'mota': fields.text('Mô tả'),
                'link': fields.char("Link",size=200),
                'dsbacsi': fields.one2many('hr.employee', 'nganh', 'Danh sách bác sĩ'),
                }
    _defaults={
               }
    
    def capnhat_thongtin(self,cr,uid,ids,context=None):
        nganh = self.browse(cr, uid, ids[0], context=context)
		#Giang_0811_start#Them ten_url + url_nganh
        ten_url = self.pool.get('yhoc_trangchu').parser_url(nganh.name)
        url_nganh = '/nganh/%s/'%(ten_url)
		#Giang_0811_end#
        duongdan = self.pool.get('hlv.property')._get_value_project_property_by_name(cr, uid, 'path of template')
        domain = self.pool.get('hlv.property')._get_value_project_property_by_name(cr, uid, 'Domain') or '../..'
        kieufile = self.pool.get('hlv.property')._get_value_project_property_by_name(cr, uid, 'Kiểu lưu file') or 'html'
        if len(nganh.dsbacsi) > 0:
#Doc file
            if os.path.exists(duongdan + '/template/nganh/thanhviennganh.html'):
                fr = open(duongdan + '/template/nganh/thanhviennganh.html', 'r')
                template = fr.read()
                fr.close()
            else:
                template = ''
            
            #Giang_0811#folder_nganh = duongdan + '/nganh/%s' %str(nganh.id)
            folder_nganh = duongdan + url_nganh
            if not os.path.exists(folder_nganh):
                os.makedirs(folder_nganh)
    
    #Lay thong tin co ban
            mota = nganh.mota
            tennganh = nganh.name
            dsbacsi = nganh.dsbacsi
            template = template.replace('__TENNGANH__', tennganh)
            
    #Cập nhật tittle       
            fr = open(duongdan + '/template/trangchu/tittle.html', 'r')
            noidung_tittle = fr.read()
            fr.close()
            noidung_tittle = noidung_tittle.replace('__TITLE__','Ngành ' + nganh.name)
            template = template.replace('__TITLE__',noidung_tittle)
            
            
    #Cap nhat thanh vien        
            noidung_thanhvien = ''
            if os.path.exists(duongdan+'/template/nganh/thanhvien_tab.html'):
                fr = open(duongdan+'/template/nganh/thanhvien_tab.html', 'r')
                thanhvien_tab_ = fr.read()
                fr.close()
            else:
                thanhvien_tab_ = ''
    
            linkthanhvien = ''
            for tv in dsbacsi:
                if tv.active and tv.link:
                    capbac = tv.capbac or ''
                    trinhdo = self.pool.get('hlv.property')._get_value_project_property_by_name(cr, uid, 'Trình độ chuyên môn') or '[]'
                    for r in eval(trinhdo):
                        if r[0] == capbac:
                            capbac = r[1]
                            break
                    photo = domain + '/template/trangchu/images/default_customer.png'
                    if tv.image:
                        name_url = self.pool.get('yhoc_trangchu').parser_url(str(tv.name))
                        link_url = name_url
                        filename = str(tv.id) + '-profile-' + link_url
                        if not os.path.exists(duongdan+'/images/profile/%s-profile-%s.jpg'%(str(tv.id),tv.link_url)):
                            folder_hinh_profile = duongdan + '/images/profile'
                            self.pool.get('yhoc_thongtin').ghihinhxuong(folder_hinh_profile, filename, tv.image, 150, 150, context=context)
                        photo = domain + '/images/profile/%s.jpg' %(filename)
        ##############################                             
                    thanhvien_tab = ''
                    thanhvien_tab = thanhvien_tab_
                    thanhvien_tab = thanhvien_tab.replace('__DANHXUNG__', tv.danhxung or '')
                    thanhvien_tab = thanhvien_tab.replace('__TENTHANHVIEN__', tv.name)
                    thanhvien_tab = thanhvien_tab.replace('__HINHTHANHVIEN__', photo)
                    #Giang_0511#thanhvien_tab = thanhvien_tab.replace('__LINKTHANHVIEN__', '../../../../../../profile/%s/index.%s'%(tv.link_url, kieufile))
                    thanhvien_tab = thanhvien_tab.replace('__LINKTHANHVIEN__', '../../../../../../profile/%s/'%(tv.link_url))
                    thanhvien_tab = thanhvien_tab.replace('__EMAIL__', tv.work_email or '')
                    thanhvien_tab = thanhvien_tab.replace('__TRINHDOCHUYENMON__', capbac)
                    thanhvien_tab = thanhvien_tab.replace('__NGANH__',tv.nganh.name or '')
                    if tv.nganh and tv.chuyennganh:
                        thanhvien_tab = thanhvien_tab.replace('__CHUYENNGANH__',' - ' + tv.chuyennganh or '')
                    else:
                        thanhvien_tab = thanhvien_tab.replace('__CHUYENNGANH__',tv.chuyennganh or '')
                    noidung_thanhvien += thanhvien_tab
            
            template = template.replace('__THANHVIENNGANH__', noidung_thanhvien)
            
            #Giang_0811#super(yhoc_nganh,self).write(cr,uid,[nganh.id],{'link':domain + '/nganh/%s/index.%s'%(nganh.id,kieufile)}, context=context)
            super(yhoc_nganh,self).write(cr,uid,[nganh.id],{'link': domain + url_nganh}, context=context)
            import codecs  
            fw = codecs.open(folder_nganh +'/index.' + kieufile,'w','utf-8')
            fw.write(template)
            fw.close()
            
            #Cap nhat menu nganh
            folder_trangchu = duongdan + '/trangchu/vi'
            self.pool.get('yhoc_trangchu').capnhat_menu_nganh(cr, uid, folder_trangchu, context)
            
            
            return template, duongdan, domain
yhoc_nganh()

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

class yhoc_customer(osv.osv):
    
    _inherit = 'res.partner'
    ###
    _columns = {
        'link': fields.char('Link', size=500),
        'gioithieu': fields.text('Giới thiệu'),
        'dsbacsi': fields.one2many('hr.employee', 'noilamviec_id', 'Danh sách bác sĩ'),
        'diachi': fields.char('Địa chỉ', size=500),
    }
    
    _defaults = {
                 'customer':True,
                 'supplier':False,
                 }
    
    def capnhat_thongtin(self,cr,uid,ids,context):
        duongdan = self.pool.get('hlv.property')._get_value_project_property_by_name(cr, uid, 'path of template')
        domain = self.pool.get('hlv.property')._get_value_project_property_by_name(cr, uid, 'Domain') or '../..'
        kieufile = self.pool.get('hlv.property')._get_value_project_property_by_name(cr, uid, 'Kiểu lưu file') or 'html'
        khachhang = self.browse(cr,uid,ids[0],context)
        if os.path.exists(duongdan + '/template/profile_khachhang/index.html'):
            fr = open(duongdan + '/template/profile_khachhang/index.html', 'r')
            template = fr.read()
            fr.close()
        else:
            template = ''

#Tao folder cho thongtin
        folder_profile = duongdan + '/profile_khachhang/%s' %str(khachhang.id)
        if not os.path.exists(folder_profile):
            os.makedirs(folder_profile)
            
#Lay thong tin chung
        tenkhachhang = khachhang.name
        
        photo = domain + '/images/donor.jpg'
        if khachhang.image:
            if not os.path.exists(folder_profile + '/images/partner'):
                os.makedirs(folder_profile + '/images/partner')
            path_hinh_ghixuong = folder_profile + '/images/anhprofile.jpg'
            fw= open(path_hinh_ghixuong,'wb')
            fw.write(base64.decodestring(khachhang.image))
            fw.close()
            photo = 'images/anhprofile.jpg'
            from PIL import Image
            try:
                im = Image.open(path_hinh_ghixuong)
                width, height = im.size
                if width>height:
                    ratio = float(width)/float(200)
                else:
                    ratio = float(height)/float(200)
                im.resize(((int(width/ratio),int(height/ratio))), Image.ANTIALIAS).save(path_hinh_ghixuong)
            except:
                im = im.convert('RGB')
                im.resize(((int(width/ratio),int(height/ratio))), Image.ANTIALIAS).save(path_hinh_ghixuong)




##################################################
        template = template.replace('__TENPROFILE__', tenkhachhang)
        template = template.replace('__PHOTO__', photo)
        template = template.replace('__LINKPROFILE__', '''../../profile_khachhang/%s/index.%s'''%(khachhang.id,kieufile))
        template = template.replace('__LOAI__', '')
        template = template.replace('__WEBSITE__', khachhang.website or '(Chưa cập nhật)')
        template = template.replace('__DIACHI__', khachhang.diachi or '(Chưa cập nhật)')
        template = template.replace('__GIOITHIEU__', khachhang.gioithieu or '(Chưa cập nhật)')
        
#Cap nhat danh sach cac bac si
        if khachhang.customer == False:
            noidung_dsbs = '''<fieldset class="profile_table">
                            <legend class="table_title">Các thành viên tham gia cộng đồng</legend>
                            __BACSI__                            
                            </fieldset>'''
            noidung_thanhvien = ''
            if os.path.exists(duongdan+'/template/profile_khachhang/thanhvien_tab.html'):
                fr = open(duongdan+'/template/profile_khachhang/thanhvien_tab.html', 'r')
                thanhvien_tab_ = fr.read()
                fr.close()
            else:
                thanhvien_tab_ = ''
    
            linkthanhvien = ''
            for tv in khachhang.dsbacsi:
                if tv.active:
                    capbac = tv.capbac or ''
                    trinhdo = self.pool.get('hlv.property')._get_value_project_property_by_name(cr, uid, 'Trình độ chuyên môn') or '[]'
                    for r in eval(trinhdo):
                        if r[0] == capbac:
                            capbac = r[1]
                            break
                    if not tv.link:
                        try:
    #                        context.update({'nguoitaobaiviet':tv.id or 0})
                            self.pool.get('hr.employee').capnhat_thongtin(cr, uid, [tv.id], context=context)
                        except:
                            pass
                    photo = domain + '/template/trangchu/images/default_customer.png'
                    if tv.image:
                        if not os.path.exists(folder_profile + '/images/thanhvien'):
                            os.makedirs(folder_profile + '/images/thanhvien')
                        path_hinh_ghixuong = folder_profile + '/images/thanhvien' + '/thanhvien_image_%s.jpg' %(tv.id,)
                        fw= open(path_hinh_ghixuong,'wb')
                        fw.write(base64.decodestring(tv.image))
                        fw.close()
                        photo = 'images/thanhvien/thanhvien_image_%s.jpg' %(tv.id,)
                        from PIL import Image
                        try:
                            im = Image.open(path_hinh_ghixuong)
                            width, height = im.size
                            if width>height:
                                ratio = float(width)/float(160)
                            else:
                                ratio = float(height)/float(160)
                            im.resize(((int(width/ratio),int(height/ratio))), Image.ANTIALIAS).save(path_hinh_ghixuong)
                        except:
                            im = im.convert('RGB')
                            im.resize(((int(width/ratio),int(height/ratio))), Image.ANTIALIAS).save(path_hinh_ghixuong)
        ##############################                             
                    thanhvien_tab = ''
                    thanhvien_tab = thanhvien_tab_
                    thanhvien_tab = thanhvien_tab.replace('__DANHXUNG__', tv.danhxung or '')
                    thanhvien_tab = thanhvien_tab.replace('__TENTHANHVIEN__', tv.name)
                    thanhvien_tab = thanhvien_tab.replace('__HINHTHANHVIEN__', photo)
                    thanhvien_tab = thanhvien_tab.replace('__LINKTHANHVIEN__', '../../profile/%s/index.%s'%(tv.id, kieufile))
                    thanhvien_tab = thanhvien_tab.replace('__EMAIL__', tv.work_email or '')
                    thanhvien_tab = thanhvien_tab.replace('__TRINHDOCHUYENMON__', capbac)
                    thanhvien_tab = thanhvien_tab.replace('__NGANH__',tv.nganh.name or '')
                    if tv.nganh and tv.chuyennganh:
                        thanhvien_tab = thanhvien_tab.replace('__CHUYENNGANH__',' - ' + tv.chuyennganh or '')
                    else:
                        thanhvien_tab = thanhvien_tab.replace('__CHUYENNGANH__',tv.chuyennganh or '')
                    noidung_thanhvien += thanhvien_tab
            
            noidung_dsbs = noidung_dsbs.replace('__BACSI__', noidung_thanhvien)
            template = template.replace('__DANHSACHBACSI__', noidung_dsbs)
        else:
            template = template.replace('__DANHSACHBACSI__', '')
            
        
        #write
        import codecs  
        fw= codecs.open(folder_profile+'/index.'+kieufile,'w','utf-8')
        fw.write(template)
        fw.close()
        
        link_xemnhanh = domain + '/profile_khachhang/%s/index.%s'%(khachhang.id,kieufile)
        super(yhoc_customer,self).write(cr,uid,ids,{'link':link_xemnhanh},context=context)
        
        if khachhang.supplier:
            self.pool.get('yhoc_trangchu').capnhat_nhataitro(cr, uid, duongdan, domain, kieufile, context)
            
        return template,duongdan
yhoc_customer()

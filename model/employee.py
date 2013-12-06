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


class yhoc_quatrinhdaotao(osv.osv):
    _name = 'yhoc_quatrinhdaotao'
    _columns = {
                'namtotnghiep': fields.char('Năm tốt nghiệp',size=30),
                'trinhdo': fields.char('Trình độ',size=100),
                'name': fields.many2one('res.partner','Nơi đào tạo', required="1"),
                'nganhdaotao': fields.char('Ngành đào tạo',size=100),
                'employee_id': fields.many2one('hr.employee', 'Thành viên', required='1'),
                }
yhoc_quatrinhdaotao()

class yhoc_lienket(osv.osv):
    _name = "yhoc_lienket"
    _description = "Lien ket"
    _order = "name"

    _columns = {
        'name': fields.char('Tên liên kết', size=500, required="1"),
        'linklienket': fields.char('Link liên kết', size=500, required="1"),
        'employee_id': fields.many2one('hr.employee', 'Thành viên', required='1'), 
    }

yhoc_lienket()

class yhoc_employee(osv.osv):
    
    _inherit = 'hr.employee'
    
#    def _get_help_information(self, cr, uid, ids, name, args, context=None):
#        '''
#        '''
#        return self.pool.get('hlv.help.page').get_help(cr, uid, self._name, name, ids) 
#    
    def _get_trinhdo(self,cr, uid, context=None):
        trinhdo = self.pool.get('hlv.property')._get_value_project_property_by_name(cr, uid, 'Trình độ chuyên môn') or '[]'
        return eval(trinhdo)
    
    def _get_baivietmoi(self, cr, uid, ids, field_name, arg, context=None):
        result = {}
        for record in self.browse(cr, uid, ids, context=context):
            dsbaivietmoi = self.pool.get('yhoc_thongtin').search(cr, uid, [('state','=','done'),('nguoidich.id','=',record.id)], order='create_date desc', context=context)
            result[record.id] = []
            for bv in self.pool.get('yhoc_thongtin').browse(cr, uid, dsbaivietmoi, context=context):
                result[record.id].append(bv.id)
        return result
    
    def _get_soluongbaiviet(self, cr, uid, ids, field_name, arg, context=None):
        result = {}
        for record in self.browse(cr, uid, ids, context=context):
#            dsbaivietmoi = self.pool.get('yhoc_thongtin').search(cr, uid, [('state','=','done'),('nguoidich.id','=',record.id)], context=context)
            result[record.id] = 0
            for bv in record.thongtin:
                result[record.id] += 1
        return result
    
    def _get_tongxem_baiviet(self, cr, uid, ids, field_name, arg, context=None):
        if not context:
            context = {}
        result = {}
        for record in self.browse(cr, uid, ids, context=context):
            result[record.id] = 0
            for bv in record.thongtin:
                result[record.id] += bv.soluongxem
        return result
    
    def _get_duan(self, cr, uid, ids, field_name, arg, context=None):
        if not context:
            context = {}
        duan_ids = self.pool.get('yhoc_duan').search(cr, uid, [], context=context)
        result = {}
        for record in self.browse(cr, uid, ids, context=context):
            result[record.id] = []
            for da in self.pool.get('yhoc_duan').browse(cr, uid,duan_ids, context=context):
                for m in da.thanhvienthamgia:
                    if m.nhanvien.id == record.id:
                        result[record.id].append(da.id)
                        break
        return result
#    
    def _get_employee_id(self, cr, uid, ids, context=None):
        result = {}
        for line in self.pool.get('yhoc_thongtin').browse(cr, uid, ids, context=context):
            result[line.nguoidich.id] = True
        return result.keys()
    
    _columns = {
        'gioithieu': fields.text('Giới thiệu'),        
        'lienket': fields.one2many('yhoc_lienket', 'employee_id','Liên kết'),        
        'link':fields.char('Link',size=1000),
        'trietlysong': fields.char('Triết lý sống', size=1000, required="1"),
        'danhxung': fields.char('Danh Xưng (viết tắt)',size=100),
        'nganh': fields.many2one('yhoc_nganh','Ngành'),
        'chuyennganh': fields.char('Chuyên ngành',size=100),
        'capbac': fields.selection(_get_trinhdo, 'Trình độ chuyên môn'),
        'thongtin':fields.function(_get_baivietmoi, type='many2many', relation='yhoc_thongtin', string='Thông tin'),
        'quatrinhdaotao': fields.one2many('yhoc_quatrinhdaotao', 'employee_id', 'Quá trình đào tạo'),
        'duan':fields.function(_get_duan, type='many2many', relation='yhoc_duan', string='Dự án'),
        'noilamviec_id': fields.many2one('res.partner', 'Nơi làm việc'),
#        'help' : fields.function(_get_help_information, method=True, string='Help', type="text"),
        'soluongxem': fields.integer("Số lượng người xem"),
        'tongxem_baiviet':fields.function(_get_tongxem_baiviet, type='integer', string='Tổng lượt xem'),
        'loaithanhvien': fields.selection([('bacsi','Bác sĩ'),('congtacvien','Cộng tác viên')], 'Loại thành viên'),
        'soluongbaiviet': fields.function(_get_soluongbaiviet, type='integer', string='Số lượng bài viết', store={
                'yhoc_thongtin': (_get_employee_id,['nguoidich'], 5),
                }),
        'link_url':fields.char('Link url',size=1000),
        'google_plus_acc':fields.char('Google+',size=500),
        'facebook_acc':fields.char('Facebook',size=500),
        'keyword_ids': fields.many2many('yhoc_keyword', 'thanhvien_keyword_rel', 'thanhvien_id', 'keyword_id', 'Keyword'),
        'main_key':fields.many2one('yhoc_keyword', 'Từ khóa chính'),
            }
    
    _defaults={
               'danhxung':'BS.',
               'trietlysong':'Vì Sức Khỏe Cộng Đồng',
               'loaithanhvien':'bacsi',
               }
    
    def create(self, cr, uid, vals,context=None):
        if 'loaithanhvien' in vals and vals['loaithanhvien'] == 'congtacvien':
           vals.update({'danhxung':''})
        return super(yhoc_employee,self).create(cr, uid, vals, context=context)
    
    def write(self, cr, uid, ids, vals, context=None):
        tv = self.browse(cr,uid,ids[0])
        nganhtr = tv.nganh
        ok = super(yhoc_employee,self).write(cr, uid, ids, vals, context=context)
        if ('nganh' in vals):
            if nganhtr:
                self.pool.get('yhoc_nganh').capnhat_thongtin(cr,uid,[tv.nganh.id],context)
            self.pool.get('yhoc_nganh').capnhat_thongtin(cr,uid,[vals['nganh']],context)
        return ok
    
    def capnhat_profiletrongtrangbaiviet(self, cr, uid, ids, context=None):
        duongdan = self.pool.get('hlv.property')._get_value_project_property_by_name(cr, uid, 'path of template')
        domain = self.pool.get('hlv.property')._get_value_project_property_by_name(cr, uid, 'Domain') or '../..'
        kieufile = self.pool.get('hlv.property')._get_value_project_property_by_name(cr, uid, 'Kiểu lưu file') or 'html'
        tv = self.browse(cr,uid,ids[0])
        name_url = self.pool.get('yhoc_trangchu').parser_url(str(tv.name))
        folder_profile = duongdan + '/profile/%s' %name_url
        if not os.path.exists(folder_profile):
            os.makedirs(folder_profile)
            
        if os.path.exists(duongdan+'/template/profile/profile.html'):
            fr = open(duongdan+'/template/profile/profile.html', 'r')
            template_ = fr.read()
            fr.close()
        else:
            template_ = ''
				
        if tv:
    #Cap nhat thong tin nguoi viet
            photo = ''
            if tv.image:
                if not os.path.exists(duongdan + '/images/profile'):
                    os.makedirs(duongdan + '/images/profile')
                filename = str(tv.id) + '-profile-' + name_url
                folder_hinh_profile = duongdan + '/images/profile'
                self.pool.get('yhoc_thongtin').ghihinhxuong(folder_hinh_profile, filename, tv.image, 150, 150, context=context)
                photo = domain + '/images/profile/%s.jpg' %(filename)
        
            template = template_.replace('__HINHNGUOIDICH__', photo)
            
            capbac = tv.capbac or ''
            trinhdo = self.pool.get('hlv.property')._get_value_project_property_by_name(cr, uid, 'Trình độ chuyên môn') or '[]'
            chuyenmon = ''
            for r in eval(trinhdo):
                if r[0] == capbac:
                    chuyenmon = r[1]
                    break
			#Giang_2011# Chỉnh sửa thông tin dưới profile trong bài viết
#            template = template.replace('__TRINHDOCHUYENMON__',chuyenmon)
            template = template.replace('__DANHXUNGNT__',tv.danhxung or '')
#            template = template.replace('__NGANH__',(tv.nganh and tv.nganh.name) or '')
#            if tv.nganh and tv.chuyennganh:
#                template = template.replace('__CHUYENNGANH__',' - ' + tv.chuyennganh or '')
#            else:
#                template = template.replace('__CHUYENNGANH__',tv.chuyennganh or '')
            template = template.replace('__NGUOIDICH__',tv.name)
            template = template.replace('__LINKNGUOIDICH__',tv.link or '#')
			
			#Giang_2011# Kiểm tra, nếu có thông tin thì hiển thị,không thì loại bỏ
            description =''
#            if chuyenmon:
#                description += chuyenmon
            if tv.nganh:
                description += '<span>%s</span>' %tv.nganh.name
            if tv.chuyennganh:
                description += '<span>%s</span>' %tv.chuyennganh
            if tv.noilamviec_id.name:
                description += '<span>%s</span>' %tv.noilamviec_id.name
            
            template = template.replace('__DESCRIPTION__',description)

            if os.path.exists(duongdan+'/template/profile/profile_item.html'):
                fr = open(duongdan+'/template/profile/profile_item.html', 'r')
                link_item_ = fr.read()
                fr.close()
            else:
                link_item_ = ''
			
            alllink_item_ = ''
            if tv.work_email:
				link_item = link_item_.replace('__LINK__', 'mailto:' + tv.work_email)
				link_item = link_item.replace('__TIITLELINK__', 'Gửi email cho tác giả')
				link_item = link_item.replace('__IMAGELINK__', domain + '/images/icon/email.png')
				alllink_item_ += link_item
            if tv.facebook_acc:
				link_item = link_item_.replace('__LINK__', tv.facebook_acc)
				link_item = link_item.replace('__TIITLELINK__', 'Facebook')
				link_item = link_item.replace('__IMAGELINK__', domain + '/images/icon/facebook.png')
				alllink_item_ += link_item
            if tv.google_plus_acc:
				link_item = link_item_.replace('__LINK__', tv.google_plus_acc)
				link_item = link_item.replace('__TIITLELINK__', 'Google+')
				link_item = link_item.replace('__IMAGELINK__', domain + '/images/icon/google_plus.png')
				alllink_item_ += link_item
            if os.path.exists(duongdan+'/tags/' + name_url):
                link_item = link_item_.replace('__LINK__', domain + '/tags/' + name_url + '/')
                link_item = link_item.replace('__TIITLELINK__', 'Những đóng góp của tác giả')
                link_item = link_item.replace('__IMAGELINK__', domain + '/images/icon/yhoccongdong.png')
                alllink_item_ += link_item

            template = template.replace('__PROFILEITEM__', alllink_item_)	
			
        import codecs  
        fw= codecs.open(folder_profile+'/profiletrongtrangbaiviet.html','w','utf-8')
        fw.write(template)
        fw.close()
        return True
    
    def profile_otrangchu(self, cr, uid, ids, context=None):
        duongdan = self.pool.get('hlv.property')._get_value_project_property_by_name(cr, uid, 'path of template')
        domain = self.pool.get('hlv.property')._get_value_project_property_by_name(cr, uid, 'Domain') or '../..'
        kieufile = self.pool.get('hlv.property')._get_value_project_property_by_name(cr, uid, 'Kiểu lưu file') or 'html'
        tv = self.browse(cr,uid,ids[0])
        name_url = self.pool.get('yhoc_trangchu').parser_url(str(tv.name))
        folder_profile = duongdan + '/profile/%s' %name_url
#        if not os.path.exists(folder_profile):
#            os.makedirs(folder_profile)
            
        if os.path.exists(duongdan+'/template/trangchu/bacsi_tab.html'):
            fr = open(duongdan+'/template/trangchu/bacsi_tab.html', 'r')
            profile_tab_ = fr.read()
            fr.close()
        else:
            profile_tab_ = ''
                
        if tv:
            photo = ''
            if tv.image:
                if not os.path.exists(duongdan + '/images/profile'):
                    os.makedirs(duongdan + '/images/profile')
                filename = str(tv.id) + '-profile-' + name_url
                folder_hinh_profile = duongdan + '/images/profile'
                self.pool.get('yhoc_thongtin').ghihinhxuong(folder_hinh_profile, filename, tv.image, 150, 150, context=context)
                photo = domain + '/images/profile/%s.jpg' %(filename)
        
            template = profile_tab_.replace('__PHOTO__', photo)
            
            capbac = tv.capbac or ''
            trinhdo = self.pool.get('hlv.property')._get_value_project_property_by_name(cr, uid, 'Trình độ chuyên môn') or '[]'
            chuyenmon = ''
            for r in eval(trinhdo):
                if r[0] == capbac:
                    chuyenmon = r[1]
                    break
            #Giang_2011# Chỉnh sửa thông tin dưới profile trong bài viết
            template = template.replace('__DANHXUNGNT__',tv.danhxung or '')
            template = template.replace('__NAME__',tv.name)
            template = template.replace('__CHUYENNGANH__',tv.chuyennganh or '')
            template = template.replace('__TRINHDOCHUYENMON__',chuyenmon)
            template = template.replace('__LINK__',tv.link or '#')
            
                        
            link_item_ = '<a href="__LINK__" title="__TIITLELINK__"><img src="__IMAGELINK__"></a>'
            
            alllink_item_ = ''
            if tv.work_email:
                link_item = link_item_.replace('__LINK__', 'mailto:' + tv.work_email)
                link_item = link_item.replace('__TIITLELINK__', 'Gửi email cho tác giả')
                link_item = link_item.replace('__IMAGELINK__', domain + '/images/icon/email.png')
                alllink_item_ += link_item
            if tv.facebook_acc:
                link_item = link_item_.replace('__LINK__', tv.facebook_acc)
                link_item = link_item.replace('__TIITLELINK__', 'Facebook')
                link_item = link_item.replace('__IMAGELINK__', domain + '/images/icon/facebook.png')
                alllink_item_ += link_item
            if tv.google_plus_acc:
                link_item = link_item_.replace('__LINK__', tv.google_plus_acc)
                link_item = link_item.replace('__TIITLELINK__', 'Google+')
                link_item = link_item.replace('__IMAGELINK__', domain + '/images/icon/google_plus.png')
                alllink_item_ += link_item
            if os.path.exists(duongdan+'/tags/' + name_url):
                link_item = link_item_.replace('__LINK__', domain + '/tags/' + name_url + '/')
                link_item = link_item.replace('__TIITLELINK__', 'Những đóng góp của tác giả')
                link_item = link_item.replace('__IMAGELINK__', domain + '/images/icon/yhoccongdong.png')
                alllink_item_ += link_item

            template = template.replace('__PROFILEITEM__', alllink_item_)    
            
        return template
        

	#Giang_2011#Cập nhật button follow tác giả
    def capnhat_authorfollow(self, cr, uid, ids, context=None):
        duongdan = self.pool.get('hlv.property')._get_value_project_property_by_name(cr, uid, 'path of template')
        domain = self.pool.get('hlv.property')._get_value_project_property_by_name(cr, uid, 'Domain') or '../..'
        kieufile = self.pool.get('hlv.property')._get_value_project_property_by_name(cr, uid, 'Kiểu lưu file') or 'html'
        tv = self.browse(cr,uid,ids[0])
        name_url = self.pool.get('yhoc_trangchu').parser_url(str(tv.name))
        import codecs
#        if tv.facebook_acc:
#            if os.path.exists(duongdan+'/template/profile/follow_facebook.html'):
#                fr = open(duongdan+'/template/profile/follow_facebook.html', 'r')
#                template_ = fr.read()
#                fr.close()
#            else:
#                template_ = ''
#            template = template_.replace('__FACEBOOK__', tv.facebook_acc)
#            fw = codecs.open(duongdan +'/profile/%s/follow_facebook.html'%(name_url),'w','utf-8')
#            fw.write(template)
#            fw.close()
        
        if tv.google_plus_acc:
            if os.path.exists(duongdan+'/template/profile/follow_googleplus.html'):
                fr = open(duongdan+'/template/profile/follow_googleplus.html', 'r')
                template_ = fr.read()
                fr.close()
            else:
                template_ = ''
            template = template_.replace('__GOOGLEPLUS__', tv.google_plus_acc)
            fw = codecs.open(duongdan +'/profile/%s/follow_googleplus.html'%(name_url),'w','utf-8')
            fw.write(template)
            fw.close()
        
#        if tv.twitter_acc:
#            if os.path.exists(duongdan+'/template/profile/follow_twitter.html'):
#                fr = open(duongdan+'/template/profile/follow_twitter.html', 'r')
#                template_ = fr.read()
#                fr.close()
#            else:
#                template_ = ''
#            template = template_.replace('__TWITTER__', tv.facebook_acc)
#            template = template_.replace('__TWITTERNAME__', tv.name)
#            fw = codecs.open(duongdan +'/profile/%s/follow_twitter.html'%(name_url),'w','utf-8')
#            fw.write(template)
#            fw.close()
        
        return True
    
	#Giang_1811# Author_box
    def capnhat_authorbox(self, cr, uid, ids, context=None):
        duongdan = self.pool.get('hlv.property')._get_value_project_property_by_name(cr, uid, 'path of template')
        domain = self.pool.get('hlv.property')._get_value_project_property_by_name(cr, uid, 'Domain') or '../..'
        kieufile = self.pool.get('hlv.property')._get_value_project_property_by_name(cr, uid, 'Kiểu lưu file') or 'html'
        tv = self.browse(cr,uid,ids[0])
        name_url = self.pool.get('yhoc_trangchu').parser_url(str(tv.name))
            
        if os.path.exists(duongdan+'/template/profile/author_box.html'):
            fr = open(duongdan+'/template/profile/author_box.html', 'r')
            template_ = fr.read()
            fr.close()
        else:
            template_ = ''
            
        if os.path.exists(duongdan+'/template/profile/author_box_item.html'):
            fr = open(duongdan+'/template/profile/author_box_item.html', 'r')
            item_ = fr.read()
            fr.close()
        else:
            item_ = ' '
                
        if tv:
            photo = ''
            if tv.image:
                if not os.path.exists(duongdan + '/images/profile'):
                    os.makedirs(duongdan + '/images/profile')
                filename = str(tv.id) + '-profile-' + name_url
                folder_hinh_profile = duongdan + '/images/profile'
                self.pool.get('yhoc_thongtin').ghihinhxuong(folder_hinh_profile, filename, tv.image, 150, 150, context=context)
                photo = domain + '/images/profile/%s.jpg' %(filename)
        
            template = template_.replace('__HINHNGUOIDICH__', photo)
            template = template.replace('__LINKNGUOIDICH__',tv.link or '#')
            template = template.replace('__DANHXUNGNT__',tv.danhxung or '')
            template = template.replace('__NGUOIDICH__',tv.name)
            
            capbac = tv.capbac or ''
            trinhdo = self.pool.get('hlv.property')._get_value_project_property_by_name(cr, uid, 'Trình độ chuyên môn') or '[]'
            chuyenmon = ''
            for r in eval(trinhdo):
                if r[0] == capbac:
                    chuyenmon = r[1]
                    break
            description =''
            if chuyenmon:
                description += chuyenmon
            if tv.nganh:
                description += '''</br>Ngành: ''' + tv.nganh.name
            if tv.chuyennganh:
                description += '''</br>Chuyên: ''' + tv.chuyennganh
            if tv.noilamviec_id.name:
                description += '''</br>Công tác tại: ''' + tv.noilamviec_id.name
            
            template = template.replace('__DESCRIPTION__',description)
            
            if tv.facebook_acc:
                tab_facebook = '''<li class="ts-fab-facebook-link">
                <a href="#facebook">Facebook</a>
            </li>'''
                template = template.replace('<!--__TABFACEBOOK__-->',tab_facebook)
                item = item_.replace('__TYPE__', 'facebook')
                item = item.replace('__LINK__', tv.facebook_acc)
                item = item.replace('__HINH__', photo)
                item = item.replace('__NAME__', tv.name)
#                item = item.replace('__FOLLOW_AUTHOR__','<?php include("' + duongdan + '/profile/%s/follow_facebook.html'%name_url + '"); ?>')
                item = item.replace('__FOLLOW_AUTHOR__','<!---->')
                template = template.replace('<!--__FACEBOOK_FOLLOW__-->',item)

            if tv.google_plus_acc:
                tab_googleplus = '''<li class="ts-fab-googleplus-link">
                <a href="#googleplus">Google+</a>
            </li>'''
                template = template.replace('<!--__TABGOOGLEPLUS__-->',tab_googleplus)
                item = item_.replace('__TYPE__', 'googleplus')
                item = item.replace('__LINK__', tv.google_plus_acc)
                item = item.replace('__HINH__', photo)
                item = item.replace('__NAME__', tv.name)
                item = item.replace('__FOLLOW_AUTHOR__','<?php include("' + duongdan + '/profile/%s/follow_googleplus.html'%name_url + '"); ?>')
                template = template.replace('<!--__GOOGLEPLUS_FOLLOW__-->',item)
            
#            if tv.twitter_acc:
#                tab_twitter = '''<li class="ts-fab-twitter-link">
#                <a href="#twitter">Twitter</a>
#            </li>'''
#                template = template.replace('<!--__TABTWITTER__-->',tab_twitter)
#                item = item_.replace('__TYPE__', 'twitter')
#                item = item.replace('__LINK__', tv.twitter_acc)
#                item = item.replace('__HINH__', photo)
#                item = item.replace('__NAME__', tv.name)
#                item = item.replace('__FOLLOW_AUTHOR__', duongdan + '/profile/%s/follow_twitter.html'%name_url)
#                template = template.replace('<!--__TWITTER_FOLLOW__-->',item) 

            template = template.replace('__TATCABAIVIET__', domain + '/tags/%s/'%name_url)
            template = template.replace('__BAIVIETMOI__', duongdan + '/profile/%s/author_baivietmoi.html'%name_url)
                        
        import codecs  
        fw = codecs.open(duongdan +'/profile/%s/author_box.html'%(name_url),'w','utf-8')
        fw.write(template)
        fw.close()
        return True
    
    def capnhat_trangtvcongtac(self,cr,uid,context=None):
        duongdan = self.pool.get('hlv.property')._get_value_project_property_by_name(cr, uid, 'path of template')
        domain = self.pool.get('hlv.property')._get_value_project_property_by_name(cr, uid, 'Domain') or '../..'
        kieufile = self.pool.get('hlv.property')._get_value_project_property_by_name(cr, uid, 'Kiểu lưu file') or 'html'
        
        trangchu_pool = self.pool.get('yhoc_trangchu')
        trangchu_id = trangchu_pool.search(cr, uid, [], context=context)
        if trangchu_id:
            if os.path.exists(duongdan+'/template/trangchu/thanhviencongtac.html'):
                fr = open(duongdan+'/template/trangchu/thanhviencongtac.html', 'r')
                congtac_template = fr.read()
                fr.close()
            else:
                congtac_template = ''
                
            trangchu = trangchu_pool.browse(cr, uid, trangchu_id[0], context=context)
            folder_trangchu = duongdan + '/trangchu/vi'
            if not os.path.exists(folder_trangchu):
                os.makedirs(folder_trangchu) 
            if os.path.exists(duongdan+'/template/trangchu/thanhvien_tab.html'):
                fr = open(duongdan+'/template/trangchu/thanhvien_tab.html', 'r')
                thanhvien_tab_ = fr.read()
                fr.close()
            else:
                thanhvien_tab_ = ''
                
            
            nhomctv = self.search(cr, uid, [('loaithanhvien','=','congtacvien')], context=context)
            if not context:
                context = {}
            context.update({'trangthanhvien':True})
            noidung_congtac = self.pool.get('yhoc_trangchu').capnhat_trangthanhvien(cr, uid, domain, folder_trangchu,thanhvien_tab_, nhomctv, context)
            congtac_template = congtac_template.replace('__THANHVIENCONGTAC__', noidung_congtac)
            
            #Cập nhật tittle       
            fr = open(duongdan + '/template/trangchu/tittle.html', 'r')
            noidung_tittle = fr.read()
            fr.close()
            noidung_tittle = noidung_tittle.replace('__TITLE__','Nhóm cộng tác viên')
            congtac_template = congtac_template.replace('__TITLE__',noidung_tittle)
            congtac_template = congtac_template.replace('__DUONGDAN__',duongdan)
            
        import codecs
        fw = codecs.open(folder_trangchu + '/nhomcongtac.' + kieufile,'w','utf-8')
        fw.write(congtac_template)
        fw.close()
        return True
    
    def capnhat_thongtin(self,cr,uid,ids,context=None):
        duongdan = self.pool.get('hlv.property')._get_value_project_property_by_name(cr, uid, 'path of template')
        domain = self.pool.get('hlv.property')._get_value_project_property_by_name(cr, uid, 'Domain') or '../..'
        kieufile = self.pool.get('hlv.property')._get_value_project_property_by_name(cr, uid, 'Kiểu lưu file') or 'html'
        nhanvien = self.browse(cr,uid,ids[0])
        name_url = self.pool.get('yhoc_trangchu').parser_url(str(nhanvien.name))
        #Giang_0511#link_url = str(nhanvien.id) +'-' +name_url
        link_url = name_url
        if not context:
            context = {}
        
        
        if os.path.exists(duongdan + '/template/profile/index.html'):
            fr = open(duongdan + '/template/profile/index.html', 'r')
            template = fr.read()
            fr.close()
        else:
            template = ''

#Tao folder cho thongtin
        folder_profile = duongdan + '/profile/%s/' %link_url
        if not os.path.exists(folder_profile):
            os.makedirs(folder_profile)
            
#Lay thong tin chung
        tennhanvien = nhanvien.name
        trietly = nhanvien.trietlysong
        email = nhanvien.work_email or ''
        gioithieu = nhanvien.gioithieu
        lienket = nhanvien.lienket   
        link = nhanvien.link
        tongxem_baiviet = nhanvien.tongxem_baiviet or 0
        capbac = nhanvien.capbac or ''
        duan = nhanvien.duan
        quatrinhdaotao = nhanvien.quatrinhdaotao
        thongtin = nhanvien.thongtin
        trinhdo = self.pool.get('hlv.property')._get_value_project_property_by_name(cr, uid, 'Trình độ chuyên môn') or '[]'
        baiviet_hieudinh = self.pool.get('yhoc_thongtin').search(cr, uid, [('state','=','done'),('nguoihieudinh.id','=',nhanvien.id)], context=context)
        
        chuyenmon = ''
        for r in eval(trinhdo):
            if r[0] == capbac:
                chuyenmon = r[1]
                break
            
        photo = ''
        if nhanvien.image:
            
            if not os.path.exists(duongdan + '/images/profile'):
                os.makedirs(duongdan + '/images/profile')
            filename = str(nhanvien.id) + '-profile-' + name_url
            folder_hinh_profile = duongdan + '/images/profile'
            self.pool.get('yhoc_thongtin').ghihinhxuong(folder_hinh_profile, filename, nhanvien.image, 150, 150, context=context)
            photo = '../../../../../../images/profile/%s.jpg'%(filename)
#            path_hinh_ghixuong = duongdan + '/images/profile' + '/%s-profile-%s.jpg' %(str(nhanvien.id),name_url)
#            fw = open(path_hinh_ghixuong,'wb')
#            fw.write(base64.decodestring(nhanvien.image))
#            fw.close()
#            try:
#                from PIL import Image
#                im = Image.open(path_hinh_ghixuong)
#                width, height = im.size
#                maxi=width*1.0
#                if width<height:
#                    maxi=height*1.0
#                resizeFactor=500/maxi
#                im.resize((int(width*resizeFactor),int(height*resizeFactor))).save(path_hinh_ghixuong)
#            except:
#                fw = open(path_hinh_ghixuong,'wb')
#                fw.write(base64.decodestring(nhanvien.image))
#                fw.close()

#Cap nhat lien ket
        noidung_lienket = ''
        if os.path.exists(duongdan+'/template/profile/link_tab.html'):
            fr = open(duongdan+'/template/profile/link_tab.html', 'r')
            lienket_tab_ = fr.read()
            fr.close()
        else:
            lienket_tab_ = ''
        
        for lk in lienket:
            lienket_tab =''
            lienket_tab = lienket_tab_.replace('__LINK__', lk.linklienket)
            lienket_tab = lienket_tab.replace('__NOIDUNG__', lk.name)
            noidung_lienket += lienket_tab
            
        template = template.replace('__LIENKET__',noidung_lienket)
        
        
#Cập nhat qua trinh dao tao
        noidung_quatrindaotao = ''
        if os.path.exists(duongdan+'/template/profile/table4col_tab.html'):
            fr = open(duongdan+'/template/profile/table4col_tab.html', 'r')
            quatrinh_tab_ = fr.read()
            fr.close()
        else:
            quatrinh_tab_ = ''            
            
        for qt in quatrinhdaotao:
            quatrinh_tab = quatrinh_tab_.replace('__COL1__', qt.name.name or '')
            quatrinh_tab = quatrinh_tab.replace('__COL2__', qt.nganhdaotao or '')
            quatrinh_tab = quatrinh_tab.replace('__COL3__', qt.trinhdo or '')
            quatrinh_tab = quatrinh_tab.replace('__COL4__', qt.namtotnghiep or '')
            noidung_quatrindaotao += quatrinh_tab
        template = template.replace('__QUATRINHDAOTAO__',noidung_quatrindaotao)
        
#Cập nhat bai viet
#        noidung_baiviet = ''
#        if os.path.exists(duongdan+'/template/profile/table_baiviet_tab.html'):
#            fr = open(duongdan+'/template/profile/table_baiviet_tab.html', 'r')
#            baiviet_tab_ = fr.read()
#            fr.close()
#        else:
#            baiviet_tab_ = ''            
#        
#        tongcamon = 0
#        for bv in thongtin:
#            baiviet_tab = baiviet_tab_.replace('__COL1__', bv.name or '')
#            baiviet_tab = baiviet_tab.replace('__LINK1__', '../../thongtin/%s/index.%s'%(bv.id, kieufile))
#            baiviet_tab = baiviet_tab.replace('__COL2__', (bv.duan and bv.duan.name) or '')
#            baiviet_tab = baiviet_tab.replace('__LINK2__', (bv.duan and bv.duan.link) or '#')
#            #baiviet_tab = baiviet_tab.replace('__COL3__', str('--'))
#            baiviet_tab = baiviet_tab.replace('__COL4__', str(bv.soluongxem) or '0')
#            tongcamon += 0
#            noidung_baiviet += baiviet_tab
#        
#        #Thêm tổng xem các bài viết
#        baiviet_tab = ''
#        baiviet_tab = baiviet_tab_.replace('__COL1__', '')
#        baiviet_tab = baiviet_tab.replace('__COL2__', '')
#        baiviet_tab = baiviet_tab.replace('__COL3__', "Tổng lượt xem")
#        baiviet_tab = baiviet_tab.replace('__COL4__', str(tongxem_baiviet))
#        noidung_baiviet += baiviet_tab
#        template = template.replace('__BAIVIET1__',noidung_baiviet)
        template = template.replace('__BAIVIET1__','%s/profile/%s/baiviettrongprofile.html'%(duongdan,link_url))        
        tongcamon = self.pool.get('yhoc_thongtin').capnhat_baiviettrongprofile(cr, uid, ids, context)
        
        
##################################################
        template = template.replace('__TENPROFILE__', tennhanvien)
        template = template.replace('__ANHPROFILE__', photo)
        template = template.replace('__TRIETLY__', trietly or '')
        template = template.replace('__LINKPROFILE__', link or '''%s/profile/%s/'''%(domain,link_url))
        template = template.replace('__EMAIL__', email or '(Chưa cập nhật)')
        template = template.replace('__GIOITHIEU__', gioithieu or '(Chưa cập nhật)')
#        template = template.replace('__TONGHIEUDINH__', str(len(baiviet_hieudinh)))
        template = template.replace('__TONGCAMON__', str(tongcamon))
        template = template.replace('__DANHXUNG__',nhanvien.danhxung or '')
        template = template.replace('__NGANH__',nhanvien.nganh.name or '')
        template = template.replace('__LINKNOILAMVIEC__','../../profile_khachhang/%s/index.%s'%(nhanvien.noilamviec_id.id, kieufile))
        template = template.replace('__NOILAMVIEC__',nhanvien.noilamviec_id.name or '(Chưa cập nhật)')        
        template = template.replace('__CHUYENNGANH__',nhanvien.chuyennganh or '')
        template = template.replace('__TRINHDOCHUYENMON__',chuyenmon)
#        template = template.replace('__TONGBAIVIET__', str(len(thongtin)))

#Cap nhat tong hieu dinh va tong dong gop
#        self.pool.get('yhoc_thongtin').capnhat_tonghieudinh_donggop(cr, uid, ids, context=context)
#        if os.path.exists(folder_profile+'/tonghieudinh_donggop_div.' + kieufile):
#            fr = open(folder_profile+'/tonghieudinh_donggop_div.' + kieufile, 'r')
#            tonghieudinh_donggop = fr.read()
#            fr.close()
#        template = template.replace('__TONGDONGGOP_HIEUDINH__',tonghieudinh_donggop)
        ##################################################
        
        #Giang_0511#link_xemnhanh = '''%s/profile/%s/index.%s'''%(domain,link_url,kieufile)
        link_xemnhanh = '''%s/profile/%s/'''%(domain,link_url)
        super(yhoc_employee,self).write(cr,uid,ids,{'link':link_xemnhanh,
                                                    'link_url': link_url}, context=context) 
        
        #Cap nhat du an
#        noidung_duan = ''
#        if os.path.exists(duongdan+'/template/profile/table_link_tab.html'):
#            fr = open(duongdan+'/template/profile/table_link_tab.html', 'r')
#            duan_tab_ = fr.read()
#            fr.close()
#        else:
#            duan_tab_ = ''
#                    
#        for da in duan:
#            duan_tab =''
#            for m in da.thanhvienthamgia:
#                if m.nhanvien.id == nhanvien.id:
#                    duan_tab = duan_tab_.replace('__LINK__', '../../duan/%s/index.%s'%(da.id, kieufile))
#                    duan_tab = duan_tab.replace('__COL1__', da.name)
#                    duan_tab = duan_tab.replace('__COL2__', m.name)
#            noidung_duan += duan_tab
        self.pool.get('yhoc_duan').capnhat_duantrongprofile(cr, uid, ids, context)

        template = template.replace('__DUAN__','duantrongprofile.html')
        template = template.replace('__ID_PROFILE__',str(nhanvien.id))
        import codecs

        fw= codecs.open(folder_profile+'/index.' + kieufile,'w','utf-8')
        fw.write(template)
        fw.close()
        
        
        #Cap nhat nganh
        if nhanvien.nganh:
            self.pool.get('yhoc_nganh').capnhat_thongtin(cr,uid,[nhanvien.nganh.id],context)
        
        #Cap nhat trang cong tac vien
        if nhanvien.loaithanhvien == 'congtacvien':
            self.capnhat_trangtvcongtac(cr, uid, context)
        
        self.capnhat_profiletrongtrangbaiviet(cr, uid, ids, context=context)
        
        #Giang_1911# Cap nhat author follow (Google+ , Facebook, Twitter)
        self.capnhat_authorfollow(cr, uid, ids, context)
        #Giang_1811# Cap nhat author box
        self.capnhat_authorbox(cr, uid, ids, context)
        
        return template,duongdan,domain
    
yhoc_employee()


class res_users(osv.osv):
    _inherit='res.users'
    
    def create(self, cr, uid, vals, context=None):
        vals.update({'password':'1'})
        return super(res_users,self).create(cr, uid, vals, context=context)
res_users()
    

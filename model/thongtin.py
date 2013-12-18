# -*- encoding: utf-8 -*-
from osv import fields,osv
from tools.translate import _
import time
from datetime import datetime, date
import os
import base64,os,re
import sys
import facebook
reload(sys)
sys.setdefaultencoding("utf8")


class yhoc_thongtin(osv.osv):
    _name = "yhoc_thongtin"
    _order = 'date desc'
    
    _STATE_THONGTIN = [('nhap','Chờ dịch'),('choduyet','Chờ hiệu đính'), ('daduyet','Chờ xuất bản'),('done','Đã xuất bản'),('huy','Đã hủy')]
    
    def _default_quyensuabaiviet(self, cr, uid, context=None):
        result = {}
        user = self.pool.get('res.users').browse(cr, uid, uid, context=context)
        result = False
        if uid == 1:
            result = True
        else:
            for group in user.groups_id:
                if group.name == 'Điều hành' or group.name == 'Trưởng dự án':
                    result = True
                    break
        return result
    
    def _kiemtra_quyensuabaiviet(self, cr, uid, ids, name, args, context=None):
        result = {}
        user = self.pool.get('res.users').browse(cr, uid, uid, context=context)
        bv = self.browse(cr, uid, ids[0], context=context)
        for r in ids:
            result[r] = False
            if uid == 1:
                result[r] = True
            elif (bv.nguoidich.user_id and bv.nguoidich.user_id.id == uid) or (bv.nguoihieudinh.user_id and bv.nguoihieudinh.user_id.id == uid):
                result[r] = True
            else:
                for group in user.groups_id:
                    if group.name == 'Điều hành' or group.name == 'Trưởng dự án':
                        result[r] = True
                        break
        return result

    def onchange_duan_id(self, cr, uid, ids, duan_id, context=None):
        if context is None:
            context = {}
        if not duan_id:
            return {}
        duan = self.pool.get('yhoc_duan').browse(cr, uid, duan_id, context=context)
        if duan:
            return {'value': {'nguoihieudinh': duan.truongduan.id}}
        
    _columns = {
                'name': fields.char('Tên thông tin',size=200,required="1"),
                'hinhdaidien':fields.binary('Hình mô tả (chọn hình nhỏ)'),
                'motangan':fields.char('Mô tả ngắn',size=500),
                'noidung':fields.text('Nội dung'),
                'create_date':fields.datetime('Ngày tạo'),
                'date': fields.datetime('Ngày xuất bản'),
                'create_uid':fields.many2one('res.users','Người tạo'),
                'sequence':fields.integer('Thứ tự hiện (Sequence)'),#Thứ tự hiện
                'link':fields.char('Link thông tin',size=500),
                'duan':fields.many2one('yhoc_duan', 'Dự án'),
                'nguonbaiviet': fields.char('Nguồn bài viết', size=200),
                'link_tree':fields.char('Link tree',size=1000),
                'nguoihieudinh':fields.many2one('hr.employee', 'Người hiệu đính', required="1"),
#                'help': fields.function(_get_help_information, method=True, string='Help', type="text"),
#                'comment': fields.one2many('yhoc_comment', 'baiviet_id', 'Commnents'),
                'state': fields.selection(_STATE_THONGTIN, 'State'),
                'nguoidich':fields.many2one('hr.employee', 'Người dịch'),
                'soluongxem': fields.integer("Số lượng người xem"),
                'is_write': fields.function(_kiemtra_quyensuabaiviet, method=True, string='Is write', type="boolean"),
                'is_post_fb': fields.boolean('Is post fb'),
                'fb_post_id':fields.char('FB post ID',size=20),
                'attachment': fields.one2many('yhoc.attachment', 'baiviet_id', 'Đính kèm'),
                'keyword_ids': fields.many2many('yhoc_keyword', 'thongtin_keyword_rel', 'thongtin_id', 'keyword_id', 'Keyword'),
                'link_url':fields.char('Link url',size=1000),
                'url_thongtin':fields.char('URL',size=1000),
                'main_key':fields.many2one('yhoc_keyword', 'Từ khóa chính'),
                'hinhlon':fields.binary('Hình lớn (ở trang chủ)'),               
                }
    _defaults = {
                 'is_write': _default_quyensuabaiviet,
                 'state':'nhap',
                 'is_post_fb':False
                 }
    

    def unlink(self, cr, uid, ids, context=None):
        duongdan = self.pool.get('hlv.property')._get_value_project_property_by_name(cr, uid, 'path of template')
        kieufile = self.pool.get('hlv.property')._get_value_project_property_by_name(cr, uid, 'Kiểu lưu file') or 'html'
        for id in ids:
            folder = duongdan + '/thongtin/%s/index.%s'%(id,kieufile)
            if os.path.exists(folder):
                os.remove(folder)
        ok = super(yhoc_thongtin, self).unlink(cr, uid, ids, context=context)
        thongtin_cungtacgia = self.search(cr, uid, [('create_uid','=',uid)], context=context)
        for tt in thongtin_cungtacgia:
            try:
                self.capnhat_thongtin(cr, uid, [tt], context=context)
            except:
                pass
        return ok

    def act_chodich_thongtin(self, cr, uid, ids, context = None):
        return super(yhoc_thongtin,self).write(cr, uid, ids, {'state':'nhap'}, context=context)
    
    def act_choduyet_thongtin(self, cr, uid, ids, context = None):
        for r in self.browse(cr, uid, ids, context=context):
            if not r.nguoidich:
                raise osv.except_osv(('Message'), ('Chưa có thông tin người dịch!'))
        return super(yhoc_thongtin,self).write(cr, uid, ids, {'state':'choduyet'}, context=context)
    
    def act_choxuatban_thongtin(self, cr, uid, ids, context = None):
        return super(yhoc_thongtin,self).write(cr, uid, ids, {'state':'daduyet'}, context=context)
    
    def act_daxuatban_thongtin(self, cr, uid, ids, context = None):
        ok = super(yhoc_thongtin,self).write(cr, uid, ids, {'state':'done'}, context=context)
        self.xuatban_thongtin(cr, uid, ids, context)
        return ok
    
    def act_huy_thongtin(self, cr, uid, ids, context = None):
        return super(yhoc_thongtin,self).write(cr, uid, ids, {'state':'huy'}, context=context)
   
    def create(self, cr, uid, vals, context=None):
        if 'url_thongtin' in vals and vals['url_thongtin']==False:
            name_url = self.pool.get('yhoc_trangchu').parser_url(vals['name'])
            vals.update({'url_thongtin':name_url})
        return super(yhoc_thongtin,self).create(cr,uid,vals,context=context)
    
    def write(self,cr, uid, ids, vals, context=None):
#        self.tao_mucluc(cr, uid, context)

#Giang_2011# Trên server trước lúc cập nhật (20/11/2013-12:00AM) không có nên comment lại !
        # ###################
        # a = self.pool.get('yhoc_keyword').search(cr, uid, [],context=context)
        # for i in a:
            # vals = {}
            # self.pool.get('yhoc_keyword').write(cr,uid, [i], vals, context=context)
        # ###################
# #        print vals

        for r in self.browse(cr, uid, ids, context=context):
            if 'name' in vals:
                name_url = self.pool.get('yhoc_trangchu').parser_url(str(vals['name']))
                vals.update({'url_thongtin':name_url})
            elif 'url_thongtin' not in vals and not r.url_thongtin:
                name_url = self.pool.get('yhoc_trangchu').parser_url(str(r.name))
                vals.update({'url_thongtin':name_url})
                
            if uid != 1:
                if r.is_write == False:
                    raise osv.except_osv(('Message'), ('Bạn không có quyền sửa bài viết của người khác!'))
        return super(yhoc_thongtin,self).write(cr, uid, ids, vals, context=context)
    
#    def capnhat_tonghieudinh_donggop(self, cr, uid, nhanvien_ids, context=None):
#        duongdan = self.pool.get('hlv.property')._get_value_project_property_by_name(cr, uid, 'path of template')
#        domain = self.pool.get('hlv.property')._get_value_project_property_by_name(cr, uid, 'Domain') or '../..'
#        kieufile = self.pool.get('hlv.property')._get_value_project_property_by_name(cr, uid, 'Kiểu lưu file') or 'html'
#        nhanvien = self.pool.get('hr.employee').browse(cr,uid,nhanvien_ids[0])
#        folder_profile = duongdan + '/profile/%s' %str(nhanvien.id)
#        if not os.path.exists(folder_profile):
#            os.makedirs(folder_profile)
#        thongtin = nhanvien.thongtin
#        baiviet_hieudinh = self.pool.get('yhoc_thongtin').search(cr, uid, [('state','=','done'),('nguoihieudinh.id','=',nhanvien.id)], context=context)
#        template = '''<p>__TONGBAIVIET__ bài đóng góp</p>
#                <p>__TONGHIEUDINH__ bài hiệu đính</p>'''
#        template = template.replace('__TONGHIEUDINH__', str(len(baiviet_hieudinh)))
#        template = template.replace('__TONGBAIVIET__', str(len(thongtin)))
#        
#        import codecs  
#        fw= codecs.open(folder_profile+'/tonghieudinh_donggop_div.' + kieufile,'w','utf-8')
#        fw.write(template)
#        fw.close()
        
    def capnhat_baiviettrongprofile(self, cr, uid, nhanvien_ids, context=None):
        duongdan = self.pool.get('hlv.property')._get_value_project_property_by_name(cr, uid, 'path of template')
        domain = self.pool.get('hlv.property')._get_value_project_property_by_name(cr, uid, 'Domain') or '../..'
        kieufile = self.pool.get('hlv.property')._get_value_project_property_by_name(cr, uid, 'Kiểu lưu file') or 'html'
        nhanvien = self.pool.get('hr.employee').browse(cr,uid,nhanvien_ids[0])
        thongtin = nhanvien.thongtin
        #tongxem_baiviet = nhanvien.tongxem_baiviet or 0
        tongxem_baiviet = []
        folder_profile = duongdan + '/profile/%s' %str(nhanvien.link_url)
        if not os.path.exists(folder_profile):
            os.makedirs(folder_profile)
        
        noidung_baiviet = '<?php include("%s/count_tv.php");?>'%duongdan
        if os.path.exists(duongdan+'/template/profile/table_baiviet_tab.html'):
            fr = open(duongdan+'/template/profile/table_baiviet_tab.html', 'r')
            baiviet_tab_ = fr.read()
            fr.close()
        else:
            baiviet_tab_ = ''            
        
        tongdonggop = 0
        for bv in thongtin:
            tongxem_baiviet.append(bv.id)
            baiviet_tab = baiviet_tab_.replace('__COL1__', bv.name or '')
            baiviet_tab = baiviet_tab.replace('__LINK1__', domain + '/%s/'%(bv.link_url))
            baiviet_tab = baiviet_tab.replace('__COL2__', (bv.duan and bv.duan.name) or '')
            baiviet_tab = baiviet_tab.replace('__LINK2__', (bv.duan and bv.duan.link) or '#')
            #baiviet_tab = baiviet_tab.replace('__COL3__', str('--'))
            baiviet_tab = baiviet_tab.replace('__COL4__', '<?php echo soluongxem_baiviet(%s);?>' %(str(bv.id) or '0'))
            tongdonggop += 0
            noidung_baiviet += baiviet_tab
        
        #Thêm tổng xem các bài viết
        
        tongxem_baiviet = str(tuple(tongxem_baiviet))
        baiviet_tab = ''
        baiviet_tab = baiviet_tab_.replace('__COL1__', '')
        baiviet_tab = baiviet_tab.replace('__COL2__', '')
        baiviet_tab = baiviet_tab.replace('__COL3__', "Tổng lượt xem")
        baiviet_tab = baiviet_tab.replace('__COL4__', '<?php echo tongsoluongxem_baiviet("%s");?>' %str(tongxem_baiviet))
        noidung_baiviet += baiviet_tab
        
        import codecs  
        fw= codecs.open(folder_profile+'/baiviettrongprofile.html','w','utf-8')
        fw.write(noidung_baiviet)
        fw.close()
        
        return tongdonggop

#Giang_1811# Bai viet moi cua tac gia - trong author box
    def capnhat_baivietmoicuatacgia(self, cr, uid, nhanvien_ids, baiviet_id, context=None):
        duongdan = self.pool.get('hlv.property')._get_value_project_property_by_name(cr, uid, 'path of template')
        domain = self.pool.get('hlv.property')._get_value_project_property_by_name(cr, uid, 'Domain') or '../..'
        kieufile = self.pool.get('hlv.property')._get_value_project_property_by_name(cr, uid, 'Kiểu lưu file') or 'html'
        thongtin = self.pool.get('yhoc_thongtin').search(cr, uid, [('nguoidich.id','=',nhanvien_ids[0]),('id','!=',baiviet_id),('state','=','done')], limit=3, order='date desc', context=context)
        if os.path.exists(duongdan+'/template/profile/author_baivietmoi.html'):
            fr = open(duongdan+'/template/profile/author_baivietmoi.html', 'r')
            author_baivietmoi_ = fr.read()
            fr.close()
        else:
            author_baivietmoi_ = ''
            
        author_listbaivietmoi_ =''
        for bv in thongtin:
            bv_moi = self.pool.get('yhoc_thongtin').browse(cr, uid, bv, context=context)
            author_baivietmoi = author_baivietmoi_.replace('__TENBAIVIET__', bv_moi.name)
            author_baivietmoi = author_baivietmoi.replace('__LINKBAIVIET__', domain + '/%s/'%(bv_moi.link_url))
            date_default = datetime.strptime(bv_moi.date, '%Y-%m-%d %H:%M:%S')
            date = date_default.strftime('%d/%m/%Y')
            author_baivietmoi = author_baivietmoi.replace('__NGAYDANG__', date)
            author_listbaivietmoi_ += author_baivietmoi
        
        nhanvien = self.pool.get('hr.employee').browse(cr,uid,nhanvien_ids[0])
        
        import codecs
        if not os.path.exists(duongdan + '/profile/%s'%nhanvien.link_url):
            os.makedirs(duongdan + '/profile/%s'%nhanvien.link_url)
            
        fw= codecs.open(duongdan + '/profile/%s/author_baivietmoi.html'%nhanvien.link_url,'w','utf-8')
        fw.write(author_listbaivietmoi_)
        fw.close()
        
        return True
    
    def ghihinhxuong(self, path, filename, image, heigh, width, context=None):
        if not os.path.exists(path):
            os.makedirs(path)
        path_hinh_ghixuong = path + '/'+ filename +'.jpg'
        fw = open(path_hinh_ghixuong,'wb')
        fw.write(base64.decodestring(image))
        fw.close()
        self.resize_image(path_hinh_ghixuong, heigh, width, context=context)
        return True
        
    def resize_image(self, path, height, width, context=None):
        from PIL import Image
        im = Image.open(path)
        try:
            width_o, height_o = im.size
            ratio = float(width_o)/float(height_o)
            if width_input and height_input:
                width = width_input
                height = height_input
            elif width_input and not height_input:
                width = width_input
                height = int(width/ratio)
            elif not width_input and height_input:
                height = height_input
                width = int(height * ratio)
            else:
                height = height_o
                width = width_o

            im.resize(((int(width),int(height))), Image.ANTIALIAS).save(path)
        except:
            im = im.convert('RGB')
            im.resize(((int(width),int(height))), Image.ANTIALIAS).save(path)
        return True
        
    def xuatban_thongtin(self,cr,uid,ids,context=None):
 #       cr.execute("""update yhoc_thongtin set date=write_date where state='done'""")
        if not context:
            context = {} 
        duongdan = self.pool.get('hlv.property')._get_value_project_property_by_name(cr, uid, 'path of template')
        domain = self.pool.get('hlv.property')._get_value_project_property_by_name(cr, uid, 'Domain') or '../..'
        kieufile = self.pool.get('hlv.property')._get_value_project_property_by_name(cr, uid, 'Kiểu lưu file') or 'html'
        thongtin = self.browse(cr,uid,ids[0],context)
        self.tao_mucluc(cr, uid, ids, context=context)
        
        if thongtin.url_thongtin:
            name_url = thongtin.url_thongtin
        else:
            name_url = self.pool.get('yhoc_trangchu').parser_url(str(thongtin.name))
#        link_url = thongtin.duan.link_url + '/%s'%(name_url)
        link_url = 'thongtin/%s'%(name_url)
        
        fr= open(duongdan+'/template/thongtin/thongtin.html', 'r')
        template = fr.read()
        fr.close()
        
#Tao folder cho thongtin
        folder_thongtin = duongdan + '/thongtin/%s'%(name_url)
        folder_thongtin_data = folder_thongtin + '/data/'
        if not os.path.exists(folder_thongtin):
            os.makedirs(folder_thongtin)
        if not os.path.exists(folder_thongtin_data):
            os.makedirs(folder_thongtin_data)
            
#Lay thong tin chung
        tuade_thongtin = thongtin.name
        noidung_thongtin = thongtin.noidung or '(Chưa cập nhật)'
        date = thongtin.date
        tv = thongtin.nguoidich
        if not date:
            date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        if tv:
##################################################
            template = template.replace('__TUADETHONGTIN__', tuade_thongtin)
            date_default = datetime.strptime(date, '%Y-%m-%d %H:%M:%S')
            template = template.replace('__NGAYTAO__', date_default.strftime('%d/%m/%Y %H:%M'))
            template = template.replace('__NOIDUNG_THONGTIN__', thongtin.noidung or '')
            template = template.replace('__MOTANGAN__', thongtin.motangan or '')
            
            
    #Ghi anh bai viet 
        photo = ''
        if thongtin.hinhdaidien:
            #NEWWWWWWWWWWWWWWWWWWWWW
            folder_hinh_thongtin = duongdan+'/images/thongtin'
            filename = str(thongtin.id) + '-thongtin-' + name_url
            self.ghihinhxuong(folder_hinh_thongtin, filename, thongtin.hinhdaidien, 95, 125, context=context)
            photo = domain + '/images/thongtin/%s-thongtin-%s.jpg'%(str(thongtin.id),name_url)
            
        else:
            if thongtin.duan.photo:
#                if not os.path.exists(folder_thongtin + '/images'):
#                    os.makedirs(folder_thongtin + '/images')
#                path_hinh_ghixuong = folder_thongtin + '/images' + '/anhbaiviet.jpg'
#                fw = open(path_hinh_ghixuong,'wb')
#                fw.write(base64.decodestring(thongtin.duan.photo))
#                fw.close()
#                self.resize_image(path_hinh_ghixuong, 95, 125, context=context)
                
                #NEWWWWWWWWWWWWWWWWWWWWW
                folder_hinh_thongtin = duongdan+'/images/thongtin'
                filename = str(thongtin.id) + '-thongtin-' + name_url
                self.ghihinhxuong(folder_hinh_thongtin, filename, thongtin.duan.photo, 95, 125, context=context)
                photo = domain + '/images/thongtin/%s-thongtin-%s.jpg'%(str(thongtin.id),name_url)
                
        template = template.replace('__DOMAIN__',domain)
        template = template.replace('__URL__',domain + '/%s/'%link_url)
        template = template.replace('__ITEMTYPE__','NewsArticle')
        template = template.replace('__DANHXUNGNT__',tv.danhxung or '')
        template = template.replace('__NGUOIDICH__',str(tv.name))
        if tv.google_plus_acc:
            template = template.replace('__LINKNGUOIDICH__',tv.google_plus_acc +'?rel=author')
        else:
            template = template.replace('__LINKNGUOIDICH__',tv.link or '#')
        #Giang_2011#Khi bấm nút xuất bản bài viết, không cần phải cập nhật profile trong bài viết
        #self.pool.get('hr.employee').capnhat_profiletrongtrangbaiviet(cr, uid, [tv.id], context)
        #Giang_1311#template = template.replace('__THONGTINNGUOIVIET__',duongdan + '/profile/%s/profiletrongtrangbaiviet.html' %str(tv.id))       
        template = template.replace('__THONGTINNGUOIVIET__',duongdan + '/profile/%s/profiletrongtrangbaiviet.html' %str(tv.link_url))            
        
        #Giang_1811# Author Bai viet moi
        self.capnhat_baivietmoicuatacgia(cr, uid, [tv.id], ids[0], context)
        #Giang_1811# Author box
        template = template.replace('__AUTHORBOX__',duongdan + '/profile/%s/author_box.html' %str(tv.link_url))            
        
        template = template.replace('__DUAN__', thongtin.duan.name or '')
        template = template.replace('__LINKDUAN__', domain + '/%s/'%thongtin.duan.link_url or '#')
        template = template.replace('__SOLUONGBAIVIET__', str(thongtin.duan.soluongbaiviet))
        
        template = template.replace('__NGUONBAIVIET__', thongtin.nguonbaiviet or '')
        
        nguoihd_ids = self.pool.get('hr.employee').search(cr, uid, [('id','=',thongtin.nguoihieudinh.id)], context=context)
        nguoihd = self.pool.get('hr.employee').browse(cr, uid, nguoihd_ids[0], context=context)
        template = template.replace('__NGUOIHIEUDINH__', nguoihd.name or '')
        template = template.replace('__LINKNGUOIHIEUDINH__', nguoihd.link or '#')
        template = template.replace('__DANHXUNGHD__', nguoihd.danhxung or '')


#    ####################################################################
        #Giang_0112# Cập nhật link tree trong bài viết
        self.capnhat_linktree_trongbaiviet(cr, uid, thongtin, duongdan, domain, folder_thongtin_data, context)
        
        
        
        template = template.replace('__HINHBAIVIET__', photo)
        #template = template.replace('__MOTA__', thongtin.motangan or thongtin.name)
        
        link_xemnhanh = domain + '/%s/'%link_url
        super(yhoc_thongtin,self).write(cr,uid,ids,{'link':link_xemnhanh,
                                                    'date':date,
                                                    'link_url':link_url}, context=context)
        
        self.pool.get('yhoc_duan').capnhat_baivietcungduantrongbaiviet(cr, uid, [thongtin.duan.id], context)
        template = template.replace('__BAIVIET_CUNGCHUDE__', duongdan + '/%s/baivietcungduantrongbaiviet.php' %str(thongtin.duan.link_url))
        self.pool.get('yhoc_duan').capnhat_baivietcungduantrongbaiviet_end(cr, uid, [thongtin.duan.id], context)
        template = template.replace('__BAIVIETCUNGDUAN_END__', domain + '/%s/baivietcungduantrongbaiviet_end.html' %str(thongtin.duan.link_url))
        
        cungchude = self.search(cr, uid, [('duan.id', '=',thongtin.duan.id),('state','=','done')], order='sequence', context=context)
        cungchude = self.browse(cr, uid, cungchude, context)
        path = duongdan + '/' + link_url +'/baivietcungduantrongbaiviet_end.html'
        context.update({'ten_template':'baivietmoi_tab_new'})
        self.pool.get('yhoc_trangchu').capnhat_baivietmoi(cr, uid, cungchude, path, context)
        
#Cap nhat tag        
        self.pool.get('yhoc_keyword').chenbaimoivaotag(cr, uid, thongtin.keyword_ids, thongtin.id, context=context)
        tags = thongtin.keyword_ids
        list_tag = ''
        temp_ = '''<a href="__LINKTAG__" class="HeaderTagCloud">__NAMETAG__</a>
		'''
        for t in tags:
            temp = ''
            name = self.pool.get('yhoc_trangchu').parser_url(t.name)
            temp = temp_.replace('__LINKTAG__',domain+'/tags/'+name)
            temp = temp.replace('__NAMETAG__',t.name)
            list_tag += temp
        template = template.replace('__LIST_TAGS__', list_tag)
        template = template.replace('__DUONGDAN__', duongdan)
        template = template.replace('__ID__', str(thongtin.id))
            
        
        import codecs  
        fw= codecs.open(folder_thongtin+'/index.%s'%(kieufile),'w','utf-8')
        fw.write(template)
        fw.close()

#Cap nhat bai viet moi
        trangchu_ids = self.pool.get('yhoc_trangchu').search(cr, uid, ['|',('name','=',thongtin.nguoidich.name),('id','=',1)], context=context)
        for tentrang in trangchu_ids:
            trangchu_rc = self.pool.get('yhoc_trangchu').browse(cr, uid, tentrang, context=context)
            if trangchu_rc.id == 1:
                tentrang_url = 'vi'
            else:
                tentrang_url = self.pool.get('yhoc_trangchu').parser_url(str(trangchu_rc.name))
            path = duongdan + '/trangchu/%s/baivietmoi.html'%tentrang_url
            self.pool.get('yhoc_trangchu').capnhat_baivietmoi(cr, uid, trangchu_rc.baivietmoi,path, context)
            
        self.pool.get('yhoc_duan').capnhat_thongtin(cr,uid,[thongtin.duan.id],context)
#        self.pool.get('yhoc_chude').capnhat_thongtin(cr,uid,[thongtin.duan.chude_id.id],context)
        self.capnhat_baiviettrongprofile(cr, uid, [thongtin.nguoidich.id], context)
        
#Giang_2411# Cap nhat share button
        self.capnhat_sharebutton(cr, uid, thongtin.id, context=context)
#Tao trang Blog
        self.taotrangblog(cr, uid, context)
        
#cap nhat tong hieu dinh va tong dong gop
#        self.capnhat_tonghieudinh_donggop(cr, uid, [tv.id], context)

        return template,duongdan,domain

    def del_post_fb(self,cr,uid,ids, context=None):
        duongdan = self.pool.get('hlv.property')._get_value_project_property_by_name(cr, uid, 'path of template')
        FACEBOOK_PROFILE_ID = '525884304122872'
        access_token_page = self.pool.get('hlv.property')._get_value_project_property_by_name(cr, uid, 'access_token_page_fb') or '/'
        for bv in self.browse(cr,uid,ids, context=None):
            if bv.fb_post_id and access_token_page != '/':
                graph = facebook.GraphAPI(str(access_token_page))
                graph.delete_request(FACEBOOK_PROFILE_ID,bv.fb_post_id)
                super(yhoc_profile_thongtin,self).write(cr,uid,ids,{'is_post_fb':False,'fb_post_id':''}, context=context)
        return True
    
    def post_fb(self,cr,uid,ids, context=None):
        import urllib 
        import urlparse
        
        domain = self.pool.get('hlv.property')._get_value_project_property_by_name(cr, uid, 'Domain') or '../..'
        duongdan = self.pool.get('hlv.property')._get_value_project_property_by_name(cr, uid, 'path of template')
        access_token_page = self.pool.get('hlv.property')._get_value_project_property_by_name(cr, uid, 'access_token_page_fb') or '/'
        
        #access_token_page='AAAHxBEJZAaGQBAJ7E2YZB40gVnwfTaZAGL20ZAwC2iuutlRrD9O632wBjZBHRXWrQhbvyDi7KZAeZC4asbyvVLDF8ZC3pxMGWsUQiFKmDQdTuRHqBkcvcfYStAenGWLUU2AZD'

        #Giang_1911#local# for bv in self.browse(cr,uid,ids, context=None):
		#Giang_2011# Chỉnh sửa theo lúc lấy từ Server
        bv = self.browse(cr,uid,ids[0], context=None)
        
        if bv.state != 'done':
            raise osv.except_osv(('Message'), ('Chưa thể đăng 1 bài viết lên facebook khi chưa xuất bản lên website!'))
        if bv.state == 'done' and access_token_page != '/':
            

#                FACEBOOK_APP_ID = '546475572029540'
#                FACEBOOK_APP_SECRET = 'dcf0e2796a6577732d5c5f60978579e2'

            FACEBOOK_PROFILE_ID = '525884304122872'
            #FACEBOOK_PROFILE_ID = '100002499548724'
            
#                oauth_args = dict(client_id     = FACEBOOK_APP_ID,
#                                  client_secret = FACEBOOK_APP_SECRET,
#                                  grant_type    = 'client_credentials')
#                oauth_response = urllib.urlopen('https://graph.facebook.com/oauth/access_token?' + urllib.urlencode(oauth_args)).read()
            access_token_app = facebook.get_app_access_token('546475572029540', 'dcf0e2796a6577732d5c5f60978579e2')
            graph = facebook.GraphAPI(str(access_token_page))
			########################################################
            accounts = graph.get_connections("100002499548724", "accounts")
            for acc in accounts['data']:
            	if acc['id'] == '525884304122872':
            		graph = facebook.GraphAPI(str(acc['access_token']))
            		print access_token_page
            		print acc['access_token']
            ############################################################
            name = bv.name
            name_url = self.pool.get('yhoc_trangchu').parser_url(str(bv.name))
            link = bv.link
            picture = domain + '/images/thongtin/%s-thongtin-%s.jpg'%(str(bv.id),name_url)
            
            if not os.path.exists(duongdan+'/images/thongtin/%s-thongtin-%s.jpg'%(str(bv.id),name_url)):
            	if bv.hinhdaidien:
            		folder_hinh_thongtin = duongdan+'/images/thongtin'
            		filename = str(bv.id) + '-thongtin-' + name_url
            		self.pool.get('yhoc_thongtin').ghihinhxuong(folder_hinh_thongtin, filename, bv.hinhdaidien, 95, 125, context=context)
            
            description = bv.motangan or '(Chưa cập nhật mô tả)'
            attach = {
              "name": name,
              "link": link,
              "description": description,
              "picture" : picture,
              "page_token" : str(access_token_page)
            }
            msg = name
            post = graph.put_wall_post(message=msg, attachment=attach,profile_id=FACEBOOK_PROFILE_ID)
            post_id = post['id'].replace(FACEBOOK_PROFILE_ID+'_','')
            super(yhoc_thongtin,self).write(cr,uid,ids,{'is_post_fb':True,'fb_post_id':post_id}, context=context)

        return True
    
    def auto_tags(self,cr, uid, ids, context=None):
        thongtin = self.browse(cr, uid, ids[0], context=context)
        cur_key = thongtin.keyword_ids
        kq = []
        for k in cur_key:
            kq.append(k.id)
        noidung = thongtin.noidung
        noidung = noidung.lower()
        tags = self.pool.get('yhoc_keyword').search(cr, uid, [], order='priority desc', context=context)
        
        list = {}
        for t in tags:
            t = self.pool.get('yhoc_keyword').browse(cr, uid, t, context=context)
            find = noidung.count((t.name).lower())
            
            if find > 0:
                list.update({t.id: find})
        list_tags = sorted(list, key=list.get, reverse=True)
#        if len(list_tags)>9:        
#            for i in range(0,9):
#                if list_tags[i] not in kq:
#                    kq.append(list_tags[i])
#        else:
        kq = list_tags
        
        bs_tag = self.pool.get('yhoc_keyword').search(cr, uid, [('name','=',thongtin.nguoidich.name)],context=context)
        if bs_tag and bs_tag[0] not in kq:
            kq.append(bs_tag[0])
        elif not bs_tag:
            bs_tag = self.pool.get('yhoc_keyword').create(cr, uid, {'name':thongtin.nguoidich.name}, context=context)
            if bs_tag not in kq:
                kq.append(bs_tag)
        
        hd_tag = self.pool.get('yhoc_keyword').search(cr, uid, [('name','=',thongtin.nguoihieudinh.name)],context=context)
        if hd_tag and hd_tag[0] not in kq:
            kq.append(hd_tag[0])
        elif not hd_tag:
            #Giang_0511#nguoidich->nguoihieudinh
            hd_tag = self.pool.get('yhoc_keyword').create(cr, uid, {'name':thongtin.nguoihieudinh.name}, context=context)
            if hd_tag not in kq:
                kq.append(hd_tag)
        
        duan_tag = self.pool.get('yhoc_keyword').search(cr, uid, [('name','=',thongtin.duan.name)],context=context)
        if duan_tag and duan_tag[0] not in kq:
            kq.append(duan_tag[0])
        elif not duan_tag:
            duan_tag = self.pool.get('yhoc_keyword').create(cr, uid, {'name':thongtin.duan.name}, context=context)
            if duan_tag not in kq:
                kq.append(duan_tag)
        
        list_chude = self.pool.get('yhoc_chude').get_tree_obj(cr, uid, thongtin.duan.chude_id)
        for cd in list_chude:
            cd_tag = self.pool.get('yhoc_keyword').search(cr, uid, [('name','=',cd.name)],context=context)
            if cd_tag and cd_tag[0] not in kq:
                kq.append(cd_tag[0])
            elif not cd_tag:
                cd_tag = self.pool.get('yhoc_keyword').create(cr, uid, {'name':cd.name}, context=context)
                if cd_tag not in kq:
                    kq.append(cd_tag)
        ok = False
        if kq:
#             ok = super(yhoc_thongtin,self).write(cr, uid, ids, {'keyword_ids': [[6, False, kq]]}, context=context)
             ok = super(yhoc_thongtin,self).write(cr, uid, ids, {'keyword_ids': [[6, False, kq]]}, context=context)
        return ok
     #{'keyword_ids': [[6, False, [243, 382, 785, 799, 846, 878, 922, 924, 923]]]}
     
#Giang_2411# Cap nhat share button cua bai viet
    def capnhat_sharebutton(self, cr, uid, ids, context=None):
        duongdan = self.pool.get('hlv.property')._get_value_project_property_by_name(cr, uid, 'path of template')
        domain = self.pool.get('hlv.property')._get_value_project_property_by_name(cr, uid, 'Domain') or '../..'
        bv = self.browse(cr,uid,ids)
        if os.path.exists(duongdan+'/template/thongtin/share_button16.html'):
            fr = open(duongdan+'/template/thongtin/share_button16.html', 'r')
            template_ = fr.read()
            fr.close()
        else:
            template_ = ''
        template = template_.replace('__DOMAIN__', domain)
        template = template.replace('__URL__', domain + '/%s/'%bv.link_url)
        template = template.replace('__TITTLE__', bv.name)
        import codecs  
        fw = codecs.open(duongdan + '/%s/share_button16.html'%bv.link_url,'w','utf-8')
        fw.write(template)
        fw.close()
		
        if os.path.exists(duongdan+'/template/thongtin/share_button32.html'):
            fr = open(duongdan+'/template/thongtin/share_button32.html', 'r')
            template_ = fr.read()
            fr.close()
        else:
            template_ = ''
        template = template_.replace('__DOMAIN__', domain)
        template = template.replace('__URL__', domain + '/%s/'%bv.link_url)
        template = template.replace('__TITTLE__', bv.name)
        fw = codecs.open(duongdan + '/%s/share_button32.html'%bv.link_url,'w','utf-8')
        fw.write(template)
        fw.close()     
        return True
    
    def taotrangblog(self,cr,uid,context=None):
        dsbaivietmoi = self.pool.get('yhoc_thongtin').search(cr, uid, [('state','=','done')], limit=15, order='date desc', context=context)
        duongdan = self.pool.get('hlv.property')._get_value_project_property_by_name(cr, uid, 'path of template')
        domain = self.pool.get('hlv.property')._get_value_project_property_by_name(cr, uid, 'Domain') or '../..'
        kieufile = self.pool.get('hlv.property')._get_value_project_property_by_name(cr, uid, 'Kiểu lưu file') or 'html'
        
        folder_tags = duongdan + '/blog'
        if not os.path.exists(folder_tags):
            os.makedirs(folder_tags)
                
        if os.path.exists(duongdan+'/template/blog/index.html'):
            fr = open(duongdan+'/template/blog/index.html', 'r')
            template_ = fr.read()
            fr.close()
        else:
            template_ = ''
            
        if os.path.exists(duongdan+'/template/blog/blog_item.html'):
            fr = open(duongdan+'/template/blog/blog_item.html', 'r')
            item_ = fr.read()
            fr.close()
        else:
            item_ = ''
            
        all_item_ = ''    
        
        for t in dsbaivietmoi:  
            thongtin = self.pool.get('yhoc_thongtin').browse(cr, uid, t, context=context)

            item = item_.replace('__NGUOIHIEUDINH__', thongtin.nguoihieudinh.name or '')
            item = item.replace('__LINKNGUOIHIEUDINH__', thongtin.nguoihieudinh.link or '#')
            item = item.replace('__DANHXUNGHD__', thongtin.nguoihieudinh.danhxung or '')
            
            item = item.replace('__DANHXUNGNT__',thongtin.nguoidich.danhxung or '')
            item = item.replace('__NGUOIDICH__',thongtin.nguoidich.name)
            item = item.replace('__LINKNGUOIDICH__',thongtin.nguoidich.link or '#')
            
            item = item.replace('__NAME__',thongtin.name or '')
            item = item.replace('__NGAYTAO__',thongtin.date)
            item = item.replace('__MOTANGAN__',thongtin.motangan or '(Chưa cập nhật)')
            item = item.replace('__LINK__',domain + '/%s'%(thongtin.link_url))
            #Giang_2411# Them share button vao blog
            item = item.replace('__SHAREBUTTON__',duongdan + '/%s/share_button16.html'%(thongtin.link_url))
            item = item.replace('__SOLUOTXEM__',str(thongtin.soluongxem))
            date_default = datetime.strptime(thongtin.date, '%Y-%m-%d %H:%M:%S')
            item = item.replace('__DAY__', date_default.strftime('%d'))
            item = item.replace('__MONTH__','T' + date_default.strftime('%m'))
            item = item.replace('__YEAR__',date_default.strftime('%Y'))
            if thongtin.url_thongtin:
                name_url = thongtin.url_thongtin
            else:
                name_url = self.pool.get('yhoc_trangchu').parser_url(str(thongtin.name))
            #Giang_0511#
            item = item.replace('__IMAGE__',domain + '/images/thongtin/%s-thongtin-%s.jpg'%(str(thongtin.id),name_url))                
            all_item_ += item

        template = template_.replace('__DUONGDAN__', duongdan)
        template = template.replace('__DOMAIN__', domain)
        template = template.replace('__ITEMTYPE__', 'WebPage')
        template = template.replace('__BLOGNAME__', 'SỨC KHỎE MỖI NGÀY')



        template = template.replace('__SIDEBARMENU__', '''<?php include("%s/trangchu/vi/baivietnoibac.html")?>'''%duongdan)
        template = template.replace('__CHUDENOIBAC__', '''<?php include("%s/trangchu/vi/duanhoanthanh.html")?>'''%duongdan)
        template = template.replace('__BLOG_ITEMS__', all_item_)
        import codecs  




        fw = codecs.open(folder_tags +'/index.%s'%kieufile,'w','utf-8')
        fw.write(template)
        fw.close()
        return True


    def tao_mucluc(self, cr, uid, ids, context=None):
#        self.replace_tukhoa(cr, uid, ids, context=context)
        duongdan = self.pool.get('hlv.property')._get_value_project_property_by_name(cr, uid, 'path of template')
        domain = self.pool.get('hlv.property')._get_value_project_property_by_name(cr, uid, 'Domain') or '../..'
        kieufile = self.pool.get('hlv.property')._get_value_project_property_by_name(cr, uid, 'Kiểu lưu file') or 'html'
        thongtin = self.browse(cr,uid,ids[0],context)
        
        if thongtin.url_thongtin:
            name_url_thongtin = thongtin.url_thongtin
        else:
            name_url_thongtin = self.pool.get('yhoc_trangchu').parser_url(str(thongtin.name))
        noidung = thongtin.noidung
        
        if os.path.exists(duongdan+'/template/thongtin/menu.html'):
            fr = open(duongdan+'/template/thongtin/menu.html', 'r')
            template_ = fr.read()
            fr.close()
        else:
            template_ = ''
        
        temp_ = '''<li><a href="__LINK__"><span>__STT__. </span><span>__NAME__</span></a></li>'''
        
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(noidung)        
        #print(soup.prettify())
        all_h2 = soup.find_all("h2")
#        a['id']='abc'
        menu = ''
        STT = 1
        link = domain + '/thongtin/'+name_url_thongtin
        for tag in all_h2:
            temp = ''
            name_url = ''
            name =''
            if tag.string:
                name = tag.string
                name = name.strip()
                name_url = self.pool.get('yhoc_trangchu').parser_url(tag.string)
            strong = tag.find_all('strong')
            for i in strong:
                if i.string:
                    name = i.string
                    name_url = self.pool.get('yhoc_trangchu').parser_url(i.string)
                    break
            span = tag.find_all('span')
            for i in span:
                if i.string:
                    name = i.string
                    name_url = self.pool.get('yhoc_trangchu').parser_url(i.string)
                    break
#                        name_url = self.pool.get('yhoc_trangchu').parser_url(c.string)
            temp = temp_.replace('__LINK__', link + '/#' + name_url)
            temp = temp.replace('__NAME__', str(name))
            temp = temp.replace('__STT__', str(STT))
            STT +=1
            menu += temp
            kw = self.pool.get('yhoc_keyword').search(cr, uid, ['|',('name','=',name),('khongdau','=',name_url)],context=context)
            if not kw:
                vals = {
                        'name':name,
                        'khongdau':name_url,
                        'loai_tukhoa':'theh2',
                        }
                self.pool.get('yhoc_keyword').create(cr, uid, vals, context=context)
            tag['id'] = name_url
        template_ = template_.replace('__MENU_ITEM__', menu)
        
        if not os.path.exists(duongdan +'/thongtin/%s'%name_url_thongtin):
            os.makedirs(duongdan +'/thongtin/%s'%name_url_thongtin)
            
        import codecs  
        fw = codecs.open(duongdan +'/thongtin/%s/menu.html'%name_url_thongtin,'w','utf-8')
        fw.write(template_)
        fw.close()
#        print(soup.prettify())
#        menu += soup.prettify()
        vals = {'noidung':soup.prettify()}
        self.write(cr, uid, ids, vals, context=context)
#        self.xuatban_thongtin(cr, uid, ids, context=context)
        return True
    
    def replace_tukhoa(self, cr, uid, ids, context=None):
        '''Hàm này dùng để thay thế các từ trong bài viết thành các đường link trỏ tới trang tags (giống wikipedia)'''
        duongdan = self.pool.get('hlv.property')._get_value_project_property_by_name(cr, uid, 'path of template')
        domain = self.pool.get('hlv.property')._get_value_project_property_by_name(cr, uid, 'Domain') or '../..'
        kieufile = self.pool.get('hlv.property')._get_value_project_property_by_name(cr, uid, 'Kiểu lưu file') or 'html'
        thongtin = self.browse(cr,uid,ids[0],context)
        noidung = thongtin.noidung
        
        keys = self.pool.get('yhoc_keyword').search(cr, uid, [('loai_tukhoa','=',False)], context=context)
        list = []
        i = 0
        for record in keys:
            i=i+1
            record = self.pool.get('yhoc_keyword').browse(cr, uid, record, context=context)
            dp_1 = self.pool.get('yhoc_keyword').search(cr,uid,[('name','ilike','%'+record.name+'%'),('name','!=',record.name)])
            if dp_1:
                for rc in dp_1:
                    i=i+1
                    rc = self.pool.get('yhoc_keyword').browse(cr, uid, rc, context=context)
                    find = noidung.count(rc.name)
                    if find:
                        noidung = noidung.replace(rc.name,'__K_%s__'%i)
                        list.append({'id':'__K_%s__'%i,'key':rc.name})
            else:
                find = noidung.count(record.name)
                if find:
                    noidung = noidung.replace(record.name,'__K_%s__'%i)
                    list.append({'id':'__K_%s__'%i,'key':record.name})
#                noidung = noidung.lower()
#                find = noidung.count((t.name).lower())
        for l in list:
            key = self.pool.get('yhoc_keyword').search(cr,uid,[('name','=',l['key'])], context=context)
            if key:
                tt = self.search(cr, uid, [('keyword_ids','=',key[0])], context=context)
                key = self.pool.get('yhoc_keyword').browse(cr,uid,key[0],context=context)
                name = self.pool.get('yhoc_trangchu').parser_url(key.name)
                if tt:
                    noidung = noidung.replace(l['id'],'<a href="%s/tags/%s">%s</a>'%(domain,name,key.name))
                else:
                    noidung = noidung.replace(l['id'],key.name)
        vals = {'noidung':noidung}
        self.write(cr, uid, ids, vals, context=context)
        return True

    def capnhattukhoachinhchobaiviet(self, cr, uid, ids, context=None):
        '''Hàm này dùng để cập nhật từ khóa chính của bài viết vào danh sách các từ khóa, tránh sai sot link trong dự án'''
        kq = []
        thongtin = self.browse(cr, uid, ids[0], context=context)
        if thongtin.main_key and thongtin.main_key not in thongtin.keyword_ids:
            for k in thongtin.keyword_ids:
                kq.append(k.id)
            kq.append(thongtin.main_key.id)
        vals = {'keyword_ids': [[6, False, list(set(kq))]]}
        self.write(cr, uid, ids, vals, context=context)
        return True

    def capnhat_linktree_trongbaiviet(self, cr, uid, thongtin, duongdan, domain, folder_thongtin_data, context=None):
        if os.path.exists(duongdan+'/template/thongtin/linktree.html'):
            fr = open(duongdan+'/template/thongtin/linktree.html', 'r')
            template_ = fr.read()
            fr.close()
        else:
            template_ = ''
            
        if os.path.exists(duongdan+'/template/thongtin/linktree_item.html'):
            fr = open(duongdan+'/template/thongtin/linktree_item.html', 'r')
            item_ = fr.read()
            fr.close()
        else:
            item_ = ''
            
        all_item_=''
        item = item_.replace('__LINK__', domain)
        item = item.replace('__NAME__', 'Trang chủ')
        all_item_ += item

        linktree = []
        treechude = []
        treechude = self.pool.get('yhoc_chude').dequy(treechude, thongtin.duan.chude_id)
        treechude.insert(0,thongtin.duan.chude_id)
        for i in range(len(treechude)):
            item = item_.replace('__LINK__', domain + '/%s/'%(treechude[len(treechude)-i-1].link_url))
            item = item.replace('__NAME__', treechude[len(treechude)-i-1].name)
            linktree.append(item)
            all_item_ += item
        item = item_.replace('__LINK__', thongtin.duan.link or '#')
        item = item.replace('__NAME__', thongtin.duan.name)
        linktree.append(item)
        all_item_ += item
        res = ''
        res = " > ".join(linktree)
        super(yhoc_thongtin,self).write(cr,uid,[thongtin.id],{'link_tree':res}, context=context)
        template = template_.replace('__LINKTREEITEM__', all_item_)

        import codecs  
        fw= codecs.open(folder_thongtin_data + 'linktree.html','w','utf-8')
        fw.write(template)
        fw.close()
        return True


yhoc_thongtin()


class yhoc_attachment(osv.osv):
    _inherit = 'yhoc.attachment'
    
    _columns = {
                'baiviet_id':fields.many2one('yhoc_thongtin','Bài viết'),
    }
    
yhoc_attachment()

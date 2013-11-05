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
    _order = 'sequence'
    
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
                'date': fields.datetime('NgÀY ĐĂNG'),
                'create_uid':fields.many2one('res.users','Người tạo'),
                'sequence':fields.integer('Thứ tự hiện (Sequence)'),#Thứ tự hiện
                'link':fields.char('Link thông tin',size=500),
                'duan':fields.many2one('yhoc_duan', 'Dự án'),
                'nguonbaiviet': fields.char('Nguồn bài viết', size=200),
                'link_tree':fields.char('Link tree',size=1000),
                'nguoihieudinh':fields.many2one('hr.employee', 'Người hiệu đính', required="1"),
#                'help': fields.function(_get_help_information, method=True, string='Help', type="text"),
                'comment': fields.one2many('yhoc_comment', 'baiviet_id', 'Commnents'),
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
        if 'url_thongtin' not in vals:
            name_url = self.pool.get('yhoc_trangchu').parser_url(str(thongtin.name))
            vals.update({'url_thongtin':name_url})
        return super(yhoc_thongtin,self).create(cr,uid,vals,context=context)
    
    def write(self,cr, uid, ids, vals, context=None):
#        print vals
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
            baiviet_tab = baiviet_tab.replace('__LINK1__', '../../../../../../%s'%(bv.link_url))
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
        if not os.path.exists(folder_thongtin):
            os.makedirs(folder_thongtin)
            
#        folder_thongtin = duongdan+'/thongtin/%s'%(thongtin.id)
#        if not os.path.exists(folder_thongtin):
#            os.makedirs(folder_thongtin)
            
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
            template = template.replace('__NGAYTAO__', date)
            template = template.replace('__NOIDUNG_THONGTIN__', thongtin.noidung or '')
            
    #Cập nhật tittle       
            fr = open(duongdan + '/template/trangchu/tittle.html', 'r')
            noidung_tittle = fr.read()
            fr.close()
            noidung_tittle = noidung_tittle.replace('__TITLE__',thongtin.name)
            template = template.replace('__TITLE__',noidung_tittle)
            template = template.replace('__TITLE_BV__',thongtin.name)
            
    #Ghi anh bai viet 
        photo = ''
        if thongtin.hinhdaidien:
#            folder_thongtin = duongdan+'/thongtin/%s'%(thongtin.id)
#            if not os.path.exists(folder_thongtin + '/images'):
#                os.makedirs(folder_thongtin + '/images')
#            path_hinh_ghixuong = folder_thongtin + '/images' + '/anhbaiviet.jpg'
#            fw = open(path_hinh_ghixuong,'wb')
#            fw.write(base64.decodestring(thongtin.hinhdaidien))
#            fw.close()
#            self.resize_image(path_hinh_ghixuong, 95, 125, context=context)
            
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
                
    #Cap nhat thong tin nguoi viet
#            photo = ''
#            if tv.image:
#                if not os.path.exists(folder_thongtin + '/images'):
#                    os.makedirs(folder_thongtin + '/images')
#                path_hinh_ghixuong = folder_thongtin + '/images/anhprofile.jpg'
#                fw = open(path_hinh_ghixuong,'wb')
#                fw.write(base64.decodestring(tv.image))
#                fw.close()
#                photo = 'images/anhprofile.jpg'
#        
#            template = template.replace('__HINHNGUOIDICH__', photo)
#            
#            capbac = tv.capbac or ''
#            trinhdo = self.pool.get('hlv.property')._get_value_project_property_by_name(cr, uid, 'Trình độ chuyên môn') or '[]'
#            chuyenmon = ''
#            for r in eval(trinhdo):
#                if r[0] == capbac:
#                    chuyenmon = r[1]
#                    break
#            template = template.replace('__TRINHDOCHUYENMON__',chuyenmon)
#            template = template.replace('__DANHXUNGNT__',tv.danhxung or '')
#            template = template.replace('__NGANH__',(tv.nganh and tv.nganh.name) or '')
#            if tv.nganh and tv.chuyennganh:
#                template = template.replace('__CHUYENNGANH__',' - ' + tv.chuyennganh or '')
#            else:
#                template = template.replace('__CHUYENNGANH__',tv.chuyennganh or '')
        template = template.replace('__DANHXUNGNT__',tv.danhxung or '')
        template = template.replace('__NGUOIDICH__',tv.name)
        if tv.google_plus_acc:
            template = template.replace('__LINKNGUOIDICH__',tv.google_plus_acc +'?rel=author')
        else:
            template = template.replace('__LINKNGUOIDICH__',tv.link or '#')
        
        self.pool.get('hr.employee').capnhat_profiletrongtrangbaiviet(cr, uid, [tv.id], context)             
        template = template.replace('__THONGTINNGUOIVIET__',duongdan + '/profile/%s/profiletrongtrangbaiviet.html' %str(tv.id))            
        
        template = template.replace('__CHUDE__', thongtin.duan.name or '') 
        
        template = template.replace('__NGUONBAIVIET__', thongtin.nguonbaiviet or '')
        
        nguoihd_ids = self.pool.get('hr.employee').search(cr, uid, [('id','=',thongtin.nguoihieudinh.id)], context=context)
        nguoihd = self.pool.get('hr.employee').browse(cr, uid, nguoihd_ids[0], context=context)
        template = template.replace('__NGUOIHIEUDINH__', nguoihd.name or '')
        template = template.replace('__LINKNGUOIHIEUDINH__', nguoihd.link or '#')
        template = template.replace('__DANHXUNGHD__', nguoihd.danhxung or '')


#    ####################################################################
        temp_ = '''<a href="__LINK__">__NAME__</a>'''
        linktree = []
        res = ''
        treechude = []
        treechude = self.pool.get('yhoc_chude').dequy(treechude, thongtin.duan.chude_id)
        treechude.insert(0,thongtin.duan.chude_id)
        
        for i in range(len(treechude)):
            temp = temp_.replace('__LINK__', treechude[len(treechude)-i-1].link or '#')
            temp = temp.replace('__NAME__', treechude[len(treechude)-i-1].name)
            linktree.append(temp)
        #Giang_0511#linktree.insert(0,'''<a href="../../../../../../trangchu/vi/">Trang chủ</a>''')
        linktree.insert(0,'''<a href="http://yhoccongdong.com">Trang chủ</a>''')
        temp = temp_.replace('__LINK__', thongtin.duan.link or '#')
        temp = temp.replace('__NAME__', thongtin.duan.name)
        linktree.append(temp)
        
#        temp = temp_.replace('__LINK__', thongtin.link or '#')
#        temp = temp.replace('__NAME__', thongtin.name)
#        linktree.append(temp)
            
        res = " > ".join(linktree)
#            context.update({'from_update':True})
        self.write(cr,uid,[thongtin.id],{'link_tree':res}, context=context)
        
        template = template.replace('__LINKTREE__', res)
        template = template.replace('__HINHBAIVIET__', photo)
        template = template.replace('__MOTA__', thongtin.motangan or thongtin.name)
        
        link_xemnhanh = domain + '/' + link_url
        super(yhoc_thongtin,self).write(cr,uid,ids,{'link':link_xemnhanh,
                                                    'date':date,
                                                    'link_url':link_url}, context=context)
        
#Lấy thông tin cùng du an:
#            cungchude = self.search(cr, uid, [('duan.id', '=',thongtin.duan.id)], order='sequence', context=context)
#            cungchude_tab_ = '''<li><a href="__LINKBAIVIET__">__TENBAIVIET__</a></li>'''
#            all_cungchude = '' 
#            for ccd in cungchude:
#                ccdr = self.browse(cr, uid, ccd, context=context)
#                cungchude_tab = cungchude_tab_.replace('__LINKBAIVIET__', ccdr.link or '#')
#                cungchude_tab = cungchude_tab.replace('__TENBAIVIET__', ccdr.name)
#                all_cungchude += cungchude_tab
#
        self.pool.get('yhoc_duan').capnhat_baivietcungduantrongbaiviet(cr, uid, [thongtin.duan.id], context)
        template = template.replace('__BAIVIET_CUNGCHUDE__', duongdan + '/%s/baivietcungduantrongbaiviet.php' %str(thongtin.duan.link_url))
        
        cungchude = self.search(cr, uid, [('duan.id', '=',thongtin.duan.id),('state','=','done')], order='sequence', context=context)
        cungchude = self.browse(cr, uid, cungchude, context)
        path = duongdan + '/' + link_url +'/baivietcungduantrongbaiviet_end.html'
        self.pool.get('yhoc_trangchu').capnhat_baivietmoi(cr, uid, cungchude, path, context)
        
#Cap nhat tag        
        self.pool.get('yhoc_keyword').capnhat_tag(cr, uid, thongtin.keyword_ids, thongtin.id, context=context)
        tags = thongtin.keyword_ids
        list_tag = ''
        temp_ = '''<a href="__LINKTAG__"><span style="font-size:14px;">__NAMETAG__</span></a>,&nbsp;'''
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
        trangchu_ids = self.pool.get('yhoc_trangchu').search(cr, uid, [], context=context)
        trangchu_rc = self.pool.get('yhoc_trangchu').browse(cr, uid, trangchu_ids[0], context=context)
        path = duongdan + '/trangchu/vi/baivietmoi.html'
        self.pool.get('yhoc_trangchu').capnhat_baivietmoi(cr, uid, trangchu_rc.baivietmoi,path, context)
            
        self.pool.get('yhoc_duan').capnhat_thongtin(cr,uid,[thongtin.duan.id],context)
        self.capnhat_baiviettrongprofile(cr, uid, [thongtin.nguoidich.id], context)
        
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
        for bv in self.browse(cr,uid,ids, context=None):
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
#                folder_thongtin = duongdan+'/chude/%s'%(bv.link_url,)
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
        noidung = thongtin.noidung
        noidung = noidung.lower()
        tags = self.pool.get('yhoc_keyword').search(cr, uid, [], order='priority desc', context=context)
        kq = []
        list = {}
        for t in tags:
            t = self.pool.get('yhoc_keyword').browse(cr, uid, t, context=context)
            find = noidung.count((t.name).lower())
            
            if find > 0:
                list.update({t.id: find})
        list_tags = sorted(list, key=list.get, reverse=True)
        if len(list_tags)>9:        
            for i in range(0,9):
                kq.append(list_tags[i])
        else:
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
            
        tag_item_ = ''    
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
            if thongtin.url_thongtin:
                name_url = thongtin.url_thongtin
            else:
                name_url = self.pool.get('yhoc_trangchu').parser_url(str(thongtin.name))
            #Giang_0511#
            item = item.replace('__IMAGE__',domain + '/images/thongtin/%s-thongtin-%s.jpg'%(str(thongtin.id),name_url))                
            tag_item_ += item

            
            
        template = template_.replace('__TAGNAME__', 'Các bài viết mới')
        template = template.replace('__SIDEBARMENU__', '''<?php include("../trangchu/vi/baivietnoibac.html")?>''')
        template = template.replace('__CHUDENOIBAC__', '''<?php include("../trangchu/vi/duanhoanthanh.html")?>''')
        import codecs  
        fw = codecs.open(folder_tags +'/tag_item.html','w','utf-8')
        fw.write(tag_item_)
        fw.close()
        
        fw = codecs.open(folder_tags +'/index.%s'%kieufile,'w','utf-8')
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

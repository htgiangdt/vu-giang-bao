# -*- encoding: utf-8 -*-
from osv import fields,osv
from tools.translate import _
import time
from datetime import datetime, date
import base64,os,re


class yhoc_duan(osv.osv):

    _name = "yhoc_duan"    
    
    def _kiemtra_hoanthanh(self, cr, uid, ids, name, args, context=None):
        result = {}
        for r in ids:
            duan_all = self.pool.get('yhoc_thongtin').search(cr, uid, [('duan.id', '=',r)], context=context)
            duan_done = self.pool.get('yhoc_thongtin').search(cr, uid, [('duan.id', '=',r),('state','=','done')], context=context)
            result[r] = False
            if len(duan_all) == len(duan_done):
                result[r] = True
        return result
    
    def _get_tilehoanthanh(self, cr, uid, ids, name, args, context=None):
        result = {}
        for r in ids:
            duan_all = self.pool.get('yhoc_thongtin').search(cr, uid, [('duan.id', '=',r)], context=context)
            duan_done = self.pool.get('yhoc_thongtin').search(cr, uid, [('duan.id', '=',r),('state','=','done')], context=context)
            result[r] = 0
            if len(duan_all) == len(duan_done):
                result[r] = 100
            else:
                print len(duan_done)
                print len(duan_all)
                print (len(duan_done)*100)/len(duan_all)
                result[r] = (len(duan_done)*100)/len(duan_all)
        return result
    
    def _get_duan_id(self, cr, uid, ids, context=None):
        result = {}
        for line in self.pool.get('yhoc_thongtin').browse(cr, uid, ids, context=context):
            result[line.duan.id] = True
        return result.keys()
    

    
    _columns = {
                'name':fields.char('Tên dự án',size=500,required='1'),
                'description':fields.text('Giới thiệu'),
                'link':fields.char('Link dự án',size=1000),
                'chude_id': fields.many2one('yhoc_chude','Chủ đề'),
                'photo': fields.binary('Hình',filters='*.png,*.gif,*.jpg'),
                'link_tree':fields.char('Link tree',size=1000),
                'sequence': fields.integer('Thứ tự'),
                'truongduan':fields.many2one('hr.employee', 'Trưởng dự án',required='1'),
                'thanhvienthamgia':fields.one2many('hlv_vaitro', 'duan_id', string='Thành viên tham gia'),
                'thongtin':fields.one2many('yhoc_thongtin', 'duan', string='Bài viết'),
                'soluongxem': fields.integer("Số lượng người xem"),
                'is_done': fields.function(_kiemtra_hoanthanh, method=True, string='Is Done', type="boolean", store={
                                                        'yhoc_duan':(lambda self, cr, uid, ids, c={}: ids,['thongtin'],10),
                                                        'yhoc_thongtin': (_get_duan_id,['duan'], 10),}),
                'tilehoanthanh': fields.function(_get_tilehoanthanh, type='integer', string='Tỉ lệ hoàn thành', store={
                                                        'yhoc_duan':(lambda self, cr, uid, ids, c={}: ids,['thongtin'],10),
                                                        'yhoc_thongtin': (_get_duan_id,['duan'], 10),}),
                'link_url':fields.char('Link url',size=1000),
                'keyword_ids': fields.many2many('yhoc_keyword', 'duan_keyword_rel', 'duan_id', 'keyword_id', 'Keyword'),
                'main_key':fields.many2one('yhoc_keyword', 'Từ khóa chính'),
                'soluongbaiviet':fields.integer("Số lượng bài viết"),
                }
                
    
    _defaults = {
                 'is_done':False
                 }
    
    def capnhat_duantrongprofile(self, cr, uid, nhanvien_ids, context=None):
        duongdan = self.pool.get('hlv.property')._get_value_project_property_by_name(cr, uid, 'path of template')
        domain = self.pool.get('hlv.property')._get_value_project_property_by_name(cr, uid, 'Domain') or '../..'
        kieufile = self.pool.get('hlv.property')._get_value_project_property_by_name(cr, uid, 'Kiểu lưu file') or 'html'
        nhanvien = self.pool.get('hr.employee').browse(cr, uid, nhanvien_ids[0], context=context)
        duan = nhanvien.duan
        folder_profile = duongdan + '/profile/%s' %nhanvien.link_url
        if not os.path.exists(folder_profile):
            os.makedirs(folder_profile)
        noidung_duan = ''
        if os.path.exists(duongdan+'/template/profile/table_link_tab.html'):
            fr = open(duongdan+'/template/profile/table_link_tab.html', 'r')
            duan_tab_ = fr.read()
            fr.close()
        else:
            duan_tab_ = ''
                    
        for da in duan:
            duan_tab =''
            for m in da.thanhvienthamgia:
                if m.nhanvien.id == nhanvien.id:
                    duan_tab = duan_tab_.replace('__LINK__', domain + '/%s/'%(da.link_url))
                    duan_tab = duan_tab.replace('__COL1__', da.name)
                    duan_tab = duan_tab.replace('__COL2__', m.name)
            noidung_duan += duan_tab
        
        import codecs  
        fw= codecs.open(folder_profile+'/duantrongprofile.html','w','utf-8')
        fw.write(noidung_duan)
        fw.close()              
        return True
    
    
    def capnhat_baivietcungduantrongbaiviet(self, cr, uid, ids, context=None):
        duongdan = self.pool.get('hlv.property')._get_value_project_property_by_name(cr, uid, 'path of template')
        domain = self.pool.get('hlv.property')._get_value_project_property_by_name(cr, uid, 'Domain') or '../..'
        kieufile = self.pool.get('hlv.property')._get_value_project_property_by_name(cr, uid, 'Kiểu lưu file') or 'html'
        duan = self.browse(cr, uid, ids[0], context=context)
        folder_duan = duongdan + '/%s/' %str(duan.link_url)
        if not os.path.exists(folder_duan):
            os.makedirs(folder_duan)
        cungchude = self.pool.get('yhoc_thongtin').search(cr, uid, [('duan.id', '=',duan.id),('state','=','done')], order='sequence', context=context)
        #Giang_0112#
#        cungchude_tab_ = '''<li><a href="__LINKBAIVIET__">__TENBAIVIET__</a></li>'''
        cungchude_tab_ = '''<li> <img class="thongtinleftimg" src="__HINHDUAN__"/><a href="__LINKBAIVIET__">__TENBAIVIET__</a></li>
        '''
        all_cungchude = '' 
        for ccd in cungchude:
            ccdr = self.pool.get('yhoc_thongtin').browse(cr, uid, ccd, context=context)
            cungchude_tab = cungchude_tab_.replace('__LINKBAIVIET__', domain + '/%s/'%(ccdr.link_url))
#                else:
#                    cungchude_tab = cungchude_tab_.replace('__LINKBAIVIET__', '#')
            cungchude_tab = cungchude_tab.replace('__TENBAIVIET__', ccdr.name)
            ten_url = self.pool.get('yhoc_trangchu').parser_url(ccdr.name)
            cungchude_tab = cungchude_tab.replace('__HINHDUAN__', domain + '/images/thongtin/%s-thongtin-%s.jpg'%(str(ccdr.id),ccdr.url_thongtin))
            all_cungchude += cungchude_tab
        
        import codecs  
        fw= codecs.open(folder_duan+'/baivietcungduantrongbaiviet.' + kieufile,'w','utf-8')
        fw.write(all_cungchude)
        fw.close()  
        return True

    def capnhat_baivietcungduantrongbaiviet_end(self, cr, uid, ids, context=None):
        duongdan = self.pool.get('hlv.property')._get_value_project_property_by_name(cr, uid, 'path of template')
        domain = self.pool.get('hlv.property')._get_value_project_property_by_name(cr, uid, 'Domain') or '../..'
        kieufile = self.pool.get('hlv.property')._get_value_project_property_by_name(cr, uid, 'Kiểu lưu file') or 'html'
        duan = self.browse(cr, uid, ids[0], context=context)
        folder_duan = duongdan + '/%s/' %str(duan.link_url)
        if not os.path.exists(folder_duan):
            os.makedirs(folder_duan)
        if os.path.exists(duongdan+'/template/duan/baivietcungduan_trongbaiviet.html'):
            fr = open(duongdan+'/template/duan/baivietcungduan_trongbaiviet.html', 'r')
            template_ = fr.read()
            fr.close()
        else:
            template_ = ''
        
        if os.path.exists(duongdan+'/template/duan/baivietcungduan_item.html'):
            fr = open(duongdan+'/template/duan/baivietcungduan_item.html', 'r')
            item_ = fr.read()
            fr.close()
        else:
            item_ = ''
            
        cungduan = self.pool.get('yhoc_thongtin').search(cr, uid, [('duan.id', '=',duan.id),('state','=','done')], order='sequence', context=context)
        all_item_ = '' 
        for i in range(0,len(cungduan)):
            cdar = self.pool.get('yhoc_thongtin').browse(cr, uid, cungduan[i], context=context)
            item = item_.replace('__LINKBAIVIET__', domain + '/%s/'%(cdar.link_url))
            item = item.replace('__TENBAIVIET__', cdar.name)
            ten_url = self.pool.get('yhoc_trangchu').parser_url(cdar.name)
            item = item.replace('__HINHBAIVIET__', domain + '/images/thongtin/%s-thongtin-%s.jpg'%(str(cdar.id),cdar.url_thongtin))
            if i%4 == 0:
                item = item.replace('<!--<li class="cloned">-->', '<li class="cloned">')
                item = item.replace('<!--</li>-->', '')
                all_item_ += item
            elif i%4 == 3:
                item = item.replace('<!--<li class="cloned">-->', '')
                item = item.replace('<!--</li>-->', '</li>')
                all_item_ += item
            else:
                item = item.replace('<!--<li class="cloned">-->', '')
                item = item.replace('<!--</li>-->', '')
                all_item_ += item
        if len(cungduan)%4 <> 3:
            all_item_ += '</li>'
            
        template = template_.replace('__BAIVIETCUNGDUAN_ITEM__', all_item_)
        template = template.replace('__DOMAIN__', domain)
        
        import codecs  
        fw= codecs.open(folder_duan+'/baivietcungduantrongbaiviet_end.html','w','utf-8')
        fw.write(template)
        fw.close()  
        return True
    
    def capnhat_thanhvienthamgia_trongduan(self, cr, uid, ids, context=None):
        duongdan = self.pool.get('hlv.property')._get_value_project_property_by_name(cr, uid, 'path of template')
        domain = self.pool.get('hlv.property')._get_value_project_property_by_name(cr, uid, 'Domain') or '../..'
        kieufile = self.pool.get('hlv.property')._get_value_project_property_by_name(cr, uid, 'Kiểu lưu file') or 'html'
        duan = self.browse(cr, uid, ids[0], context=context)
        folder_duan = duongdan + '/%s/' %str(duan.link_url)
        
        if os.path.exists(duongdan+'/template/duan/thanhvienthamgia_trongduan.html'):
            fr = open(duongdan+'/template/duan/thanhvienthamgia_trongduan.html', 'r')
            template_ = fr.read()
            fr.close()
        else:
            template_ = ''
        
        if os.path.exists(duongdan+'/template/duan/thanhvienthamgia_item.html'):
            fr = open(duongdan+'/template/duan/thanhvienthamgia_item.html', 'r')
            item_ = fr.read()
            fr.close()
        else:
            item_ = ''
        all_item_ = ''
        tv_ids = duan.thanhvienthamgia
        for i in range(0,len(tv_ids)):
            tv = tv_ids[i].nhanvien
            #tv = self.pool.get('hr.employee').browse(cr, uid, tv_ids[i].id, context=context)
            name_url = self.pool.get('yhoc_trangchu').parser_url(str(tv.name))
            if tv:
                photo = ''
                if tv.image:
                    filename = str(tv.id) + '-profile-' + name_url
                    photo = domain + '/images/profile/%s.jpg' %(filename)

                capbac = tv.capbac or ''
                trinhdo = self.pool.get('hlv.property')._get_value_project_property_by_name(cr, uid, 'Trình độ chuyên môn') or '[]'
                chuyenmon = ''
                for r in eval(trinhdo):
                    if r[0] == capbac:
                        chuyenmon = r[1]
                        break
                item = item_.replace('__DANHXUNG__', tv.danhxung or '')
                item = item.replace('__TENTHANHVIEN__', str(tv.name))
                item = item.replace('__HINHTHANHVIEN__', photo)
                item = item.replace('__LINKTHANHVIEN__', domain + '/profile/%s/'%(tv.link_url))
                item = item.replace('__CHUYENNGANH__',tv.chuyennganh or '')
                item = item.replace('__TRINHDOCHUYENMON__',chuyenmon)
                
                link_item_ = '''<a href="__LINK__" title="__TIITLELINK__"><img src="__IMAGELINK__"></a>
                '''
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
                item = item.replace('__PROFILEITEM__', alllink_item_)
                                
                if i%4 == 0:
                    item = item.replace('<!--<li class="cloned">-->', '<li class="cloned">')
                    item = item.replace('<!--</li>-->', '')
                    all_item_ += item
                elif i%4 == 3:
                    item = item.replace('<!--<li class="cloned">-->', '')
                    item = item.replace('<!--</li>-->', '</li>')
                    all_item_ += item
                else:
                    item = item.replace('<!--<li class="cloned">-->', '')
                    item = item.replace('<!--</li>-->', '')
                    all_item_ += item
        if len(tv_ids)%4 <> 3:
            all_item_ += '</li>'
            
        template = template_.replace('__THANHVIENTHAMGIA_ITEM__', all_item_)
        template = template.replace('__DOMAIN__', domain)
        
        import codecs  
        fw= codecs.open(folder_duan+'/thanhvienthamgia_trongduan.html','w','utf-8')
        fw.write(template)
        fw.close()  
        return True
    
    def capnhat_thanhvien(self, cr, uid, duan, folder_duan, context=None):
        kieufile = self.pool.get('hlv.property')._get_value_project_property_by_name(cr, uid, 'Kiểu lưu file') or 'html'
        duongdan = self.pool.get('hlv.property')._get_value_project_property_by_name(cr, uid, 'path of template')
        domain = self.pool.get('hlv.property')._get_value_project_property_by_name(cr, uid, 'Domain') or '../..'
        
        noidung_thanhvien = ''
        if os.path.exists(duongdan+'/template/duan/thanhvien_tab.html'):
            fr = open(duongdan+'/template/duan/thanhvien_tab.html', 'r')
            thanhvien_tab_ = fr.read()
            fr.close()
        else:
            thanhvien_tab_ = ''
        
        tv_ids = duan.thanhvienthamgia
        linkthanhvien = ''
        for member in tv_ids:
            tv = member.nhanvien
            name_url_tv = self.pool.get('yhoc_trangchu').parser_url(str(tv.name))
            capbac = tv.capbac or ''
            trinhdo = self.pool.get('hlv.property')._get_value_project_property_by_name(cr, uid, 'Trình độ chuyên môn') or '[]'
            for r in eval(trinhdo):
                if r[0] == capbac:
                    capbac = r[1]
                    break
            photo = domain + '/template/trangchu/images/default_customer.png'
            if tv.image:
                if not os.path.exists(duongdan + '/images/profile'):
                    os.makedirs(duongdan + '/images/profile')
                path_hinh_ghixuong = duongdan + '/images/profile' + '/%s-profile-%s.jpg' %(str(tv.id),name_url_tv)
                fw= open(path_hinh_ghixuong,'wb')
                fw.write(base64.decodestring(tv.image))
                fw.close()
                photo = domain + '/images/profile/%s-profile-%s.jpg' %(str(tv.id),name_url_tv)
                self.pool.get('yhoc_thongtin').resize_image(path_hinh_ghixuong, 145, 145, context=context)
#                from PIL import Image
#                try:
#                    im = Image.open(path_hinh_ghixuong)
#                    width, height = im.size
#                    if width>height:
#                        ratio = float(width)/float(145)
#                    else:
#                        ratio = float(height)/float(145)
#                    im.resize(((int(width/ratio),int(height/ratio))), Image.ANTIALIAS).save(path_hinh_ghixuong)
#                except:
#                    im = im.convert('RGB')
#                    im.resize(((int(width/ratio),int(height/ratio))), Image.ANTIALIAS).save(path_hinh_ghixuong)
                    
                    
##############################                             
            thanhvien_tab = ''
            thanhvien_tab = thanhvien_tab_
            thanhvien_tab = thanhvien_tab.replace('__DANHXUNG__', tv.danhxung or '')
            thanhvien_tab = thanhvien_tab.replace('__TENTHANHVIEN__', tv.name)
            thanhvien_tab = thanhvien_tab.replace('__HINHTHANHVIEN__', photo)
            thanhvien_tab = thanhvien_tab.replace('__LINKTHANHVIEN__', domain + '/profile/%s/'%(tv.link_url))
            thanhvien_tab = thanhvien_tab.replace('__VAITRO__', member.name or '')
            noidung_thanhvien += thanhvien_tab
            
        if not os.path.exists(folder_duan + '/data'):
            os.makedirs(folder_duan + '/data')
        import codecs
        fw = codecs.open(folder_duan + '/data/thanhvien_thamgia_duan.html','w','utf-8')
        fw.write(str(noidung_thanhvien))
        fw.close()
        return True
    
    def capnhat_baivietcungduan(self, cr, uid, duan, folder_duan, context=None):
        kieufile = self.pool.get('hlv.property')._get_value_project_property_by_name(cr, uid, 'Kiểu lưu file') or 'html'
        domain = self.pool.get('hlv.property')._get_value_project_property_by_name(cr, uid, 'Domain') or '../..'
        duongdan = self.pool.get('hlv.property')._get_value_project_property_by_name(cr, uid, 'path of template')
        cungduan = self.pool.get('yhoc_thongtin').search(cr, uid, [('duan.id', '=',duan.id)], order='sequence', context=context)
        cungduan_tab_ = '''<a href="__LINKBAIVIETDUAN__">__TENBAIVIETDUAN__</a></br>'''
        #Giang_3011# Số lượng bài viết trong dự án
        super(yhoc_duan,self).write(cr,uid,[duan.id],{'soluongbaiviet':len(cungduan)}, context=context)
        all_cungduan = '' 
        for cda in cungduan:
            cungduan_tab = ''
            cdar = self.pool.get('yhoc_thongtin').browse(cr, uid, cda, context=context)
            if cdar.state != 'done':
                cungduan_tab = cungduan_tab_.replace('__LINKBAIVIETDUAN__', '#')
                cungduan_tab = cungduan_tab.replace('__TENBAIVIETDUAN__', str(cdar.sequence) + '. ' +cdar.name + ' (Chưa dịch)')
            else:
                cungduan_tab = cungduan_tab_.replace('__LINKBAIVIETDUAN__', domain + '/%s/'%(cdar.link_url))
                cungduan_tab = cungduan_tab.replace('__TENBAIVIETDUAN__', str(cdar.sequence) + '. ' +cdar.name)
            all_cungduan += cungduan_tab
        
        if not os.path.exists(folder_duan+'/data'):
            os.makedirs(folder_duan+'/data')
        import codecs
        fw = codecs.open(folder_duan+'/data/danhsachbaiviet.html','w','utf-8')
        fw.write(str(all_cungduan))
        fw.close()
        return  True
    
    def capnhat_thongtin(self,cr,uid,ids,context=None):
       
        duongdan = self.pool.get('hlv.property')._get_value_project_property_by_name(cr, uid, 'path of template')
        domain = self.pool.get('hlv.property')._get_value_project_property_by_name(cr, uid, 'Domain') or '../..'
        kieufile = self.pool.get('hlv.property')._get_value_project_property_by_name(cr, uid, 'Kiểu lưu file') or 'html'
        duan = self.browse(cr, uid, ids[0], context=context)
        ten_url = self.pool.get('yhoc_trangchu').parser_url(duan.name)
#        link_url = duan.chude_id.link_url + '/%s' %(ten_url)
        link_url = 'duan/%s'%(ten_url)
        #Doc file
        if os.path.exists(duongdan + '/template/duan/duan.html'):
            fr = open(duongdan + '/template/duan/duan.html', 'r')
            template = fr.read()
            fr.close()
        else:
            template = ''
        
        folder_duan = duongdan + '/duan/%s'%(ten_url)
        if not os.path.exists(folder_duan):
            os.makedirs(folder_duan)

#Lay thong tin co ban
        gioithieu = duan.description
        tenduan = duan.name
        chude = duan.chude_id.name
        
        
#Cập nhật tittle       
        fr = open(duongdan + '/template/trangchu/tittle.html', 'r')
        noidung_tittle = fr.read()
        fr.close()
        noidung_tittle = noidung_tittle.replace('__TITLE__','Dự án ' + duan.name)
        template = template.replace('__TITLE__',noidung_tittle)
        template = template.replace('__DUONGDAN__',duongdan)
        template = template.replace('__ID__', str(duan.id))
        
#Lấy du an cùng chủ đề:
        self.pool.get('yhoc_chude').capnhat_chudetrongtrangduan(cr, uid, duan.chude_id, context)
        template = template.replace('__CHUDETRONGTRANGDUAN__',duongdan+'/%s/data/chudetrongtrangduan.html'%str(duan.chude_id.link_url))
        
#Cập nhật bài viết cùng dự án
        self.capnhat_baivietcungduan(cr, uid, duan, folder_duan, context)
            
#Cập nhật thanhf vien tham gia
        #self.capnhat_thanhvien(cr, uid, duan, folder_duan, context)
        self.capnhat_thanhvienthamgia_trongduan(cr, uid, ids, context)

#Giang_0812#
        self.capnhat_sharebutton(cr, uid, duan.id, context=context)
        
#Cap nhật noi dung co ban
        template = template.replace('__TENDUAN__', tenduan)
        template = template.replace('__GIOITHIEU__', gioithieu or '(Chưa cập nhật)')
        template = template.replace('__CHUDE__', chude or '')
        
                
#Ghi file
        fr = open(duongdan + '/template/trangchu/tittle.html', 'r')
        noidung_tittle = fr.read()
        fr.close()
        noidung_tittle = noidung_tittle.replace('__TITLE__','Dự án ' + tenduan)
        template = template.replace('__TITLE__',noidung_tittle)
        
##set profile_link
        super(yhoc_duan,self).write(cr,uid,[duan.id],{'link':domain + '/%s/'%link_url,
                                                      'link_url': link_url}, context=context)
        #Giang_0112# Cập nhật link tree trong bai viết
        self.capnhat_linktree(cr, uid, ids, context)
#        temp_ = '''<a href="__LINK__">__NAME__</a>'''
#        
#        linktree = []
#        treechude = []
#        treechude = self.pool.get('yhoc_chude').dequy(treechude, duan.chude_id)
#        treechude.insert(0,duan.chude_id)
#        for i in range(len(treechude)):
#            temp = temp_.replace('__LINK__', domain + '/%s/'%(treechude[len(treechude)-i-1].link_url))
#            temp = temp.replace('__NAME__', treechude[len(treechude)-i-1].name)
#            linktree.append(temp)
#        linktree.insert(0,'''<a href="http://yhoccongdong.com">Trang chủ</a>''')
#        
#        temp = temp_.replace('__LINK__', duan.link or '#')
#        temp = temp.replace('__NAME__', duan.name)
#        linktree.append(temp)
        
#        res = ''
#        res = " > ".join(linktree)
#        super(yhoc_duan,self).write(cr,uid,[duan.id],{'link_tree':res}, context=context)
        template = template.replace('__LINKTREE__', str(duan.link_tree))
        template = template.replace('__TUADEDUAN__', duan.name)
        template = template.replace('__MOTA__', str(duan.description) or '')
        template = template.replace('__HINHDUAN__', domain + '/images/%s-duan-%s.jpg' %(str(duan.id),ten_url))
        
        import codecs  
        fw= codecs.open(folder_duan+'/index.' + kieufile,'w','utf-8')
        fw.write(template)
        fw.close()
        
        self.pool.get('yhoc_chude').capnhat_thongtin(cr, uid, [duan.chude_id.id], context)
        return template, duongdan, domain
    
    def capnhat_linktree(self,cr,uid,ids,context=None):
        duongdan = self.pool.get('hlv.property')._get_value_project_property_by_name(cr, uid, 'path of template')
        domain = self.pool.get('hlv.property')._get_value_project_property_by_name(cr, uid, 'Domain') or '../..'
        kieufile = self.pool.get('hlv.property')._get_value_project_property_by_name(cr, uid, 'Kiểu lưu file') or 'html'
        if os.path.exists(duongdan+'/template/duan/linktree_trongbaiviet.html'):
            fr = open(duongdan+'/template/duan//linktree_trongbaiviet.html', 'r')
            template_ = fr.read()
            fr.close()
        else:
            template_ = ''
            
        if os.path.exists(duongdan+'/template/duan/linktree_item.html'):
            fr = open(duongdan+'/template/duan/linktree_item.html', 'r')
            item_ = fr.read()
            fr.close()
        else:
            item_ = ''
        all_item_=''
        item = item_.replace('__LINK__', domain)
        item = item.replace('__NAME__', 'Trang chủ')
        all_item_ += item
        duan = self.browse(cr, uid, ids[0], context=context)
        linktree = []
        treechude = []
        treechude = self.pool.get('yhoc_chude').dequy(treechude, duan.chude_id)
        treechude.insert(0,duan.chude_id)
        for i in range(len(treechude)):
            item = item_.replace('__LINK__', domain + '/%s/'%(treechude[len(treechude)-i-1].link_url))
            item = item.replace('__NAME__', treechude[len(treechude)-i-1].name)
            linktree.append(item)
            all_item_ += item
        item = item_.replace('__LINK__', duan.link or '#')
        item = item.replace('__NAME__', duan.name)
        linktree.append(item)
        all_item_ += item
        res = ''
        res = " > ".join(linktree)
        super(yhoc_duan,self).write(cr,uid,[duan.id],{'link_tree':res}, context=context)
        template = template_.replace('__LINKTREEITEM__', all_item_)
                
        import codecs  
        fw= codecs.open(duongdan +'/%s/linktree_trongbaiviet.html'%duan.link_url,'w','utf-8')
        fw.write(template)
        fw.close()
        return True
    
    def capnhat_sharebutton(self, cr, uid, ids, context=None):
        duongdan = self.pool.get('hlv.property')._get_value_project_property_by_name(cr, uid, 'path of template')
        domain = self.pool.get('hlv.property')._get_value_project_property_by_name(cr, uid, 'Domain') or '../..'
        duan = self.browse(cr,uid,ids)
        if os.path.exists(duongdan+'/template/duan/share_social_button.html'):
            fr = open(duongdan+'/template/duan/share_social_button.html', 'r')
            template_ = fr.read()
            fr.close()
        else:
            template_ = ''
        template = template_.replace('__DOMAIN__', domain)
        template = template.replace('__URL__', domain + '/%s/'%duan.link_url)
        template = template.replace('__TITLE__', duan.name)
        template = template.replace('__DESCRIPTION__', str(duan.description))
        name_url = self.pool.get('yhoc_trangchu').parser_url(str(duan.name))
        photo = domain + '/images/duan/%s-duan-%s.jpg'%(str(duan.id),name_url)
        template = template.replace('__IMAGE__', photo)
        import codecs  
        fw = codecs.open(duongdan + '/%s/share_social_button.html'%duan.link_url,'w','utf-8')
        fw.write(template)
        fw.close()
        return True
    
yhoc_duan()
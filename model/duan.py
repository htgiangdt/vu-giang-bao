# -*- encoding: utf-8 -*-
from osv import fields,osv
from tools.translate import _
import time
from datetime import datetime, date
from email.Utils import formatdate
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
                'noidung':fields.text('Nội dung'),
                'link':fields.char('Link dự án',size=1000),
                'chude_id': fields.many2one('yhoc_chude','Chủ đề'),
                'photo': fields.binary('Hình',filters='*.png,*.gif,*.jpg'),
                'link_tree':fields.char('Link tree',size=1000),
                'sequence': fields.integer('Thứ tự'),
                'truongduan':fields.many2one('hr.employee', 'Trưởng dự án',required='1'),
                #'thanhvienthamgia':fields.one2many('hlv_vaitro', 'duan_id', string='Thành viên tham gia'),
                'thanhvienthamgia':fields.many2many('hr.employee', 'duan_thanhvien_rel', 'duan_id', 'thanhvien_id', 'Thành viên tham gia'),
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

    def capnhat_thanhvienthamgia(self, cr, uid, ids, context=None):
        for id in ids:
            kq = [] 
            tt = self.pool.get('yhoc_thongtin').search(cr, uid, [('duan','=',id)],context=context)
            for t in tt:
                t = self.pool.get('yhoc_thongtin').browse(cr, uid, t, context=context)
                if t.nguoidich:
                    kq.append(t.nguoidich.id)
                if t.nguoihieudinh:
                    kq.append(t.nguoihieudinh.id)
            vals = {'thanhvienthamgia': [[6, False, list(set(kq))]]}
            self.write(cr, uid, [id], vals, context=context)
        return True


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
                if m.id == nhanvien.id:
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
        cungchude_tab_ = '''<li><a href="__LINKBAIVIET__"><img class="thongtinleftimg" src="__HINHDUAN__" alt="__TENBAIVIET__"/>__TENBAIVIET__</a></li>
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
            tv = tv_ids[i]
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
                
                link_item_ = '''<a href="__LINK__" title="__TITLELINK__" target="_blank"><img src="__IMAGELINK__" alt="__TITLELINK__"/></a>
                '''
                alllink_item_ = ''
                if tv.work_email:
                    link_item = link_item_.replace('__LINK__', 'mailto:' + tv.work_email)
                    link_item = link_item.replace('__TITLELINK__', 'Gửi email cho tác giả')
                    link_item = link_item.replace('__IMAGELINK__', domain + '/images/icon/email.png')
                    alllink_item_ += link_item
                if tv.facebook_acc:
                    link_item = link_item_.replace('__LINK__', tv.facebook_acc)
                    link_item = link_item.replace('__TITLELINK__', 'Facebook')
                    link_item = link_item.replace('__IMAGELINK__', domain + '/images/icon/facebook.png')
                    alllink_item_ += link_item
                if tv.google_plus_acc:
                    link_item = link_item_.replace('__LINK__', tv.google_plus_acc)
                    link_item = link_item.replace('__TITLELINK__', 'Google+')
                    link_item = link_item.replace('__IMAGELINK__', domain + '/images/icon/google_plus.png')
                    alllink_item_ += link_item
                if os.path.exists(duongdan+'/tags/' + name_url):
                    link_item = link_item_.replace('__LINK__', domain + '/tags/' + name_url + '/')
                    link_item = link_item.replace('__TITLELINK__', 'Những đóng góp của tác giả')
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
        cungduan = self.pool.get('yhoc_thongtin').search(cr, uid, [('state', '=','done'),('duan.id', '=',duan.id)], order='sequence', context=context)
        if os.path.exists(duongdan+'/template/duan/baivietcungduan_tab.html'):
            fr = open(duongdan+'/template/duan/baivietcungduan_tab.html', 'r')
            cungduan_tab_ = fr.read()
            fr.close()
        else:
            cungduan_tab_ = ''
        
        if os.path.exists(duongdan + '/template/duan/mucluc.html'):
            fr = open(duongdan + '/template/duan/mucluc.html', 'r')
            mucluc_ = fr.read()
            fr.close()
        else:
            mucluc_ = ''
            
        if os.path.exists(duongdan + '/template/duan/mucluc_item.html'):
            fr = open(duongdan + '/template/duan/mucluc_item.html', 'r')
            mucluc_item_ = fr.read()
            fr.close()
        else:
            mucluc_item_ = ''
                
        #Giang_3011# Số lượng bài viết trong dự án
        super(yhoc_duan,self).write(cr,uid,[duan.id],{'soluongbaiviet':len(cungduan)}, context=context)
        all_cungduan = ''
        all_mucluc_ = ''
        all_mucluc_inculde_ = ''
        STT = 1
        for cda in cungduan:
            cungduan_tab = ''
            cdar = self.pool.get('yhoc_thongtin').browse(cr, uid, cda, context=context)
            name_url = self.pool.get('yhoc_trangchu').parser_url(cdar.name)
            
            # Mục lục item của dự án
            mucluc_item = mucluc_item_.replace('__TEN_MUCLUC__', cdar.name)
            mucluc_item = mucluc_item.replace('__LINK_MUCLUC__', cdar.duan.link + '#%s'%name_url)
            mucluc_item = mucluc_item.replace('__STT__', str(STT))
            all_mucluc_ += mucluc_item
            ##########################
            
            date = ''
            photo = ''
            if cdar.hinhdaidien:
                if not os.path.exists(duongdan + '/images/thongtin'):
                    os.makedirs(duongdan + '/images/thongtin')
                path_hinh_ghixuong = duongdan + '/images/thongtin' + '/%s-thongtin-%s.jpg' %(str(cdar.id),name_url)
                fw = open(path_hinh_ghixuong,'wb')
                fw.write(base64.decodestring(cdar.hinhdaidien))
                fw.close()
                photo = domain + '/images/thongtin/%s-thongtin-%s.jpg' %(str(cdar.id),name_url)
            if cdar.state != 'done':
                cungduan_tab = cungduan_tab_.replace('__LINKBAIVIETDUAN__', '#')
                cungduan_tab = cungduan_tab.replace('__STT__', str(STT))
                cungduan_tab = cungduan_tab.replace('__TENBAIVIETDUAN__', cdar.name + ' (Chưa dịch)')
            else:
                cungduan_tab = cungduan_tab_.replace('__LINKBAIVIETDUAN__', domain + '/%s/'%(cdar.link_url))
                cungduan_tab = cungduan_tab.replace('__STT__', str(STT))
                cungduan_tab = cungduan_tab.replace('__TENBAIVIETDUAN__', cdar.name)
                date_default = datetime.strptime(cdar.date, '%Y-%m-%d %H:%M:%S')
                date = date_default.strftime('%d/%m/%Y')
                
            STT += 1            
            cungduan_tab = cungduan_tab.replace('__PHOTO__', photo)
            cungduan_tab = cungduan_tab.replace('__DESCRIPTION__', cdar.motangan or '(Chưa cập nhật mô tả)')
            cungduan_tab = cungduan_tab.replace('__URLNAME__', name_url)
            cungduan_tab = cungduan_tab.replace('__NGAYDANG__', date)
            cungduan_tab = cungduan_tab.replace('__SOLUONGXEM__', str(cdar.soluongxem))
            cungduan_tab = cungduan_tab.replace('__MUCLUC__', '''<?php include("../../thongtin/%s/menu.html")?>'''%name_url)
            
            
            if cdar.nguoidich:
                cungduan_tab = cungduan_tab.replace('__DANHXUNGNT__',cdar.nguoidich.danhxung or '')
                cungduan_tab = cungduan_tab.replace('__NGUOIDICH__',cdar.nguoidich.name)
                cungduan_tab = cungduan_tab.replace('__LINKNGUOIDICH__',cdar.nguoidich.link or '#')
            else:
                cungduan_tab = cungduan_tab.replace('__DANHXUNGNT__','(Chưa phân công)')
                cungduan_tab = cungduan_tab.replace('__NGUOIDICH__','')
                cungduan_tab = cungduan_tab.replace('__LINKNGUOIDICH__','#')
                
            if cdar.nguoihieudinh:
                cungduan_tab = cungduan_tab.replace('__NGUOIHIEUDINH__', cdar.nguoihieudinh.name or '')
                cungduan_tab = cungduan_tab.replace('__LINKNGUOIHIEUDINH__', cdar.nguoihieudinh.link or '#')
                cungduan_tab = cungduan_tab.replace('__DANHXUNGHD__', cdar.nguoihieudinh.danhxung or '')
            else:
                cungduan_tab = cungduan_tab.replace('__NGUOIHIEUDINH__', '(Chưa phân công)')
                cungduan_tab = cungduan_tab.replace('__LINKNGUOIHIEUDINH__', '#')
                cungduan_tab = cungduan_tab.replace('__DANHXUNGHD__', '')
                
            all_cungduan += cungduan_tab
        
        #Mục lục duan
        mucluc = mucluc_.replace('__MUCLUC_ITEM__', all_mucluc_)
        mucluc = mucluc.replace('__MUCLUC_TITLE__', 'Nội dung chính')
        
        if not os.path.exists(folder_duan+'/data'):
            os.makedirs(folder_duan+'/data')
        import codecs
        fw = codecs.open(folder_duan+'/data/danhsachbaiviet.html','w','utf-8')
        fw.write(str(all_cungduan))
        fw.close()
        
        fw = codecs.open(folder_duan+'/data/mucluc.html','w','utf-8')
        fw.write(str(mucluc))
        fw.close()
        
        return  True
    
    def capnhat_thongtin(self,cr,uid,ids,context=None):
       
        duongdan = self.pool.get('hlv.property')._get_value_project_property_by_name(cr, uid, 'path of template')
        domain = self.pool.get('hlv.property')._get_value_project_property_by_name(cr, uid, 'Domain') or '../..'
        kieufile = self.pool.get('hlv.property')._get_value_project_property_by_name(cr, uid, 'Kiểu lưu file') or 'html'
        self.capnhat_thanhvienthamgia(cr, uid, ids, context)
        
        duan = self.browse(cr, uid, ids[0], context=context)
        ten_url = self.pool.get('yhoc_trangchu').parser_url(duan.name)
        link_url = 'duan/%s'%(ten_url)
        #Doc file
        if os.path.exists(duongdan + '/template/duan/duan.html'):
            fr = open(duongdan + '/template/duan/duan.html', 'r')
            template = fr.read()
            fr.close()
        else:
            template = ''
        
        folder_duan = duongdan + '/duan/%s'%(ten_url)
        folder_duan_data = folder_duan + '/data/'
        if not os.path.exists(folder_duan):
            os.makedirs(folder_duan)
        if not os.path.exists(folder_duan_data):
            os.makedirs(folder_duan_data)

#Lay thong tin co ban
        gioithieu = duan.description
        tenduan = duan.name
        chude = duan.chude_id.name
        chude_link = duan.chude_id.link
        
        
#Cập nhật tittle
        template = template.replace('__DUONGDAN__',duongdan)
        template = template.replace('__DOMAIN__',domain)
        template = template.replace('__ID__', str(duan.id))
        template = template.replace('__URL__', domain + '/%s/'%link_url)
        
#Lấy du an cùng chủ đề:
        self.pool.get('yhoc_chude').capnhat_chudetrongtrangduan(cr, uid, duan.chude_id, context)
        template = template.replace('__CHUDETRONGTRANGDUAN__',duongdan+'/%s/data/chudetrongtrangduan.html'%str(duan.chude_id.link_url))
            
#Cập nhật thanhf vien tham gia
        #self.capnhat_thanhvien(cr, uid, duan, folder_duan, context)
        self.capnhat_thanhvienthamgia_trongduan(cr, uid, ids, context)

#Giang_0812#
        self.capnhat_sharebutton(cr, uid, duan, duongdan, domain, folder_duan_data, context)
        
#Cap nhật noi dung co ban
        template = template.replace('__TENDUAN__', tenduan)
        template = template.replace('__GIOITHIEU__', gioithieu or '(Chưa cập nhật)')
        template = template.replace('__CHUDE__', chude or '')
        template = template.replace('__LINKCHUDE__', chude_link or '#')
                
#Ghi file
        fr = open(duongdan + '/template/trangchu/tittle.html', 'r')
        noidung_tittle = fr.read()
        fr.close()
        noidung_tittle = noidung_tittle.replace('__TITLE__','Dự án ' + tenduan)
        template = template.replace('__TITLE__',noidung_tittle)
        
#Cap nhat RSS du an
        if duan.chude_id.parent_id.name == 'Trang chủ':
			self.capnhat_rssduan(cr, uid, duan, context)
##set profile_link
        super(yhoc_duan,self).write(cr,uid,[duan.id],{'link':domain + '/%s/'%link_url,
                                                      'link_url': link_url}, context=context)
        
        #Cập nhật bài viết cùng dự án
        self.capnhat_baivietcungduan(cr, uid, duan, folder_duan, context)
        
        #Giang_0112# Cập nhật link tree trong dự án
        self.capnhat_linktree_trongduan(cr, uid, duan, duongdan, domain, folder_duan_data, context)
        
        sql = '''select write_date from yhoc_duan where id=%s'''%str(duan.id)
        cr.execute(sql)
        write_date = cr.fetchone()[0]
        write_date = write_date.split('.')
        template = template.replace('__TUADEDUAN__', duan.name)
        if duan.description:
            template = template.replace('__MOTA__', str(duan.description))
        else:
            template = template.replace('__MOTA__', 'Đang cập nhật')
        
        #Thêm nội dung vào dự án
        if duan.noidung:
            noidung_template_ ='''<div id="noidungthongtin" style="padding-top:15px; line-height: 25px; max-width:700px; display;block; clear: both; text-align:justify;" itemprop="articleBody">    
                    __NOIDUNG_DUAN__
                    <p>&nbsp;</p>
                </div>'''
            noidung_template = noidung_template_.replace('__NOIDUNG_DUAN__', str(duan.noidung))
            template = template.replace('<!--__NOIDUNG__-->', noidung_template)
        template = template.replace('__DANHXUNG__', duan.truongduan.danhxung or '')
        template = template.replace('__TRUONGDUAN__', duan.truongduan.name or '')
        template = template.replace('__LINKTRUONGDA__', duan.truongduan.link or '')
        template = template.replace('__LASTUPDATE__', write_date[0])
        
        
        chudecon_da = self.pool.get('yhoc_duan').search(cr, uid, [('chude_id','=',duan.chude_id.id),('link','!=',False)])
        chudecon_cd = self.pool.get('yhoc_chude').search(cr, uid, [('parent_id','=',duan.chude_id.id),('link','!=',False)])
        chudecon = chudecon_cd + chudecon_da
        template = template.replace('__SODUANLIENQUAN__', str(len(chudecon)))
        template = template.replace('__HINHDUAN__', domain + '/images/%s-duan-%s.jpg' %(str(duan.id),ten_url))
        
        truongda_name_url = self.pool.get('yhoc_trangchu').parser_url(duan.truongduan.name)
        if os.path.exists(duongdan+'/profile/%s/profiletrongtrangbaiviet.html'%truongda_name_url):
            template = template.replace('__PROFILETRUONGDA__', '''<?php include("../../profile/%s/profiletrongtrangbaiviet.html")?>'''%truongda_name_url)
        else:
            self.pool.get('hr.employee').capnhat_profiletrongtrangbaiviet(cr, uid, [duan.truongduan.id], context=context)
            template = template.replace('__PROFILETRUONGDA__', '''<?php include("../../profile/%s/profiletrongtrangbaiviet.html")?>'''%truongda_name_url)
        template = template.replace('__THANHVIEN_THAMGIA__', domain + '/%s/thanhvienthamgia_trongduan.html'%link_url)

        template = template.replace('__AUTHORBOX__',duongdan + '/profile/%s/author_box.html' %truongda_name_url)            

        tags = duan.keyword_ids
        list_tag = self.pool.get('yhoc_keyword').capnhat_listtag_ophiacuoi(cr, uid, tags, context=context)
        template = template.replace('__LIST_TAGS__', list_tag)
        
        import codecs  
        fw= codecs.open(folder_duan+'/index.' + kieufile,'w','utf-8')
        fw.write(template)
        fw.close()
        
        self.pool.get('yhoc_chude').capnhat_thongtin(cr, uid, [duan.chude_id.id], context)
        return template, duongdan, domain    

    def capnhat_linktree_trongduan(self, cr, uid, duan, duongdan, domain, folder_duan_data, context=None):
        if os.path.exists(duongdan+'/template/duan/linktree.html'):
            fr = open(duongdan+'/template/duan/linktree.html', 'r')
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
        linktree = []
        treechude = []
        treechude = self.pool.get('yhoc_chude').dequy(treechude, duan.chude_id)
        treechude.insert(0,duan.chude_id)
        for i in range(len(treechude)):
            item = item_.replace('__LINK__', domain + '/%s/'%(treechude[len(treechude)-i-1].link_url))
            item = item.replace('__NAME__', treechude[len(treechude)-i-1].name)
            linktree.append(item)
            all_item_ += item
        res = ''
        res = " > ".join(linktree)
        super(yhoc_duan,self).write(cr,uid,[duan.id],{'link_tree':res}, context=context)
        template = template_.replace('__LINKTREEITEM__', all_item_)
        
        import codecs  
        fw= codecs.open(folder_duan_data + 'linktree_duan.html','w','utf-8')
        fw.write(template)
        fw.close()
        return True

    
    def capnhat_rssduan(self, cr, uid, duan, context=None):
        duongdan = self.pool.get('hlv.property')._get_value_project_property_by_name(cr, uid, 'path of template')
        domain = self.pool.get('hlv.property')._get_value_project_property_by_name(cr, uid, 'Domain') or '../..'
        if os.path.exists(duongdan+'/template/rss/rss_template.rss'):
            fr = open(duongdan+'/template/rss/rss_template.rss', 'r')
            template_ = fr.read()
            fr.close()
        else:
            template_ = ''
            
        if os.path.exists(duongdan+'/template/rss/rss_item.rss'):
            fr = open(duongdan+'/template/rss/rss_item.rss', 'r')
            rss_item_ = fr.read()
            fr.close()
        else:
            rss_item_ = ''
                
        name = self.pool.get('yhoc_trangchu').parser_url(duan.name)
        template = template_.replace('__TITLECHANNEL__', duan.name)
        template = template.replace('__MOTACHANNEL__', duan.description or 'Đang Cập Nhật')
        template = template.replace('__LINKCHANNEL__', domain +'/rss/%s.rss'%(name))
        template = template.replace('__HINHCHANNEL__', domain + '/images/%s-duan-%s.jpg' %(str(duan.id),name))
        
        cungduan = self.pool.get('yhoc_thongtin').search(cr, uid, [('state','=','done'),('duan', '=',duan.id)], limit=10, order='date desc', context=context)

        allrss_item_ = ''
        for cda in cungduan:
            thongtin = self.pool.get('yhoc_thongtin').browse(cr, uid, cda, context=context)
            rss_item = rss_item_.replace('__TITLEITEM__', thongtin.name or '')
            rss_item = rss_item.replace('__MOTAITEM__', thongtin.motangan or '(Chưa cập nhật)')
            rss_item = rss_item.replace('__LINKITEM__', thongtin.link + '/' or '#')
            date = thongtin.date.split('.')
            date = datetime.strptime(date[0], '%Y-%m-%d %H:%M:%S')
            date_rfc822 = formatdate(time.mktime(date.timetuple()))
            rss_item = rss_item.replace('__DATEITEM__', date_rfc822)
            if thongtin.url_thongtin:
                name_url = thongtin.url_thongtin
            else:
                name_url = self.pool.get('yhoc_trangchu').parser_url(str(thongtin.name))
            rss_item = rss_item.replace('__IMAGEITEM__', domain + '/images/thongtin/%s-thongtin-%s.jpg'%(str(thongtin.id),name_url))
            allrss_item_ += rss_item
                    
        template = template.replace('__RSSITEM__', allrss_item_)
        
        import codecs
        if not os.path.exists(duongdan +'/%s/'%duan.link_url):
            os.makedirs(duongdan +'/%s/'%duan.link_url)
            
        fw = codecs.open(duongdan +'/rss/%s.rss'%(name),'w','utf-8')
        fw.write(template)
        fw.close()     
        return True
      
    def capnhat_sharebutton(self, cr, uid, duan, duongdan, domain, folder_duan_data, context=None):
        if os.path.exists(duongdan+'/template/duan/share_button.html'):
            fr = open(duongdan+'/template/duan/share_button.html', 'r')
            template_ = fr.read()
            fr.close()
        else:
            template_ = ''
        template = template_.replace('__DOMAIN__', domain)
        template = template.replace('__URL__', domain + '/%s/'%duan.link_url)
        name = str(duan.name)
        name = name.replace(' ', '%20')
        template = template.replace('__TITLE__', str(name))
        if not os.path.exists(folder_duan_data):
            os.makedirs(folder_duan_data)
        import codecs  
        fw = codecs.open(folder_duan_data + 'share_button.html','w','utf-8')
        fw.write(template)
        fw.close()
        return template

    def auto_tags(self,cr, uid, ids, context=None):
        kq = []
        duan = self.browse(cr, uid, ids[0], context=context)
        tt = self.pool.get('yhoc_thongtin').search(cr, uid, [('duan','=',ids[0])], context=context)
        for t in tt:
            t = self.pool.get('yhoc_thongtin').browse(cr, uid, t, context=context) 
            if t.main_key:
                kq.append(t.main_key.id)
        for bv in duan.thanhvienthamgia:
            bs_tag = self.pool.get('yhoc_keyword').search(cr, uid, [('name','=',bv.name)],context=context)
            if bs_tag:
                kq.append(bs_tag[0])
            elif not bs_tag:
                bs_tag = self.pool.get('yhoc_keyword').create(cr, uid, {'name':bv.name}, context=context)
                if bs_tag not in kq:
                    kq.append(bs_tag)
                    
        vals = {'keyword_ids': [[6, False, list(set(kq))]]}
        self.write(cr, uid, ids, vals, context=context)
        return True
yhoc_duan()

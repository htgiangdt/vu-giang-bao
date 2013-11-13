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

class yhoc_keyword(osv.osv):
    _name = "yhoc_keyword"
    _description = "Keyword"
#    _order = "comment_date desc"

    def _get_kwlienquan(self, cr, uid, ids, field_name, arg, context=None):
        result = {}
        
        dsbaiviet = self.pool.get('yhoc_thongtin').search(cr, uid, [('state','=','done'),('keyword_ids','=',ids[0])], context=context)
        sql = '''select keyword_id,count(*) as solanxuathien 
                from thongtin_keyword_rel,yhoc_keyword  
                where thongtin_id in (select thongtin_id from thongtin_keyword_rel where keyword_id=%s)
                and keyword_id=id and keyword_id not in (%s,-1)
                group by keyword_id,name
                order by solanxuathien desc'''%(ids[0],ids[0])
        cr.execute(sql)
        kq = []
        dict_1 = cr.dictfetchall()
        print dict_1
        for k in dict_1:
            diem = 0
            for b in dsbaiviet:
                sql = '''select keyword_id from thongtin_keyword_rel where thongtin_id=%s'''%b
                cr.execute(sql)
                key_bv = [r[0] for r in cr.fetchall()]    
                if k['keyword_id'] in key_bv and ids[0] in key_bv:
                    diem+=1
            kq.append({'keyword_id':k['keyword_id'],
                       'solanxuathien':diem})
        print '==================='
        print kq
#        sql = '''select keyword_id,count(*) as solanxuathien 
#                from thongtin_keyword_rel,yhoc_keyword  
#                where thongtin_id in (select thongtin_id from thongtin_keyword_rel where keyword_id=%s)
#                and keyword_id=id and keyword_id not in (%s,-1)
#                group by keyword_id,name
#                order by solanxuathien desc
#                limit 15
#                    '''%(ids[0],ids[0])
#        
#        kwlienquan = cr.dictfetchall()  
        for record in self.browse(cr, uid, ids, context=context):
            result[record.id] = []
            if len(kq)<11:
                for kw in kq:
                    result[record.id].append(kw['keyword_id'])
            else:
                for i in range(0,10):
                    result[record.id].append(kq[i]['keyword_id'])
        return result
    
    def _get_baivietmoi(self, cr, uid, ids, field_name, arg, context=None):
        result = {}
        dsbaivietmoi = self.pool.get('yhoc_thongtin').search(cr, uid, [('state','=','done'),('keyword_ids','=',ids[0])], limit=8, order='date desc', context=context)  
        for record in self.browse(cr, uid, ids, context=context):
            result[record.id] = []
            for bv in self.pool.get('yhoc_thongtin').browse(cr, uid, dsbaivietmoi, context=context):
                result[record.id].append(bv.id)
        return result
    
    def _get_baivietnoibac(self, cr, uid, ids, field_name, arg, context=None):
        result = {}
        dsbaiviet = self.pool.get('yhoc_thongtin').search(cr, uid, [('state','=','done'),('keyword_ids','=',ids[0])], limit=10, order='soluongxem desc', context=context)  
        for record in self.browse(cr, uid, ids, context=context):
            result[record.id] = []
            for bv in self.pool.get('yhoc_thongtin').browse(cr, uid, dsbaiviet, context=context):
                result[record.id].append(bv.id)
        return result
    
    def _get_baivietbanner(self, cr, uid, ids, field_name, arg, context=None):
        result = {}
        dsbaiviet = self.pool.get('yhoc_thongtin').search(cr, uid, [('state','=','done'),('hinhlon','!=',False)], limit=30, order='soluongxem desc', context=context)  
        for record in self.browse(cr, uid, ids, context=context):
            result[record.id] = []
            for bv in self.pool.get('yhoc_thongtin').browse(cr, uid, dsbaiviet, context=context):
                result[record.id].append(bv.id)
        return result
    
    
    
    _columns = {
        'name': fields.char('Keyword', size=500, required=1),
        'khongdau': fields.char('Keyword', size=500, required=1),
        'priority': fields.integer('Priority'),
        'thongtin_ids': fields.many2many('yhoc_thongtin', 'thongtin_keyword_rel', 'keyword_id', 'thongtin_id', 'Keyword'),
        'soluongxem': fields.integer("Số lượng người xem"),
        'description':fields.text('Giới thiệu'),
        'kwlienquan_ids': fields.function(_get_kwlienquan, type='many2many', relation='yhoc_keyword', string='Từ khóa liên quan'),
        'baivietnoibac':fields.function(_get_baivietnoibac, type='many2many', relation='yhoc_thongtin', string='Bài viết nổi bậc'),
        'baivietmoi':fields.function(_get_baivietmoi, type='many2many', relation='yhoc_thongtin', string='Bài viết mới'),
        'baivietbanner':fields.function(_get_baivietbanner, type='many2many', relation='yhoc_thongtin', string='Banner'),
        'baiviet_ids': fields.many2many('yhoc_thongtin', 'thongtin_keyword_rel', 'keyword_id','thongtin_id', 'Bài viết chứa từ khóa'),
    }

    _defaults = {
    }
    
    def create(self, cr, uid, vals, context=None):
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
    
    def capnhat_chude_tag(self,cr, uid,chudenoibac, duongdan, domain,kieufile, context=None):
        folder_trangchu = duongdan + '/trangchu/vi'
        if os.path.exists(duongdan+'/template/trangchu/sidebar_menu_tab.html'):
            fr = open(duongdan+'/template/trangchu/sidebar_menu_tab.html', 'r')
            sidebar_menu_tab_ = fr.read()
            fr.close()
            all_sidebar_menu_tab = ''
            import random
            baivietnoibac = random.sample(chudenoibac, 6)       
            for bv in baivietnoibac:
                if not bv.link:
                    try:
                        self.pool.get('yhoc_thongtin').xuatban_thongtin(cr, uid, [bv.id], context=context)
                    except:
                        pass
                else:
                    photo = ''
                    if bv.hinhdaidien:
                        name_url = self.parser_url(bv.name)
                        filename = str(bv.id) + '-thongtin-' + name_url
                        if not os.path.exists(duongdan+'/images/thongtin/%s-thongtin-%s.jpg'%(str(bv.id),name_url)):
                            folder_hinh_baiviet = duongdan + '/images/thongtin'
                            self.pool.get('yhoc_thongtin').ghihinhxuong(folder_hinh_baiviet, filename, bv.hinhdaidien, 95,125, context=context)
                        photo = domain + '/images/thongtin/%s.jpg' %(filename)
#                        path_hinh_ghixuong = duongdan + '/thongtin/%s/images/anhbaiviet.jpg'%(bv.id)
#                        if not os.path.exists(path_hinh_ghixuong):
#                            fw = open(path_hinh_ghixuong,'wb')
#                            fw.write(base64.decodestring(bv.hinhdaidien))
#                            fw.close()
#                        photo = '../../thongtin/%s/images/anhbaiviet.jpg' %(bv.id,)
                    sidebar_menu_tab = sidebar_menu_tab_.replace('__IMAGE__',photo)
                    sidebar_menu_tab = sidebar_menu_tab.replace('__NAME__',bv.name)
                    sidebar_menu_tab = sidebar_menu_tab.replace('__LINK__','../../../../../../%s'%(bv.link_url))
                    all_sidebar_menu_tab += sidebar_menu_tab 
            
            import codecs
            fw = codecs.open(folder_trangchu +'/baivietnoibac.html','w','utf-8')
            fw.write(str(all_sidebar_menu_tab))
            fw.close()
    
    def capnhat_tag(self, cr, uid, tag_ids, tt_id, context=None):
        duongdan = self.pool.get('hlv.property')._get_value_project_property_by_name(cr, uid, 'path of template')
        domain = self.pool.get('hlv.property')._get_value_project_property_by_name(cr, uid, 'Domain') or '../..'
        kieufile = self.pool.get('hlv.property')._get_value_project_property_by_name(cr, uid, 'Kiểu lưu file') or 'html'
        if os.path.exists(duongdan+'/template/tags/index.html'):
            fr = open(duongdan+'/template/tags/index.html', 'r')
            template_ = fr.read()
            fr.close()
        else:
            template_ = ''
            
        if os.path.exists(duongdan+'/template/tags/tag_item.html'):
            fr = open(duongdan+'/template/tags/tag_item.html', 'r')
            item_ = fr.read()
            fr.close()
        else:
            item_ = ''
                
        for t in tag_ids:  
            name = self.pool.get('yhoc_trangchu').parser_url(t.name)          
            folder_tags = duongdan + '/tags/%s' %str(name)
            if not os.path.exists(folder_tags):
                os.makedirs(folder_tags)
            
            if not os.path.exists(folder_tags +'/tag_item.html'):
                import codecs  
                fw = codecs.open(folder_tags +'/tag_item.html','w','utf-8')
                fw.write('<!--NEWITEM-->')
                fw.close()
            fr = open(folder_tags+'/tag_item.html', 'r')
            tag_item_ = fr.read()
            fr.close()
            
            thongtin = self.pool.get('yhoc_thongtin').browse(cr, uid, tt_id, context=context)
            find = tag_item_.count(thongtin.name) 
            if find == 0:
                item = item_.replace('__NGUOIHIEUDINH__', thongtin.nguoihieudinh.name or '')
                item = item.replace('__LINKNGUOIHIEUDINH__', thongtin.nguoihieudinh.link or '#')
                item = item.replace('__DANHXUNGHD__', thongtin.nguoihieudinh.danhxung or '')
                
                item = item.replace('__DANHXUNGNT__',thongtin.nguoidich.danhxung or '')
                item = item.replace('__NGUOIDICH__',thongtin.nguoidich.name)
                item = item.replace('__LINKNGUOIDICH__',thongtin.nguoidich.link or '#')
                
                item = item.replace('__NAME__',thongtin.name or '')
                item = item.replace('__NGAYTAO__',thongtin.date)
                item = item.replace('__MOTANGAN__',thongtin.motangan or '(Chưa cập nhật)')
                item = item.replace('__LINK__','../../../../../../%s'%(thongtin.link_url))
                name_url = self.pool.get('yhoc_trangchu').parser_url(str(thongtin.name))
                item = item.replace('__IMAGE__',domain + '/images/thongtin/%s-thongtin-%s.jpg'%(str(thongtin.id),name_url))                
                tag_item_ = tag_item_.replace('<!--NEWITEM-->',item)

            
            
            template = template_.replace('__TAGNAME__', t.name)
            template = template.replace('__SIDEBARMENU__', '''<?php include("../../trangchu/vi/baivietnoibac.html")?>''')
            template = template.replace('__CHUDENOIBAC__', '''<?php include("../../trangchu/vi/duanhoanthanh.html")?>''')
            import codecs  
            fw = codecs.open(folder_tags +'/tag_item.html','w','utf-8')
            fw.write(tag_item_)
            fw.close()
            
            fw = codecs.open(folder_tags +'/index.%s'%kieufile,'w','utf-8')
            fw.write(template)
            fw.close()
            
            
        return True
    
    def tukhoalienquan(self,cr,uid,context=None):
        
        return 0
yhoc_keyword()
    






class yhoc_search_kw(osv.osv):
    _name = "yhoc_search_kw"
    _columns = {
                'name':fields.char('Search',size=500),
                }
    
    def create(self, cr, uid, vals,context=None):
        vanban = self.browse(cr, uid, 1, context=context)
        chuoi = self.pool.get('x_vanban').khongdau(vanban.name)
        sql = '''  select id,loai
                        from 
                        (
                            (select id, search_khongdau,ngayky, 'vbden' as loai from x_vanban_den where phobien = 'xahoi')
                            union
                            (select id, search_khongdau,ngayky, 'vbdi' as loai from x_vanban where phobien = 'xahoi')
                            order by ngayky desc
                        ) as kq
                        where search_khongdau ilike '%'''+chuoi+'''%'
                           '''
        cr.execute(sql)
        vanban_ids = cr.dictfetchall()
        
        duongdan = self.pool.get('hlv.property')._get_value_project_property_by_name(cr, uid, 'path of template')
        domain = self.pool.get('hlv.property')._get_value_project_property_by_name(cr, uid, 'Domain') or '../..'
        kieufile = self.pool.get('hlv.property')._get_value_project_property_by_name(cr, uid, 'Kiểu lưu file') or 'html'
#        
#        fr= open(duongdan+'/template/index_search.html', 'r')
#        template_ = fr.read()
#        fr.close()
#
#        fr= open(duongdan+'/template/search_tab.html', 'r')
#        search_tab_ = fr.read()
#        fr.close()
#        
#        
#        noidungvanban = ''
#        for i in range(0,len(vanban_ids)):
#            if vanban_ids[i]['loai'] == 'vbdi':
#                vanban = self.pool.get('x_vanban').browse(cr, uid, vanban_ids[i]['id'], context=context)
#                noibanhanh = 'ĐH Nguyễn Tất Thành'
#            else:
#                vanban = self.pool.get('x_vanban_den').browse(cr, uid, vanban_ids[i]['id'], context=context)
#                noibanhanh = vanban.noibanhanh.name or ''
#            search_tab = ''                    
#            search_tab = search_tab_.replace('__SOVAOSO__', vanban.name or '')
#            search_tab = search_tab.replace('__LOAIVANBAN__', vanban.loaivanban.name or '')
#            search_tab = search_tab.replace('__TRICHYEU__', vanban.trich_yeu or '')
#            search_tab = search_tab.replace('__NGAYBANHANH__', vanban.ngayky or '')
#            search_tab = search_tab.replace('__LINKVANBAN__', '%s/index.%s'%(vanban.id,kieufile))
#            search_tab = search_tab.replace('__NGUOIKY__', vanban.nguoiky.name or '')
#            noidungvanban += search_tab
#            
#        template = template_.replace('__NOIDUNGVANBAN__', noidungvanban)
        import codecs  
        fw= codecs.open(duongdan+'/search_result.php','w','utf-8')
        fw.write('1111111111111')
        fw.close()
        return True
        
yhoc_search_kw()

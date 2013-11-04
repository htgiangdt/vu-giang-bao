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

    
    _columns = {
        'name': fields.char('Keyword', size=500, required=1),
        'priority': fields.integer('Priority'),
        'thongtin_ids': fields.many2many('yhoc_thongtin', 'thongtin_keyword_rel', 'keyword_id', 'thongtin_id', 'Keyword'),
        'soluongxem': fields.integer("Số lượng người xem"),
        'description':fields.text('Giới thiệu'),
        'kwlienquan_ids': fields.many2many('yhoc_keyword', 'keyword_kwlienquan_rel', 'keyword_id', 'kwlienquan_id', 'Từ khóa liên quan'),
    }

    _defaults = {
    }
    
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
    
    

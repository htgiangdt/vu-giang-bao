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
                       'solanxuathien':diem,
                       'solanroot':k['solanxuathien']})
        import operator
#        aa = sorted(kq.items(), key=lambda x: x[1])
        d = sorted(kq, key = lambda user: (user['solanxuathien']))
        kq_fn = []
        for i in range(1,len(d)):
            x = (d[len(d)-i]['solanxuathien']*d[len(d)-i]['solanxuathien'])/d[len(d)-i]['solanroot']
            kq_fn.append({'keyword_id':d[len(d)-i]['keyword_id'],
                       'solanxuathien':x})
        
        print kq_fn    
        kq_fn = sorted(kq_fn, key = lambda user: (user['solanxuathien']))
            
#        print '==================='
#        print kq
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
            dp_1 = self.search(cr,uid,[('name','ilike','%'+record.name+'%'),('name','!=',record.name)])
            
            if len(dp_1)<11:
                for i in dp_1:
                    result[record.id].append(i)
            else:
                for i in range(0,11):
                    result[record.id].append(dp_1[i])
            dp_2 = []
            id_dp_2 = self.search(cr,uid,[])
            for id in id_dp_2:
                r = self.browse(cr, uid, id, context=context)
                if (r.name in record.name and r.name != record.name):
                    dp_2.append(id)
                    
            if len(dp_2)<9:       
                for i in dp_2:
                    result[record.id].append(i)
            else:
                for i in range(0,9):
                    result[record.id].append(pd_2[i])
                
            if len(kq_fn)<8:
                for kw in kq_fn:
                    result[record.id].append(kw['keyword_id'])
            else:
                for i in range(0,8):
                    result[record.id].append(kq_fn[i]['keyword_id'])
        return result
    
    def _get_baivietmoi(self, cr, uid, ids, field_name, arg, context=None):
        result = {}
        for record in self.browse(cr, uid, ids, context=context):
            dsbaivietmoi = self.pool.get('yhoc_thongtin').search(cr, uid, [('state','=','done'),('keyword_ids','=',record.id)], limit=8, order='date desc', context=context)
            result[record.id] = []
            for bv in self.pool.get('yhoc_thongtin').browse(cr, uid, dsbaivietmoi, context=context):
                result[record.id].append(bv.id)
        return result
    
    def _get_baivietnoibac(self, cr, uid, ids, field_name, arg, context=None):
        result = {}
        for record in self.browse(cr, uid, ids, context=context):
            dsbaiviet = self.pool.get('yhoc_thongtin').search(cr, uid, [('state','=','done'),('keyword_ids','=',record.id)], limit=10, order='soluongxem desc', context=context)
            result[record.id] = []
            for bv in self.pool.get('yhoc_thongtin').browse(cr, uid, dsbaiviet, context=context):
                result[record.id].append(bv.id)
        return result
    
    def _get_baivietbanner(self, cr, uid, ids, field_name, arg, context=None):
        result = {}
        for record in self.browse(cr, uid, ids, context=context):
            dsbaiviet = self.pool.get('yhoc_thongtin').search(cr, uid, [('state','=','done'),('hinhlon','!=',False),('keyword_ids','=',record.id)], limit=30, order='soluongxem desc', context=context)
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
        if 'khongdau' not in vals or ('khongdau' in vals and vals['khongdau']==False):
            name_url = self.pool.get('yhoc_trangchu').parser_url(vals['name'])
            vals.update({'khongdau':name_url})
        return super(yhoc_keyword,self).create(cr,uid,vals,context=context)
    
    def write(self,cr, uid, ids, vals, context=None):
#        self.pool.get('yhoc_search_kw').create(cr, uid,{'name':'123'},context=context)
        r = self.browse(cr, uid, ids[0], context=context)
        if 'name' in vals:
            name_url = self.pool.get('yhoc_trangchu').parser_url(str(vals['name']))
            vals.update({'khongdau':name_url})
        elif 'khongdau' not in vals and not r.khongdau:
            name_url = self.pool.get('yhoc_trangchu').parser_url(str(r.name))
            vals.update({'khongdau':name_url})
        return super(yhoc_keyword,self).write(cr, uid, ids, vals, context=context)
    
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
            template = template.replace('__ID_TAG__', str(t.id))
            baivietnoibac = t.baivietnoibac
            #self.pool.get('yhoc_trangchu').capnhat_baivietnoibac(cr,uid, baivietnoibac, folder_tags, domain, kieufile, context=context)
            #template = template.replace('__SIDEBARMENU__', '''<?php include("%s/tags/%s/baivietnoibac.html")?>'''%(domain,name))
            #template = template.replace('__CHUDENOIBAC__', '''<?php include("../../trangchu/vi/duanhoanthanh.html")?>''')
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
                'khongdau':fields.char('Search',size=500),
                'soluottim':fields.integer('Số lượt tìm'),
                }
    
    def create(self, cr, uid, vals,context=None):
        keyword = self.browse(cr, uid, 1, context=context)
        chuoi = self.pool.get('yhoc_trangchu').parser_url(keyword.name)
        
        cr.execute('''select id from yhoc_search_kw where khongdau='%s' and id not in (1,-1)'''%chuoi)
        ids = map(lambda x: x[0], cr.fetchall())
        if not ids:            
            vals={}
            vals.update({'name':keyword.name,
                         'khongdau':chuoi})
            super(yhoc_search_kw,self).create(cr, uid, vals,context=context)
#            cr.execute('''insert into yhoc_search_kw(id,name,khongdau) values('%s','%s')'''%(keyword.name,chuoi))
        else:
            k = self.browse(cr, uid, ids[0], context=context)
            cr.execute('''update yhoc_search_kw set name = '%s', khongdau = '%s',soluottim=%s where id=%s'''%(keyword.name,chuoi,k.soluottim+1,ids[0]))
        
        
        
        
#        chuoi = self.pool.get('yhoc_trangchu').parser_url('bệnh ung thư')
        kqsearch = self.pool.get('yhoc_keyword').search(cr, uid, [('khongdau','=',chuoi)])
                
        duongdan = self.pool.get('hlv.property')._get_value_project_property_by_name(cr, uid, 'path of template')
        domain = self.pool.get('hlv.property')._get_value_project_property_by_name(cr, uid, 'Domain') or '../..'
        kieufile = self.pool.get('hlv.property')._get_value_project_property_by_name(cr, uid, 'Kiểu lưu file') or 'html'
        
        fr= open(duongdan+'/template/search/search_index.html', 'r')
        template_ = fr.read()
        fr.close()

        fr= open(duongdan+'/template/search/search_tag_item.html', 'r')
        search_tab_ = fr.read()
        fr.close()
        
        template = template_.replace('__SIDEBARMENU__', '''<?php include("trangchu/vi/baivietnoibac.html")?>''')
        template = template.replace('__CHUDENOIBAC__', '''<?php include("trangchu/vi/duanhoanthanh.html")?>''')
        
        noidungkeyword = ''
        if kqsearch:
#            keyword_ids = self.pool.get('yhoc_thongtin').search(cr, uid, [('keyword_ids','=',kqsearch[0])])
#            
#            for i in range(0,len(keyword_ids)):
#                thongtin = self.pool.get('yhoc_thongtin').browse(cr, uid, keyword_ids[i], context=context)
#                search_tab = ''                    
#                search_tab = search_tab_.replace('__NGUOIHIEUDINH__', thongtin.nguoihieudinh.name or '')
#                search_tab = search_tab.replace('__LINKNGUOIHIEUDINH__', thongtin.nguoihieudinh.link or '#')
#                search_tab = search_tab.replace('__DANHXUNGHD__', thongtin.nguoihieudinh.danhxung or '')
#                
#                search_tab = search_tab.replace('__DANHXUNGNT__',thongtin.nguoidich.danhxung or '')
#                search_tab = search_tab.replace('__NGUOIDICH__',thongtin.nguoidich.name)
#                search_tab = search_tab.replace('__LINKNGUOIDICH__',thongtin.nguoidich.link or '#')
#                
#                search_tab = search_tab.replace('__NAME__',thongtin.name or '')
#                search_tab = search_tab.replace('__NGAYTAO__',thongtin.date)
#                search_tab = search_tab.replace('__MOTANGAN__',thongtin.motangan or '(Chưa cập nhật)')
#                search_tab = search_tab.replace('__LINK__','../../../../../../%s'%(thongtin.link_url))
#                name_url = self.pool.get('yhoc_trangchu').parser_url(str(thongtin.name))
#                search_tab = search_tab.replace('__IMAGE__',domain + '/images/thongtin/%s-thongtin-%s.jpg'%(str(thongtin.id),name_url))
#                noidungkeyword += search_tab
#                       
#            
            kqsearch = self.pool.get('yhoc_keyword').browse(cr, uid, kqsearch[0],context=context)
            name = self.pool.get('yhoc_trangchu').parser_url(kqsearch.name)
            redirect = '''<script language="javascript" type="text/javascript">window.location.href="../../tags/%s/index.php";</script>'''%name
            template = template.replace('__TAGNAME__', redirect)
            
            
        else:
            template = template.replace('__TAGNAME__', keyword.name)
            kqsearch = self.pool.get('yhoc_keyword').search(cr, uid, [('khongdau','ilike','%'+chuoi+'%')])
            if kqsearch:
                temp_ = '''<a href="__LINK__">__NAME__</a>'''
                for kq in kqsearch:
                    kq = self.pool.get('yhoc_keyword').browse(cr,uid,kq,context=context)
                    temp = ''
                    name = self.pool.get('yhoc_trangchu').parser_url(kq.name)
                    temp = temp_.replace('__LINK__',domain+'/tags/'+name)
                    temp = temp.replace('__NAME__', kq.name)
                    noidungkeyword += temp
            else:
                noidungkeyword = 'Không tìm thấy kết quả'
                
               
        import codecs  
        fw = codecs.open(duongdan +'/search_item.html','w','utf-8')
        fw.write(noidungkeyword)
        fw.close()
        
        fw = codecs.open(duongdan +'/search_result.%s'%kieufile,'w','utf-8')
        fw.write(template)
        fw.close()
        return True
        
yhoc_search_kw()

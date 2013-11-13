# -*- encoding: utf-8 -*-
from osv import fields,osv
from tools.translate import _
import time
from datetime import datetime, date
import os
import base64,os,re
import sys
import codecs
from bsddb.dbtables import _columns
reload(sys)
sys.setdefaultencoding("utf8")

class x_lienket(osv.osv):
    _name = 'x_lienket'
    _columns = {
                'name':fields.char("Tên",size=100, required='1'),
                'photo': fields.binary('Photo'),
                'url':fields.char("URL", size=500, required='1'),
                'datas_fname': fields.char('Filename',size=256),
                'sequence':fields.integer("Thứ tự hiện"),
                'trangchu_id':fields.many2one('yhoc_trangchu','Trang chủ'),
                'description': fields.text('Mô tả ngắn'),
                }
x_lienket()
    
class yhoc_trangchu(osv.osv):
    _name = "yhoc_trangchu"
    
    
    def _get_baivietmoi(self, cr, uid, ids, field_name, arg, context=None):
        result = {}
        dsbaivietmoi = self.pool.get('yhoc_thongtin').search(cr, uid, [('state','=','done')], limit=8, order='date desc', context=context)  
        for record in self.browse(cr, uid, ids, context=context):
            result[record.id] = []
            for bv in self.pool.get('yhoc_thongtin').browse(cr, uid, dsbaivietmoi, context=context):
                result[record.id].append(bv.id)
        return result
    
    def _get_baivietnoibac(self, cr, uid, ids, field_name, arg, context=None):
        result = {}
        dsbaiviet = self.pool.get('yhoc_thongtin').search(cr, uid, [('state','=','done')], limit=30, order='soluongxem desc', context=context)  
        for record in self.browse(cr, uid, ids, context=context):
            result[record.id] = []
            for bv in self.pool.get('yhoc_thongtin').browse(cr, uid, dsbaiviet, context=context):
                result[record.id].append(bv.id)
        return result
    
    def _get_duanhoanthanh(self, cr, uid, ids, field_name, arg, context=None):
        result = {}
        sql = '''select duan_done.duan 
                 from 
                    (select count(t.id) as sobaiviet,t.duan 
                        from yhoc_thongtin t, yhoc_duan d 
                        where t.duan = d.id
                            and state='done'
                        group by t.duan) as duan_done,
                    
                    (select count(t.id) as sobaiviet,t.duan 
                    from yhoc_thongtin t, yhoc_duan d 
                    where t.duan = d.id
                    group by t.duan) as duan_all
                where duan_done.duan = duan_all.duan
                        and duan_done.sobaiviet= duan_all.sobaiviet
                    '''
        cr.execute(sql)
        duanhoanchinh = cr.fetchall()  
        for record in self.browse(cr, uid, ids, context=context):
            result[record.id] = []
            for da in self.pool.get('yhoc_duan').browse(cr,uid,[x[0] for x in duanhoanchinh],context={}):
                result[record.id].append(da.id)
        return result
        
    _columns = {
                'name':fields.char("Tên",size=500, required='1'),
                'banner': fields.one2many('x_lienket', 'trangchu_id', 'Banner'),
                'chudenoibac':fields.function(_get_baivietnoibac, type='many2many', relation='yhoc_thongtin', string='Bài viết nổi bậc'),
                'baivietmoi':fields.function(_get_baivietmoi, type='many2many', relation='yhoc_thongtin', string='Bài viết mới'),
                'muctieu': fields.text('Ý tưởng và mục tiêu'),
                'thungo': fields.text('Thư ngỏ'),
                'duanhoanthanh': fields.function(_get_duanhoanthanh, type='many2many', relation='yhoc_duan', string='Dự án hoàn thành'),
                }
    _defaults={
              
               }
    
    def write(self, cr, uid, ids, vals, context=None):
        self.auto_capnhat(cr, uid)
        return super(yhoc_trangchu,self).write(cr, uid, ids, vals, context=context)
    
    def capnhat_alltag(self, cr, uid, ids, context=None):
        duongdan = self.pool.get('hlv.property')._get_value_project_property_by_name(cr, uid, 'path of template')
        domain = self.pool.get('hlv.property')._get_value_project_property_by_name(cr, uid, 'Domain') or '../..'
        kieufile = self.pool.get('hlv.property')._get_value_project_property_by_name(cr, uid, 'Kiểu lưu file') or 'html'
        all_tag = self.pool.get('yhoc_keyword').search(cr, uid, [], context=context)
        for t in all_tag:
            t = self.pool.get('yhoc_keyword').browse(cr, uid, t, context=context)
            if t.thongtin_ids:
                
                name = self.pool.get('yhoc_trangchu').parser_url(t.name)
                
                if os.path.exists(duongdan+'/template/tags/index.html'):
                    fr = open(duongdan+'/template/tags/index.html', 'r')
                    template_ = fr.read()
                    fr.close()
                else:
                    template_ = ''
                    
                folder_tags = duongdan + '/tags/%s' %str(name)
                if not os.path.exists(folder_tags):
                    os.makedirs(folder_tags)                
                if os.path.exists(folder_tags +'/tag_item.html'):
                    os.remove(folder_tags +'/tag_item.html')
                
                
                import codecs  
                fw = codecs.open(folder_tags +'/tag_item.html','w','utf-8')
                fw.write('<!--NEWITEM-->')
                fw.close()
                
                fr = open(folder_tags+'/tag_item.html', 'r')
                tag_item_ = fr.read()
                fr.close()
                
                if os.path.exists(duongdan+'/template/tags/tag_item.html'):
                    fr = open(duongdan+'/template/tags/tag_item.html', 'r')
                    item_ = fr.read()
                    fr.close()
                else:
                    item_ = ''
            
                for thongtin in t.thongtin_ids:
                    item = item_.replace('__NGUOIHIEUDINH__', thongtin.nguoihieudinh.name or '')
                    item = item.replace('__LINKNGUOIHIEUDINH__', thongtin.nguoihieudinh.link or '#')
                    item = item.replace('__DANHXUNGHD__', thongtin.nguoihieudinh.danhxung or '')
                    
                    item = item.replace('__DANHXUNGNT__',thongtin.nguoidich.danhxung or '')
                    item = item.replace('__NGUOIDICH__',thongtin.nguoidich.name)
                    item = item.replace('__LINKNGUOIDICH__',thongtin.nguoidich.link or '#')
                    
                    item = item.replace('__NAME__',thongtin.name or '')
                    item = item.replace('__NGAYTAO__',thongtin.date or '')
                    item = item.replace('__MOTANGAN__',thongtin.motangan or '(Chưa cập nhật)')
                    #Giang_0511#item = item.replace('__LINK__','../../../../../../%s'%(thongtin.link_url))
                    item = item.replace('__LINK__',domain + '/%s/'%(thongtin.link_url))
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
                
    def capnhat_allduan(self, cr, uid, ids=None, context=None):
        duan = self.pool.get('yhoc_duan').search(cr, uid, [])
        for da in duan:
            self.pool.get('yhoc_duan').capnhat_thongtin(cr,uid,[da], context)
        return True
    
    def capnhat_allchude(self, cr, uid, ids=None, context=None):
        chude = self.pool.get('yhoc_chude').search(cr, uid, [])
        for cd in chude:
            self.pool.get('yhoc_chude').capnhat_thongtin(cr,uid,[cd],context)
            #Giang#0911- Cap Nhat RSS Chu De
            self.pool.get('yhoc_chude').capnhat_rsschude(cr,uid,[cd],context)
        self.pool.get('yhoc_chude').taotrangrss(cr, uid, context)
        return True
    
    def capnhat_allthanhvien(self, cr, uid, ids=None, context=None):
        user = self.pool.get('hr.employee').search(cr, uid, [], context=context)
        for u in user:
            self.pool.get('hr.employee').capnhat_thongtin(cr, uid, [u], context=context)
        return True
    
    def capnhat_alltin(self, cr, uid, ids=None, context=None):
        tintuc = self.pool.get('yhoc_thongtin').search(cr, uid, [('state','=','done')])
        for tt in tintuc:
            self.pool.get('yhoc_thongtin').xuatban_thongtin(cr,uid,[tt])
        return True
    
    def capnhat_allnganh(self, cr, uid, ids=None, context=None):
        nganh = self.pool.get('yhoc_nganh').search(cr, uid, [])
        for tt in nganh:
            self.pool.get('yhoc_nganh').capnhat_thongtin(cr,uid,[tt])
        return True
    
    def auto_capnhat(self,cr, uid):
        duongdan = self.pool.get('hlv.property')._get_value_project_property_by_name(cr, uid, 'path of template')
        obj = ['yhoc_thongtin', 'yhoc_duan', 'yhoc_chude', 'hr.employee', 'yhoc_nganh']
        from random import choice
        import random
        ran_obj = random.randint(0,4)
        error = False
        if os.path.exists(duongdan+'/cron_log.txt'):
            fr = open(duongdan+'/cron_log.txt', 'r')
            log = fr.read()
            fr.close()
        try :
            if obj[ran_obj] == 'yhoc_thongtin':
                list_item = self.pool.get(obj[ran_obj]).search(cr, uid, [('state','=','done')])
                item = choice(list_item)
                self.pool.get(obj[ran_obj]).xuatban_thongtin(cr,uid,[item],{})
            else:
                list_item = self.pool.get(obj[ran_obj]).search(cr, uid, [])
                item = choice(list_item)
                self.pool.get(obj[ran_obj]).capnhat_thongtin(cr,uid,[item],{})
        except:
            error = True
        
        if error:
            log += '<' + str(obj[ran_obj]) + '-' + str(item) +'>'
        else:
            log += '[' + str(obj[ran_obj]) + '-' + str(item) +']'

        
        import codecs  
        fw= codecs.open(duongdan+'/cron_log.txt','w','utf-8')
        fw.write(log)
        fw.close()
        return True

    def unlink(self,cr, uid, ids, context=None):
        raise osv.except_osv('Warning!', 'Bạn không thể xóa trang chủ!')
    
    def capnhat_header(self, cr, uid, chudecha, duongdan, domain, folder_trangchu, context=None):
        kieufile = self.pool.get('hlv.property')._get_value_project_property_by_name(cr, uid, 'Kiểu lưu file') or 'html'
        header_template = ''
        if os.path.exists(duongdan+'/template/trangchu/header.html'):
            #Doc file header
            fr = open(duongdan+'/template/trangchu/header.html', 'r')
            header_template = fr.read()
            fr.close()
        
#Doc file root menu tab
            root_menu = '' 
            all_sub_menu = ''
            all_sidebar_menu_tab = ''      
            for chude in chudecha:
                chude = self.pool.get('yhoc_chude').browse(cr, uid, chude, context=context)
                if chude.link:
                    root_menu_tab = '''<li><a href="__LINK__" rel="__REL__" __TRIGGER__>__TENMENU__</a></li>'''
                    #Giang_0511#root_menu_tab = root_menu_tab.replace('__LINK__', '../../../../../../%s/'%(chude.link_url))
                    root_menu_tab = root_menu_tab.replace('__LINK__', domain + '/%s/'%(chude.link_url))
                    root_menu_tab = root_menu_tab.replace('__REL__', 'item'+str(chude.id))
                    root_menu_tab = root_menu_tab.replace('__TENMENU__', chude.name)
                    
                    chudecon_da = self.pool.get('yhoc_duan').search(cr, uid, [('chude_id','=',chude.id)])
                    chudecon_cd = self.pool.get('yhoc_chude').search(cr, uid, [('parent_id','=',chude.id)])
                    chudecon = chudecon_da + chudecon_cd
                    sub_menu_tab = ''
                    if chudecon:
                        all_item_sub_menu = ''
                        root_menu_tab = root_menu_tab.replace('__TRIGGER__', 'class="trigger"')
                        #doc sub menu tab
                        fr = open(duongdan+'/template/trangchu/sub_menu_tab.html', 'r')
                        sub_menu_tab = fr.read()
                        fr.close()
                        sub_menu_tab = sub_menu_tab.replace('__REL__', 'item'+str(chude.id))
                        for cd in chudecon_cd:
                            cd = self.pool.get('yhoc_chude').browse(cr, uid, cd, context=context)
                            if cd.link:
                                item_sub_menu_tab = '''<li><a href="__LINK__" >__NAME__</a></li>'''
                                #Giang_0511#item_sub_menu_tab = item_sub_menu_tab.replace('__LINK__', '../../../../../../%s/'%(cd.link_url))
                                item_sub_menu_tab = item_sub_menu_tab.replace('__LINK__', domain + '/%s/'%(cd.link_url))
                                item_sub_menu_tab = item_sub_menu_tab.replace('__NAME__', cd.name)
                                all_item_sub_menu += item_sub_menu_tab
                            
                        for cd in chudecon_da:
                            cd = self.pool.get('yhoc_duan').browse(cr, uid, cd, context=context)
                            if cd.link:
                                item_sub_menu_tab = '''<li><a href="__LINK__" >__NAME__</a></li>'''
                                #Giang_0511#item_sub_menu_tab = item_sub_menu_tab.replace('__LINK__', '../../../../../../%s/'%(cd.link_url))
                                item_sub_menu_tab = item_sub_menu_tab.replace('__LINK__', domain + '/%s/'%(cd.link_url))
                                item_sub_menu_tab = item_sub_menu_tab.replace('__NAME__', cd.name)
                                all_item_sub_menu += item_sub_menu_tab
                            
                        sub_menu_tab = sub_menu_tab.replace('__ITEMSUBMENU__', all_item_sub_menu)
                    else:
                        root_menu_tab = root_menu_tab.replace('__TRIGGER__', '')
                    root_menu += root_menu_tab
                    all_sub_menu += sub_menu_tab
            
            header_template = header_template.replace('__ROOTMENU__', root_menu)
            header_template = header_template.replace('__SUBMENU__', all_sub_menu)
            
            #Cap nhat link cong dong bac si
            dsnganh = self.pool.get('yhoc_nganh').search(cr, uid, [('name','!=','Công nghệ thông tin'),('link','!=',False)], limit=1, context=context)
            if dsnganh:
                nganh = self.pool.get('yhoc_nganh').browse(cr, uid, dsnganh[0], context=context)
                #Giang_0511#header_template = header_template.replace('__LINKCONGDONGBS__', '../../../../../../nganh/%s/'%(nganh.id))
                #Giang_0811#header_template = header_template.replace('__LINKCONGDONGBS__', domain + '/nganh/%s/'%(nganh.id))
                header_template = header_template.replace('__LINKCONGDONGBS__','%s'%(nganh.link))
            else:
                header_template = header_template.replace('__LINKCONGDONGBS__', '#')
#Doc file menu san pham tab
            header_template = header_template.replace('__KIEUFILE__', kieufile)
            header_template = header_template.replace('__DOMAIN__', domain)
            if not os.path.exists(folder_trangchu):
                os.makedirs(folder_trangchu)    
            fw = codecs.open(folder_trangchu + '/header.html','w','utf-8')
            fw.write(header_template)
            fw.close()
        return header_template
    
    #Giang_0511#def capnhat_footer(self, cr, uid, chudecha, duongdan, folder_trangchu,context=None):
    def capnhat_footer(self, cr, uid, chudecha, duongdan, domain, folder_trangchu,context=None):
        #Doc file footer
        kieufile = self.pool.get('hlv.property')._get_value_project_property_by_name(cr, uid, 'Kiểu lưu file') or 'html'
        li_tab_ = '''<li><a href="__LINK__">__NAME__</a></li>'''
        
        if os.path.exists(duongdan+'/template/trangchu/footer.html'):
            fr = open(duongdan+'/template/trangchu/footer.html', 'r')
            footer_template = fr.read()
            fr.close()
        else:
            footer_template = ''
            
        chunkyfootercolumn_ = ''
        if os.path.exists(duongdan+'/template/trangchu/footer_menu.html'):
            fr = open(duongdan+'/template/trangchu/footer_menu.html', 'r')
            chunkyfootercolumn_ = fr.read()
            fr.close()
        
        footer_menu = ''
        for chude in chudecha:
             
            chude = self.pool.get('yhoc_chude').browse(cr, uid, chude, context=context)
            if chude.link:
                #Giang_0511#chunkyfootercolumn = chunkyfootercolumn_.replace('__LINK_CHUDECHA__', '../../../../../../%s/'%(chude.link_url))
                chunkyfootercolumn = chunkyfootercolumn_.replace('__LINK_CHUDECHA__',domain + '/%s/'%(chude.link_url))
                chunkyfootercolumn = chunkyfootercolumn.replace('__NAME_CHUDECHA__', chude.name)
                
                chudecon_da = self.pool.get('yhoc_duan').search(cr, uid, [('chude_id','=',chude.id)])
                chudecon_cd = self.pool.get('yhoc_chude').search(cr, uid, [('parent_id','=',chude.id)])
                chudecon = chudecon_da + chudecon_cd
                sub_menu_tab = ''
                if chudecon:
                    all_item_sub_menu = ''
                    #doc sub menu tab
                    for cd in chudecon_cd:
                        cd = self.pool.get('yhoc_chude').browse(cr, uid, cd, context=context)
                        if cd.link:
                            #Giang_0511#li_tab = li_tab_.replace('__LINK__', '../../../../../../%s/'%(cd.link_url))
                            li_tab = li_tab_.replace('__LINK__', domain + '/%s/'%(cd.link_url))
                            li_tab = li_tab.replace('__NAME__', cd.name)
                            all_item_sub_menu += li_tab
                        
                    for cd in chudecon_da:
                        cd = self.pool.get('yhoc_duan').browse(cr, uid, cd, context=context)
                        if cd.link:
                            #Giang_0511#li_tab = li_tab_.replace('__LINK__', '../../../../../../%s/'%(cd.link_url))
                            li_tab = li_tab_.replace('__LINK__', domain + '/%s/'%(cd.link_url))
                            li_tab = li_tab.replace('__NAME__', cd.name)
                            all_item_sub_menu += li_tab
                        
                    chunkyfootercolumn = chunkyfootercolumn.replace('__CHUDECON__', all_item_sub_menu)
                    footer_menu += chunkyfootercolumn
                    
        footer_template = footer_template.replace('__FOOTER_MENU__', footer_menu)  
        if not os.path.exists(folder_trangchu):
            os.makedirs(folder_trangchu)    
        fw = codecs.open(folder_trangchu + '/footer.html','w','utf-8')
        fw.write(footer_template)
        fw.close()
        return footer_template
    
#    def capnhat_chude(self,cr,uid,ids=None,context=None):
#        self.capnhat_trangchu(cr, uid, [1], context=context)
#        chude = self.pool.get('yhoc_chude').search(cr, uid, [], context=context)
#        for cd in chude:
#            self.pool.get('yhoc_chude').capnhat_thongtin(cr, uid, [cd], context=context)
#        
#        domain = self.pool.get('hlv.property')._get_value_project_property_by_name(cr, uid, 'Domain') or '../..'
#        duongdan = self.pool.get('hlv.property')._get_value_project_property_by_name(cr, uid, 'path of template')
#        folder_trangchu = duongdan + '/trangchu/vi'
#        chudecha = self.pool.get('yhoc_chude').search(cr, uid, [('parent_id','=',False)])
#        self.capnhat_footer(cr, uid, duongdan, folder_trangchu, context=context)
#        self.capnhat_header(cr, uid, chudecha, duongdan, domain, folder_trangchu, context=context)
#        return True
    
#    def capnhat_duan(self,cr,uid,ids=None,context=None):
#        self.capnhat_trangchu(cr, uid, [1], context=context)
#        duan = self.pool.get('yhoc_duan').search(cr, uid, [], context=context)
#        for da in duan:
#            self.pool.get('yhoc_duan').capnhat_thongtin(cr, uid, [da], context=context)
#        
#        return True
    
#    def capnhat_baiviet(self,cr,uid,ids=None,context=None):
#        self.capnhat_trangchu(cr, uid, [1], context=context)
#        baiviet = self.pool.get('hlv_thongtin').search(cr, uid, [('state','=','done')], context=context)
#        
#        for bv in baiviet:
#            self.pool.get('hlv_thongtin').xuatban_thongtin(cr, uid, [bv], context=context)
#        
#        
#        duan = self.pool.get('yhoc_duan').search(cr, uid, [], context=context)
#        for da in duan:
#            self.pool.get('yhoc_duan').capnhat_thongtin(cr, uid, [da], context=context)
#        
#        return True
    
#    def capnhat_employee(self,cr,uid,ids=None,context=None):
#        self.capnhat_trangchu(cr, uid, [1], context=context)
#        user = self.pool.get('hr.employee').search(cr, uid, [], context=context)
#        for u in user:
#            self.pool.get('hr.employee').capnhat_thongtin(cr, uid, [u], context=context)
#        
#        self.capnhat_trangchu(cr, uid, [1], context)
#        return True
    
#    def capnhat_partner(self,cr,uid,ids=None,context=None):
#        self.capnhat_trangchu(cr, uid, [1], context=context)
#        cus = self.pool.get('res.partner').search(cr, uid, [], context=context)
#        for c in cus:
#            self.pool.get('res.partner').capnhat_thongtin(cr, uid, [c], context=context)
#        
#        self.capnhat_trangchu(cr, uid, [1], context)
#        return True
    
#    def capnhat_nganh(self,cr,uid,ids=None,context=None):
#        self.capnhat_trangchu(cr, uid, [1], context=context)
#        nganh = self.pool.get('yhoc_nganh').search(cr, uid, [], context=context)
#        for n in nganh:
#            self.pool.get('yhoc_nganh').capnhat_thongtin(cr, uid, [n], context=context)
#        
#        self.capnhat_trangchu(cr, uid, [1], context)
#        return True
    
    def capnhat_thongtin(self,cr,uid,ids=None,context=None):
        self.capnhat_trangchu(cr, uid, [1], context=context)
        
#        chude = self.pool.get('yhoc_chude').search(cr, uid, [], context=context)
#        for cd in chude:
#            self.pool.get('yhoc_chude').capnhat_thongtin(cr, uid, [cd], context=context)
#            
#        duan = self.pool.get('yhoc_duan').search(cr, uid, [], context=context)
#        for da in duan:
#            self.pool.get('yhoc_duan').capnhat_thongtin(cr, uid, [da], context=context)
#            
#        baiviet = self.pool.get('yhoc_thongtin').search(cr, uid, [('state','=','done')], context=context)
#        for bv in baiviet:
#            self.pool.get('hlv_thongtin').xuatban_thongtin(cr, uid, [bv], context=context)
#            
#        user = self.pool.get('hr.employee').search(cr, uid, [], context=context)
#        for u in user:
#            self.pool.get('hr.employee').capnhat_thongtin(cr, uid, [u], context=context)
#            
#        cus = self.pool.get('res.partner').search(cr, uid, [], context=context)
#        for c in cus:
#            self.pool.get('res.partner').capnhat_thongtin(cr, uid, [c], context=context)
#            
#        nganh = self.pool.get('yhoc_nganh').search(cr, uid, [], context=context)
#        for n in nganh:
#            self.pool.get('yhoc_nganh').capnhat_thongtin(cr, uid, [n], context=context)
        return True
        
    def capnhat_menu_nganh(self, cr, uid, folder_trangchu, context=None):
        kieufile = self.pool.get('hlv.property')._get_value_project_property_by_name(cr, uid, 'Kiểu lưu file') or 'html'
        dsnganh = self.pool.get('yhoc_nganh').search(cr, uid, [('name','!=','Công nghệ thông tin')], context=context)
        temp = '''<li><a href="__LINKNGANH__">__TENNGANH__</a></li>'''
        menunganh = ''
        for n in self.pool.get('yhoc_nganh').browse(cr, uid, dsnganh, context=context):
            if len(n.dsbacsi) > 0:
                nganh_tab = ''
                if not n.link:
                    try:
                        self.pool.get('yhoc_nganh').capnhat_thongtin(cr,uid,[n.id], context=context)
                    except:
                        pass   
                #Giang_0811#nganh_tab = temp.replace('__LINKNGANH__', '../../nganh/%s/'%(n.id))
                nganh_tab = temp.replace('__LINKNGANH__', '%s'%(n.link))
                nganh_tab = nganh_tab.replace('__TENNGANH__', n.name)
                menunganh += nganh_tab
                
        import codecs
        fw = codecs.open(folder_trangchu + '/menu_nganh.html','w','utf-8')
        fw.write(menunganh)
        fw.close()
        return True
    
    def capnhat_trangthanhvien(self,cr, uid, domain, folder_trangchu, thanhvien_tab_, ids, context=None):
        if not context:
            context = {}
        kieufile = self.pool.get('hlv.property')._get_value_project_property_by_name(cr, uid, 'Kiểu lưu file') or 'html'
        noidung_thanhvien = ''
        for r in ids:
            if 'trangthanhvien' not in context:
                m = self.pool.get('hlv_vaitro').browse(cr, uid, r)
                tv = m.nhanvien
                vaitro = m.name
            else:
                tv = self.pool.get('hr.employee').browse(cr, uid, r)
                vaitro = ''  
            trinhdo = self.pool.get('hlv.property')._get_value_project_property_by_name(cr, uid, 'Trình độ chuyên môn') or '[]'
            photo = domain + '/template/trangchu/images/default_customer.png'
            if tv.image:
                if not os.path.exists(folder_trangchu + '/images/thanhvien'):
                    os.makedirs(folder_trangchu + '/images/thanhvien')
                path_hinh_ghixuong = folder_trangchu + '/images/thanhvien' + '/thanhvien_image_%s.jpg' %(tv.id,)
                fw= open(path_hinh_ghixuong,'wb')
                fw.write(base64.decodestring(tv.image))
                fw.close()
                photo = 'images/thanhvien/thanhvien_image_%s.jpg' %(tv.id,)
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
##############################                             
            thanhvien_tab = ''
            thanhvien_tab = thanhvien_tab_
            thanhvien_tab = thanhvien_tab.replace('__DANHXUNG__', tv.danhxung or '')
            thanhvien_tab = thanhvien_tab.replace('__TENTHANHVIEN__', tv.name)
            thanhvien_tab = thanhvien_tab.replace('__HINHTHANHVIEN__', photo)
            #Giang_0511#thanhvien_tab = thanhvien_tab.replace('__LINKTHANHVIEN__', '../../profile/%s/'%(tv.id))
            thanhvien_tab = thanhvien_tab.replace('__LINKTHANHVIEN__', '../../profile/%s/'%(tv.link_url))
            thanhvien_tab = thanhvien_tab.replace('__EMAIL__', vaitro or '')
            thanhvien_tab = thanhvien_tab.replace('__CHUCVU__', '')
            noidung_thanhvien += thanhvien_tab
        return noidung_thanhvien
        
    def capnhat_nhataitro(self,cr, uid, duongdan, domain, kieufile,context=None):
        folder_trangchu = duongdan + '/trangchu/vi'
        noidung_nhataitro = ''
        if os.path.exists(duongdan+'/template/trangchu/nhataitro.html'):
            fr = open(duongdan+'/template/trangchu/nhataitro.html', 'r')
            thanhvien_template = fr.read()
            fr.close()
        else:
            thanhvien_template = ''
        
        if os.path.exists(duongdan+'/template/trangchu/thanhvien_tab.html'):
            fr = open(duongdan+'/template/trangchu/thanhvien_tab.html', 'r')
            thanhvien_tab_ = fr.read()
            fr.close()
        else:
            thanhvien_tab_ = ''
        partner_ids = self.pool.get('res.partner').search(cr, uid, [('supplier','=',True)],context=context)
        for tv in partner_ids:
            tv = self.pool.get('res.partner').browse(cr, uid, tv, context=context)
            photo = domain + '/images/donor.jpg'
            if tv.image:
                if not os.path.exists(folder_trangchu + '/images/partner'):
                    os.makedirs(folder_trangchu + '/images/partner')
                path_hinh_ghixuong = folder_trangchu + '/images/partner' + '/partner_image_%s.jpg' %(tv.id,)
                fw= open(path_hinh_ghixuong,'wb')
                fw.write(base64.decodestring(tv.image))
                fw.close()
                photo = 'images/partner/partner_image_%s.jpg' %(tv.id,)
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
##############################                       
            thanhvien_tab = ''
            thanhvien_tab = thanhvien_tab_
            thanhvien_tab = thanhvien_tab.replace('__DANHXUNG__', '')
            thanhvien_tab = thanhvien_tab.replace('__TENTHANHVIEN__', tv.name)
            thanhvien_tab = thanhvien_tab.replace('__HINHTHANHVIEN__', photo)
            #Giang_1311#thanhvien_tab = thanhvien_tab.replace('__LINKTHANHVIEN__', '../../profile/%s/'%(tv.id))
            thanhvien_tab = thanhvien_tab.replace('__LINKTHANHVIEN__', '../../profile/%s/'%(tv.link_url))
            thanhvien_tab = thanhvien_tab.replace('__EMAIL__', tv.website or '')
            thanhvien_tab = thanhvien_tab.replace('__CHUCVU__', '')
            noidung_nhataitro += thanhvien_tab
            
        thanhvien_template = thanhvien_template.replace('__NHATAITRO__',noidung_nhataitro)
        
        #Cập nhật tittle       
        fr = open(duongdan + '/template/trangchu/tittle.html', 'r')
        noidung_tittle = fr.read()
        fr.close()
        noidung_tittle = noidung_tittle.replace('__TITLE__','Nhà tài trợ')
        thanhvien_template = thanhvien_template.replace('__TITLE__',noidung_tittle)
        thanhvien_template = thanhvien_template.replace('__DUONGDAN__',duongdan)
        
        
        import codecs
        fw = codecs.open(folder_trangchu + '/nhataitro.' + kieufile,'w','utf-8')
        fw.write(thanhvien_template)
        fw.close()
        
        return True
    
    def capnhat_dieuhanhvaphattrien(self, cr, uid, duongdan, domain, kieufile, context=None):
        folder_trangchu = duongdan + '/trangchu/vi'
        noidung_phattrien = ''
        noidung_dieuhanh = ''
        if os.path.exists(duongdan+'/template/trangchu/thanhvien.html'):
            fr = open(duongdan+'/template/trangchu/thanhvien.html', 'r')
            thanhvien_template = fr.read()
            fr.close()
        else:
            thanhvien_template = ''
        
        if os.path.exists(duongdan+'/template/trangchu/thanhvien_tab.html'):
            fr = open(duongdan+'/template/trangchu/thanhvien_tab.html', 'r')
            thanhvien_tab_ = fr.read()
            fr.close()
        else:
            thanhvien_tab_ = ''
        
        #Cap nhat nhom phat trien
        npt_id = self.pool.get('hlv_nhom').search(cr, uid, [('name','=','Nhóm phát triển')],context=context)
        npt = self.pool.get('hlv_nhom').browse(cr, uid, npt_id[0])
        member_ids = [-1,-1]
        for m in npt.member:
            member_ids.append(m.id)
        phattrien_ids = self.pool.get('hlv_vaitro').search(cr, uid, [('id','in',tuple(member_ids))], order='sequence', context=context)
        noidung_phattrien = self.capnhat_trangthanhvien(cr, uid, domain, folder_trangchu,thanhvien_tab_,phattrien_ids, context=context)
        
        #Cap nhat nhom điều hành
        npt_id = self.pool.get('hlv_nhom').search(cr, uid, [('name','=','Nhóm điều hành')],context=context)
        npt = self.pool.get('hlv_nhom').browse(cr, uid, npt_id[0])
        member_ids = [-1,-1]
        for m in npt.member:
            member_ids.append(m.id)
        dieuhanh_ids = self.pool.get('hlv_vaitro').search(cr, uid, [('id','in',tuple(member_ids))], order='sequence', context=context)
        noidung_dieuhanh = self.capnhat_trangthanhvien(cr, uid, domain, folder_trangchu,thanhvien_tab_,dieuhanh_ids, context=context)
        
        ###########################
        thanhvien_template = thanhvien_template.replace('__THANHVIENPHATRIEN__',noidung_phattrien)
        thanhvien_template = thanhvien_template.replace('__THANHVIENDIEUHANH__',noidung_dieuhanh)
        
        #Cập nhật tittle       
        fr = open(duongdan + '/template/trangchu/tittle.html', 'r')
        noidung_tittle = fr.read()
        fr.close()
        noidung_tittle = noidung_tittle.replace('__TITLE__','Nhóm phát triển')
        thanhvien_template = thanhvien_template.replace('__TITLE__',noidung_tittle)
        thanhvien_template = thanhvien_template.replace('__DUONGDAN__',duongdan)
        
        import codecs
        fw = codecs.open(folder_trangchu + '/nhomphattrien.' + kieufile,'w','utf-8')
        fw.write(thanhvien_template)
        fw.close()
    
    def capnhat_baivietmoi(self, cr, uid, list_baiviet_rc, path_luu_xuong, context=None):
#        Cap nhat bai viet moi
        domain = self.pool.get('hlv.property')._get_value_project_property_by_name(cr, uid, 'Domain') or '../..'
        duongdan = self.pool.get('hlv.property')._get_value_project_property_by_name(cr, uid, 'path of template')
        kieufile = self.pool.get('hlv.property')._get_value_project_property_by_name(cr, uid, 'Kiểu lưu file') or 'html'

        fr = open(duongdan+'/template/trangchu/baivietmoi_tab.html', 'r')
        baivietmoi_tab_ = fr.read()
        fr.close()
            
        all_baivietmoi = ''
        
        for bv in list_baiviet_rc:
            baivietmoi_tab = ''
            photo = ''
            if bv.hinhdaidien or thongtin.duan.photo:
                name_url = self.parser_url(bv.name)
                filename = str(bv.id) + '-thongtin-' + name_url
                if not os.path.exists(duongdan+'/images/thongtin/%s-thongtin-%s.jpg'%(str(bv.id),name_url)):
                    if bv.hinhdaidien:
                        folder_hinh_thongtin = duongdan+'/images/thongtin'
                        filename = str(bv.id) + '-thongtin-' + name_url
                        self.pool.get('yhoc_thongtin').ghihinhxuong(folder_hinh_thongtin, filename, bv.hinhdaidien, 95, 125, context=context)
                        
                    else:
                        if bv.duan.photo:
                            folder_hinh_thongtin = duongdan+'/images/thongtin'
                            filename = str(thongtin.id) + '-thongtin-' + name_url
                            self.pool.get('yhoc_thongtin').ghihinhxuong(folder_hinh_thongtin, filename, bv.duan.photo, 95, 125, context=context)
                photo = domain + '/images/thongtin/%s-thongtin-%s.jpg'%(str(bv.id),name_url)
                    
            #Giang_0511#baivietmoi_tab = baivietmoi_tab_.replace('__LINK__', '../../../../../../%s'%(bv.link_url))
            baivietmoi_tab = baivietmoi_tab_.replace('__LINK__', domain + '/%s/'%(bv.link_url))
            baivietmoi_tab = baivietmoi_tab.replace('__NAME__', bv.name)
            baivietmoi_tab = baivietmoi_tab.replace('__IMAGE__', photo)
            all_baivietmoi += baivietmoi_tab
            
        import codecs
        fw = codecs.open(path_luu_xuong,'w','utf-8')
        fw.write(str(all_baivietmoi))
        fw.close()

    def capnhat_baivietnoibac(self,cr, uid,chudenoibac, duongdan, domain,kieufile, context=None):
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
                        #Giang_0511#photo = '../../../../../../images/thongtin/%s.jpg' %(filename)
                        photo = domain + '/images/thongtin/%s.jpg' %(filename)
#                        path_hinh_ghixuong = duongdan + '/thongtin/%s/images/anhbaiviet.jpg'%(bv.id)
#                        if not os.path.exists(path_hinh_ghixuong):
#                            fw = open(path_hinh_ghixuong,'wb')
#                            fw.write(base64.decodestring(bv.hinhdaidien))
#                            fw.close()
#                        photo = '../../thongtin/%s/images/anhbaiviet.jpg' %(bv.id,)
                    sidebar_menu_tab = sidebar_menu_tab_.replace('__IMAGE__',photo)
                    sidebar_menu_tab = sidebar_menu_tab.replace('__NAME__',bv.name)
                    #Giang_0511#sidebar_menu_tab = sidebar_menu_tab.replace('__LINK__','../../../../../../%s'%(bv.link_url))
                    sidebar_menu_tab = sidebar_menu_tab.replace('__LINK__',domain + '/%s/'%(bv.link_url))
                    all_sidebar_menu_tab += sidebar_menu_tab 
            
            import codecs
            fw = codecs.open(folder_trangchu +'/baivietnoibac.html','w','utf-8')
            fw.write(str(all_sidebar_menu_tab))
            fw.close()
    
    def capnhat_thungo(self,cr,uid,thungo,duongdan,domain,kieufile,context=None):
        folder_trangchu = duongdan + '/trangchu/vi'
        if os.path.exists(duongdan+'/template/trangchu/thungo.html'):
            fr = open(duongdan+'/template/trangchu/thungo.html', 'r')
            template_thungo = fr.read()
            fr.close()
        else:
            template_thungo = ''
        template_thungo = template_thungo.replace('__THUNGO__',thungo or '(Chưa cập nhật)')
        
        #Cập nhật tittle       
        fr = open(duongdan + '/template/trangchu/tittle.html', 'r')
        noidung_tittle = fr.read()
        fr.close()
        noidung_tittle = noidung_tittle.replace('__TITLE__','Thư ngỏ')
        template_thungo = template_thungo.replace('__TITLE__',noidung_tittle)
        template_thungo = template_thungo.replace('__DUONGDAN__',duongdan)
        
        import codecs  
        fw = codecs.open(folder_trangchu +'/thungo.' + kieufile,'w','utf-8')
        fw.write(template_thungo)
        fw.close()
    
    def capnhat_muctieu(self,cr,uid,muctieu,duongdan,domain,kieufile,context=None):
        folder_trangchu = duongdan + '/trangchu/vi'
        noidung_sanglap = ''
        if os.path.exists(duongdan+'/template/trangchu/muctieu.html'):
            fr = open(duongdan+'/template/trangchu/muctieu.html', 'r')
            template_muctieu = fr.read()
            fr.close()
        else:
            template_muctieu = ''
        template_muctieu = template_muctieu.replace('__MUCTIEU__',muctieu or '(Chưa cập nhật)')
        
        #Cap nhat nhom sang lap
        npt_id = self.pool.get('hlv_nhom').search(cr, uid, [('name','=','Nhóm sáng lập')],context=context)
        npt = self.pool.get('hlv_nhom').browse(cr, uid, npt_id[0])
        member_ids = [-1,-1]
        noidung_sanglap += '''Nhóm sáng lập:</br>'''
        temp_ = '''<a href="__LINK__">__NAME__</a><br/>'''
        for m in npt.member:
            #Giang_0511#temp = temp_.replace('__LINK__','../../profile/%s/'%(m.nhanvien.id))
            temp = temp_.replace('__LINK__','../../profile/%s/'%(m.nhanvien.link_url))
            temp = temp.replace('__NAME__',m.nhanvien.name)
            noidung_sanglap += temp

        template_muctieu = template_muctieu.replace('__THANHVIENSANGLAP__',noidung_sanglap)
        
        #Cập nhật tittle       
        fr = open(duongdan + '/template/trangchu/tittle.html', 'r')
        noidung_tittle = fr.read()
        fr.close()
        noidung_tittle = noidung_tittle.replace('__TITLE__','Ý tưởng và mục tiêu')
        template_muctieu = template_muctieu.replace('__TITLE__',noidung_tittle)
        template_muctieu = template_muctieu.replace('__DUONGDAN__',duongdan)
        
        import codecs  
        fw = codecs.open(folder_trangchu +'/muctieuytuong.' + kieufile,'w','utf-8')
        fw.write(template_muctieu)
        fw.close()
    
    def capnhat_trangchu(self,cr,uid,ids,context):
        trangchu = self.browse(cr, uid, ids[0], context=context)
        duongdan = self.pool.get('hlv.property')._get_value_project_property_by_name(cr, uid, 'path of template')
        domain = self.pool.get('hlv.property')._get_value_project_property_by_name(cr, uid, 'Domain') or '../..'
        kieufile = self.pool.get('hlv.property')._get_value_project_property_by_name(cr, uid, 'Kiểu lưu file') or 'html'
        if not os.path.exists(duongdan):
            os.makedirs(duongdan)
            
        folder_trangchu = duongdan + '/trangchu/vi'
        if not os.path.exists(folder_trangchu):
            os.makedirs(folder_trangchu) 
            
        
#Doc file template
        if os.path.exists(duongdan+'/template/trangchu/trangchu.html'):
            fr = open(duongdan+'/template/trangchu/trangchu.html', 'r')
            template = fr.read()
            fr.close()
        else:
            template = ''
        
        banner = trangchu.banner
        chudenoibac = trangchu.chudenoibac
        thungo = trangchu.thungo
        duanhoanthanh = trangchu.duanhoanthanh
        muctieu = trangchu.muctieu
        
        chudecha = self.pool.get('yhoc_chude').search(cr, uid, [('parent_id','=',False)])
        noidung_header = self.capnhat_header(cr, uid, chudecha, duongdan, domain, folder_trangchu, context=None)
        #Giang_0511#noidung_footer = self.capnhat_footer(cr, uid, chudecha, duongdan, folder_trangchu,context=context)
        noidung_footer = self.capnhat_footer(cr, uid, chudecha, duongdan, domain, folder_trangchu,context=context)
        
#Câp nhật menu các bài viết nổi bậc
        self.capnhat_baivietnoibac(cr,uid, chudenoibac, duongdan, domain, kieufile, context=context)
        template = template.replace('__SIDEBARMENU__', '''<?php include("../../trangchu/vi/baivietnoibac.html")?>''')
        
#Tao file menu nganh
        self.capnhat_menu_nganh(cr, uid, folder_trangchu, context)
                
#Cap nhat thành viên phat trien
        self.capnhat_dieuhanhvaphattrien(cr, uid, duongdan, domain, kieufile, context=context)
        
        
#Cap nhat nha tai tro
        self.capnhat_nhataitro(cr, uid, duongdan, domain, kieufile, context)                
        
#Cap nhât trang thu ngo
        self.capnhat_thungo(cr, uid, thungo,duongdan, domain,kieufile,context=context)
        
#Cap nhât trang y tuong va muc tieu
        self.capnhat_muctieu(cr, uid,muctieu,duongdan,domain,kieufile,context=context)
        

#Cap nhat anh trang chu        
        all_anhtrangchu = ''
        fr = open(duongdan+'/template/trangchu/anhtrangchu_tab.html', 'r')
        anhtrangchu_tab_ = fr.read()
        fr.close()
        import random 
        banner = random.sample(banner, 3)
        for anh in banner:
            photo = ''
            if anh.photo:
                if not os.path.exists(folder_trangchu + '/images/trangchu'):
                    os.makedirs(folder_trangchu + '/images/trangchu')
                path_hinh_ghixuong = folder_trangchu + '/images/trangchu' + '/anhtrangchu_%s.jpg' %(anh.id,)
                fw = open(path_hinh_ghixuong,'wb')
                fw.write(base64.decodestring(anh.photo))
                fw.close()
                photo = 'images/trangchu/anhtrangchu_%s.jpg' %(anh.id,)
            anhtrangchu_tab = anhtrangchu_tab_.replace('__LINK__', anh.url or '#')
            anhtrangchu_tab = anhtrangchu_tab.replace('__IMAGE__', photo)
            anhtrangchu_tab = anhtrangchu_tab.replace('__NAME__', anh.name)
            anhtrangchu_tab = anhtrangchu_tab.replace('__MOTANGAN__', anh.description or '(Chưa cập nhật)')
            all_anhtrangchu += anhtrangchu_tab
            
        template = template.replace('__ANHTRANGCHU__',all_anhtrangchu)

#cập nhật dự án hoàn chỉnh (bên phải)
        all_chudenoibac = ''
        import random 
        duanhoanthanh = random.sample(duanhoanthanh, 8)
        for nb in duanhoanthanh:
            chudenoibac_tab = '''<li><a href="__LINK__"><strong>__NAME__</strong></a></li>'''
            #Giang_0511#chudenoibac_tab = chudenoibac_tab.replace('__LINK__', '../../../../../../%s/'%(nb.link_url)) 
            chudenoibac_tab = chudenoibac_tab.replace('__LINK__', domain + '/%s/'%(nb.link_url))
            chudenoibac_tab = chudenoibac_tab.replace('__NAME__', nb.name)
            all_chudenoibac += chudenoibac_tab
        
        import codecs
        fw = codecs.open(folder_trangchu +'/duanhoanthanh.html','w','utf-8')
        fw.write(str(all_chudenoibac))
        fw.close()
        template = template.replace('__CHUDENOIBAC__', '''<?php include("../../trangchu/vi/duanhoanthanh.html")?>''')
#        template = template.replace('__CHUDENOIBAC__', all_chudenoibac)
        
                    
#Cap nhat bai viet moi
        #=======================================================================
        # all_baivietmoi = ''
        # for bv in baivietmoi:
        #    if bv.duan.photo:
        #        if not os.path.exists(folder_trangchu + '/images/trangchu'):
        #            os.makedirs(folder_trangchu + '/images/trangchu')
        #        path_hinh_ghixuong = folder_trangchu + '/images/trangchu' + '/anhbaivietmoi_%s.jpg' %(bv.id,)
        #        fw = open(path_hinh_ghixuong,'wb')
        #        fw.write(base64.decodestring(bv.duan.photo))
        #        fw.close()
        #        photo = 'images/trangchu/anhbaivietmoi_%s.jpg' %(bv.id,)
        #    
        #    fr = open(duongdan+'/template/trangchu/baivietmoi_tab.html', 'r')
        #    baivietmoi_tab = fr.read()
        #    fr.close()
        #    if bv.hinhdaidien:
        #        if not os.path.exists(folder_trangchu + '/images/trangchu'):
        #            os.makedirs(folder_trangchu + '/images/trangchu')
        #        path_hinh_ghixuong = folder_trangchu + '/images/trangchu' + '/anhbaivietmoi_%s.jpg' %(bv.id,)
        #        fw = open(path_hinh_ghixuong,'wb')
        #        fw.write(base64.decodestring(bv.hinhdaidien))
        #        fw.close()
        #        photo = 'images/trangchu/anhbaivietmoi_%s.jpg' %(bv.id,)
        #    baivietmoi_tab = baivietmoi_tab.replace('__LINK__', bv.link or '#')
        #    baivietmoi_tab = baivietmoi_tab.replace('__NAME__', bv.name)
        #    baivietmoi_tab = baivietmoi_tab.replace('__IMAGE__', photo)
        #    all_baivietmoi += baivietmoi_tab
        # template = template.replace('__BAIVIETMOI__', all_baivietmoi)
        #=======================================================================
        
        #Cập nhật tittle       
        fr = open(duongdan + '/template/trangchu/tittle.html', 'r')
        noidung_tittle = fr.read()
        fr.close()
        noidung_tittle = noidung_tittle.replace('__TITLE__','Y học cộng đồng - Trang chủ')
        template = template.replace('__TITLE__',noidung_tittle)
        template = template.replace('__DUONGDAN__',duongdan)
        
        import codecs  
        fw = codecs.open(folder_trangchu +'/index.' + kieufile,'w','utf-8')
        fw.write(template)
        fw.close()

        return template

    
    def parser_url(self, utf8_str):
        utf8_str = str(utf8_str).lower().strip()
        INTAB = "ạảãàáâậầấẩẫăắằặẳẵóòọõỏôộổỗồốơờớợởỡéèẻẹẽêếềệểễúùụủũưựữửừứíìịỉĩýỳỷỵỹđ"
        INTAB = [ch.encode('utf8') for ch in unicode(INTAB, 'utf8')]    
        OUTTAB = "a"*17 + "o"*17 + "e"*11 + "u"*11 + "i"*5 + "y"*5 + "d"    
        r = re.compile("|".join(INTAB))
        replaces_dict = dict(zip(INTAB, OUTTAB))
        chuoikhongdau = r.sub(lambda m: replaces_dict[m.group(0)], utf8_str)
        
        INTAB = "ẠẢÃÀÁÂẬẦẤẨẪĂẮẰẶẲẴÓÒỌÕỎÔỘỔỖỒỐƠỚỢỞỠÉÈẺẸẼÊẾỀỆỂỄÚÙỤỦŨƯỰỮỬỪỨÍÌỊỈĨÝỲỶỶỴỸĐ"
        INTAB = [ch.encode('utf8') for ch in unicode(INTAB, 'utf8')]    
        OUTTAB = "a"*17 + "o"*17 + "e"*11 + "u"*11 + "i"*5 + "y"*5 + "d"    
        r = re.compile("|".join(INTAB))
        replaces_dict = dict(zip(INTAB, OUTTAB))
        chuoikhongdau = r.sub(lambda m: replaces_dict[m.group(0)], chuoikhongdau)
        chuoikhongdau = chuoikhongdau.lower()
        list = chuoikhongdau.split(' ');
        kq = '-'.join(list)
        for char in '?/:*<>|':  
            kq = kq.replace(char,'')
        return kq
    
yhoc_trangchu()

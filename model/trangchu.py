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
        for record in self.browse(cr, uid, ids, context=context):
            if record.id == 1:
                dsbaivietmoi = self.pool.get('yhoc_thongtin').search(cr, uid, [('state','=','done')], limit=8, order='date desc', context=context)
            else:
                thanhvien_id = self.pool.get('hr.employee').search(cr, uid, [('name','=',record.name)], context=context)
                dsbaivietmoi = self.pool.get('yhoc_thongtin').search(cr, uid, ['&',('state','=','done'),('nguoidich.id','=',thanhvien_id)], limit=8, order='date desc', context=context)
            result[record.id] = []
            for bv in self.pool.get('yhoc_thongtin').browse(cr, uid, dsbaivietmoi, context=context):
                result[record.id].append(bv.id)
        return result
    
    def _get_chudenoibac(self, cr, uid, ids, field_name, arg, context=None):
        result = {}
        for record in self.browse(cr, uid, ids, context=context):
            if record.id == 1:
#                dsbaiviet = self.pool.get('yhoc_chude').search(cr, uid, [('parent_id','!=',False),('link','!=',False)], limit=10, order='soluongxem desc', context=context)
                sql = '''select cd.id
                        from yhoc_chude cd
                        where cd.link is not null                            
                        and cd.soluongxem>0
                        order by cd.soluongxem desc
                        limit 10'''
                cr.execute(sql)
                dsbaiviet = [r[0] for r in cr.fetchall()]
            else:
                sql = '''select temp.id
                        from(
                            select distinct cd.id,cd.soluongxem
                            from yhoc_chude cd, yhoc_duan da
                            where chude_id = cd.id
                            and cd.link is not null
                            and da.truongduan=%s
                            and cd.soluongxem>0
                            order by cd.soluongxem desc
                            limit 10
                        ) as temp'''
                thanhvien_id = self.pool.get('hr.employee').search(cr, uid, [('name','=',record.name)], context=context)
                cr.execute(sql,(thanhvien_id[0],))
                dsbaiviet_ = cr.fetchall()
                dsbaiviet = []
                for cd in self.pool.get('yhoc_chude').browse(cr,uid,[x[0] for x in dsbaiviet_],context={}):
                    dsbaiviet.append(cd.id)
                
            result[record.id] = []
            for bv in self.pool.get('yhoc_chude').browse(cr, uid, dsbaiviet, context=context):
                result[record.id].append(bv.id)
        return result
    
    def _get_duannoibac(self, cr, uid, ids, field_name, arg, context=None):
        result = {}
        sql = '''select duan_done.duan
                 from 
                    (select count(t.id) as sobaiviet,t.duan,d.soluongxem
                    from yhoc_thongtin t, yhoc_duan d 
                    where t.duan = d.id
                        and state='done'
                        and truongduan in %s
                    group by t.duan,d.soluongxem) as duan_done,
                    
                    (select count(t.id) as tongsobaiviet,t.duan 
                    from yhoc_thongtin t, yhoc_duan d 
                    where t.duan = d.id
                    group by t.duan) as duan_all
                where duan_done.duan = duan_all.duan
                and duan_done.sobaiviet > duan_all.tongsobaiviet/2
                and duan_all.tongsobaiviet > %s 
                and duan_done.soluongxem > 0
                order by duan_done.soluongxem desc
                limit 20
                '''
        for record in self.browse(cr, uid, ids, context=context):
            if record.id == 1:
                all_thanhvien = self.pool.get('hr.employee').search(cr, uid, [], context=context)
                cr.execute(sql,(tuple(all_thanhvien),5))
                duanhoanchinh = cr.fetchall()   
            else:
                thanhvien_id = self.pool.get('hr.employee').search(cr, uid, [('name','=',record.name)], context=context)
                thanhvien_id += [-2,-1]
                cr.execute(sql,(tuple(thanhvien_id),0))
                duanhoanchinh = cr.fetchall()
            result[record.id] = []
            for da in self.pool.get('yhoc_duan').browse(cr,uid,[x[0] for x in duanhoanchinh],context={}):
                result[record.id].append(da.id)
        return result

    def _get_baivietbanner(self, cr, uid, ids, field_name, arg, context=None):
        result = {}
        for record in self.browse(cr, uid, ids, context=context):
            if record.id == 1:
                dsbaiviet = self.pool.get('yhoc_thongtin').search(cr, uid, [('state','=','done'),('hinhlon','!=',False)], limit=30, order='soluongxem desc', context=context)
            else:
                thanhvien_id = self.pool.get('hr.employee').search(cr, uid, [('name','=',record.name)], context=context)
                dsbaiviet = self.pool.get('yhoc_thongtin').search(cr, uid, ['&',('state','=','done'),'&',('hinhlon','!=',False),'|',('nguoidich.id','=',thanhvien_id),('nguoihieudinh.id','=',thanhvien_id)], limit=8, order='date desc', context=context)
            result[record.id] = []
            for bv in self.pool.get('yhoc_thongtin').browse(cr, uid, dsbaiviet, context=context):
                result[record.id].append(bv.id)
        return result
        
    _columns = {
                'name':fields.char("Tên",size=500, required='1'),
				'title': fields.char("Tên website",size=65),
				'description': fields.char("Mô tả ngắn",size=255),
                'banner': fields.one2many('x_lienket', 'trangchu_id', 'Banner'),
                'chudenoibac':fields.function(_get_chudenoibac, type='many2many', relation='yhoc_chude', string='Bài viết nổi bậc'),
                'baivietmoi':fields.function(_get_baivietmoi, type='many2many', relation='yhoc_thongtin', string='Bài viết mới'),
                'muctieu': fields.text('Ý tưởng và mục tiêu'),
                'thungo': fields.text('Thư ngỏ'),
                'duanhoanthanh': fields.function(_get_duannoibac, type='many2many', relation='yhoc_duan', string='Dự án hoàn thành'),
                'baivietbanner':fields.function(_get_baivietbanner, type='many2many', relation='yhoc_thongtin', string='Banner'),
                'tukhoa_dinhhuong': fields.many2many('yhoc_keyword', 'trangchu_keyword_rel', 'trangchu_id', 'keyword_id', 'Từ khóa định hướng'),
                'wordpress_info':fields.char("Wordpress",size=500),
                }
    _defaults={
              
               }
    
    def write(self, cr, uid, ids, vals, context=None):
        self.auto_capnhat(cr, uid)
        return super(yhoc_trangchu,self).write(cr, uid, ids, vals, context=context)
    
    def capnhat_alltag(self,cr, uid, ids, context=None):
        all_tags = self.pool.get('yhoc_keyword').search(cr, uid, [('baiviet_ids','!=',False)], context=context)
        for t in all_tags:
            self.pool.get('yhoc_keyword').capnhat_toanbotrangtag(cr, uid, [t], context=context)
        return True
    
    def capnhat_tuakhoalienquan(self,cr, uid, ids, context=None):
        all_tags = self.pool.get('yhoc_keyword').search(cr, uid, [('baiviet_ids','!=',False)], context=context)
        for t in all_tags:
            self.pool.get('yhoc_keyword').capnhat_kwlienquan(cr, uid, [t], context=context)
        return True
    
                
    def capnhat_allduan(self, cr, uid, ids=None, context=None):
        duan = self.pool.get('yhoc_duan').search(cr, uid, [])
        for da in duan:
            self.pool.get('yhoc_duan').capnhat_thongtin(cr,uid,[da], context)
        return True
    
    def capnhat_thanhvienthamgiaduan(self, cr, uid, ids=None, context=None):
        duan = self.pool.get('yhoc_duan').search(cr, uid, [])
        for da in duan:
            self.pool.get('yhoc_duan').capnhat_thanhvienthamgia(cr, uid, [da], context=context)
        return True
    
    def capnhat_tagschoduan(self, cr, uid, ids=None, context=None):
        duan = self.pool.get('yhoc_duan').search(cr, uid, [])
        for da in duan:
            self.pool.get('yhoc_duan').auto_tags(cr, uid, [da], context=context)
        return True
    
    def capnhat_allchude(self, cr, uid, ids=None, context=None):
        chude = self.pool.get('yhoc_chude').search(cr, uid, [('parent_id.name','!=','Trang chủ'),('link','!=',False)] )
        for cd in chude:
            self.pool.get('yhoc_chude').capnhat_thongtin(cr,uid,[cd],context)
        return True
    
    def capnhat_tagschochude(self, cr, uid, ids=None, context=None):
        chude = self.pool.get('yhoc_chude').search(cr, uid, [('parent_id.name','!=','Trang chủ'),('link','!=',False)] )
        for cd in chude:
            self.pool.get('yhoc_chude').auto_tags(cr, uid, [cd], context=context)
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
    
    def capnhat_allthuoc(self, cr, uid, ids=None, context=None):
        sql = '''select id from yhoc_thongtin
                where nguoidich = 141               
                '''
        cr.execute(sql)
        thuoc = [r[0] for r in cr.fetchall()]
        for t in thuoc:
            self.pool.get('yhoc_thongtin').xuatban_thongtin(cr,uid,[t])
        return True
    def capnhat_tukhoachinhvaodstukhoa(self, cr, uid, ids=None, context=None):
        tintuc = self.pool.get('yhoc_thongtin').search(cr, uid, [('state','=','done')])
        for tt in tintuc:
            self.pool.get('yhoc_thongtin').capnhattukhoachinhchobaiviet(cr,uid,[tt],context=context)
        return True
    
    def capnhat_allmenu(self, cr, uid, ids=None, context=None):
        tintuc = self.pool.get('yhoc_thongtin').search(cr, uid, [('state','=','done')])
        for tt in tintuc:
            self.pool.get('yhoc_thongtin').tao_mucluc(cr,uid,[tt],context=context)
        return True
    
    def capnhat_lenwp_cacchuyentrang(self, cr, uid, ids, context=None):
        chuyentrang = self.browse(cr, uid, ids[0], context=context)
        thanhvien_id = self.pool.get('hr.employee').search(cr, uid, [('name','=',chuyentrang.name)], context=context)
        dsbaiviet = self.pool.get('yhoc_thongtin').search(cr, uid, ['&',('state','=','done'),('nguoidich.id','=',thanhvien_id)], order='date asc', context=context)
        self.post_to_wordpress(cr, uid, ids, dsbaiviet, context=context)
        return True
    
    
    def capnhat_allnganh(self, cr, uid, ids=None, context=None):
        nganh = self.pool.get('yhoc_nganh').search(cr, uid, [])
        for tt in nganh:
            self.pool.get('yhoc_nganh').capnhat_thongtin(cr,uid,[tt])
        return True
    
    def capnhat_tin_nhanh(self, cr, uid, ids=None, context=None):
        tintuc = self.pool.get('yhoc_thongtin').search(cr, uid, [('state','=','done')])
        for tt in tintuc:
            if tt % 10 == context['phan']:
                self.pool.get('yhoc_thongtin').xuatban_thongtin(cr,uid,[tt])
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
    
    def capnhat_header(self, cr, uid, ids, chudecha, duongdan, domain, folder_trangchu, context=None):
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
                    root_menu_tab = '''<li><a href="__LINK__" rel="__REL__" __TRIGGER__>__TENMENU__</a></li>
                    '''
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
                                item_sub_menu_tab = '''<li><a href="__LINK__" >__NAME__</a></li>
                                '''
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
            #Giang_1711#
            header_template = header_template.replace('__DOMAIN__', domain)

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
            fw = codecs.open(folder_trangchu + '/header1.html','w','utf-8')
            fw.write(header_template)
            fw.close()
        return header_template
    
    #Giang_0511#def capnhat_footer(self, cr, uid, chudecha, duongdan, folder_trangchu,context=None):
    def capnhat_footer(self, cr, uid, chudecha, duongdan, domain, folder_trangchu,context=None):
        #Doc file footer
        sequence = self.pool.get('hlv.property')._get_value_project_property_by_name(cr, uid, 'Thứ tự menu footer') or '[]'
        sequence = eval(sequence)
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
        for s in sequence:
             
            chude = self.pool.get('yhoc_chude').search(cr, uid, [('name','=',s)], context=context)
            if chude:
                chude = self.pool.get('yhoc_chude').browse(cr, uid, chude[0], context=context)
                if chude.link:
                    #Giang_0511#chunkyfootercolumn = chunkyfootercolumn_.replace('__LINK_CHUDECHA__', '../../../../../../%s/'%(chude.link_url))
    #                chunkyfootercolumn = chunkyfootercolumn_.replace('__LINK_CHUDECHA__',domain + '/%s/'%(chude.link_url))
                    chunkyfootercolumn = chunkyfootercolumn_.replace('__NAME_CHUDECHA__', chude.name)
                    
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
        fw = codecs.open(folder_trangchu + '/footer1.html','w','utf-8')
        fw.write(footer_template)
        fw.close()
        return footer_template
    
    
    def capnhat_thongtin(self,cr,uid,ids,context=None):
        self.capnhat_trangchu(cr, uid, ids, context=context)
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
        if not context:
            context = {}
        if 'ten_template' in context:
            ten_template = context['ten_template']
        else:
            ten_template = 'baivietmoi_tab'
#        Cap nhat bai viet moi
        domain = self.pool.get('hlv.property')._get_value_project_property_by_name(cr, uid, 'Domain') or '../..'
        duongdan = self.pool.get('hlv.property')._get_value_project_property_by_name(cr, uid, 'path of template')
        kieufile = self.pool.get('hlv.property')._get_value_project_property_by_name(cr, uid, 'Kiểu lưu file') or 'html'

        fr = open(duongdan+'/template/trangchu/%s.html'%ten_template, 'r')
        baivietmoi_tab_ = fr.read()

        fr.close()
            
        all_baivietmoi = ''
        
        for i in range(0,len(list_baiviet_rc)):
            bv = list_baiviet_rc[i]
            baivietmoi_tab = ''
            photo = ''
            if bv.hinhdaidien or bv.duan.photo:
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
            if i%2==0:
                baivietmoi_tab = baivietmoi_tab.replace('__CLASS__', '')
            elif i%2==1:
                baivietmoi_tab = baivietmoi_tab.replace('__CLASS__', 'class="last"')
            all_baivietmoi += baivietmoi_tab
            
        import codecs
        fw = codecs.open(path_luu_xuong,'w','utf-8')
        fw.write(str(all_baivietmoi))
        fw.close()
        

    def capnhat_baivietnoibac(self,cr, uid,chudenoibac, path_luu_xuong, domain,kieufile, context=None):
        '''Dùng ở trang chủ và keyword'''
        
        duongdan = self.pool.get('hlv.property')._get_value_project_property_by_name(cr, uid, 'path of template')
        if os.path.exists(duongdan+'/template/trangchu/sidebar_menu_tab.html'):
            fr = open(duongdan+'/template/trangchu/sidebar_menu_tab.html', 'r')
            sidebar_menu_tab_ = fr.read()
            fr.close()
            all_sidebar_menu_tab = ''
            if len(chudenoibac)>4:
                import random
                baivietnoibac = random.sample(chudenoibac, 4)
            else:
                baivietnoibac = chudenoibac
                
            for bv in baivietnoibac:
                if not bv.link:
                    try:
                        self.pool.get('yhoc_chude').capnhat_thongtin(cr, uid, [bv.id], context=context)
                    except:
                        pass
                else:
                    photo = ''
                    if bv.photo:
                        name_url = self.parser_url(bv.name)
                        filename = str(bv.id) + '-chude-' + name_url
                        if not os.path.exists(duongdan+'/images/chude/%s-chude-%s.jpg'%(str(bv.id),name_url)):
                            folder_hinh_baiviet = duongdan + '/images/chude'
                            self.pool.get('yhoc_thongtin').ghihinhxuong(folder_hinh_baiviet, filename, bv.hinhdaidien, 110,110, context=context)
                        #Giang_0511#photo = '../../../../../../images/thongtin/%s.jpg' %(filename)
                        photo = domain + '/images/chude/%s.jpg' %(filename)
#                        path_hinh_ghixuong = duongdan + '/thongtin/%s/images/anhbaiviet.jpg'%(bv.id)
#                        if not os.path.exists(path_hinh_ghixuong):
#                            fw = open(path_hinh_ghixuong,'wb')
#                            fw.write(base64.decodestring(bv.hinhdaidien))
#                            fw.close()
#                        photo = '../../thongtin/%s/images/anhbaiviet.jpg' %(bv.id,)
                    sidebar_menu_tab = sidebar_menu_tab_.replace('__IMAGE__',photo)
                    sidebar_menu_tab = sidebar_menu_tab.replace('__NAME__',bv.name)
                    sidebar_menu_tab = sidebar_menu_tab.replace('__DESCRIPTION__',bv.description or '(Chưa cập nhật)')
                    #Giang_0511#sidebar_menu_tab = sidebar_menu_tab.replace('__LINK__','../../../../../../%s'%(bv.link_url))
                    sidebar_menu_tab = sidebar_menu_tab.replace('__LINK__',domain + '/%s/'%(bv.link_url))
                    all_sidebar_menu_tab += sidebar_menu_tab 
            
            import codecs
            fw = codecs.open(path_luu_xuong +'/baivietnoibac.html','w','utf-8')
            fw.write(str(all_sidebar_menu_tab))
            fw.close()
            
    def capnhat_dsbacsiotrangchu(self, cr, uid, context=None):
        duongdan = self.pool.get('hlv.property')._get_value_project_property_by_name(cr, uid, 'path of template')
        domain = self.pool.get('hlv.property')._get_value_project_property_by_name(cr, uid, 'Domain') or '../..'
        sql = '''select id
                from     (select h.id, count(t.id) as sobaiviet from hr_employee h, yhoc_thongtin t
                    where h.id = t.nguoidich
                    group by h.id
                    order by sobaiviet desc
                    limit 20
                    ) as kq
                
                '''
        cr.execute(sql)
        dsbacsi = cr.fetchall()
        if len(dsbacsi)>10:
            import random
            dsbacsi = random.sample(dsbacsi, 10)
        else:
            dsbacsi = dsbacsi
        
        dsbacsi = self.pool.get('hr.employee').browse(cr,uid,[x[0] for x in dsbacsi],context={})
        kq = ''
        for i in range(0,len(dsbacsi)):
            if i%2 == 0:
                temp = '<li>'
                temp += self.pool.get('hr.employee').profile_otrangchu(cr, uid, [dsbacsi[i].id], context=context)
            elif i%2 == 1:
                temp += self.pool.get('hr.employee').profile_otrangchu(cr, uid, [dsbacsi[i].id], context=context)
                temp += '</li>'
                kq += temp
                
        
        import codecs
        fw = codecs.open(duongdan +'/trangchu/vi/dsbacsiotrangchu.html','w','utf-8')
        fw.write(kq)
        fw.close()
        return True
    
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
        template_thungo = template_thungo.replace('__DOMAIN__',domain)
        
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
        
    def capnhat_duannoibac(self, cr, uid, duongdan_luufile, dsda, soduan, context=None):
        duongdan = self.pool.get('hlv.property')._get_value_project_property_by_name(cr, uid, 'path of template')
        domain = self.pool.get('hlv.property')._get_value_project_property_by_name(cr, uid, 'Domain') or '../..'
        kieufile = self.pool.get('hlv.property')._get_value_project_property_by_name(cr, uid, 'Kiểu lưu file') or 'html'
        all_chudenoibac = ''
        fr = open(duongdan+'/template/trangchu/loatbai_tab.html', 'r')
        loatbai_tab_ = fr.read()
        fr.close()
        import random 
        if len(dsda)>soduan:
            duanhoanthanh = random.sample(dsda, soduan)
        else:
            duanhoanthanh = dsda
        for nb in duanhoanthanh:

#            chudenoibac_tab = '''<li><a href="__LINK__"><strong>__NAME__</strong></a></li>'''
            #Giang_0511#chudenoibac_tab = chudenoibac_tab.replace('__LINK__', '../../../../../../%s/'%(nb.link_url))
            name_url = self.pool.get('yhoc_trangchu').parser_url(nb.name)
            picture = domain + '/images/duan/%s-duan-%s.jpg'%(str(nb.id),name_url)
            
            if not os.path.exists(duongdan+'/images/duan/%s-duan-%s.jpg'%(str(nb.id),name_url)):
                if nb.photo:
                    folder_hinh_thongtin = duongdan+'/images/duan'
                    filename = str(nb.id) + '-duan-' + name_url
                    self.pool.get('yhoc_thongtin').ghihinhxuong(folder_hinh_thongtin, filename, nb.photo, 135, 105, context=context)
                    
            loatbai_tab = loatbai_tab_.replace('__LINK__', domain + '/%s/'%(nb.link_url))
            loatbai_tab = loatbai_tab.replace('__NAME__', nb.name)
            loatbai_tab = loatbai_tab.replace('__PHOTO__', picture)
            loatbai_tab = loatbai_tab.replace('__DESCRIPTION__', nb.description or '(Chưa cập nhật)')
            loatbai_tab = loatbai_tab.replace('__ICON__', domain + '/images/multi_document.png')
            loatbai_tab = loatbai_tab.replace('__SOLUONGBAIVIET__', str(nb.soluongbaiviet))
            all_chudenoibac += loatbai_tab

        
        import codecs
        fw = codecs.open(duongdan_luufile +'/duanhoanthanh.html','w','utf-8')
        fw.write(str(all_chudenoibac))
        fw.close()
        return True
    
    def capnhat_trangchu(self,cr,uid,ids,context):
        trangchu = self.browse(cr, uid, ids[0], context=context)
        duongdan = self.pool.get('hlv.property')._get_value_project_property_by_name(cr, uid, 'path of template')
        domain = self.pool.get('hlv.property')._get_value_project_property_by_name(cr, uid, 'Domain') or '../..'
        kieufile = self.pool.get('hlv.property')._get_value_project_property_by_name(cr, uid, 'Kiểu lưu file') or 'html'
        if not os.path.exists(duongdan):
            os.makedirs(duongdan)
        
        if trangchu.id == 1:
            folder_trangchu = duongdan + '/trangchu/vi'
            tentrang = 'vi'
        else:
            tentrang = self.pool.get('yhoc_trangchu').parser_url(str(trangchu.name))
            folder_trangchu = duongdan + '/trangchu/%s'%tentrang
        if not os.path.exists(folder_trangchu):
            os.makedirs(folder_trangchu) 
            
        
#Doc file template
        if os.path.exists(duongdan+'/template/trangchu/trangchu.html'):
            fr = open(duongdan+'/template/trangchu/trangchu.html', 'r')
            template = fr.read()
            fr.close()
        else:
            template = ''
        
        banner = trangchu.baivietbanner
        chudenoibac = trangchu.chudenoibac
        thungo = trangchu.thungo
        duanhoanthanh = trangchu.duanhoanthanh
        muctieu = trangchu.muctieu
        
#Câp nhật menu các bài viết nổi bậc
        self.capnhat_baivietnoibac(cr,uid, chudenoibac, folder_trangchu, domain, kieufile, context=context)
        template = template.replace('__SIDEBARMENU__', '''<?php include("../../trangchu/%s/baivietnoibac.html")?>'''%tentrang)

#Cap nhât danh sach bac si noi bac o trang chu        
        self.capnhat_dsbacsiotrangchu(cr, uid, context)
                
        
#Cap nhât trang thu ngo và mục tiêu
        if trangchu.id == 1:
            self.capnhat_thungo(cr, uid, thungo,duongdan, domain,kieufile,context=context)
            self.capnhat_muctieu(cr, uid,muctieu,duongdan,domain,kieufile,context=context)
            chudecha = self.pool.get('yhoc_chude').search(cr, uid, [('parent_id.name','=','Trang chủ')])
            noidung_header = self.capnhat_header(cr, uid, [1], chudecha, duongdan, domain, folder_trangchu, context=context)
            noidung_footer = self.capnhat_footer(cr, uid, chudecha, duongdan, domain, folder_trangchu,context=context)
            #Tao file menu nganh
            self.capnhat_menu_nganh(cr, uid, folder_trangchu, context)
            #Cap nhat thành viên phat trien
            self.capnhat_dieuhanhvaphattrien(cr, uid, duongdan, domain, kieufile, context=context)
            #Cap nhat nha tai tro
            self.capnhat_nhataitro(cr, uid, duongdan, domain, kieufile, context)
            #Cap nhât danh sach các từ khóa         
#            tag_do = self.pool.get('yhoc_keyword').search(cr, uid, [('color','=','maudo')], limit=4, context=context)
#            tag_xanhla = self.pool.get('yhoc_keyword').search(cr, uid, [('color','=','mauxanhla')], limit=4, context=context)
#            tag_xanhduong = self.pool.get('yhoc_keyword').search(cr, uid, [('color','=','mauxanhduong')], limit=4, context=context)
#            tag_xam = self.pool.get('yhoc_keyword').search(cr, uid, [('color','=','mauxam')], limit=8, context=context)
#            all_tag = tag_do+tag_xanhla+tag_xanhduong+tag_xam
#            
            
            
            
            
            import random 
            kw_obj = self.pool.get('yhoc_keyword')
            all = kw_obj.search(cr, uid, [], context=context)
            sql = '''select distinct keyword_id
                    from (select keyword_id,count(thongtin_id)
                        from thongtin_keyword_rel
                        group by keyword_id                    
                        order by count(thongtin_id) desc
                        ) as temp_                    
                    '''
            cr.execute(sql)
            all_xanhduong = [r[0] for r in cr.fetchall()]
            xanhduong = random.sample(all_xanhduong, 5)
            all_maudo = kw_obj.search(cr, uid, [('soluongxem','>',0),('link','!=', False)], order="soluongxem desc", limit=len(all)*0.3, context=context)
            maudo = random.sample(all_maudo, 5)
            all_xam = kw_obj.search(cr, uid, [('id','not in', all_maudo),('id','not in', all_xanhduong),('link','!=', False)], context=context)
            mauxam = random.sample(all_xam, 5)
            
            all_tag = xanhduong+maudo+mauxam
            all_tag = kw_obj.browse(cr, uid, all_tag, context=context)
            xanhla = trangchu.tukhoa_dinhhuong
            if len(xanhla) > 4:
                xanhla = random.sample(xanhla, 4)
            all_tag+=xanhla
            
            
            
            
            
            
            
            
            list_tag = self.pool.get('yhoc_keyword').capnhat_listtag_ophiacuoi(cr, uid, all_tag, context=context)
            template = template.replace('__LIST_TAGS__', list_tag)
        else:
            #Cap nhât danh sach các từ khóa         
            tag_id = self.pool.get('yhoc_keyword').search(cr, uid, [('name','=',trangchu.name)], context=context)
            tag_rc = self.pool.get('yhoc_keyword').browse(cr, uid, tag_id[0], context=context)
            list_tag = self.pool.get('yhoc_keyword').capnhat_listtag_ophiacuoi(cr, uid, tag_rc.kwlienquan_ids, context=context)
            template = template.replace('__LIST_TAGS__', list_tag)

        

        

#Cap nhat anh trang chu        
        all_anhtrangchu = ''
        fr = open(duongdan+'/template/trangchu/anhtrangchu_tab.html', 'r')
        anhtrangchu_tab_ = fr.read()
        fr.close()
        if len(banner)>3:
            import random 
            banner = random.sample(banner, 3)
        for bv in banner:
            photo = ''
            if bv.hinhlon:
                name_url = self.pool.get('yhoc_trangchu').parser_url(str(bv.name))
                folder_hinh_thongtin = duongdan+'/images/thongtin'
                filename = str(bv.id) + '-thongtin_lon-' + name_url
                self.pool.get('yhoc_thongtin').ghihinhxuong(folder_hinh_thongtin, filename, bv.hinhlon, 390, 650 , context=context)
                photo = domain + '/images/thongtin/%s.jpg'%(filename)
            anhtrangchu_tab = anhtrangchu_tab_.replace('__LINK__', bv.link or '#')
            anhtrangchu_tab = anhtrangchu_tab.replace('__IMAGE__', photo)
            anhtrangchu_tab = anhtrangchu_tab.replace('__NAME__', bv.name)
            anhtrangchu_tab = anhtrangchu_tab.replace('__MOTANGAN__', bv.motangan or '(Chưa cập nhật)')
            all_anhtrangchu += anhtrangchu_tab
            
        template = template.replace('__ANHTRANGCHU__',all_anhtrangchu)

#cập nhật dự án nổi bậc (bên phải)
        self.capnhat_duannoibac(cr, uid, folder_trangchu, duanhoanthanh, 6, context=context)
        template = template.replace('__CHUDENOIBAC__', '''<?php include("../../trangchu/%s/duanhoanthanh.html")?>'''%tentrang)


        template = template.replace('__DUONGDAN__',duongdan)
        template = template.replace('__ITEMTYPE__', 'WebPage')
        template = template.replace('__DESCRIPTION__', trangchu.description or '')
        template = template.replace('__TITLE__', trangchu.title or '')
        template = template.replace('__URL__', domain)
        template = template.replace('__TENTRANG__', tentrang)  
        
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
    
    def post_to_wordpress(self, cr, uid, chuyentrang_ids, dsbaiviet, context=None):
        duongdan = self.pool.get('hlv.property')._get_value_project_property_by_name(cr, uid, 'path of template')
        domain = self.pool.get('hlv.property')._get_value_project_property_by_name(cr, uid, 'Domain') or '../..'
        from wordpress_xmlrpc import Client, WordPressPost
        from wordpress_xmlrpc.methods.posts import NewPost        
        from wordpress_xmlrpc.methods.taxonomies import GetTerms
        chuyentrang = self.browse(cr, uid, chuyentrang_ids[0], context=context)
#        content_ = '''<table cellspacing="1" cellpadding="1">
#                        <tbody>
#                        <tr>
#                        <td><img class="alignnone" style="margin: 10px;" alt="" src="__PHOTO__"/></td>
#                        <td><strong style="font-size: 18px;">Tóm tắt: </strong><em style="font-size: 14px;">__MOTA__</em></td>
#                        </tr>
#                        </tbody>
#                        </table>'''
        content_ = '''<strong style="font-size: 18px;">Tóm tắt: </strong><em style="font-size: 14px;">__MOTA__</em>'''
        if chuyentrang.id == 1:
            return False
        else:
            if chuyentrang.wordpress_info:
                wordpress = eval(chuyentrang.wordpress_info)
                wp = Client('http://%s.wordpress.com/xmlrpc.php'%wordpress[0], wordpress[1], wordpress[2])
                for bv in dsbaiviet:
                    post = WordPressPost()
                    bv = self.pool.get('yhoc_thongtin').browse(cr, uid, bv, context=context)
                    if bv.url_thongtin:
                        name_url = bv.url_thongtin
                    else:
                        name_url = self.pool.get('yhoc_trangchu').parser_url(str(bv.name))
                    list_tag = []
                    for tag in bv.keyword_ids:
                        if tag.name:
                            list_tag.append(tag.name)
                    post.terms_names = {'post_tag': list_tag,
                                        'category': [bv.duan.name]}
                    post.title = bv.name
                    menu = ''
                    if os.path.exists(duongdan+'/thongtin/%s/menu.html'%name_url):
                        fr = open(duongdan+'/thongtin/%s/menu.html'%name_url, 'r')
                        menu = fr.read()
                        fr.close()
                    
                    content = content_.replace('__MOTA__', bv.motangan or '(Chưa cập nhật)')
                    content = content.replace('__PHOTO__', domain + '/images/thongtin/%s-thongtin-%s.jpg'%(str(bv.id),name_url))
                    content += menu
                    link = domain + '/thongtin/%s'%name_url
                    content += '''
                    <strong style="font-size: 18px;">Xem thêm tại: </strong><a href="%s">%s</a>'''%(link,link)
                    post.content = content
                    post.post_status = 'publish'
                    kq = wp.call(NewPost(post))
                return True
yhoc_trangchu()

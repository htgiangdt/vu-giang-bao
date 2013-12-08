# -*- encoding: utf-8 -*-
from osv import fields,osv
from tools.translate import _
import time
from datetime import datetime, date
from email.Utils import formatdate
import os
import base64,os,re
import sys
reload(sys)
sys.setdefaultencoding("utf8")


class yhoc_chude(osv.osv):
        
    _name = "yhoc_chude"
    
    
    def gioihanchu(self, string, limit):
        if string:
            pb_ngan = (string).split(' ')
            pb_ngan_ = []
            if len(pb_ngan) > limit:
                for i in range(0,limit):
                    pb_ngan_.append(pb_ngan[i])
                pb_ngan_.append('...')
                pb_ngan_ = ' '.join(pb_ngan_)
            else:
                return string
            return pb_ngan_
        else:
            return ''    
    
    def name_get(self, cr, uid, ids, context=None):
        if not len(ids):
            return []
        reads = self.read(cr, uid, ids, ['name','parent_id'], context=context)
        res = []
        for record in reads:
            name = record['name']
            if record['parent_id']:
                name = record['parent_id'][1]+' / '+name
            res.append((record['id'], name))
        return res

    def _name_get_fnc(self, cr, uid, ids, prop, unknow_none, context=None):
        res = self.name_get(cr, uid, ids, context=context)
        return dict(res)
    
    _columns = {
                'name':fields.char("Tên chủ đề",size=500, required='1'),
                'photo': fields.binary('Hình',filters='*.png,*.gif,*.jpg'),
                'description':fields.text('Giới thiệu'),
                'parent_id': fields.many2one('yhoc_chude', 'Chủ đề cha'),
                'link':fields.char('Link chủ đề',size=1000),
                'link_tree':fields.char('Link tree',size=1000),
                'complete_name': fields.function(_name_get_fnc, type="char", string='Name'),
                'link_url':fields.char('Link url',size=1000),
                'soluongxem': fields.integer("Số lượng người xem"),
                'keyword_ids': fields.many2many('yhoc_keyword', 'chude_keyword_rel', 'chude_id', 'keyword_id', 'Keyword'),
                'main_key':fields.many2one('yhoc_keyword', 'Từ khóa chính'),
                'soluongchude': fields.integer("Số lượng chủ đề"),
                }
    _defaults={
               }
    
    def get_url(self,tree_obj):
        linktree = []
        for i in range(len(tree_obj)):
            name = self.pool.get('yhoc_trangchu').parser_url(str(tree_obj[len(tree_obj)-i-1].name))
            linktree.append(name)
        res = "/".join(linktree)
        return res
    
    def write(self, cr, uid, ids, vals, context=None):
        chude = self.browse(cr, uid, ids[0], context=context)
        a = self.get_tree_obj(cr, uid, chude, context=context)
        aa = self.get_url(a)
        return super(yhoc_chude,self).write(cr, uid, ids, vals, context=context)
    
    def get_tree_obj(self, cr, uid, chude, context=None):
        linktree = []
        treechude = []
        treechude = self.dequy(treechude, chude)
        treechude.insert(0,chude)
        return treechude
    
    def dequy(self, list, x):
        if not x.parent_id:
            return list
        else:
            list.append(x.parent_id)
            return self.dequy(list,x.parent_id)
    
    
    def capnhat_chudetrongtrangduan(self, cr, uid, chude, context=None):
        '''SỬ dụng bên dự án'''
        
        duongdan = self.pool.get('hlv.property')._get_value_project_property_by_name(cr, uid, 'path of template')
        domain = self.pool.get('hlv.property')._get_value_project_property_by_name(cr, uid, 'Domain') or '../..'
        folder_chude = duongdan + '/%s/' %str(chude.link_url)
        
        chudecon_da = self.pool.get('yhoc_duan').search(cr, uid, [('chude_id','=',chude.id),('link','!=',False)])
        chudecon_da = self.pool.get('yhoc_duan').browse(cr, uid, chudecon_da, context=context)
        chudecon_cd = self.pool.get('yhoc_chude').search(cr, uid, [('parent_id','=',chude.id),('link','!=',False)])
        chudecon_cd = self.pool.get('yhoc_chude').browse(cr, uid, chudecon_cd, context=context)
        chudecon = chudecon_cd + chudecon_da
        
        cungchude_tab_ = '''<li><a href="__LINKBAIVIET__">__TENBAIVIET__</a></li>'''
        all_cungchude = '' 
        for ccdr in chudecon:
            cungchude_tab = cungchude_tab_.replace('__LINKBAIVIET__', ccdr.link)
            cungchude_tab = cungchude_tab.replace('__TENBAIVIET__', ccdr.name)
            all_cungchude += cungchude_tab
        
        if not os.path.exists(folder_chude+'/data'):
            os.makedirs(folder_chude+'/data')
        import codecs
        fw = codecs.open(folder_chude+'/data/chudetrongtrangduan.html','w','utf-8')
        fw.write(str(all_cungchude))
        fw.close()
        return  True

    def capnhat_thongtin(self,cr,uid,ids,context):
        duongdan = self.pool.get('hlv.property')._get_value_project_property_by_name(cr, uid, 'path of template')
        domain = self.pool.get('hlv.property')._get_value_project_property_by_name(cr, uid, 'Domain') or '../..'
        kieufile = self.pool.get('hlv.property')._get_value_project_property_by_name(cr, uid, 'Kiểu lưu file') or 'html'
        chude = self.browse(cr, uid, ids[0], context=context)
        
        name_url = self.pool.get('yhoc_trangchu').parser_url(str(chude.name))
        link_url = 'chude/%s'%(name_url)        
        folder_chude = duongdan + '/chude/%s'%(name_url)

        duan_thuoc_cd = self.pool.get('yhoc_duan').search(cr, uid, [('chude_id','=',chude.id),('link','!=',False)])
        
        chudecon_cd = []
        chudecon_da = []
        if chude.parent_id:
            fr = open(duongdan + '/template/chude/chudecon.html', 'r')
            template = fr.read()
            fr.close()
        else:
            fr = open(duongdan + '/template/chude/chude.html', 'r')
            template = fr.read()
            fr.close()
        
        chudecon_da = self.pool.get('yhoc_duan').search(cr, uid, [('chude_id','=',chude.id),('link','!=',False)])
        chudecon_da = self.pool.get('yhoc_duan').browse(cr, uid, chudecon_da, context=context)
        chudecon_cd = self.pool.get('yhoc_chude').search(cr, uid, [('parent_id','=',chude.id),('link','!=',False)])
        chudecon_cd = self.pool.get('yhoc_chude').browse(cr, uid, chudecon_cd, context=context)
        chudecon = chudecon_cd + chudecon_da
        super(yhoc_chude,self).write(cr,uid,[chude.id],{'soluongchude':len(chudecon)}, context=context)
        
        photo = ''
        if chude.photo:
            if not os.path.exists(duongdan + '/images/chude'):
                os.makedirs(duongdan + '/images/chude')
            path_hinh_ghixuong = duongdan + '/images/chude' + '/%s-chude-%s.jpg' %(str(chude.id),name_url)
            fw = open(path_hinh_ghixuong,'wb')
            fw.write(base64.decodestring(chude.photo))
            fw.close()
            photo = domain + '/images/chude/%s-chude-%s.jpg' %(str(chude.id),name_url)
        
        template = template.replace('__ITEMTYPE__', 'WebPage')
        template = template.replace('__TENCHUDE__', chude.name)
        template = template.replace('__ID__', str(chude.id))
        template = template.replace('__URL__', domain + '/%s/'%(chude.link_url))
        template = template.replace('__DOMAIN__', domain)
        template = template.replace('__DUONGDAN__', duongdan)
        template = template.replace('__MOTACHUDE__', str(chude.description))
        template = template.replace('__HINHCHUDE__', photo)
        #date = datetime.strptime(chude.create_date, '%Y-%m-%d %H:%M:%S')
        date = datetime.now().strftime('%d-%m-%Y %H:%M')
        template = template.replace('__NGAYCAPNHAT__', date)
        self.capnhat_sharebutton(cr, uid, chude.id, context=context)
        template = template.replace('__SHARE_BUTTON__', duongdan + '/%s/share_social_button.html'%(chude.link_url))
        
        all_chude_tab = ''
        if len(chudecon) > 0:
            fr = open(duongdan + '/template/chude/chude_duan.html', 'r')
            chude_tab_ = fr.read()
            fr.close()
            fr = open(duongdan + '/template/chude/chude_mucluc.html', 'r')
            mucluc_ = fr.read()
            mucluc_item_ ='''<li><a href="__LINKMUCLUC__"><span>__TENDUAN__</span></a></li>
            '''
            fr.close()
            all_mucluc_ = ''
            for cdcr in chudecon_cd:
                name_url_cdc = self.pool.get('yhoc_trangchu').parser_url(str(cdcr.name))
                photo = ''
                if cdcr.photo:
                    if not os.path.exists(duongdan + '/images/chude'):
                        os.makedirs(duongdan + '/images/chude')
                    path_hinh_ghixuong = duongdan + '/images/chude' + '/%s-chude-%s.jpg' %(str(cdcr.id),name_url_cdc)
                    fw = open(path_hinh_ghixuong,'wb')
                    fw.write(base64.decodestring(cdcr.photo))
                    fw.close()
                    photo = domain + '/images/chude/%s-chude-%s.jpg' %(str(cdcr.id),name_url_cdc)
                
                chude_tab = chude_tab_.replace('__LINKDUAN__', domain + '/%s/'%(cdcr.link_url) or '#')
                chude_tab = chude_tab.replace('__TENDUAN__', cdcr.name)
                chude_tab = chude_tab.replace('__ID_MUCLUC__', name_url_cdc)
                chude_tab = chude_tab.replace('__SOLUOTXEM__', str(cdcr.soluongxem))
                chude_tab = chude_tab.replace('__HINHDUAN__', photo)
                chude_tab = chude_tab.replace('__MOTADUAN__', str(cdcr.description) or '')
                chude_tab = chude_tab.replace('__DUONGDAN__', duongdan)
                chude_tab = chude_tab.replace('__SHARE_BUTTON__', duongdan + '/%s/share_social_button.html'%(cdcr.link_url))
                all_chude_tab += chude_tab
                mucluc_item = mucluc_item_.replace('__TENDUAN__', cdcr.name)
                mucluc_item = mucluc_item.replace('__LINKMUCLUC__', '#%s'%name_url_cdc)
                all_mucluc_ += mucluc_item
            
            for cdcr in chudecon_da:
                name_url_cdc = self.pool.get('yhoc_trangchu').parser_url(str(cdcr.name))
                photo = ''
                if cdcr.photo:
                    if not os.path.exists(duongdan + '/images/duan'):
                        os.makedirs(duongdan + '/images/duan')
                    path_hinh_ghixuong = duongdan + '/images/duan' + '/%s-duan-%s.jpg' %(str(cdcr.id),name_url_cdc)
                    fw = open(path_hinh_ghixuong,'wb')
                    fw.write(base64.decodestring(cdcr.photo))
                    fw.close()
                    photo = domain + '/images/duan/%s-duan-%s.jpg' %(str(cdcr.id),name_url_cdc)
                chude_tab = chude_tab_.replace('__LINKDUAN__', domain + '/%s/'%(cdcr.link_url) or '#')
                chude_tab = chude_tab.replace('__TENDUAN__', cdcr.name)
                chude_tab = chude_tab.replace('__ID_MUCLUC__', name_url_cdc)
                chude_tab = chude_tab.replace('__SOLUOTXEM__', str(cdcr.soluongxem))
                chude_tab = chude_tab.replace('__HINHDUAN__', photo)
                chude_tab = chude_tab.replace('__MOTADUAN__', str(cdcr.description) or '')
                chude_tab = chude_tab.replace('__DUONGDAN__', duongdan)
                chude_tab = chude_tab.replace('__SHARE_BUTTON__', duongdan + '/%s/share_social_button.html'%(cdcr.link_url))
                all_chude_tab += chude_tab
                mucluc_item = mucluc_item_.replace('__TENDUAN__', cdcr.name)
                mucluc_item = mucluc_item.replace('__LINKMUCLUC__', '#%s'%name_url_cdc)
                all_mucluc_ += mucluc_item
                
            mucluc = mucluc_.replace('__MUCLUCITEM__', all_mucluc_)
            template = template.replace('__MUCLUC__', mucluc)
            template = template.replace('__CHUDEDUAN__', all_chude_tab)


#Lay chu de/du an thuoc chu de cha
            if chude.parent_id:
                template = template.replace('__CHUDECHA__', chude.parent_id.name)
                template = template.replace('__LINKCHUDECHA__', domain + '/%s/'%(chude.parent_id.link_url))
                chudecon_cuacha_da = self.pool.get('yhoc_duan').search(cr, uid, [('chude_id','=',chude.parent_id.id),('link','!=',False)])
                chudecon_cuacha_cd = self.pool.get('yhoc_chude').search(cr, uid, [('parent_id','=',chude.parent_id.id),('link','!=',False)])
                chudecon_cuacha = chudecon_cuacha_da + chudecon_cuacha_cd
                template = template.replace('__SOLUONGCHUDE__', str(chude.parent_id.soluongchude))
                all_cungchude = '' 
                cungchude_tab_='''<li><img class="thongtinleftimg" src="__HINHCHUDE__"/><a href="__LINKCHUDE__">__TENCHUDE__</a></li>
                '''
                if chudecon_cuacha:
                    for cd in chudecon_cuacha_cd:
                        cdr = self.browse(cr, uid, cd, context=context)
                        name_url_cdc = self.pool.get('yhoc_trangchu').parser_url(str(cdr.name))
                        photo = ''
                        if cdr.photo:
                            if not os.path.exists(duongdan + '/images/chude'):
                                os.makedirs(duongdan + '/images/chude')
                            path_hinh_ghixuong = duongdan + '/images/chude' + '/%s-chude-%s.jpg' %(str(cdr.id),name_url_cdc)
                            fw = open(path_hinh_ghixuong,'wb')
                            fw.write(base64.decodestring(cdr.photo))
                            fw.close()
                            photo = domain + '/images/chude/%s-chude-%s.jpg' %(str(cdr.id),name_url_cdc)
                        cungchude_tab = cungchude_tab_.replace('__LINKCHUDE__', domain + '/%s/'%(cdr.link_url))
                        cungchude_tab = cungchude_tab.replace('__TENCHUDE__', cdr.name)
                        cungchude_tab = cungchude_tab.replace('__HINHCHUDE__', photo)
                        all_cungchude += cungchude_tab
                    for cd in chudecon_cuacha_da:
                        cdr = self.pool.get('yhoc_duan').browse(cr, uid, cd, context=context)
                        name_url_cdc = self.pool.get('yhoc_trangchu').parser_url(str(cdr.name))
                        photo = ''
                        if cdr.photo:
                            if not os.path.exists(duongdan + '/images/duan'):
                                os.makedirs(duongdan + '/images/duan')
                            path_hinh_ghixuong = duongdan + '/images/duan' + '/%s-duan-%s.jpg' %(str(cdr.id),name_url_cdc)
                            fw = open(path_hinh_ghixuong,'wb')
                            fw.write(base64.decodestring(cdr.photo))
                            fw.close()
                            photo = domain + '/images/duan/%s-duan-%s.jpg' %(str(cdcr.id),name_url_cdc)
                        cungchude_tab = cungchude_tab_.replace('__LINKCHUDE__', domain + '/%s/'%(cdr.link_url))
                        cungchude_tab = cungchude_tab.replace('__TENCHUDE__', cdr.name)
                        cungchude_tab = cungchude_tab.replace('__HINHCHUDE__', photo)
                        all_cungchude += cungchude_tab
                        
                    template = template.replace('__CHUDE_BENTRAI__', all_cungchude)
                     
            item_ = '''<span class="crust">
                                    <a href="__LINK__" class="crumb"><span>__NAME__</span></a>
                                    <span class="arrow"><span></span></span>
                                </span>'''
            linktree = []
            res = ''
            
            treechude = []
            treechude = self.dequy(treechude, chude)
            treechude.insert(0,chude)
            all_item_ =''
            item = item_.replace('__LINK__', domain)
            item = item.replace('__NAME__', 'Trang chủ')
            all_item_ += item
            for i in range(len(treechude)):
                item = item_.replace('__LINK__', domain + '/%s/'%(treechude[len(treechude)-i-1].link_url))
                item = item.replace('__NAME__', treechude[len(treechude)-i-1].name)
                all_item_ += item
                linktree.append(item)
            template = template.replace('__LINKTREE__', all_item_)
            res = " > ".join(linktree)
            super(yhoc_chude,self).write(cr,uid,[chude.id],{'link_tree':res,
                                                            'link': domain + '/%s/'%(link_url),
                                                            'link_url':link_url}, context=context)
            #template = template.replace('__TUADECHUDE__', chude.name)
            #template = template.replace('__MOTA__', str(chude.description) or '')
            #template = template.replace('__HINHCHUDE__', domain + '/images/%s-chude-%s.jpg' %(str(chude.id),name_url))
            
            if not os.path.exists(folder_chude):
                os.makedirs(folder_chude)
            import codecs
            fw = codecs.open(folder_chude+'/index.' + kieufile,'w','utf-8')
            fw.write(str(template))
            fw.close()
            
            if not chude.parent_id:
                chudecha = self.pool.get('yhoc_chude').search(cr, uid, [('parent_id','=',False)])
                folder_trangchu = duongdan + '/trangchu/vi'
                self.pool.get('yhoc_trangchu').capnhat_header(cr, uid, chudecha, duongdan, domain, folder_trangchu, context)
            else:
                self.capnhat_thongtin(cr, uid, [chude.parent_id.id], context)
            return template, duongdan, domain
        else:
            return template, duongdan, domain

#Giang_0712#    
#    def capnhat_thongtin(self,cr,uid,ids,context):
#        duongdan = self.pool.get('hlv.property')._get_value_project_property_by_name(cr, uid, 'path of template')
#        domain = self.pool.get('hlv.property')._get_value_project_property_by_name(cr, uid, 'Domain') or '../..'
#        kieufile = self.pool.get('hlv.property')._get_value_project_property_by_name(cr, uid, 'Kiểu lưu file') or 'html'
#        chude = self.browse(cr, uid, ids[0], context=context)
#        
#        tree_obj = self.get_tree_obj(cr, uid, chude, context=context)
##        link_url = self.get_url(tree_obj)
#        name_url = self.pool.get('yhoc_trangchu').parser_url(str(chude.name))
#        link_url = 'chude/%s'%(name_url)
#        
##        folder = duongdan
##        for i in range(len(tree_obj)):
##            folder += '/%s' %(self.pool.get('yhoc_trangchu').parser_url(str(tree_obj[len(tree_obj)-i-1].name)))
##            if not os.path.exists(folder):
##                os.makedirs(folder)
#        folder_chude = duongdan + '/chude/%s'%(name_url)
##        folder_chude = duongdan + '/%s-%s' %(str(chude.id),name_url)
#        duan_thuoc_cd = self.pool.get('yhoc_duan').search(cr, uid, [('chude_id','=',chude.id),('link','!=',False)])
#        
#        chudecon_cd = []
#        chudecon_da = []
#        if chude.parent_id:
#            fr = open(duongdan + '/template/chude/chudecon.html', 'r')
#            template = fr.read()
#            fr.close()
#        else:
#            fr = open(duongdan + '/template/chude/chude.html', 'r')
#            template = fr.read()
#            fr.close()
#            
##        if os.path.exists(duongdan+'/trangchu/vi/header.html'):
##            fr = open(duongdan+'/trangchu/vi/header.html', 'r')
##            header_ = fr.read()
##            fr.close()
##        
##        if os.path.exists(duongdan+'/trangchu/vi/footer.html'):
##            fr = open(duongdan+'/trangchu/vi/footer.html', 'r')
##            footer_ = fr.read()
##            fr.close()
##            
##        template = template.replace('__HEADER__',header_)
##        template = template.replace('__FOOTER__',footer_)
#        
#        chudecon_da = self.pool.get('yhoc_duan').search(cr, uid, [('chude_id','=',chude.id),('link','!=',False)])
#        chudecon_da = self.pool.get('yhoc_duan').browse(cr, uid, chudecon_da, context=context)
#        chudecon_cd = self.pool.get('yhoc_chude').search(cr, uid, [('parent_id','=',chude.id),('link','!=',False)])
#        chudecon_cd = self.pool.get('yhoc_chude').browse(cr, uid, chudecon_cd, context=context)
#        
##        if not chude.parent_id:
##            fr = open(duongdan + '/template/chude/chude.html', 'r')
##            template = fr.read()
##            fr.close()
##            chudecon_cd = self.pool.get('yhoc_chude').search(cr, uid, [('parent_id','=',chude.id),('link','!=',False)])
##            chudecon_cd = self.browse(cr, uid, chudecon_cd, context=context)
#            
##Cập nhật tittle       
#        fr = open(duongdan + '/template/trangchu/tittle.html', 'r')
#        noidung_tittle = fr.read()
#        fr.close()
#        noidung_tittle = noidung_tittle.replace('__TITLE__','Chủ đề ' + chude.name)
#        template = template.replace('__TITLE__',noidung_tittle)
#        template = template.replace('__DUONGDAN__',duongdan)
#        template = template.replace('__ID__', str(chude.id))
#
#        chudecon = chudecon_cd + chudecon_da
#        all_chude_tab = ''
#        if len(chudecon) > 0:
#            fr = open(duongdan + '/template/chude/chude_tab.html', 'r')
#            chude_tab_ = fr.read()
#            fr.close()
#            for cdcr in chudecon_cd:
#                name_url_cdc = self.pool.get('yhoc_trangchu').parser_url(str(cdcr.name))
#                photo = ''
#                if cdcr.photo:
#                    if not os.path.exists(duongdan + '/images/chude'):
#                        os.makedirs(duongdan + '/images/chude')
#                    path_hinh_ghixuong = duongdan + '/images/chude' + '/%s-chude-%s.jpg' %(str(cdcr.id),name_url_cdc)
#                    fw = open(path_hinh_ghixuong,'wb')
#                    fw.write(base64.decodestring(cdcr.photo))
#                    fw.close()
#                    photo = domain + '/images/chude/%s-chude-%s.jpg' %(str(cdcr.id),name_url_cdc)
#                if cdcr.link_url:
#                    chude_tab = chude_tab_.replace('__LINKCHUDE__', domain + '/%s/'%(cdcr.link_url))
#                else:
#                    chude_tab = chude_tab_.replace('__LINKCHUDE__', '#')
#                chude_tab = chude_tab.replace('__ANHCHUDE__', photo)
#                chude_tab = chude_tab.replace('__TENCHUDE__', cdcr.name)
#                chude_tab = chude_tab.replace('__MOTANGAN__', self.gioihanchu(str(cdcr.description), 35) or '(Chưa cập nhật)')
#                all_chude_tab += chude_tab
#            
#            for cdcr in chudecon_da:
#                name_url_cdc = self.pool.get('yhoc_trangchu').parser_url(str(cdcr.name))
#                photo = ''
#                if cdcr.photo:
#                    if not os.path.exists(duongdan + '/images/duan'):
#                        os.makedirs(duongdan + '/images/duan')
#                    path_hinh_ghixuong = duongdan + '/images/duan' + '/%s-duan-%s.jpg' %(str(cdcr.id),name_url_cdc)
#                    fw = open(path_hinh_ghixuong,'wb')
#                    fw.write(base64.decodestring(cdcr.photo))
#                    fw.close()
#                    photo = domain + '/images/duan/%s-duan-%s.jpg' %(str(cdcr.id),name_url_cdc)
#                if cdcr.link_url: 
#                    chude_tab = chude_tab_.replace('__LINKCHUDE__', domain + '/%s/'%(cdcr.link_url))
#                else:
#                    chude_tab = chude_tab_.replace('__LINKCHUDE__', '#')
#                chude_tab = chude_tab.replace('__ANHCHUDE__', photo)
#                chude_tab = chude_tab.replace('__TENCHUDE__', cdcr.name)
#                chude_tab = chude_tab.replace('__MOTANGAN__', self.gioihanchu(str(cdcr.description), 35) or '(Chưa cập nhật)')
#                all_chude_tab += chude_tab
#                
#            template = template.replace('__CHUDECON__', all_chude_tab)
#
#
##Lay chu de/du an thuoc chu de cha
#            if chude.parent_id:
#                template = template.replace('__CHUDE__', chude.parent_id.name)
#                chudecon_cuacha_da = self.pool.get('yhoc_duan').search(cr, uid, [('chude_id','=',chude.parent_id.id),('link','!=',False)])
#                chudecon_cuacha_cd = self.pool.get('yhoc_chude').search(cr, uid, [('parent_id','=',chude.parent_id.id),('link','!=',False)])
#                chudecon_cuacha = chudecon_cuacha_da + chudecon_cuacha_cd
#                all_cungchude = '' 
#                cungchude_tab_ = '''<li><a href="__LINKBAIVIET__">__TENBAIVIET__</a></li>'''
#                if chudecon_cuacha:
#                    for cd in chudecon_cuacha_cd:
#                        cdr = self.browse(cr, uid, cd, context=context)
#                        cungchude_tab = cungchude_tab_.replace('__LINKBAIVIET__', domain + '/%s/'%(cdr.link_url))
#                        cungchude_tab = cungchude_tab.replace('__TENBAIVIET__', cdr.name)
#                        all_cungchude += cungchude_tab
#                    for cd in chudecon_cuacha_da:
#                        cdr = self.pool.get('yhoc_duan').browse(cr, uid, cd, context=context)
#                        cungchude_tab = cungchude_tab_.replace('__LINKBAIVIET__', domain + '/%s/'%(cdr.link_url))
#                        cungchude_tab = cungchude_tab.replace('__TENBAIVIET__', cdr.name)
#                        all_cungchude += cungchude_tab
#                        
#                    template = template.replace('__BAIVIET_CUNGCHUDE__', all_cungchude)
#            
##Lấy thông tin cùng chủ đề:
##            cungchude = self.pool.get('hlv_thongtin').search(cr, uid, [('public','=',True),('duan.chude_id.id', '=',chude.id)], limit=10, order='create_date desc', context=context)
##            cungchude_tab_ = '''<li><a href="__LINKBAIVIET__">__TENBAIVIET__</a></li>'''
##            all_cungchude = '' 
##            for ccd in cungchude:
##                ccdr = self.pool.get('hlv_thongtin').browse(cr, uid, ccd, context=context)
##                try:
##                    self.pool.get('hlv_thongtin').capnhat_thongtin(cr, uid, [ccd], context=context)
##                except:
##                    pass
##                cungchude_tab = cungchude_tab_.replace('__LINKBAIVIET__', ccdr.link)
##                cungchude_tab = cungchude_tab.replace('__TENBAIVIET__', ccdr.name)
##                all_cungchude += cungchude_tab
##            
##            template = template.replace('__BAIVIET_CUNGCHUDE__', all_cungchude)
#            
#            
#            temp_ = '''<a href="__LINK__">__NAME__</a>'''
#            linktree = []
#            res = ''
##            temp = temp_.replace('__LINK__', chude.link or '#')
##            temp = temp.replace('__NAME__', chude.name)
##            linktree.append(temp)
#            
#            treechude = []
#            treechude = self.dequy(treechude, chude)
#            treechude.insert(0,chude)
#            
#            for i in range(len(treechude)):
#                temp = temp_.replace('__LINK__', domain + '/%s/'%(treechude[len(treechude)-i-1].link_url))
#                temp = temp.replace('__NAME__', treechude[len(treechude)-i-1].name)
#                linktree.append(temp)
##            if chude.parent_id:
##                temp = temp_.replace('__LINK__', chude.parent_id.link or '#')
##                temp = temp.replace('__NAME__', chude.parent_id.name)
##                linktree.insert(0,temp)
#                
#                
#            linktree.insert(0,'''<a href="../../../../../../trangchu/vi/'''  + '''">Trang chủ</a>''')
#            res = " > ".join(linktree)
#            super(yhoc_chude,self).write(cr,uid,[chude.id],{'link_tree':res,
#                                                            'link': domain + '/%s/'%(link_url),
#                                                            'link_url':link_url}, context=context)
#            template = template.replace('__LINKTREE__', res)
#            template = template.replace('__TUADECHUDE__', chude.name)
#            template = template.replace('__MOTA__', str(chude.description) or '')
#            template = template.replace('__HINHCHUDE__', domain + '/images/%s-chude-%s.jpg' %(str(chude.id),name_url))
#            
#            if not os.path.exists(folder_chude):
#                os.makedirs(folder_chude)
#            import codecs
#            fw = codecs.open(folder_chude+'/index.' + kieufile,'w','utf-8')
#            fw.write(str(template))
#            fw.close()
#            
#            if not chude.parent_id:
#                chudecha = self.pool.get('yhoc_chude').search(cr, uid, [('parent_id','=',False)])
#                folder_trangchu = duongdan + '/trangchu/vi'
#                self.pool.get('yhoc_trangchu').capnhat_header(cr, uid, chudecha, duongdan, domain, folder_trangchu, context)
#            else:
#                self.capnhat_thongtin(cr, uid, [chude.parent_id.id], context)
#            return template, duongdan, domain
#        else:
#            return template, duongdan, domain
             
#Giang#0911-Cap Nhat RSS ChuDe
    def capnhat_rsschude(self, cr, uid, cd_id, context=None):
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
        chude = self.browse(cr, uid, cd_id[0], context=context)
        if chude.parent_id:
            name = self.pool.get('yhoc_trangchu').parser_url(chude.name)
            #template = template_.replace('__LINKRSS__', domain + '/rss/%s.rss'%(name))
            template = template_.replace('__TITLECHANNEL__', chude.name)
            template = template.replace('__MOTACHANNEL__', chude.description or '(Chưa Cập Nhật)')
            template = template.replace('__LINKCHANNEL__', domain +'/rss/%s.rss'%(name))
            template = template.replace('__HINHCHANNEL__', domain + '/images/%s-chude-%s.jpg' %(str(chude.id),name))
            
            cungchude = self.pool.get('yhoc_thongtin').search(cr, uid, [('state','=','done'),('duan.chude_id.id', '=',chude.id)], limit=10, order='date desc', context=context)

            allrss_item_ = ''
            for ccd in cungchude:
                thongtin = self.pool.get('yhoc_thongtin').browse(cr, uid, ccd, context=context)
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
            fw = codecs.open(duongdan +'/rss/%s.rss'%(name),'w','utf-8')
            fw.write(template)
            fw.close()     
        return True
    
    def taotrangrss(self,cr,uid,context=None):
        duongdan = self.pool.get('hlv.property')._get_value_project_property_by_name(cr, uid, 'path of template')
        domain = self.pool.get('hlv.property')._get_value_project_property_by_name(cr, uid, 'Domain') or '../..'
        kieufile = self.pool.get('hlv.property')._get_value_project_property_by_name(cr, uid, 'Kiểu lưu file') or 'html'
        
        folder_tags = duongdan + '/rss'
        if not os.path.exists(folder_tags):
            os.makedirs(folder_tags)
                
        if os.path.exists(duongdan+'/template/rss/index.html'):
            fr = open(duongdan+'/template/rss/index.html', 'r')
            template_ = fr.read()
            fr.close()
        else:
            template_ = ''
            
        if os.path.exists(duongdan+'/template/rss/rss_item.html'):
            fr = open(duongdan+'/template/rss/rss_item.html', 'r')
            item_ = fr.read()
            fr.close()
        else:
            item_ = ''
        
        chude = self.pool.get('yhoc_chude').search(cr, uid, [('link','!=',False)])
        
        rss_item_ = ''
        for cd in chude:
            cd = self.browse(cr, uid, cd, context=context)
            if cd.parent_id:
                name = self.pool.get('yhoc_trangchu').parser_url(cd.name)
                item = item_.replace('__TITLECHUDE__', cd.name) 
                item = item.replace('__LINKCHUDE__', domain +'/rss/%s.rss'%(name) or '#')                
                rss_item_ += item

        import codecs  
        fw = codecs.open(folder_tags +'/rss_item.html','w','utf-8')
        fw.write(rss_item_)
        fw.close()
        
        fw = codecs.open(folder_tags +'/index.%s'%kieufile,'w','utf-8')
        fw.write(template_)
        fw.close()
        return True
    
    def capnhat_sharebutton(self, cr, uid, ids, context=None):
        duongdan = self.pool.get('hlv.property')._get_value_project_property_by_name(cr, uid, 'path of template')
        domain = self.pool.get('hlv.property')._get_value_project_property_by_name(cr, uid, 'Domain') or '../..'
        chude = self.browse(cr,uid,ids)
        if os.path.exists(duongdan+'/template/chude/share_social_button.html'):
            fr = open(duongdan+'/template/chude/share_social_button.html', 'r')
            template_ = fr.read()
            fr.close()
        else:
            template_ = ''
        template = template_.replace('__DOMAIN__', domain)
        template = template.replace('__URL__', domain + '/%s/'%chude.link_url)
        template = template.replace('__TITLE__', chude.name)
        template = template.replace('__DESCRIPTION__', str(chude.description))
        name_url = self.pool.get('yhoc_trangchu').parser_url(str(chude.name))
        photo = domain + '/images/chude/%s-chude-%s.jpg'%(str(chude.id),name_url)
        template = template.replace('__IMAGE__', photo)
        folder_chude = duongdan + '/%s/'%chude.link_url
        if not os.path.exists(folder_chude):
                os.makedirs(folder_chude)
        import codecs  
        fw = codecs.open(duongdan + '/%s/share_social_button.html'%chude.link_url,'w','utf-8')
        fw.write(template)
        fw.close()
        return True

yhoc_chude()

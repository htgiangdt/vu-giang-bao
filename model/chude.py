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
                'noidung':fields.text('Nội dung'),
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
    
#    def dequy(self, list, x):
#        if not x.parent_id:
#            return list
#        else:
#            list.append(x.parent_id)
#            return self.dequy(list,x.parent_id)

    def dequy(self, list, x):
        if x.parent_id.name == 'Trang chủ':
            return list
        else:
            list.append(x.parent_id)
            return self.dequy(list,x.parent_id)
    
    def capnhat_chudetrongtrangduan(self, cr, uid, chude, context=None):
        '''SỬ dụng bên dự án - các dự án cùng chủ đề'''
        
        duongdan = self.pool.get('hlv.property')._get_value_project_property_by_name(cr, uid, 'path of template')
        domain = self.pool.get('hlv.property')._get_value_project_property_by_name(cr, uid, 'Domain') or '../..'
        folder_chude = duongdan + '/%s/' %str(chude.link_url)
        
        chudecon_da = self.pool.get('yhoc_duan').search(cr, uid, [('chude_id','=',chude.id),('link','!=',False)])
        chudecon_da = self.pool.get('yhoc_duan').browse(cr, uid, chudecon_da, context=context)
        chudecon_cd = self.pool.get('yhoc_chude').search(cr, uid, [('parent_id','=',chude.id),('link','!=',False)])
        chudecon_cd = self.pool.get('yhoc_chude').browse(cr, uid, chudecon_cd, context=context)
        chudecon = chudecon_cd + chudecon_da
        
        #cungchude_tab_ = '''<li><a href="__LINKBAIVIET__">__TENBAIVIET__</a></li>'''
        cungchude_tab_ = '''<li> <img class="thongtinleftimg" src="__PHOTO__"/><a href="__LINKBAIVIET__">__TENBAIVIET__</a></li>'''
        all_cungchude = '' 
        for ccdr in chudecon:
            name_url_ccdr = self.pool.get('yhoc_trangchu').parser_url(str(ccdr.name))
            photo = ''
            if ccdr.photo:
                if not os.path.exists(duongdan + '/images/chude'):
                    os.makedirs(duongdan + '/images/chude')
                path_hinh_ghixuong = duongdan + '/images/chude' + '/%s-chude-%s.jpg' %(str(ccdr.id),name_url_ccdr)
                fw = open(path_hinh_ghixuong,'wb')
                fw.write(base64.decodestring(ccdr.photo))
                fw.close()
                photo = domain + '/images/chude/%s-chude-%s.jpg' %(str(ccdr.id),name_url_ccdr)
                
            cungchude_tab = cungchude_tab_.replace('__LINKBAIVIET__', ccdr.link)
            cungchude_tab = cungchude_tab.replace('__TENBAIVIET__', ccdr.name)
            cungchude_tab = cungchude_tab.replace('__PHOTO__', photo)
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
        folder_chude_data = folder_chude + '/data/'

        duan_thuoc_cd = self.pool.get('yhoc_duan').search(cr, uid, [('chude_id','=',chude.id),('link','!=',False)])
        
        chudecon_cd = []
        chudecon_da = []
		
        if os.path.exists(duongdan + '/template/chude/chude.html'):
            fr = open(duongdan + '/template/chude/chude.html', 'r')
            template = fr.read()
            fr.close()
        else:
            template = ''
        
        chudecon_da = self.pool.get('yhoc_duan').search(cr, uid, [('chude_id','=',chude.id),('link','!=',False)])
        chudecon_da = self.pool.get('yhoc_duan').browse(cr, uid, chudecon_da, context=context)
        chudecon_cd = self.pool.get('yhoc_chude').search(cr, uid, [('parent_id','=',chude.id),('link','!=',False)])
        chudecon_cd = self.pool.get('yhoc_chude').browse(cr, uid, chudecon_cd, context=context)
        chudecon = chudecon_cd + chudecon_da
		
        super(yhoc_chude,self).write(cr,uid,[chude.id],{'soluongchude':len(chudecon),
                                                        'link': domain + '/%s/'%(link_url),
                                                        'link_url':link_url}, context=context)        
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
        template = template.replace('__URL__', domain + '/chude/%s/'%name_url)
        template = template.replace('__DOMAIN__', domain)
        template = template.replace('__DUONGDAN__', duongdan)
        if chude.description:
            template = template.replace('__MOTACHUDE__', str(chude.description))
        else:
            template = template.replace('__MOTACHUDE__', 'Đang cập nhật')
        if chude.noidung:
            noidung_template_ ='''<div id="noidungthongtin" style="padding-top:15px; line-height: 25px; max-width:700px; display;block; clear: both; text-align:justify;" itemprop="articleBody">    
                    __NOIDUNG_CHUDE__
                    <p>&nbsp;</p>
                </div>'''
            noidung_template = noidung_template_.replace('__NOIDUNG_CHUDE__', str(chude.noidung))
            template = template.replace('<!--__NOIDUNG__-->', noidung_template)
        template = template.replace('__HINHCHUDE__', photo)
        #date = datetime.strptime(chude.create_date, '%Y-%m-%d %H:%M:%S')
        date = datetime.now().strftime('%d-%m-%Y %H:%M')
        template = template.replace('__NGAYCAPNHAT__', date)
        share_button = self.capnhat_sharebutton(cr, uid, chude, duongdan, domain, folder_chude_data, context=context)
        template = template.replace('__SHARE_BUTTON__', share_button)
        
        all_chude_tab = ''
        if len(chudecon) > 0:
            if os.path.exists(duongdan + '/template/chude/chude_duan.html'):
                fr = open(duongdan + '/template/chude/chude_duan.html', 'r')
                chude_tab_ = fr.read()
                fr.close()
            else:
                chude_tab_ = ''
                
            if os.path.exists(duongdan + '/template/chude/mucluc.html'):
                fr = open(duongdan + '/template/chude/mucluc.html', 'r')
                mucluc_ = fr.read()
                fr.close()
            else:
                mucluc_ = ''
                
            if os.path.exists(duongdan + '/template/chude/mucluc_item.html'):
                fr = open(duongdan + '/template/chude/mucluc_item.html', 'r')
                mucluc_item_ = fr.read()
                fr.close()
            else:
                mucluc_item_ = ''
            
            all_mucluc_ = ''
            STT = 1
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
                chude_tab = chude_tab.replace('__STT__', str(STT))
                chude_tab = chude_tab.replace('__ID_MUCLUC__', name_url_cdc)
                chude_tab = chude_tab.replace('__SOLUOTXEM__', str(cdcr.soluongxem))
                chude_tab = chude_tab.replace('__HINHDUAN__', photo)
                chude_tab = chude_tab.replace('__MUCLUC__', '''<?php include("%s/chude/%s/data/mucluc.html")?>'''%(duongdan,name_url_cdc))
                if cdcr.description:
                    chude_tab = chude_tab.replace('__MOTADUAN__', str(cdcr.description))
                else:
                    chude_tab = chude_tab.replace('__MOTADUAN__', 'Đang cập nhật')
                chude_tab = chude_tab.replace('__DUONGDAN__', duongdan)
                chude_tab = chude_tab.replace('__SHARE_BUTTON__', duongdan + '/%s/data/share_button.html'%(cdcr.link_url))
                all_chude_tab += chude_tab
                # Mục lục của chủ đề
                mucluc_item = mucluc_item_.replace('__TEN_MUCLUC__', cdcr.name)
                mucluc_item = mucluc_item.replace('__LINK_MUCLUC__', cdcr.parent_id.link + '#%s'%name_url_cdc)
                mucluc_item = mucluc_item.replace('__STT__', str(STT))
                all_mucluc_ += mucluc_item
                STT += 1
            
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
                chude_tab = chude_tab.replace('__STT__', str(STT))
                chude_tab = chude_tab.replace('__ID_MUCLUC__', name_url_cdc)
                chude_tab = chude_tab.replace('__SOLUOTXEM__', str(cdcr.soluongxem))
                chude_tab = chude_tab.replace('__HINHDUAN__', photo)
                chude_tab = chude_tab.replace('__MUCLUC__', '''<?php include("%s/duan/%s/data/mucluc.html")?>'''%(duongdan,name_url_cdc))
                if cdcr.description:
                    chude_tab = chude_tab.replace('__MOTADUAN__', str(cdcr.description))
                else:
                    chude_tab = chude_tab.replace('__MOTADUAN__', 'Đang cập nhật')
                chude_tab = chude_tab.replace('__DUONGDAN__', duongdan)
                chude_tab = chude_tab.replace('__SHARE_BUTTON__', duongdan + '/%s/data/share_button.html'%(cdcr.link_url))
                all_chude_tab += chude_tab
                # Mục lục của chủ đề
                mucluc_item = mucluc_item_.replace('__TEN_MUCLUC__', cdcr.name)
                mucluc_item = mucluc_item.replace('__LINK_MUCLUC__', cdcr.chude_id.link + '#%s'%name_url_cdc)
                mucluc_item = mucluc_item.replace('__STT__', str(STT))
                all_mucluc_ += mucluc_item
                STT += 1
                
            mucluc = mucluc_.replace('__MUCLUC_ITEM__', all_mucluc_)
            mucluc = mucluc.replace('__MUCLUC_TITLE__', 'Nội dung chính')
            #template = template.replace('__CHUDEDUAN__', all_chude_tab)


#Lay chu de/du an thuoc chu de cha
            if chude.parent_id:
                template = template.replace('__CHUDECHA__', chude.parent_id.name)
                if chude.parent_id.name =='Trang chủ':
                    template = template.replace('__LINKCHUDECHA__', domain)
                    template = template.replace('__SOLUONGCHUDE__', '<!---->')
                else:
                    template = template.replace('__LINKCHUDECHA__', domain + '/%s/'%(chude.parent_id.link_url))
                    template = template.replace('__SOLUONGCHUDE__', str(chude.parent_id.soluongchude))
                chudecon_cuacha_da = self.pool.get('yhoc_duan').search(cr, uid, [('chude_id','=',chude.parent_id.id),('link','!=',False)])
                chudecon_cuacha_cd = self.pool.get('yhoc_chude').search(cr, uid, [('parent_id','=',chude.parent_id.id),('link','!=',False)])
                chudecon_cuacha = chudecon_cuacha_da + chudecon_cuacha_cd
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
            
            # Cập nhật link tree trong chủ đề
            self.capnhat_linktree_trongchude(cr, uid, chude, duongdan, domain, folder_chude_data, context)
            
#            # Cập nhật từ khóa cuối trang chủ đề
#            tags = chude.keyword_ids
#            list_tag = self.pool.get('yhoc_keyword').capnhat_listtag_ophiacuoi(cr, uid, tags, context=context)
#            template = template.replace('<!--__LIST_TAGS__-->', list_tag)

            if not os.path.exists(folder_chude):
                os.makedirs(folder_chude)
                
            if not os.path.exists(folder_chude_data):
                os.makedirs(folder_chude_data)
            #Cập nhật RSS
            #self.capnhat_rsschude(cr,uid,chude.id,context)
            #self.taotrangrss(cr, uid,duongdan, domain, context)
            
            
            import codecs
            fw = codecs.open(folder_chude_data + 'mucluc.html','w','utf-8')
            fw.write(str(mucluc))
            fw.close()
            
            fw = codecs.open(folder_chude_data + 'chude_duan.html','w','utf-8')
            fw.write(str(all_chude_tab))
            fw.close()
            
            fw = codecs.open(folder_chude+'/index.' + kieufile,'w','utf-8')
            fw.write(str(template))
            fw.close()
            
            if chude.parent_id.name == 'Trang chủ':
                chudecha = self.pool.get('yhoc_chude').search(cr, uid, [('parent_id.name','=','Trang chủ')])
                folder_trangchu = duongdan + '/trangchu/vi'
                self.pool.get('yhoc_trangchu').capnhat_header(cr, uid, chudecha, duongdan, domain, folder_trangchu, context)
            elif chude.parent_id:
                self.capnhat_thongtin(cr, uid, [chude.parent_id.id], context)
            return template, duongdan, domain
        else:
            return template, duongdan, domain

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
        chude = self.browse(cr, uid, cd_id, context=context)
        if chude.parent_id:
            name = self.pool.get('yhoc_trangchu').parser_url(chude.name)
            #template = template_.replace('__LINKRSS__', domain + '/rss/%s.rss'%(name))
            template = template_.replace('__TITLECHANNEL__', chude.name)
            template = template.replace('__MOTACHANNEL__', chude.description or 'Đang Cập Nhật')
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
    
    def taotrangrss(self, cr, uid, duongdan, domain,context=None):
        sequence = self.pool.get('hlv.property')._get_value_project_property_by_name(cr, uid, 'Thứ tự menu footer') or '[]'
        sequence = eval(sequence)
        kieufile = self.pool.get('hlv.property')._get_value_project_property_by_name(cr, uid, 'Kiểu lưu file') or 'html'
        folder_rss = duongdan + '/rss'
        if not os.path.exists(folder_rss):
            os.makedirs(folder_rss)
            
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
        all_item_ = ''
        li_tab_ = '''<li><a href="__LINK__">__NAME__</a></li>
        '''
        for s in sequence:
            chude = self.pool.get('yhoc_chude').search(cr, uid, [('name','=',s)], context=context)
            if chude:
                chude = self.pool.get('yhoc_chude').browse(cr, uid, chude[0], context=context)
                if chude.link:
                    item = item_.replace('__NAME_CHUDECHA__', chude.name)
                    chudecon_da = self.pool.get('yhoc_duan').search(cr, uid, [('chude_id','=',chude.id)])
                    chudecon_cd = self.pool.get('yhoc_chude').search(cr, uid, [('parent_id','=',chude.id)])
                    chudecon = chudecon_da + chudecon_cd
                    if chudecon:
                        all_li_ = ''
                        #doc sub menu tab
                        for cd in chudecon_cd:
                            cd = self.pool.get('yhoc_chude').browse(cr, uid, cd, context=context)
                            if cd.link:
                                name = self.pool.get('yhoc_trangchu').parser_url(cd.name)
                                li_tab = li_tab_.replace('__LINK__', domain +'/rss/%s.rss'%(name))
                                li_tab = li_tab.replace('__NAME__', cd.name)
                                all_li_ += li_tab
                            
                        for cd in chudecon_da:
                            cd = self.pool.get('yhoc_duan').browse(cr, uid, cd, context=context)
                            if cd.link:
                                name = self.pool.get('yhoc_trangchu').parser_url(cd.name)
                                li_tab = li_tab_.replace('__LINK__', domain +'/rss/%s.rss'%(name))
                                li_tab = li_tab.replace('__NAME__', cd.name)
                                all_li_ += li_tab
                            
                        item = item.replace('__CHUDECON__', all_li_)
                        all_item_ += item
                        
        import codecs  
        fw = codecs.open(folder_rss +'/rss_item.html','w','utf-8')
        fw.write(all_item_)
        fw.close()
                    
        template = template_.replace('__RSS_ITEMS__', folder_rss +'/rss_item.html')
        template = template.replace('__DUONGDAN__', duongdan)
        template = template.replace('__DOMAIN__', domain)
        
        fw = codecs.open(folder_rss +'/index.%s'%kieufile,'w','utf-8')
        fw.write(template)
        fw.close()
        return True
    
    def capnhat_sharebutton(self, cr, uid, chude, duongdan, domain, folder_chude_data, context=None):
        if os.path.exists(duongdan+'/template/chude/share_button.html'):
            fr = open(duongdan+'/template/chude/share_button.html', 'r')
            template_ = fr.read()
            fr.close()
        else:
            template_ = ''
        template = template_.replace('__DOMAIN__', domain)
        template = template.replace('__URL__', domain + '/%s/'%chude.link_url)
        template = template.replace('__TITLE__', chude.name)
        if not os.path.exists(folder_chude_data):
            os.makedirs(folder_chude_data)
        import codecs  
        fw = codecs.open(folder_chude_data + 'share_button.html','w','utf-8')
        fw.write(template)
        fw.close()
        return template
    
    def auto_tags(self,cr, uid, ids, context=None):
        kq = []
        chude = self.browse(cr, uid, ids[0], context=context)
        chudecon = self.search(cr, uid, [('parent_id','=',ids[0])], context=context)
        duancon = self.pool.get('yhoc_duan').search(cr, uid, [('chude_id','=',ids[0])], context=context)
        for da in duancon:
            da = self.pool.get('yhoc_duan').browse(cr, uid, da, context=context) 
            if da.main_key:
                kq.append(da.main_key.id)
            for tv in da.thanhvienthamgia:
                bs_tag = self.pool.get('yhoc_keyword').search(cr, uid, [('name','=',tv.name)],context=context)
                if bs_tag:
                    kq.append(bs_tag[0])
                elif not bs_tag:
                    bs_tag = self.pool.get('yhoc_keyword').create(cr, uid, {'name':tv.name}, context=context)
                    if bs_tag not in kq:
                        kq.append(bs_tag)
        for cd in chudecon:
            cd = self.browse(cr, uid, cd, context=context) 
            if cd.main_key:
                kq.append(cd.main_key.id)
                    
        vals = {'keyword_ids': [[6, False, list(set(kq))]]}
        self.write(cr, uid, ids, vals, context=context)
        return True
    
    def capnhat_linktree_trongchude(self, cr, uid, chude, duongdan, domain, folder_chude_data, context=None):
        if os.path.exists(duongdan+'/template/chude/linktree.html'):
            fr = open(duongdan+'/template/chude/linktree.html', 'r')
            template_ = fr.read()
            fr.close()
        else:
            template_ = ''
            
        if os.path.exists(duongdan+'/template/chude/linktree_item.html'):
            fr = open(duongdan+'/template/chude/linktree_item.html', 'r')
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
        treechude = self.dequy(treechude, chude)
        treechude.insert(0,chude)
        for i in range(len(treechude)-1):
            item = item_.replace('__LINK__', domain + '/%s/'%(treechude[len(treechude)-i-1].link_url))
            item = item.replace('__NAME__', treechude[len(treechude)-i-1].name)
            linktree.append(item)
            all_item_ += item
        res = ''
        res = " > ".join(linktree)
        super(yhoc_chude,self).write(cr,uid,[chude.id],{'link_tree':res}, context=context)
        template = template_.replace('__LINKTREEITEM__', all_item_)
        
        import codecs  
        fw= codecs.open(folder_chude_data + 'linktree_chude.html','w','utf-8')
        fw.write(template)
        fw.close()
        return True

    
yhoc_chude()

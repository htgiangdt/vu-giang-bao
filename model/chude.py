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
        folder_chude = duongdan + '/%s' %str(chude.link_url)
        
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
        
        tree_obj = self.get_tree_obj(cr, uid, chude, context=context)
#        link_url = self.get_url(tree_obj)
        name_url = self.pool.get('yhoc_trangchu').parser_url(str(chude.name))
        link_url = 'chude/%s'%(name_url)
        
#        folder = duongdan
#        for i in range(len(tree_obj)):
#            folder += '/%s' %(self.pool.get('yhoc_trangchu').parser_url(str(tree_obj[len(tree_obj)-i-1].name)))
#            if not os.path.exists(folder):
#                os.makedirs(folder)
        folder_chude = duongdan + '/chude/%s'%(name_url)
#        folder_chude = duongdan + '/%s-%s' %(str(chude.id),name_url)
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
            
#        if os.path.exists(duongdan+'/trangchu/vi/header.html'):
#            fr = open(duongdan+'/trangchu/vi/header.html', 'r')
#            header_ = fr.read()
#            fr.close()
#        
#        if os.path.exists(duongdan+'/trangchu/vi/footer.html'):
#            fr = open(duongdan+'/trangchu/vi/footer.html', 'r')
#            footer_ = fr.read()
#            fr.close()
#            
#        template = template.replace('__HEADER__',header_)
#        template = template.replace('__FOOTER__',footer_)
        
        chudecon_da = self.pool.get('yhoc_duan').search(cr, uid, [('chude_id','=',chude.id),('link','!=',False)])
        chudecon_da = self.pool.get('yhoc_duan').browse(cr, uid, chudecon_da, context=context)
        chudecon_cd = self.pool.get('yhoc_chude').search(cr, uid, [('parent_id','=',chude.id),('link','!=',False)])
        chudecon_cd = self.pool.get('yhoc_chude').browse(cr, uid, chudecon_cd, context=context)
        
#        if not chude.parent_id:
#            fr = open(duongdan + '/template/chude/chude.html', 'r')
#            template = fr.read()
#            fr.close()
#            chudecon_cd = self.pool.get('yhoc_chude').search(cr, uid, [('parent_id','=',chude.id),('link','!=',False)])
#            chudecon_cd = self.browse(cr, uid, chudecon_cd, context=context)
            
#Cập nhật tittle       
        fr = open(duongdan + '/template/trangchu/tittle.html', 'r')
        noidung_tittle = fr.read()
        fr.close()
        noidung_tittle = noidung_tittle.replace('__TITLE__','Chủ đề ' + chude.name)
        template = template.replace('__TITLE__',noidung_tittle)
        template = template.replace('__DUONGDAN__',duongdan)
        template = template.replace('__ID__', str(chude.id))

        chudecon = chudecon_cd + chudecon_da
        all_chude_tab = ''
        if len(chudecon) > 0:
            fr = open(duongdan + '/template/chude/chude_tab.html', 'r')
            chude_tab_ = fr.read()
            fr.close()
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
                if cdcr.link_url:
                    chude_tab = chude_tab_.replace('__LINKCHUDE__', '../../../../../../%s/'%(cdcr.link_url))
                else:
                    chude_tab = chude_tab_.replace('__LINKCHUDE__', '#')
                chude_tab = chude_tab.replace('__ANHCHUDE__', photo)
                chude_tab = chude_tab.replace('__TENCHUDE__', cdcr.name)
                chude_tab = chude_tab.replace('__MOTANGAN__', self.gioihanchu(str(cdcr.description), 35) or '(Chưa cập nhật)')
                all_chude_tab += chude_tab
            
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
                if cdcr.link_url: 
                    chude_tab = chude_tab_.replace('__LINKCHUDE__', '../../../../../../../%s/'%(cdcr.link_url))
                else:
                    chude_tab = chude_tab_.replace('__LINKCHUDE__', '#')
                chude_tab = chude_tab.replace('__ANHCHUDE__', photo)
                chude_tab = chude_tab.replace('__TENCHUDE__', cdcr.name)
                chude_tab = chude_tab.replace('__MOTANGAN__', self.gioihanchu(str(cdcr.description), 35) or '(Chưa cập nhật)')
                all_chude_tab += chude_tab
                
            template = template.replace('__CHUDECON__', all_chude_tab)


#Lay chu de/du an thuoc chu de cha
            if chude.parent_id:
                template = template.replace('__CHUDE__', chude.parent_id.name)
                chudecon_cuacha_da = self.pool.get('yhoc_duan').search(cr, uid, [('chude_id','=',chude.parent_id.id),('link','!=',False)])
                chudecon_cuacha_cd = self.pool.get('yhoc_chude').search(cr, uid, [('parent_id','=',chude.parent_id.id),('link','!=',False)])
                chudecon_cuacha = chudecon_cuacha_da + chudecon_cuacha_cd
                all_cungchude = '' 
                cungchude_tab_ = '''<li><a href="__LINKBAIVIET__">__TENBAIVIET__</a></li>'''
                if chudecon_cuacha:
                    for cd in chudecon_cuacha_cd:
                        cdr = self.browse(cr, uid, cd, context=context)
                        cungchude_tab = cungchude_tab_.replace('__LINKBAIVIET__', '../../../../../../%s/'%(cdr.link_url))
                        cungchude_tab = cungchude_tab.replace('__TENBAIVIET__', cdr.name)
                        all_cungchude += cungchude_tab
                    for cd in chudecon_cuacha_da:
                        cdr = self.pool.get('yhoc_duan').browse(cr, uid, cd, context=context)
                        cungchude_tab = cungchude_tab_.replace('__LINKBAIVIET__', '../../../../../../%s/'%(cdr.link_url))
                        cungchude_tab = cungchude_tab.replace('__TENBAIVIET__', cdr.name)
                        all_cungchude += cungchude_tab
                        
                    template = template.replace('__BAIVIET_CUNGCHUDE__', all_cungchude)
            
#Lấy thông tin cùng chủ đề:
#            cungchude = self.pool.get('hlv_thongtin').search(cr, uid, [('public','=',True),('duan.chude_id.id', '=',chude.id)], limit=10, order='create_date desc', context=context)
#            cungchude_tab_ = '''<li><a href="__LINKBAIVIET__">__TENBAIVIET__</a></li>'''
#            all_cungchude = '' 
#            for ccd in cungchude:
#                ccdr = self.pool.get('hlv_thongtin').browse(cr, uid, ccd, context=context)
#                try:
#                    self.pool.get('hlv_thongtin').capnhat_thongtin(cr, uid, [ccd], context=context)
#                except:
#                    pass
#                cungchude_tab = cungchude_tab_.replace('__LINKBAIVIET__', ccdr.link)
#                cungchude_tab = cungchude_tab.replace('__TENBAIVIET__', ccdr.name)
#                all_cungchude += cungchude_tab
#            
#            template = template.replace('__BAIVIET_CUNGCHUDE__', all_cungchude)
            
            
            temp_ = '''<a href="__LINK__">__NAME__</a>'''
            linktree = []
            res = ''
#            temp = temp_.replace('__LINK__', chude.link or '#')
#            temp = temp.replace('__NAME__', chude.name)
#            linktree.append(temp)
            
            treechude = []
            treechude = self.dequy(treechude, chude)
            treechude.insert(0,chude)
            
            for i in range(len(treechude)):
                temp = temp_.replace('__LINK__', '../../../../../../%s/'%(treechude[len(treechude)-i-1].link_url))
                temp = temp.replace('__NAME__', treechude[len(treechude)-i-1].name)
                linktree.append(temp)
#            if chude.parent_id:
#                temp = temp_.replace('__LINK__', chude.parent_id.link or '#')
#                temp = temp.replace('__NAME__', chude.parent_id.name)
#                linktree.insert(0,temp)
                
                
            linktree.insert(0,'''<a href="../../../../../../trangchu/vi/'''  + '''">Trang chủ</a>''')
            res = " > ".join(linktree)
            super(yhoc_chude,self).write(cr,uid,[chude.id],{'link_tree':res,
                                                            'link': domain + '/%s/'%(link_url),
                                                            'link_url':link_url}, context=context)
            template = template.replace('__LINKTREE__', res)
            template = template.replace('__TUADECHUDE__', chude.name)
            template = template.replace('__MOTA__', str(chude.description) or '')
            template = template.replace('__HINHCHUDE__', domain + '/images/%s-chude-%s.jpg' %(str(chude.id),name_url))
            
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
        
yhoc_chude()

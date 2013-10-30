# -*- coding: utf-8 -*-
##############################################################################

from osv import osv,fields
from datetime import datetime
import base64,os


class hlv_vaitro(osv.osv):
    _name = 'hlv_vaitro'

    _columns = {
        'name':fields.char("Vai trò",size=500, required="1"),
        'nhanvien': fields.many2one('hr.employee','Nhân viên', required="1"),
        'sequence': fields.integer('Thứ tự'),
        'duan_id': fields.many2one('yhoc_duan','Dự án'),
    }
    _defaults = {
        'sequence': 0,
    }
hlv_vaitro()

class hlv_nhom(osv.osv):
    _name = 'hlv_nhom'

    _columns = {
        'name':fields.char("Name",size=500, required="1"),
        'member': fields.many2many('hlv_vaitro','nhom_member_ref','nhom_id','member_id','Thành viên nhóm', required="1"),
    }    
    
    def create(self, cr, uid, vals, context=None):
        nhanvien_nhom_ids = []
        if 'member' in vals:
            for mem in  vals['member']:
                nhanvien_nhom_ids.append(mem[2]['nhanvien'])
            for mem in  vals['member']:
                if nhanvien_nhom_ids.count(mem[2]['nhanvien']) > 1:
                    tennv = self.pool.get('hr.employee').read(cr,uid, mem[2]['nhanvien'], ['name'], context=context)
                    raise osv.except_osv('Warning !', "Nhân viên %s đã tồn tại trong nhóm"%tennv['name'])
        res = super(hlv_nhom, self).create(cr, uid, vals, context=context)
        return res
    
    def write(self, cr, uid, ids, vals, context=None):
        '''
        {'member': [[4, 25, False], [4, 26, False], [4, 28, False], [2, 29, False]]}
        so dau tien: - 0: create
                     - 1: update
                     - 2: delete
                     - 4: normal
        '''
        for id in ids:
            nhanvien_nhom_ids = []
            nhom = self.browse(cr, uid, id, context=context)
            for mem in nhom.member:
                nhanvien_nhom_ids.append(mem.nhanvien.id)
            if 'member' in vals:
                for mem in  vals['member']:
                    if mem[0] == 0:
                        if mem[2]['nhanvien'] in nhanvien_nhom_ids:
                            tennv = self.pool.get('hr.employee').read(cr,uid, mem[2]['nhanvien'], ['name'], context=context)          
                            raise osv.except_osv('Warning !', "Nhân viên %s đã tồn tại trong nhóm"%tennv['name'])
        return super(hlv_nhom, self).write(cr, uid, ids, vals, context=context)
hlv_nhom()


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:


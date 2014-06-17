#!/usr/bin/env python
import sys,re
from collections import Counter
from random import shuffle
dict_h = {}
link_h = {}
couple_h = {}
inst_a = []
if_name = ''
md_name = ''

def calc(list1,list2):
    add=[]
    for i in list1:
        if i in dict_h.keys():
            add = dict_h[i]
    list1 = list1 + add
    c = Counter(list1) - Counter(list2)
    return len(list1) - len(list(c.elements()))

def parse_dic():
    f = open(sys.argv[1],'r')
    for line in f.readlines():
        line_a = line.split()
        for dic_wd in line_a:
            dict_h[dic_wd] = line_a
    f.close()

def parse_list():
    global md_name
    f = open(sys.argv[2],'r')
    re_if_name = re.compile('^\s*interface\s+(\w+)')
    re_md_name = re.compile('^\s*module\s+(\w+)')
    re_if_sig = re.compile('^\s*(wire|logic)\s*(\[.*\])?\s*(\w+)')
    re_dut_sig = re.compile('^\s*[^\/\/\*]*?(input|output|inout)\s+(wire|reg)?\s*(\[.*\])?\s*(\w+)')
    unknown_pool = []
    l_mem = f.readlines()
    for l_index,l_line in enumerate(l_mem):
        l_a = l_line.split()
        f_f = open(l_a.pop(0),'r')
        for f_line in f_f.readlines():
            if l_index != len(l_mem) - 1:
                if re_if_name.match(f_line):
                    if_name = re_if_name.match(f_line).group(1)
                    link_h[if_name] = {}
                    if not l_a:
                        raise NameError("can't find %s 's couple"%if_name)
                    for re_wd in l_a:
                        link_h[if_name][re_wd] = {}
                        link_h[if_name][re_wd]['if_info_a'] = []
                        link_h[if_name][re_wd]['dut_info_a'] = []
                elif re_if_sig.match(f_line) and link_h.has_key(if_name):
                    for re_wd in link_h[if_name].keys():
                        link_h[if_name][re_wd]['if_info_a'].append(re_if_sig.match(f_line).groups())
            else:
                if re_md_name.match(f_line):
                    md_name = re_md_name.match(f_line).group(1)
                elif re_dut_sig.match(f_line):
                    dut_info = re_dut_sig.match(f_line).groups()
                    match = 0
                    for if_n in link_h.keys():
                        for re_wd in link_h[if_n].keys():
                            if re.search(re_wd,dut_info[3]):
                                link_h[if_n][re_wd]['dut_info_a'].append(dut_info)
                                match = 1
                                break
                        if match:
                            break
                    inst_a.append(dut_info + (match,))
        f_f.close()
    f.close()

def inst_link():
    out_a0 = []
    out_a1 = []
    out_a2 = []
    sp = '*'*70
    out_a0.append('//%s\n//define reg and wire of module %s\n//%s\n'%(sp,md_name,sp))
    for dut_info in inst_a:
        wid = dut_info[2] if dut_info[2] else ''
        tbd = '' if dut_info[4] else '//TBD'
        out_a0.append('%-5s %-40s %-30s;%s\n'%(dut_info[1],wid,dut_info[3],tbd))
    out_a0.append('//%s\n//gen inst for module %s\n//parameter TBD\n//%s\n%s U_%s(\n'%(sp,md_name,sp,md_name,md_name.upper()))
    for index,dut_info in enumerate(inst_a):
        out_a0.append('\t.%-30s (%-30s)%s\n'%(dut_info[3],dut_info[3],'' if index == len(inst_a) - 1 else ','))
    out_a0.append(');\n//%s\n//gen link\n//%s\n'%(sp,sp))
    for if_n in couple_h.keys():
        for index,re_wd in enumerate(couple_h[if_n].keys()):
            tmp_input = []
            tmp_output = []
            tmp_unknown = []
            bus_index = str(index) if len(couple_h[if_n].keys()) > 1 else ''
            inst_bus_n = '_'.join(if_n.split('_')[0:-1]) + '_bus' + bus_index
            out_a1.append('%-20s %-20s;\n'%(if_n,inst_bus_n + '(/*TBD*/)'))
            out_a2.append('\n//for %s\n'%inst_bus_n)
            for if_info in couple_h[if_n][re_wd].keys():
                if_side = '%s.%s'%(inst_bus_n,if_info[2])
                for dut_info in couple_h[if_n][re_wd][if_info]:
                    dut_side = '`%s.%s'%(md_name.upper() + '_TOP_PATH',dut_info[3])
                    if len(couple_h[if_n][re_wd][if_info]) == 1:
                        if dut_info[0] == 'input':
                            tmp_input.append('assign %-50s = %-50s;\n'%(dut_side,if_side))
                        else:
                            tmp_output.append('assign %-50s = %-50s;\n'%(if_side,dut_side))
                    else:
                        if dut_info[0] == 'input':
                            tmp_unknown.append('//assign %-50s = %-50s;\n'%(dut_side,if_side))
                        else:
                            tmp_unknown.append('//assign %-50s = %-50s;\n'%(if_side,dut_side))  
            out_a2.extend(tmp_input + tmp_output + tmp_unknown)
    f = open('gen_inst_link.v','w')
    f.writelines(out_a0 + out_a1 + out_a2)
    f.close()
            
def get_couple():
    for if_n in link_h.keys():
        for re_wd in link_h[if_n].keys():
            mts = len(link_h[if_n][re_wd]['if_info_a'])
            for times in range(mts):
                if not len(link_h[if_n][re_wd]['if_info_a']):
                    break
                shuffle(link_h[if_n][re_wd]['if_info_a'])    
                for if_info in link_h[if_n][re_wd]['if_info_a']:
                    a1 = if_info[2].split('_')
                    similar = {}
                    for dut_info in link_h[if_n][re_wd]['dut_info_a']:
                        a2 = dut_info[3].split('_')
                        sim = calc(a1,a2)
                        if not similar.has_key(sim):
                            similar[sim] = []
                        similar[sim].append((if_n,re_wd,if_info,dut_info))
                    if not similar.keys():
                        break
                    sel = similar[max(similar.keys())]
                    if len(sel) == 1 or times == mts - 1:
                        if not couple_h.has_key(sel[0][0]):
                            couple_h[sel[0][0]] = {}
                        if not couple_h[sel[0][0]].has_key(sel[0][1]):
                            couple_h[sel[0][0]][sel[0][1]] = {}
                        if not couple_h[sel[0][0]][sel[0][1]].has_key(sel[0][2]):
                            couple_h[sel[0][0]][sel[0][1]][sel[0][2]] = []
                        for dut_info in sel:
                            couple_h[sel[0][0]][sel[0][1]][sel[0][2]].append(dut_info[3])
                        if len(sel) == 1:
                            link_h[if_n][re_wd]['if_info_a'].remove(sel[0][2])
                            link_h[if_n][re_wd]['dut_info_a'].remove(sel[0][3])

if len(sys.argv) != 3:
    raise NameError('argu numbers err')
else:
    parse_dic()
    parse_list()
    get_couple()
    inst_link()
 

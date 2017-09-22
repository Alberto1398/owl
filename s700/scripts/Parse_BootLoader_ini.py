#!/usr/bin/python
# -*- coding: utf-8 -*-
"""本python脚本文件用于Modify工具解析bootloader.ini，打包bootloader.ini到bootloader.bin中，
固件内要放置bootloader.ini用于Modify，此脚本也要放进固件中，初始版本工具组编写，后期由方案端维护
"""
import ConfigParser
import string, os, sys
from ctypes import *
import zlib

OWL_BOOTPARAM_MAGIC = 0x49464121
OWL_BOOTPARAM_VERSION_1_2 = 0x00010002

class owl_serial_config(Structure):
	_pack_ = 1
	_fields_ = [('uart_id', c_uint16),
                    ('uart_pad', c_uint16),
                    ('uart_baudrate', c_uint32)]
	
class owl_jtag_config(Structure):
        _pack_ = 1
        _fields_ = [('enable', c_uint16),
                    ('pad', c_uint16),
                    ('reserved', c_uint32)]
        
class owl_pmu_config(Structure):
        _pack_ = 1
        _fields_ = [('bus_id', c_uint16),
                    ('bus_mfp', c_uint16),
                    ('pmu_id', c_uint16),
                    ('vddr_pmu_dcdc_cfg', c_uint16),
                    ('reserved', c_uint32 * 2)]
        
class owl_ddr_chan_config(Structure):
        _pack_ = 1
        _fields_ = [('gate_coarse', c_uint8 * 4),
                    ('gate_fine', c_uint8 * 4),
                    ('clk_wrdqs', c_uint8 * 4),
                    ('clk_wr', c_uint8 * 4),
                    ('clk_rddqs', c_uint8 * 4)]

class owl_emmc_config(Structure):
        _pack_ = 1
        _fields_ = [('sd_clk', c_uint32)]
		
class  owl_ddr_config(Structure):
	_pack_ = 1
	_fields_ = [('ddr_clk', c_uint16),
		    ('ddr_cap', c_uint16),
		    ('ddr_bits_width', c_uint8),
		    ('rank', c_uint8),
		    ('ddr_type', c_uint8),
		    ('row_col', c_uint8),
		    ('rdodt', c_uint8),
		    ('wrodt', c_uint8),
		    ('zpzq', c_uint8),
		    ('row_col_detect', c_uint8)]
    
class chipid_data(Structure):
        _fields_ = [('dvfs',c_uint32),
                    ('gpu_sensor',c_uint16),
                    ('cpu_sensor',c_uint16),
                    ('usb_para', c_uint16),
                    ('resever', c_uint16)]
        
class owl_boot_param(Structure):
        _pack_ = 1
        _fields_ = [('magic', c_uint32),
                    ('version', c_uint32),
                    ('serial_config', owl_serial_config),
                    ('jtag_config', owl_jtag_config),
                    ('pmu_config', owl_pmu_config),
                    ('ddr_config', owl_ddr_config),
                    ('emmc_config', owl_emmc_config),
                    ('chipid', chipid_data),
                    ('checksum', c_uint32),
                    ('firstboot', c_uint32)
                    ]

PACK_MAGIC = (0x4b434150)
class boot_partition(Structure):
        _fields_ = [('name', c_char * 16),
                    ('size', c_uint),
                    ('offset', c_uint),
                    ('load_addr', c_uint),
                    ('Reserve', c_ubyte * 36),
                    ]
        
class pack_header(Structure):
        _fields_ = [('magic', c_uint),
                    ('Reserve0', c_ubyte * 56),
                    ('numPart', c_uint),
                    ('partition', boot_partition * 10),
                    ('Reserve1', c_ubyte * 64 * 5),
                    ]
owl_boot_header = pack_header()

def Init_Boot_header():
        owl_boot_header.magic = PACK_MAGIC
        owl_boot_header.numPart = 0
    
        
class owl_ini_item():
        def __init__(self, type, name, addr):
                self.type = type
                self.name = name
                self.addr = addr

ALIGN_NUM = 1024
def ALIGN(x, a):
        return ((x)+(a)-1)&~((a)-1)
RESERVE  = 1024
BUF_LEN  = 0x2000
class pack_arry():
        def __init__(self, name, loadaddr):
                self.name = name
                self.loadaddr = loadaddr

#first mbrec in storage
STORAGE_FIRST_MBRC_OFFSET = (0x0)
STORAGE_FIRST_MBRC_SIZE = (0x800)

#second mbrec in storage 
STORAGE_SECOND_MBRC_OFFSET = (0xc00)
STORAGE_SECOND_MBRC_SIZE = (0xf000)

#boot pack header in storage 
STORAGE_PACK_HEADER_OFFSET = (0xc00)
STORAGE_PACK_HEADER_SIZE = (0x400)

#default boot parameter in storage 
STORAGE_DEFAULT_BOOT_PARAM_OFFSET = (0x1000)
STORAGE_DEFAULT_BOOT_PARAM_SIZE = (0x800)

#second mbrc code in storage 
STORAGE_SECOND_MBRC_CODE_OFFSET = (0x1800)

#mbrec in mmc 
MMC_BOOT_START_OFFSET = (0x200200)	 #4097 sector 
MMC_BOOT_BACKUP_GAP = (0x100000)
MMC_BOOT_BACKUP_COUNT = (2)

MMC_BOOT_PARAM_RELA_OFFSET = (0x7d000)	 #512K 
MMC_BOOT_PARAM_SIZE = (0x800)

#mbrec in nand 
NAND_BOOT_BACKUP_COUNT = (4)
NAND_BOOT_SLC_TABLE_OFFSET = (0x800)
NAND_BOOT_SLC_TABLE_SIZE = (0x400)

#mbrec in spi nor 
SPI_BOOT_BACKUP_COUNT = (1)


#---------- bootloader in RAM information ---------- 
#shareram information 
SRAM_BASE = (0xe4060000)
SRAM_SIZE = (0x12000)

#mbrec in sharam 
MBRC_START_ADDR = (SRAM_BASE)
MBRC_MAX_SIZE = (STORAGE_SECOND_MBRC_OFFSET + STORAGE_SECOND_MBRC_SIZE)

#first mbrec in share ram address 
FIRST_MBRC_LOAD_ADDR = (SRAM_BASE)		 #0xe4060000 
FIRST_MBRC_ENTRY_ADDR = (FIRST_MBRC_LOAD_ADDR + 0x200)		 #0xe4068200 

#second mbrec in share ram address 
SECOND_MBRC_LOAD_ADDR = (SRAM_BASE + STORAGE_SECOND_MBRC_OFFSET)	 #0xe4068c00 
SECOND_MBRC_ENTRY_ADDR = (SRAM_BASE + 0x1800)	 #0xe4061800 

#boot app in ddr address 
BOOT_APP_LOAD_ADDR = (0x1000)
BOOT_APP_ENTRY_ADDR = (BOOT_APP_LOAD_ADDR)

#boot pack header in shareram address
PACK_HEADER_LOAD_ADDR = (SRAM_BASE + STORAGE_PACK_HEADER_OFFSET)
BOOT_PARAM_LOAD_ADDR = (SRAM_BASE + STORAGE_DEFAULT_BOOT_PARAM_OFFSET)

#nand slc table load address 
NAND_BOOT_SLC_TABLE_LOAD_ADDR = (0xe406fc00)

#arm-trusted-firmware in secure ddr address
SECURE_BL31_LOAD_ADDR = 0x1f000000
SECURE_BL32_LOAD_ADDR = 0x1f202000


#---------- adfudec in RAM information ---------- 
#adfudec in share ram address 
ADFUDEC_LOAD_ADDR = (0xe4065000)
ADFUDEC_MAX_SIZE = (0xd000)

#boot parameter for adfudec in share ram address 
ADFU_BOOTPARAM_LOAD_ADDR = (0xe4064000)

MBRC_NAME = "bootloader.bin"
BOOT_PARAM_NAME = "bootloader.ini"
SECURE_BL31_NAME = "bl31.bin"
SECURE_BL32_NAME = "bl32.bin"
BOOT_APP_NAME = "app.bin"

arry = [ pack_arry(MBRC_NAME, SECURE_BL32_LOAD_ADDR),
	 pack_arry(SECURE_BL31_NAME, SECURE_BL31_LOAD_ADDR),
	 pack_arry(SECURE_BL32_NAME, SECURE_BL32_LOAD_ADDR),
	 pack_arry(BOOT_APP_NAME, BOOT_APP_LOAD_ADDR),
	 pack_arry(BOOT_PARAM_NAME,  BOOT_PARAM_LOAD_ADDR),
	 pack_arry("end", 0),
        ]

    
boot_param = owl_boot_param()
INT = 0
CHAR = 1
STRING = 3
SHORT = 2
S700_ini_item = [owl_ini_item(SHORT, "jtag@jtag_enable", boot_param.jtag_config.enable),
                 owl_ini_item(SHORT, "jtag@pad", boot_param.jtag_config.pad),
                 owl_ini_item(SHORT, "pmu@bus_id", boot_param.pmu_config.bus_id),
                 owl_ini_item(SHORT, "pmu@bus_mfp", boot_param.pmu_config.bus_mfp),
                 owl_ini_item(SHORT, "pmu@pmu_id", boot_param.pmu_config.pmu_id),
                 owl_ini_item(SHORT, "pmu@vddr_pmu_dcdc_cfg", boot_param.pmu_config.vddr_pmu_dcdc_cfg),
                 owl_ini_item(SHORT, "serial@uart_id", boot_param.serial_config.uart_id),
                 owl_ini_item(SHORT, "serial@uart_pad", boot_param.serial_config.uart_pad),
                 owl_ini_item(INT, "serial@uart_baudrate", boot_param.serial_config.uart_baudrate),
                 owl_ini_item(SHORT, "ddr@ddr_clk", boot_param.ddr_config.ddr_clk),
                 owl_ini_item(SHORT, "ddr@ddr_cap" , boot_param.ddr_config.ddr_cap),
                 owl_ini_item(CHAR, "ddr@ddr_bits_width", boot_param.ddr_config.ddr_bits_width),
                 owl_ini_item(CHAR, "ddr@ddr_type", boot_param.ddr_config.ddr_type),
                 owl_ini_item(CHAR, "ddr@rank", boot_param.ddr_config.rank),
                 owl_ini_item(CHAR, "ddr@row_col", boot_param.ddr_config.row_col),
                 owl_ini_item(CHAR, "ddr@wrodt", boot_param.ddr_config.wrodt),
                 owl_ini_item(CHAR, "ddr@rdodt", boot_param.ddr_config.rdodt),
                 owl_ini_item(CHAR, "ddr@zpzq", boot_param.ddr_config.zpzq),
                 owl_ini_item(INT, "emmc@sd_clk", boot_param.emmc_config.sd_clk),
                 owl_ini_item(CHAR, "end", "end"),
                 ]

def Init_boot_param():
        boot_param.magic = OWL_BOOTPARAM_MAGIC
        boot_param.version = OWL_BOOTPARAM_VERSION_1_2
        boot_param.serial_config = owl_serial_config(5,0,115200)
        boot_param.jtag_config = owl_jtag_config(0,2)
        boot_param.pmu_config = owl_pmu_config(3,0,0)
        boot_param.emmc_config = owl_emmc_config(24)
        boot_param.firstboot = 1

   
def GetSection(name):
        pos = name.find("@")
        return name[0:pos]

def GetOption(name):
        pos = name.find("@")
        return name[pos+1:]

def debug():
        for item in S700_ini_item:
            print item.name, item.addr

def ParseValue(value):
        """将python字符串转为数字"""
        if type(value) == int or type(value) == long:
                return value
        if value.startswith("0x") or value.startswith("0X"):
                return int(value,16)
        elif value.startswith("0"):
                return int(value,8)
        elif value.startswith("0b") or value.startswith("0B"):
                return int(value,2)
        else:
                return int(value,10)
        

def SetBoot_param_value():
        """获取bootloader.ini中的值，赋值到数据结构"""
        for item in S700_ini_item:
                if item.name == "jtag@jtag_enable":
                        boot_param.jtag_config.enable = c_uint16(ParseValue(item.addr))
                if item.name == "jtag@pad":
                        boot_param.jtag_config.pad = c_uint16(ParseValue(item.addr))
                if item.name == "pmu@bus_id":
                        boot_param.pmu_config.bus_id = c_uint16(ParseValue(item.addr))
                if item.name == "pmu@bus_mfp":
                        boot_param.pmu_config.bus_mfp = c_uint16(ParseValue(item.addr))
                if item.name == "pmu@pmu_id":
                        boot_param.pmu_config.pmu_id = c_uint16(ParseValue(item.addr))
                if item.name == "pmu@vddr_pmu_dcdc_cfg":
                        boot_param.pmu_config.vddr_pmu_dcdc_cfg = c_uint16(ParseValue(item.addr))
                if item.name == "serial@uart_id":
                        boot_param.serial_config.uart_id = c_uint16(ParseValue(item.addr))
                if item.name == "serial@uart_pad":
                        boot_param.serial_config.uart_pad = c_uint16(ParseValue(item.addr))
                if item.name == "serial@uart_baudrate":
                        boot_param.serial_config.uart_baudrate = c_uint32(ParseValue(item.addr))
                if item.name == "ddr@ddr_clk":
                        boot_param.ddr_config.ddr_clk = c_uint16(ParseValue(item.addr))
                if item.name == "ddr@ddr_cap":
                        boot_param.ddr_config.ddr_cap = c_uint16(ParseValue(item.addr))
                if item.name == "ddr@ddr_bits_width":
                        boot_param.ddr_config.ddr_bits_width = c_uint8(ParseValue(item.addr))
                if item.name == "ddr@ddr_type":
                        boot_param.ddr_config.ddr_type = c_uint8(ParseValue(item.addr))
                if item.name == "ddr@rank":
                        boot_param.ddr_config.rank = c_uint8(ParseValue(item.addr))
                if item.name == "ddr@row_col":
                        boot_param.ddr_config.row_col = c_uint8(ParseValue(item.addr))
                if item.name == "ddr@wrodt":
                        boot_param.ddr_config.wrodt = c_uint8(ParseValue(item.addr))
                if item.name == "ddr@rdodt":
                        boot_param.ddr_config.rdodt = c_uint8(ParseValue(item.addr))
                if item.name == "ddr@zpzq":
                        boot_param.ddr_config.zpzq = c_uint8(ParseValue(item.addr))
                if item.name == "emmc@sd_clk":
                        boot_param.emmc_config.sd_clk = c_uint32(ParseValue(item.addr))

libc = cdll.msvcrt
fopen = libc.fopen
fwrite = libc.fwrite
fclose = libc.fclose
fseek = libc.fseek
fread = libc.fread
ftell = libc.ftell
memset = libc.memset
memcpy = libc.memcpy
SEEK_SET = 0
SEEK_CUR = 1
SEEK_END = 2

def sparse_ini(file):
    """解析bootloader.ini，并转成二进制"""
    cf = ConfigParser.ConfigParser()
    data = c_char('\0')
    cf.read(file)
    for item in S700_ini_item:
        if cf.has_option(GetSection(item.name), GetOption(item.name)):
                item.addr = cf.get(GetSection(item.name), GetOption(item.name))
    SetBoot_param_value()
    debug()
    if boot_param.serial_config.uart_id < 0 or boot_param.serial_config.uart_id > 5:
            print "your serial config error, 0 < serial_id <5\n"
            return 0
    filebin = file
    fp = fopen(filebin, "wb+")
    ret = fwrite(addressof(boot_param), 1, sizeof(owl_boot_param), fp)
    print "ret == ", ret
    fseek(fp, 1023, SEEK_SET)
    fwrite(addressof(data), 1, 1, fp)
    fclose(fp)
    return filebin

def create_arry(num, argv, pos, arry):
        i = 0
        ptr = 0
        packs = []
        temp_ptr = ""
        while i < num:
                ptr = 0
                while arry[ptr].name != "end":
                        temp_ptr = argv[i+pos][argv[i+pos].rfind("\\")+1:]
                        print "arry->name = ", arry[ptr].name, "temp_ptr = ", temp_ptr
                        if arry[ptr].name != temp_ptr:
                                ptr += 1
                                continue
                        packs.append(pack_arry(argv[i+pos], arry[ptr].loadaddr))
                        break
                if arry[ptr].name == "end":
                        print "doesn't find the bin name: ", argv[i+pos], "in database name"
                        packs.append(pack_arry(argv[i+pos], 0))
                i += 1
        packs.append(pack_arry("end", 0))
        return packs

def copydata_write(out_file, fd_out):
        """将原有文件内容读出，重新写入以便修改"""
        fd_in = fopen(out_file,"rb")
        fseek(fd_in, 0,SEEK_END)
        len = ftell(fd_in)
        data = c_buffer('\0',len)
        fread(data,len,1,fd_in)
        fseek(fd_in, 0,SEEK_SET)
        fread(data,len,1,fd_in)
        fseek(fd_in, 0,SEEK_SET)
        fclose(fd_in)
        fd_out = fopen(out_file,"wb+")
        fwrite(data, len, 1, fd_out)
        return fd_out

def get_header(fd_out, boot_header):
        buf = c_buffer('\0',BUF_LEN)
        ret = 0
        fseek(fd_out,STORAGE_SECOND_MBRC_OFFSET,SEEK_SET)
        ret = fread(buf,1,BUF_LEN,fd_out)
        if ret != BUF_LEN:
                print "ret = ", ret
                print "read error"
                return -1
        header = cast(buf,POINTER(pack_header))
        if header.contents.magic == PACK_MAGIC:
                memmove(addressof(boot_header), addressof(header.contents), sizeof(header.contents))
        else:
                boot_header.magic = PACK_MAGIC
                boot_header.numPart = 0
        return 0

def owl_update_header(header, size, offset, name, loadaddr):
        order = header.numPart
        print "name = %s, offset = %x\n" %(name,offset*512)
        header.numPart += 1
        header.partition[order].name = name
        header.partition[order].size = size
        header.partition[order].load_addr = loadaddr
        print "name = %s, address = 0x%x\n" %(name, loadaddr)
        return 1

def owl_update_header_byname(header, size, offset, name, loadaddr):
        """这里只更新header，不新增"""
        order = header.numPart
        i = 0
        while i < order:
                if header.partition[i].name == name:
                        order = i
                        break
                i += 1
        print "name = %s, offset = %x\n" %(name,offset*512)
        header.partition[order].name = name
        header.partition[order].size = size
        header.partition[order].load_addr = loadaddr
        print "name = %s, address = 0x%x\n" %(name, loadaddr)
        return 1

def owl_getoffset_byname(header, name):
        num = order = -1
        num = header.numPart
        temp_name = name[name.rfind("\\")+1:]
        print temp_name, num
        i = 0
        while i < num:
                if header.partition[i].name == temp_name:
                        order = i
                        break
                i += 1
        if order == -1:
                return -1
        else:
                return header.partition[order].offset*512
                
        
def copy_file(name, fd_out, seek):
        file_len = len = 0
        buf = c_buffer('\0', BUF_LEN)
        fd_in = fopen(name,"rb")
        if fd_in == -1:
                print "open ", name , "error"
                print "fail reason"
                return -1
        if (seek != 0):
                fseek(fd_out, seek, SEEK_SET)
        while(True):
                memset(addressof(buf),'\0',BUF_LEN)
                len = fread(buf,1,BUF_LEN,fd_in)
                file_len += len
                fwrite(buf, 1, len, fd_out)
                if len < BUF_LEN:
                        break
        fclose(fd_in)
        return file_len
        
def pack_bins(arry, out_file):
        """打包，不新增打包文件，只是对原有bootloader.bin内的文件进行更新"""
        i = j = 0
        fd_out = -1
        file_len = 0
        pos = bin_start = 0
        data = c_char('\0')
        temp_name = ""
        
        print "open ", out_file, "file"
        fd_out = copydata_write(out_file,fd_out)
        get_header(fd_out,owl_boot_header)
        fseek(fd_out, 0, SEEK_SET)
        pos = os.path.getsize(out_file)
        pos = ALIGN(pos, ALIGN_NUM)
        fseek(fd_out, pos, SEEK_SET)

        for item in arry:
                if item.name == "end":
                        break
                bin_start = owl_getoffset_byname(owl_boot_header,item.name)
                pos = bin_start
                if bin_start == -1:
                        print "continue"
                        continue
                fseek(fd_out, bin_start, SEEK_SET)
                file_len = copy_file(item.name, fd_out, 0)

                file_len = ALIGN(file_len+16, ALIGN_NUM)
                temp_name = item.name[item.name.rfind("\\")+1:]
                print "name=%s: size= 0x%x, %dkb, offset = 0x%x\n" %(temp_name,file_len,file_len/1024,bin_start)
                pos += file_len + RESERVE
                owl_update_header_byname(owl_boot_header, file_len/512, bin_start/512, temp_name, item.loadaddr)
        fseek(fd_out, STORAGE_SECOND_MBRC_OFFSET, SEEK_SET)
        print "num part = %d\n" %(owl_boot_header.numPart)
        fwrite(addressof(owl_boot_header), 1, sizeof(pack_header), fd_out)
        fseek(fd_out, pos-1, SEEK_SET)
        fwrite(addressof(data), 1, 1, fd_out)
        file_len = 0
        fclose(fd_out)

def dwchecksum(buf, offset, start, length):
        """这里求和与c++代码求和功能是一致的"""
        sum = 0
        temp_start = start / sizeof(c_uint)
        temp_length = length / sizeof(c_uint)
        i = temp_start
        value = c_uint(0)
        while i < length:
                memmove(addressof(value),addressof(buf)+i+offset,sizeof(value))
                sum += value.value
                i += sizeof(c_uint)
        print "dwchecksum is %x\n" %(sum)
        return sum

def get_offset_size(buf, name, offset, size):
        header = POINTER(pack_header)
        i = 0
        ret = -1
        header = cast(addressof(buf)+STORAGE_PACK_HEADER_OFFSET, POINTER(pack_header))
        while i < header.contents.numPart:
                if name == header.contents.partition[i].name:
                        memmove(addressof(offset), byref(c_uint(header.contents.partition[i].offset)),sizeof(c_uint))
                        memmove(addressof(size), byref(c_uint(header.contents.partition[i].size)),sizeof(c_uint))
                        ret = 0
                        print "found %s, size = 0x%x, offset = 0x%x\n" %(name,size.value,offset.value)
                i += 1
        return ret

def add_checksum_by_name(buf, name):
        offset = c_uint(0)
        size = c_uint(0)
        checksum = 0
        ret = 0

        ret = get_offset_size(buf,name,offset,size)
        if ret != 0:
                return -1
        offset = offset.value
        size = size.value
        print "%s= 0x%x\n" %(name, (offset+size)*512)
        memmove(byref(buf,(offset+size)*512-8),byref(c_uint(0x42746341)),sizeof(c_uint))
        checksum = dwchecksum(buf, offset*512, 0, size*512-4)
        checksum += 0x1234
        memmove(byref(buf,(offset+size)*512-4),byref(c_uint(checksum)),sizeof(c_uint))

        return 0
        
def add_checksum(buf, length):
        first_mbrc_size = 0x800
        second_load_size = 0
        offset = size = 0
        mbrc_sum_2k = mbrc_sum_sec = mbrc_sum_app = 0
        ret = 0
        print "add checksum for mbrc"

        memmove(addressof(buf) + STORAGE_FIRST_MBRC_SIZE - 8,byref(c_buffer("ActB")), 4)
        mbrc_sum_2k = dwchecksum(buf,0,0,STORAGE_FIRST_MBRC_SIZE-4)
        mbrc_sum_2k += 0x1234
        memmove(byref(buf,STORAGE_FIRST_MBRC_SIZE-4),byref(c_uint(mbrc_sum_2k)),sizeof(c_uint))
        print "checked first stage mbrc check sum is 0x%x\n" %(mbrc_sum_2k)
                
        memmove(byref(buf,STORAGE_SECOND_MBRC_OFFSET+STORAGE_SECOND_MBRC_SIZE-8),byref(c_uint(0x42746341)),sizeof(c_uint))
        mbrc_sum_sec = dwchecksum(buf,STORAGE_SECOND_MBRC_OFFSET,0,STORAGE_SECOND_MBRC_SIZE-4)
        mbrc_sum_sec += 0x1234
        memmove(byref(buf,STORAGE_SECOND_MBRC_OFFSET+STORAGE_SECOND_MBRC_SIZE-4),byref(c_uint(mbrc_sum_sec)),sizeof(c_uint))
        print "checked second stage mbrc check sum is 0x%x\n"  %(mbrc_sum_sec)

        ret = add_checksum_by_name(buf, SECURE_BL31_NAME)
        if ret:
                return ret
        ret = add_checksum_by_name(buf, SECURE_BL32_NAME)

        if ret:
                return ret
        ret = add_checksum_by_name(buf, BOOT_APP_NAME)
        if ret:
                return ret
        ret = add_checksum_by_name(buf, BOOT_PARAM_NAME)
        if ret:
                return ret
        
        return 0

def mbrec_checksum(file):
        i = ret = file_size = 0

        print "mbrec file: %s\n" %(file)
        file_size = os.path.getsize(file)
        if file_size < 0:
                return -1
        file_buf = c_buffer('\0', file_size)
        fp = fopen(file,"rb")
        fread(file_buf,1,file_size,fp)
        fclose(fp)
        add_checksum(file_buf,file_size)
        fp = fopen(file,"wb+")
        fwrite(file_buf,1,file_size,fp)
        fclose(fp)
        return 0
        
                        
def PackBootloaderIni(argc, bootini, bootbin):
        """Moidfy调用打包接口，请勿更改函数名和参数，保证接口不变"""
        argv = ["pack"]
        argv.append(str(unicode(bootini)))#这里接收c++传的值并转为python字符串
        argv.append(str(unicode(bootbin)))#请勿改传参方式
        Init_boot_param()
        ini_file = argv[1]
        ini_bins = sparse_ini(ini_file)
        if ini_bins == "":
                return -1
        print "ini_bins = %s\n" %(ini_bins)
        pack_num = 1
        pack_file_pos = 1

        packs =  create_arry(pack_num, argv, pack_file_pos, arry)
        out_file = argv[argc-1]
        pack_bins(packs,out_file)

        mbrec_checksum(out_file)
        return 1
"""if __name__ == '__main__':
    argc = 3
    argv  = ["pack",
            "G:\\bootloader.ini",
            "G:\\bootloader.bin"]
    PackBootloaderIni(argc,argv)
"""

"""后面部分为解析uboot.bin，提取uboot.dtb修改保存"""
IH_MAGIC = 0x27051956
IH_NMLEN = 32
def be32_to_cpu(x):
        ret = (((x & 0xff) << 24) |
              ((x & 0xff00) << 8) |
              ((x & 0xff0000) >> 8) |
              ((x & 0xff000000) >> 24))
        return ret

class uboot_image_header(Structure):
	_pack_ = 1
	_fields_ = [('ih_magic', c_uint32),
                    ('ih_hcrc', c_uint32),
                    ('ih_time', c_uint32),
                    ('ih_size', c_uint32),
                    ('ih_load', c_uint32),
                    ('ih_ep', c_uint32),
                    ('ih_dcrc', c_uint32),
                    ('ih_os', c_uint8),
                    ('ih_arch', c_uint8),
                    ('ih_type', c_uint8),
                    ('ih_comp', c_uint8),
                    ('ih_name', c_uint8 * IH_NMLEN)
                    ]

def GetUboot_dtb(uboot_bin_path, uboot_dtb_path):
        uboot_bin_path = str(unicode(uboot_bin_path))
        uboot_dtb_path = str(unicode(uboot_dtb_path))
        binLen = os.path.getsize(uboot_bin_path)
        buf = c_buffer('\0',binLen)
        fd_in = fopen(uboot_bin_path,"rb")
        fread(buf,1,binLen,fd_in)
        fclose(fd_in)
        
        fd_out = fopen(uboot_dtb_path,"wb+")
        size = c_uint32(0)
        magic = c_uint32(0)
        memmove(addressof(size),byref(buf,0x50),sizeof(c_uint32))
        offset = size.value + sizeof(uboot_image_header)
        memmove(addressof(magic),byref(buf,offset),sizeof(c_uint32))
        if magic.value != be32_to_cpu(0xD00DFEED):
                return 0
        fwrite(byref(buf,offset),1, binLen - offset, fd_out)
        fclose(fd_out)
        return 1

def Update_uboot_dtb(uboot_bin_path, uboot_dtb_path):
        uboot_bin_path = str(unicode(uboot_bin_path))
        uboot_dtb_path = str(unicode(uboot_dtb_path))
        binLen = os.path.getsize(uboot_bin_path)
        buf = c_buffer('\0',binLen)
        fd_in = fopen(uboot_bin_path,"rb")
        fread(buf,1,binLen,fd_in)
        fclose(fd_in)
        dtbLen = os.path.getsize(uboot_dtb_path)
        bufDtb = c_buffer('\0',dtbLen)
        fd_in = fopen(uboot_dtb_path,"rb")
        fread(bufDtb,1,dtbLen,fd_in)
        fclose(fd_in)
        
        fd_out = fopen(uboot_bin_path,"wb+")
        size = c_uint32(0)
        memmove(addressof(size),byref(buf,0x50),sizeof(c_uint32))
        offset = size.value + sizeof(uboot_image_header)
        fwrite(buf,1, offset, fd_out)
        fwrite(bufDtb,1,dtbLen,fd_out)

        total = offset + dtbLen
        total_align = ALIGN(total,512)
        align = total_align - total
        data = c_uint8(0)
        while align > 0:
                fwrite(addressof(data),1,1,fd_out)
                align -= 1
                
        header = cast(buf,POINTER(uboot_image_header))
        header.contents.ih_size = c_uint32(be32_to_cpu(total-sizeof(uboot_image_header)))
        fseek(fd_out,0,SEEK_SET)
        fwrite(header,1,sizeof(uboot_image_header),fd_out)
        fclose(fd_out)
        
def Update_image_header(uboot_bin_path):
        uboot_bin_path = str(unicode(uboot_bin_path))
        binLen = os.path.getsize(uboot_bin_path)
        buf = c_buffer('\0',binLen)
        fd_in = fopen(uboot_bin_path,"rb")
        fread(buf,1,binLen,fd_in)
        fclose(fd_in)
        header = cast(buf,POINTER(uboot_image_header))

        buf_sub = c_buffer('\0',be32_to_cpu(header.contents.ih_size))
        memmove(addressof(buf_sub),byref(buf,sizeof(uboot_image_header)),be32_to_cpu(header.contents.ih_size))
        checksum_calc = c_uint32(be32_to_cpu(zlib.crc32(buf_sub)))
        header.contents.ih_dcrc = checksum_calc
   
        if be32_to_cpu(header.contents.ih_magic) != IH_MAGIC:
               return 0
        
        header.contents.ih_hcrc = c_uint32(0)
        checksum_calc = c_uint32(be32_to_cpu(zlib.crc32(header.contents)))
        header.contents.ih_hcrc = checksum_calc
        
        fd_out = fopen(uboot_bin_path,"wb+")
        fwrite(buf,1,binLen,fd_out)
        fseek(fd_out,0,SEEK_SET)
        fwrite(header,1,sizeof(uboot_image_header),fd_out)
        fclose(fd_out)
        return 1
        
        
"""if __name__ == '__main__':
        GetUboot_dtb("G:\\uboot\\uboot.bin", "G:\\uboot\\uboot.dtb")
        Update_uboot_dtb("G:\\uboot\\uboot.bin", "G:\\uboot\\uboot.dtb")
        Update_image_header("G:\\uboot\\uboot.bin")
"""
        



    
    

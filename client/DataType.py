# -*- coding: utf-8 -*-

def datatype(data):
    if len(data)==0:
        return
    return datafunlist[data[0]](data)

def NULL(data):#0
    pass

def array(data):#1
    pass

    
def structure(data):#2
    result = []
    l=data[1]
    data=data[2:]
    
    for i in range(l):
        tmp,data=datatype(data)
        result += [tmp]
    return result,data

def _bool(data):
    data=data[1:]
    return data[0],data[1:]
    
def bit_string(data):
    result = []
    l=data[1]
    data=data[2:]
    l=l//8+1
    return data[:l],data[l:]

def double_long_unsigned(data):
    data=data[1:]
    try:
        return (data[0]<<24)+(data[1]<<16)+(data[2]<<8)+data[3] ,data[4:]
    except:
        return None,None

def octet_string(data):#9
    l=data[1]
    data=data[2:]
    return data[:l],data[l:]

def visible_string(data):#10
    l=data[1]
    data=data[2:]
    string=''
    for i in range(l):
        string+=chr(i)
        data=data[1:]
    return string,data

def long_unsigned(data):#18
    data=data[1:]
    return (data[0]<<8)+data[1],data[2:]

def enum(data):#22
    data=data[1:]
    return data[0],data[1:]
    
    
datafunlist=[NULL,array,structure,_bool,bit_string,5,double_long_unsigned,7,8,octet_string,visible_string,11,12,13,14,15,16,17,long_unsigned,19,20,21,enum]

# -*- coding: utf-8 -*-

import sys
from PyQt4 import QtNetwork
import time
from PyQt4  import  QtCore
from PyQt4 import QtGui
import configparser
import time
from DataType import *
import math

def s2l(data):
    D={'1':1,'2':2,'3':3,'4':4,'5':5,'6':6,'7':7,'8':8,'9':9,'0':0,'a':10,'b':11,'c':12,'d':13,'e':14,'f':15,'A':10,'B':11,'C':12,'D':13,'E':14,'F':15}
    tmp = []
    s = ''
    for i in data:
        if i == ' ':
            pass
        else:
            s += i
            
    if len(s)%2 ==1:
        s += '0'
    while s != '':
        tmp += [(D[s[0]]<<4)+D[s[1]]]
        s = s[2:]
    return tmp

def l2s(data):
    tmp=''
    str=''
    for a in data:
        str = hex(a)
        str =str[2:]
        if len(str)==1:
            str = '0'+str
        tmp += str    
    return tmp

def fcs16(data):
    b=0
    v=0
    P=0x8408
    fcstab=[]
    fcs=0xffff
    for b in range(0,256):
        v=b;
        for i in range(0,8):
            v = (v >> 1) ^ P if v & 1 else v >> 1
        fcstab += [v]

    while data:
        fcs=(fcs >> 8) ^ fcstab[(fcs ^ data[0]) & 0xff]
        data = data[1:]
    fcs ^= 0xffff
    return [fcs&0xff]+[fcs>>8]


def DatabaseQuery(oad):
    global DIC698
    return DIC698[oad]
    
    
class ClientThread(QtCore.QThread):

    def __init__(self,A,parent=None):
        QtCore.QThread.__init__(self,parent)
        global OldVersion
        global NewVersion
        global StationIP
        global StationPort
        global MessageLossRate 
        global PackageLossRate
        global Delay
        self.SerialNum = A
        self.OldVersion=OldVersion
        self.NewVersion=NewVersion
        self.StationIP = StationIP
        self.StationPort = StationPort
        self.MessageLossRate =MessageLossRate
        self.PackageLossRate = PackageLossRate
        self.C= [0x81]
        self.DIR=0x80
        self.PRM=0
        self.FucCode=1
        self.A = [5]+[A&0xff]+[A>>8&0xff]+[A>>16&0xff]+[A>>24&0xff]+[A>>32&0xff]+[A>>40&0xff]
        self.CA = [0]
        self.apdu=[]
        self.tcpSocket = None
        self.senddata = None
        self.sendstream = None
        self.CompleteSign= False
        self.upcount=0
        self.FristUp = True
        self.timer=QtCore.QTimer()
        self.tcpSocket = QtNetwork.QTcpSocket(self)
        self.tcpSocket.readyRead.connect(self.__DataReceive)
        self.tcpSocket.disconnected.connect(self.__Relogins)
        self.r_data=[]
        self.EndSign = False
        self.filename = str(self.SerialNum)
        self.done = False
        self.run()


    def run(self): 
        self.__logins()

    def __logins(self):
        self.C = [0x81]
        self.apdu=[0x01,0x00,0x00,0x00,0xb4,0x07,0xe2,0x08,0x0f,0x03,0x11,0x25,0x1d,0x01,0x82]
        if self.EndSign:
            return
        try:
            self.tcpSocket.connectToHost (self.StationIP ,int(self.StationPort))
            self.tcpSocket.waitForConnected ()
            self.timer.stop()
        except:
            self.exit_()
        
        self.__DataSend()
        self.C= [0x88]

    def __Relogins(self):
        self.timer.timeout.connect(self.__logins)
        self.timer.start( 30000 )
    
    def __destroy(self):
        self.tcpSocket.disconnectFromHost ()
        map[self.SerialNum]=None
        self.quit()
    
    def __DataSend(self):
        self.__FrameCombine()
        print ('Tx:-->', time.strftime("%H:%M:%S", time.localtime()),listI2listH(self.sendstream))
        self.tcpSocket.write (bytes(self.sendstream))#(QtCore.QByteArray(len(tmpStr),tmpStr))
        self.tcpSocket.waitForBytesWritten()


    def __DataReceive(self):
        self.buff = self.tcpSocket.readData(2048)#self.tcpSocket.readBufferSize())
        self.r_data+=list(self.buff)
        print ('Rx:<--',time.strftime("%H:%M:%S", time.localtime()),listI2listH(self.r_data))
        if self.FrameCheck()==True:
            time.sleep(Delay)
            self.__Answer()
        
    def __FrameCombine(self):
        L=[0,0]
        HCS=[0,0]
        tmp=self.C+self.A+self.CA+HCS+self.apdu
        tmpL= len(tmp)+4
        L[0]=tmpL&0xff
        L[1]=tmpL>>8
        tmp=L+self.C+self.A+self.CA
        HCS = fcs16(tmp)
        tmp+=HCS+self.apdu
        FCS = fcs16(tmp)
        tmp=[0x68]+tmp+FCS+[0x16]
        self.sendstream=tmp

    def __confirm(self): 
        self.C=[0x80]
        self.AFN=[0x00]
        self.senddata=[0x00,0x00,0x01,0x00]
        self.__DataSend()
        
    def __restart(self):
        print('term restert')
        self.tcpSocket.disconnectFromHost ()

    def __UpComplete(self):
        self.OldVersion=self.NewVersion
        self.__restart()
        '''
        self.timer.timeout.connect(self.__restart)
        self.timer.start( 60000 )
        '''

    
    def __Answer(self):
        time.sleep(1)
        if self.apdu[0]==129:#预链接响应
            return
        elif self.apdu[0]== 5:#读取请求
            self.C=[0xc3]
            self.apdu = self.GET_Request()
        elif self.apdu[0]== 6:#设置请求
            self.C=[0xc3]
            self.apdu = self.SET_Request()
        elif self.apdu[0]==7:#
            self.C=[0xc3]
            self.apdu= self.Action_Reques()
        elif self.apdu[0]==9:
            pass
        elif self.apdu[0]==9:
            pass
        elif self.apdu[0]==10:
            pass
        else:
            pass

        self.__DataSend()
        if self.done:
            self.timer.stop()
            self.timer.timeout.connect(self.__restart)
            self.timer.start( 30000 )
            

    def FrameCheck(self):
        try:
            while self.r_data[0]!=0x68:
                self.r_data=self.r_data[1:]
        except:
            return
        Datalength = self.r_data[1]+(self.r_data[2]<<8)
        if len(self.r_data) < Datalength+2:
            return False
        if self.r_data[Datalength+1] != 0x16:
            return False 
        if fcs16(self.r_data[1:Datalength-1]) != self.r_data[Datalength-1:Datalength+1]:
            return False
        addrL = (self.r_data[4]&0xf)+1
        addr = self.r_data[4:addrL+5]
        if addr != self.A:
            return False
        self.apdu=self.r_data[addrL+8:]
        self.r_data = self.r_data[Datalength+2:]
        return True
        
    def GET_Request(self):
        if self.apdu[1]==1:#读取一个对象属性请求 [1] GetRequestNormal，
            oad=l2s(self.apdu[3:7])
            print('抄读',oad)
            self.apdu[0]|=0x80
            if oad == '43000300':
                if self.done:
                    return  self.apdu[:7] + [1] + DatabaseQuery('43000311') +[0,0]
            try:
                return  self.apdu[:7] + [1] + DatabaseQuery(oad) +[0,0]
            except:
                return self.apdu[:7] + [0,6]+[0,0]
        elif self.apdu[1]==2:#读取若干个对象属性请求 [2] GetRequestNormalList，
            pass
        elif self.apdu[1]==3:#读取一个记录型对象属性请求 [3] GetRequestRecord，
            pass
        elif self.apdu[1]==4:#读取若干个记录型对象属性请求  [4] GetRequestRecordList，
            pass
        elif self.apdu[1]==5:#读取分帧响应的下一个数据块请求 [5] GetRequestNext,
            pass
        else:
            pass
    def SET_Request(self):
        if self.apdu[1]==1:#设置一个对象属性的确认信息响应 [1] SetResponseNormal，
            oad=self.apdu[1:7]
            return [0x86]+oad+[0,0,0]
        elif self.apdu[2]==1:#设置若干个对象属性的确认信息响应 [2] SetResponseNormalList，
            pass
        elif self.apdu[3]==1:#设置的确认信息以及读取的响应 [3] SetThenGetResponseNormalList
            pass
        else:
            pass

    def Action_Reques(self):
        global DIC698
        bittable = [7,6,5,4,3,2,1,0]
        if self.apdu[1]==1:#操作一个对象方法请求 [1] ActionRequest，
            tmp=self.apdu[1:7]
            oad = tmp[2:]
            if oad == [0xf0,0x01,0x07,0x00]:
                tmp,data=datatype(self.apdu[7:])
                filesize=tmp[0][2]
                blocksize=tmp[1]
                blocknum = math.ceil(filesize/blocksize)
                print('blocknum',blocknum)
                listL = math.ceil(blocknum/8)
                self.BlockStatusWord=[]
                self.BlockStatusWordmirro =[]
                for i in range(listL):
                    self.BlockStatusWord += [0]
                    self.BlockStatusWordmirro += [0]
                for i in range(blocknum):
                    self.BlockStatusWordmirro[i//8] |= 1<<bittable[i%8]
                self.filebuff = []
                for i in range(blocknum):
                    self.filebuff += [[]]

                if blocknum<128:
                    self.BlockStatusWordlen = [0x04,blocknum]
                    DIC698['f0010400'] = self.BlockStatusWordlen + self.BlockStatusWord
                elif blocknum>128 and blocknum<256:
                    self.BlockStatusWordlen = [0x04,0x81,blocknum]
                    DIC698['f0010400'] = self.BlockStatusWordlen + self.BlockStatusWord
                elif blocknum > 255 and blocknum <65536 :
                    L=[blocknum>>8]+[blocknum&0xff]
                    self.BlockStatusWordlen  = [0x04,0x82] + L
                    DIC698['f0010400'] = self.BlockStatusWordlen +self.BlockStatusWord
                else:
                    L=[blocknum>>16]+[blocknum>>8&0xff]+[blocknum&0xff]
                    self.BlockStatusWordlen  = [0x04,0x83] + L
                    DIC698['f0010400'] = self.BlockStatusWordlen +self.BlockStatusWord
                print(self.BlockStatusWordmirro,self.BlockStatusWord,'self.BlockStatusWordmirro')

            if oad == [0xf0,0x01,0x08,0x00]:
                BlockSeqNum = (self.apdu[10]<<8)+self.apdu[11]
                maxseq = len(self.BlockStatusWord)-1
                print('maxseq',maxseq)
                local = BlockSeqNum//8
                print('local',local)
                word = self.BlockStatusWord[local]
                p = 7-BlockSeqNum%8
                word = word|(1<<p)
                self.BlockStatusWord[local]=word
                DIC698['f0010400'] = self.BlockStatusWordlen+self.BlockStatusWord

                if self.apdu[13] & 0x80:
                    ll = self.apdu[13] & 0xf
                    larry = self.apdu[14:14+ll]
                    datal = 0
                    for i in larry:
                        datal <<= 8
                        datal += i
                    self.filebuff[BlockSeqNum] = self.apdu[14+ll:14+ll+datal]
                else:
                    l = self.apdu[13]
                    self.filebuff[BlockSeqNum] = self.apdu[14:14+l]
                print(self.BlockStatusWordmirro,self.BlockStatusWord,'self.BlockStatusWordmirro')
                if self.BlockStatusWordmirro == self.BlockStatusWord:
                    self.file = open(self.filename, 'wb')
                    for j in self.filebuff:
                        self.file.write(bytes(j))
                    self.file.close()
                    print('Downloading is complated!')
                    self.done = True
            return [0x87,0x01,0x00]+oad+[0,0,0,0]
        elif self.apdu[2]==2:#操作若干个对象方法请求 [2] ActionRequestList，
            pass
        elif self.apdu[2]==3:#操作若干个对象方法后读取若干个对象属性请求 [3] ActionThenGetRequestNormalList
            pass


def FileSegment(data,dataarry):
    tmp = (data[3]<<24)+(data[2]<<16)+(data[1]<<8)+data[0]
    dataarry[tmp//8]=dataarry[tmp//8]&bitcheck2[tmp%8]


def bcd(i):
    return ((i//10)<<4)+(i%10)
            
def i2h(i):
    if i== '':
        return ''
    f=['0','1','2','3','4','5','6','7','8','9','A','B','C','D','E','F']
    while i>255:
        i=i-255
    return ' '+f[(i>>4)]+f[(i&15)]

def listI2listH(data):
    tmp = ''
    data = list(data)
    for i in data:
        tmp += i2h(i)
    return tmp

bitcheck={0:0,1:1,2:2,4:3,8:4,16:5,32:6,64:7,128:8}
bitcheck1={0:254,1:253,2:251,3:247,4:239,5:223,6:191,7:127}
bitcheck2={0:1,1:2,2:4,3:8,4:16,5:32,6:64,7:128}
map={}

if __name__ == "__main__":
    global DIC698
    DIC698={}
    app = QtGui.QApplication(sys.argv)
    OldVersion=[]
    NewVersion=[]
    Config = configparser.ConfigParser()
    try :
        Config.read("config.ini")
    except:
         UserInput = input('配置文件‘config.ini’未找到，任意键退出')
         if UserInput != None:
            quit()

    opts = Config.options("698")
    for key in opts:
        DIC698[key]=s2l(Config.get("698", key))    
    tmp = []
    old = Config['OldVersion']
    for i in old:
        tmp += [0x0A] + [len(old[i])]
        for j in old[i] :
            tmp += [ord(j)]

    DIC698['43000300'] = [2,6] + tmp
    
    tmp =[]
    new = Config['NewVersion']
    for i in new:
        tmp += [0x0A] + [len(new[i])]
        for j in new[i] :
            tmp += [ord(j)]

    DIC698['43000311'] = [2,6] + tmp

    try:
        StationIP = Config.get('Station','ip')
        StationPort = Config.get('Station','port')
    except:
        StationIP = '127.0.0.1'#default
        StationPort = '1280'#default
    try:
        MessageLossRate = int(Config.get('LossRate','MessageLossRate'))
        if 0<=MessageLossRate<=100:
            pass
        else:
            MessageLossRate=0
    except:
        MessageLossRate=0
    try:
        PackageLossRate = int(Config.get('LossRate','PackageLossRate'))
        if 0<=PackageLossRate<=100:
            pass
        else:
            PackageLossRate=0
    except:
        PackageLossRate=0
    try :
        LoginInterval= int(Config.get('time','LoginInterval'))
    except:
        LoginInterval = 3
    try :
        Delay = int(Config.get('time','Delay'))
    except:
        Delay = 0
    try :
        A = int(Config.get('TermSelect','A1'))
    except:
        A = 1

    try :
        TermNum = int(Config.get('TermSelect','TermNum'))
    except:
        TermNum = 1
    for i in range(TermNum):
        map[i]=ClientThread(i+A)
        time.sleep(2)
        
        
    app.exec_()#sys.exit(app.exec_())


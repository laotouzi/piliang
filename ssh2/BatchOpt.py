# coding=utf-8
#-*- coding: utf-8 -*-
#!/usr/bin/python
import ConfigParser
import getpass
import datetime
import os
import threading
from time import sleep
import traceback
import paramiko
import sys

__author__ = 'wuwenkai'

class argsobj:
    def __init__(self,pk_path=False,port=False):
        self.pk_path = pk_path
        self.port = port or "22"
    def __str__(self,hostname,ip,username,passwd,cmd,localpath,remotepath):
        self.hostname=hostname
        self.ip = ip
        self.username = username
        self.passwd = passwd
        self.cmd = cmd
        self.localpath = localpath
        self.remotepath = remotepath
    def __int__(self,opttype):
        self.opttype = opttype

def Getssh(obj):
        try:
            #是否要上传文件，1:不是 其他：上传
            if obj.opttype < 10:
                return Getsftp(obj)
            if obj.opttype > 10:
                Getsftp(obj)
            #是否执行ssh登入，2：不是 其他：上传
            ssh=paramiko.SSHClient()
            ssh.load_system_host_keys()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            if obj.pk_path :
                try:
                    key=paramiko.RSAKey.from_private_key_file(obj.pk_path)
                except paramiko.PasswordRequiredException:
                    password = getpass.getpass('RSA key passwd:')
                    key = paramiko.RSAKey.from_private_key_file(obj.pk_path,password)
                ssh.connect(hostname=obj.ip,port=obj.port,username=obj.username,pkey=key,timeout=5)
            else:
                ssh.connect(obj.ip,obj.port,obj.username,obj.passwd,timeout=10)
            if len(obj.cmd) > 0 :
                ###exec_command
                # print "#############%s:ssh start##############"%(obj.ip)
                # for m in obj.cmd:
                #     stdin, stdout, stderr = ssh.exec_command(command=m,timeout=10)
                #     # stdin.write(obj.passwd)   #简单交互，输入 ‘Y’
                #     stdin.close()
                #     out = stdout.read().strip()
                #     err = stderr.read().strip()
                #     if err:
                #         print "<%s\texception>:"%(obj.ip),err
                #         ssh.close()
                #         sys.exit(1)
                #     print "<%s\tput_out>#\n"%(obj.ip),out
                # print "#############%s:ssh end##############"%(obj.ip)
                ###invoke_shell
                starStr = "###[-- %s --]%s:ssh start,%s##############"%(obj.hostname,obj.ip,datetime.datetime.now())
                chan=ssh.invoke_shell()
                for cmd in obj.cmd:
                    chan.send(cmd+" \n")
                    sleep(2)
                    out = chan.recv(9999)
                    starStr = starStr +"\n"+ out
                chan.close()
                endStr = "###%s:ssh end,%s##############"%(obj.ip,datetime.datetime.now())
                print starStr+"\n"+endStr
                print ""
                print ""
            ssh.close()
        except :
            print '%s\tSSHError\n'%(obj.ip)
            traceback.print_exc()

def Getsftp(obj):
    try:
        t=paramiko.Transport((obj.ip,obj.port))
        if obj.pk_path:
            private_key = paramiko.RSAKey.from_private_key_file(obj.pk_path)
            t.connect(username=obj.username,pkey=private_key)
        else:
            t.connect(username=obj.username,password=obj.passwd)
        sftp=paramiko.SFTPClient.from_transport(t)
        #上传操作
        if obj.opttype == 1 or obj.opttype == 11:
            if os.path.isdir(obj.localpath):
                # files=sftp.listdir(obj.localpath)
                files=os.listdir(obj.localpath)
                file_path=obj.localpath
            elif os.path.isfile(obj.localpath):
                files=[os.path.basename(obj.localpath)]
                file_path=os.path.dirname(obj.localpath)
            for f in files:
                print ''
                print '#########################################'
                print 'Beginning to Upload file  to %s  %s ' % (obj.ip,datetime.datetime.now())
                print 'Uploading file:',os.path.join(file_path,f),"-->",os.path.join(obj.remotepath,f)
                sftp.put(os.path.join(file_path,f),os.path.join(obj.remotepath,f))#上传
                print 'Upload file success %s ' % datetime.datetime.now()
                print '##########################################'
         #下载操作
        elif obj.opttype == 2 or obj.opttype == 12 :
            try:
                try:
                    files = sftp.listdir(obj.remotepath)
                    file_path=obj.remotepath
                except:
                    files =[os.path.basename(obj.remotepath)]
                    file_path = os.path.dirname(obj.remotepath)
                for f in files:
                    print ''
                    print '#########################################'
                    print 'Beginning to download file  from %s  %s ' % (obj.ip,datetime.datetime.now())
                    print 'Downloading file:',os.path.join(file_path,f),"-->",os.path.join(obj.localpath,f)
                    sftp.get(os.path.join(file_path,f),os.path.join(obj.localpath,f))#下载
                    print 'Download file success %s ' % datetime.datetime.now()
                    print '##########################################'
            except:
                print '#### error for down ####'
        t.close()
    except Exception:
        print "connect error!"
        traceback.print_exc()
def ConnDB():
    pass

def Config():
    redata=[]
    conf=ConfigParser.ConfigParser()
    conf.read("BatchConfig.conf")
    cmd = []
#获取配置文件默认参数
    comport=int(conf.get("mode","port"))
    opttype=int(conf.get("mode","opttype"))
    localpath=conf.get("mode","localpath")
    remotepath=conf.get("mode","remotepath")
    commands=conf.options("command")
    for c in commands:
        cmd.append(conf.get("command",c))
    print "Begin collection......"
#用户名密码ip获取
    hosts=conf.options("host")
    for no in hosts:
        obj=argsobj()
        usrmes=conf.get("host",no).split("|")
        obj.hostname=no
        obj.ip = usrmes[0].strip()
        obj.username = usrmes[1].strip()
        obj.passwd = usrmes[2].strip()
        if len(usrmes) > 3:
            if usrmes[3].strip() == "1":
                obj.pk_path=obj.passwd
        if len(usrmes) == 9:
            obj.port = int(usrmes[4].strip()) or comport
            obj.cmd = list(usrmes[5].strip()) or cmd
            obj.remotepath=usrmes[6].strip() or remotepath
            obj.opttype=usrmes[7].strip() or opttype
            obj.localpath=usrmes[8].strip() or localpath
        else:
            obj.port = comport
            obj.cmd =  cmd
            obj.remotepath=remotepath
            obj.opttype=opttype
            obj.localpath=localpath
        redata.append(obj)
    print "End collection......"
    return redata

if __name__ == "__main__":
    redata=Config()
    # arrlist=[]
    # print "------ start time :",datetime.datetime.now()
    for re in redata:
        t=threading.Thread(target=Getssh,args=(re,))
        t.setName(re.hostname)
        # t.setDaemon(True)#多线程则注释这行
        t.start()
        # t.join()#多线程则注释这行
        sleep(0.1)
    #     arrlist.append(t)
    # for th in arrlist:
    #     th.start()

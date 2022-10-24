from cProfile import run
import pstats
from pyobigram.utils import sizeof_fmt,get_file_size,createID,nice_time
from pyobigram.client import ObigramClient,inlineQueryResultArticle
from pyobigram.client import inlineKeyboardMarkup,inlineKeyboardMarkupArray,inlineKeyboardButton

from JDatabase import JsonDatabase
import shortener
import zipfile
import os
from os import walk
import infos
import xdlink
import mediafire
import datetime
import time
import youtube
import NexCloudClient
from pydownloader.downloader import Downloader
from ProxyCloud import ProxyCloud
import ProxyCloud
import socket
import tlmedia
import S5Crypto
import asyncio
import aiohttp
from yarl import URL
import re
import random
from draft_to_calendar import Draft2Calendar
import moodlews
import moodle_client
from moodle_client import MoodleClient
import S5Crypto
import uptodown
import shutil
from shutil import make_archive
import pyzipper
from shutil import rmtree

listproxy = []

def sign_url(token: str, url: URL):
    query: dict = dict(url.query)
    query["token"] = token
    path = "webservice" + url.path
    return url.with_path(path).with_query(query)

def nameRamdom():
    populaton = 'abcdefgh1jklmnopqrstuvwxyz1234567890ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    name = "".join(random.sample(populaton,10))
    return name

def downloadFile(downloader,filename,currentBits,totalBits,speed,time,args):
    try:
        bot = args[0]
        message = args[1]
        thread = args[2]
        if thread.getStore('stop'):
            downloader.stop()
        downloadingInfo = infos.createDownloading(filename,totalBits,currentBits,speed,time,tid=thread.id)
        reply_markup = inlineKeyboardMarkup(
            r1=[inlineKeyboardButton('🔴Cancelar Descarga🔴', callback_data='/cancel '+str(thread.id))]
        )
        bot.editMessageText(message,downloadingInfo,reply_markup=reply_markup)
    except Exception as ex: print(str(ex))
    pass

def uploadFile(filename,currentBits,totalBits,speed,time,args):
    try:
        bot = args[0]
        message = args[1]
        originalfile = args[2]
        thread = args[3]
        downloadingInfo = infos.createUploading(filename,totalBits,currentBits,speed,time,originalfile)
        bot.editMessageText(message,downloadingInfo)
    except Exception as ex: print(str(ex))
    pass

def processUploadFiles(filename,filesize,files,update,bot,message,thread=None,jdb=None):
    try:
        err = None
        bot.editMessageText(message,'☭reparando Para Subir... ')
        evidence = None
        fileid = None
        user_info = jdb.get_user(update.message.sender.username)
        cloudtype = user_info['cloudtype']
        proxy = ProxyCloud.parse(user_info['proxy'])
        draftlist=[]
        if cloudtype == 'moodle':
            host = user_info['moodle_host']
            user = user_info['moodle_user']
            passw = user_info['moodle_password']
            repoid = user_info['moodle_repo_id']
            token = moodlews.get_webservice_token(host,user,passw,proxy=proxy)
            token = None
            if token:
                print(token)
                for file in files:
                    data = asyncio.run(moodlews.webservice_upload_file(host,token,file,progressfunc=uploadFile,proxy=proxy,args=(bot,message,filename,thread)))
                    while not moodlews.store_exist(file):pass
                    data = moodlews.get_store(file)
                    if data[0]:
                        urls = moodlews.make_draft_urls(data[0])
                        draftlist.append({'file':file,'url':urls[0]})
                    else:
                        err = data[1]
            else:
                cli = MoodleClient(host,user,passw,repoid,proxy)
                for file in files:
                    data = asyncio.run(cli.LoginUpload(file, uploadFile, (bot, message, filename, thread)))
                    while cli.status is None: pass
                    data = cli.get_store(file)
                    if data:
                        if 'error' in data:
                            err = data['error']
                        else:
                            draftlist.append({'file': file, 'url': data['url']})
                pass
            return draftlist,err
        elif cloudtype == 'cloud':
            tokenize = False
            if user_info['tokenize']!=0:
               tokenize = True
            host = user_info['moodle_host']
            user = user_info['moodle_user']
            passw = user_info['moodle_password']
            remotepath = user_info['dir']
            client = NexCloudClient.NexCloudClient(user,passw,host,proxy=proxy)
            loged = client.login()
            bot.editMessageText(message,'🤜Subiendo ☁ Espere Mientras... 😄')
            if loged:
               originalfile = ''
               if len(files)>1:
                    originalfile = filename
               filesdata = []
               for f in files:
                   data = client.upload_file(f,path=remotepath,progressfunc=uploadFile,args=(bot,message,originalfile,thread),tokenize=tokenize)
                   filesdata.append(data)
                   os.unlink(f)                
               return filesdata,err
        return None,err
    except Exception as ex:
        bot.sendMessage(message.chat.id,f'❌Error {str(ex)}❌')
        return None,ex


def processFile(update,bot,message,file,thread=None,jdb=None):
    user_info = jdb.get_user(update.message.sender.username)
    name =''
    if user_info['rename'] == 1:
        ext = file.split('.')[-1]
        if '7z.' in file:
            ext1 = file.split('.')[-2]
            ext2 = file.split('.')[-1]
            name = nameRamdom() + '.'+ext1+'.'+ext2
        else:
            name = nameRamdom() + '.'+ext
    else:
        name = file
    os.rename(file,name)
    file_size = get_file_size(name)
    getUser = jdb.get_user(update.message.sender.username)
    max_file_size = 1024 * 1024 * getUser['zips']
    file_upload_count = 0
    client = None
    findex = 0
    if file_size > max_file_size:
        compresingInfo = infos.createCompresing(name,file_size,max_file_size)
        bot.editMessageText(message,compresingInfo)
        zipname = str(name).split('.')[0] + createID()
        mult_file = zipfile.MultiFile(zipname,max_file_size)
        zip = zipfile.ZipFile(mult_file,  mode='w', compression=zipfile.ZIP_DEFLATED)
        zip.write(name)
        zip.close()
        mult_file.close()
        data,err = processUploadFiles(name,file_size,mult_file.files,update,bot,message,jdb=jdb)
        try:
            os.unlink(name)
        except:pass
        file_upload_count = len(zipfile.files)
    else:
        data,err = processUploadFiles(name,file_size,[name],update,bot,message,jdb=jdb)
        file_upload_count = 1
    bot.editMessageText(message,'☭Recolectando Informacion...')
    evidname = ''
    files = []
    if data:
        for draft in data:
            files.append({'name':draft['file'],'directurl':draft['url']})
        if user_info['urlshort']==1:
            if len(files)>0:
                i = 0
                while i < len(files):
                    files[i]['directurl'] = shortener.short_url(files[i]['directurl'])
                    i+=1
        bot.deleteMessage(message)
        finishInfo = infos.createFinishUploading(file,file_size)
        filesInfo = infos.createFileMsg(file,files)
        bot.sendMessage(message.chat.id,finishInfo+'\n'+filesInfo,parse_mode='html')
        if len(files)>0:
            txtname = str(file).split('/')[-1].split('.')[0] + '.txt'
            sendTxt(txtname,files,update,bot)
    else:
        error = '❌Error En La Pagina❌'
        if err:
            error = err
        bot.editMessageText(message,error)

def ddl(update,bot,message,url,file_name='',thread=None,jdb=None):
    username = update.message.sender.username
    path = './'+username+'/'
    downloader = Downloader()
    file = path+downloader.download_url(url,progressfunc=downloadFile,args=(bot,message,thread))
    user_info = jdb.get_user(update.message.sender.username)
    if not os.path.isdir(username):
        os.mkdir(username)
    shutil.move(file, path)
    bot.editMessageText(message,'📥 Descarga finalizada 📥')
    if not downloader.stoping:
        if user_info['autoup'] == 1:
            if file:
                processFile(update,bot,message,file,jdb=jdb)            
                os.remove(file)
                
def sendTxt(name,files,update,bot):
                txt = open(name,'w')
                fi = 0
                for f in files:
                    separator = ''
                    if fi < len(files)-1:
                        separator += '\n'
                    txt.write(f['directurl']+separator)
                    fi += 1
                txt.close()
                bot.sendFile(update.message.chat.id,name)
                os.unlink(name)

def onmessage(update,bot:ObigramClient):
    try:
        thread = bot.this_thread
        username = update.message.sender.username
        path = './'+username+'/'
        #tl_admin_user = os.environ.get('tl_admin_user')

        #set in debug
        tl_admin_user = 'demian2008'

        jdb = JsonDatabase('database')
        jdb.check_create()
        jdb.load()

        user_info = jdb.get_user(username)
        #if username == tl_admin_user or user_info:
        if username in str(tl_admin_user).split(';') or user_info or tl_admin_user=='*':  # validate user
            if user_info is None:
                #if username == tl_admin_user:
                if username == tl_admin_user:
                    jdb.create_admin(username)
                else:
                    jdb.create_user(username)
                user_info = jdb.get_user(username)
                jdb.save()
        else:
            mensaje = "🚷No tienes acceso🚷"
            reply_markup = inlineKeyboardMarkup(
                r1=[inlineKeyboardButton('👤Contactar👤',url='https://t.me/demian2008')]
            )
            bot.sendMessage(update.message.chat.id,mensaje,reply_markup=reply_markup)
            return

        msgText = ''
        try: msgText = update.message.text
        except:pass

        if '/rename' in msgText:
            try:
                dir, subdirs, archivos = next(walk(path))
                filenmb = int(msgText.split(' ')[1])
                filespl = archivos[filenmb]
                file = path+filespl
                new_name = msgText.split(' ')[2]
                os.rename(file, path+new_name)
                bot.sendMessage(update.message.chat.id,'🔰Archivo Renombrado🔰')
            except:
                bot.sendMessage(update.message.chat.id,'❌Comando mal usado❌\n🔰Ejemplo: /rename #dearchivo NuevoNombre')
            return

        if '/rm' in msgText:
            try:
                dir, subdirs, archivos = next(walk(path))
                filenmb = int(msgText.split('_')[1])
                filespl = archivos[filenmb]
                file = path+filespl
                os.remove(file)
                bot.sendMessage(update.message.chat.id,'🗑️Archivo eliminado🗑️')
            except:
                bot.sendMessage(update.message.chat.id,'❌Comando mal usado❌\n🔰Ejemplo: /rm #dearchivo')
            return

        if '/pathrm' in msgText:
            try:
                dir, subdirs, archivos = next(walk(path))
                tosplit = int(msgText.split(' ')[1])
                to_all = subdirs[tosplit]
                to = path+to_all+'/'
                rmtree(to)
                bot.sendMessage(update.message.chat.id,'🗑️Carpeta eliminada🗑️')
            except:
                bot.sendMessage(update.message.chat.id,'❌Comando mal usado❌\n🔰Ejemplo: /pathrm #decarpeta')
            return
            
        if '/mkdir' in msgText:
            try:
                name = msgText.split(' ')[1]           
                os.mkdir(path+name)
                bot.sendMessage(update.message.chat.id,'📂Carpeta creada📂')
            except:
                bot.sendMessage(update.message.chat.id,'❌Comando mal usado❌\n🔰Ejemplo: /mkdir NombreDeCarpeta')
            return

        if '/move' in msgText:
            try:
                dir, subdirs, archivos = next(walk(path))
                filenmb = int(msgText.split(' ')[1])
                filespl = archivos[filenmb]
                file = path+filespl        
                tosplit = int(msgText.split(' ')[2])
                to_all = subdirs[tosplit]
                to = path+to_all+'/'
                shutil.move(file, to)
                bot.sendMessage(update.message.chat.id,'📦Movido📦')
            except:
                bot.sendMessage(update.message.chat.id,'❌Comando mal usado❌\n🔰Ejemplo: /move #dearchivo #decarpeta')
            return

        if '/cdir' in msgText:
            try:
                dir, subdirs, archivos = next(walk(path))
                tosplit = int(msgText.split('_')[1])
                to_all = subdirs[tosplit]
                to = path+to_all+'/'
                for s in subdirs:           
                    make_archive(path+s, 'zip', to+'/')
                    bot.sendMessage(update.message.chat.id,'🗜️Comprimido🗜️')
            except:
                bot.sendMessage(update.message.chat.id,'❌Comando mal usado❌\n🔰Ejemplo: /cdir_#dearchivo')
            return

        # comandos de admin

        if '/add_user' in msgText:
            isadmin = jdb.is_admin(username)
            if isadmin:
                try:
                    user = str(msgText).split(' ')[1]
                    jdb.create_user(user)
                    jdb.save()
                    msg = '👥@'+user+' ahora tiene acceso al bot👥'
                    bot.sendMessage(update.message.chat.id,msg)
                except:
                    bot.sendMessage(update.message.chat.id,'❌Error en el comando /adduser username❌')
            else:
                bot.sendMessage(update.message.chat.id,'❌No Tiene Permiso❌')
            return

        if '/add_admin' in msgText:
            isadmin = jdb.is_admin(username)
            if isadmin:
                try:
                    user = str(msgText).split(' ')[1]
                    jdb.create_admin(user)
                    jdb.save()
                    msg = '💠@'+user+' ahora es admin del bot💠'
                    bot.sendMessage(update.message.chat.id,msg)
                except:
                    bot.sendMessage(update.message.chat.id,'❌Error en el comando /adduser username❌')
            else:
                bot.sendMessage(update.message.chat.id,'❌No Tiene Permiso❌')
            return

        if '/ban_user' in msgText:
            isadmin = jdb.is_admin(username)
            if isadmin:
                try:
                    user = str(msgText).split(' ')[1]
                    if user == username:
                        bot.sendMessage(update.message.chat.id,'❌No Se Puede Banear Usted❌')
                        return
                    jdb.remove(user)
                    jdb.save()
                    msg = '💢@'+user+' baneado💢'
                    bot.sendMessage(update.message.chat.id,msg)
                except:
                    bot.sendMessage(update.message.chat.id,'❌Error en el comando /banuser username❌')
            else:
                bot.sendMessage(update.message.chat.id,'❌No Tiene Permiso❌')
            return

        if '/short_url' in msgText:
            isadmin = jdb.is_admin(username)
            if isadmin:
                try:
                    for user in jdb.items:
                        if jdb.items[user]['urlshort']==0:
                            jdb.items[user]['urlshort'] = 1
                            continue
                        if jdb.items[user]['urlshort']==1:
                            jdb.items[user]['urlshort'] = 0
                            continue
                    jdb.save()
                    bot.sendMessage(update.message.chat.id,'✅ShortUrl Cambiado✅')
                    statInfo = infos.createStat(username, user_info, jdb.is_admin(username))
                    reply_markup = None
                    if user_info['proxy'] != '':
                        reply_markup = inlineKeyboardMarkup(
                            r1=[inlineKeyboardButton('✘ Quitar Proxy ✘', callback_data='/deleteproxy ' + username)]
                        )
                    bot.sendMessage(update.message.chat.id, statInfo,reply_markup=reply_markup)
                except:
                    bot.sendMessage(update.message.chat.id,'❌Error en el comando /banuser username❌')
            return

        if '/get_db' in msgText:
            isadmin = jdb.is_admin(username)
            if isadmin:
                bot.sendMessage(update.message.chat.id,'📔Base De Datos📔')
                bot.sendFile(update.message.chat.id,'database.jdb')
            else:
                bot.sendMessage(update.message.chat.id,'❌No Tiene Permiso❌')
            return
        # end

        # comandos de usuario

        if '/mydata' in msgText:
            getUser = user_info
            if getUser:
                statInfo = infos.createStat(username,getUser,jdb.is_admin(username))
                reply_markup = None
                if user_info['proxy'] != '':
                    reply_markup = inlineKeyboardMarkup(
                        r1=[inlineKeyboardButton('❌Quitar Proxy❌', callback_data='/deleteproxy '+username)]
                    )
                bot.sendMessage(update.message.chat.id,statInfo,reply_markup=reply_markup)
                return

        if '/zips' in msgText:
            getUser = user_info
            if getUser:
                try:
                   size = int(str(msgText).split(' ')[1])
                   getUser['zips'] = size
                   jdb.save_data_user(username,getUser)
                   jdb.save()
                   msg = '😃Genial los zips seran de '+ sizeof_fmt(size*1024*1024)+' las partes👍'
                   bot.sendMessage(update.message.chat.id,msg)
                except:
                   bot.sendMessage(update.message.chat.id,'❌Error en el comando /zips size❌')
                return

        if '/autoup_on' in msgText:
            getUser = user_info
            if getUser:
                try:
                   getUser['autoup'] = int(1)
                   jdb.save_data_user(username,getUser)
                   jdb.save()
                   msg = '📤Autoup: ✅'
                   bot.sendMessage(update.message.chat.id,msg)
                except:
                   bot.sendMessage(update.message.chat.id,'❌Error en el comando /autoup_on❌')
                return            
                                
        if '/autoup_off' in msgText:
            getUser = user_info
            if getUser:
                try:
                   getUser['autoup'] = int(0)
                   jdb.save_data_user(username,getUser)
                   jdb.save()
                   msg = '📤Autoup: ✔️'
                   bot.sendMessage(update.message.chat.id,msg)
                except:
                   bot.sendMessage(update.message.chat.id,'❌Error en el comando /autoup_off❌')
                return            

        if '/acc' in msgText:
            try:
                account = str(msgText).split(' ',2)[1].split(',')
                user = account[0]
                passw = account[1]
                getUser = user_info
                if getUser:
                    getUser['moodle_user'] = user
                    getUser['moodle_password'] = passw
                    jdb.save_data_user(username,getUser)
                    jdb.save()
                    statInfo = infos.createStat(username,getUser,jdb.is_admin(username))
                    reply_markup = None
                    if user_info['proxy'] != '':
                        reply_markup = inlineKeyboardMarkup(
                            r1=[inlineKeyboardButton('✘ Quitar Proxy ✘', callback_data='/deleteproxy ' + username)]
                        )
                    bot.sendMessage(update.message.chat.id,statInfo,reply_markup=reply_markup)
            except:
                bot.sendMessage(update.message.chat.id,'❌Error en el comando /account user,password❌')
            return

        if '/host' in msgText:
            try:
                cmd = str(msgText).split(' ',2)
                host = cmd[1]
                getUser = user_info
                if getUser:
                    getUser['moodle_host'] = host
                    jdb.save_data_user(username,getUser)
                    jdb.save()
                    statInfo = infos.createStat(username,getUser,jdb.is_admin(username))
                    reply_markup = None
                    if user_info['proxy'] != '':
                        reply_markup = inlineKeyboardMarkup(
                            r1=[inlineKeyboardButton('✘ Quitar Proxy ✘', callback_data='/deleteproxy ' + username)]
                        )
                    bot.sendMessage(update.message.chat.id,statInfo,reply_markup=reply_markup)
            except:
                bot.sendMessage(update.message.chat.id,'❌Error en el comando /host moodlehost❌')
            return

        if '/repo' in msgText:
            try:
                cmd = str(msgText).split(' ',2)
                repoid = int(cmd[1])
                getUser = user_info
                if getUser:
                    getUser['moodle_repo_id'] = repoid
                    jdb.save_data_user(username,getUser)
                    jdb.save()
                    statInfo = infos.createStat(username,getUser,jdb.is_admin(username))
                    reply_markup = None
                    if user_info['proxy'] != '':
                        reply_markup = inlineKeyboardMarkup(
                            r1=[inlineKeyboardButton('✘ Quitar Proxy ✘', callback_data='/deleteproxy ' + username)]
                        )
                    bot.sendMessage(update.message.chat.id,statInfo,reply_markup=reply_markup)
            except:
                bot.sendMessage(update.message.chat.id,'❌Error en el comando /repo id❌')
            return

        if '/tokenize_on' in msgText:
            try:
                getUser = user_info
                if getUser:
                    getUser['tokenize'] = 1
                    jdb.save_data_user(username,getUser)
                    jdb.save()
                    statInfo = infos.createStat(username,getUser,jdb.is_admin(username))
                    reply_markup = None
                    if user_info['proxy'] != '':
                        reply_markup = inlineKeyboardMarkup(
                            r1=[inlineKeyboardButton('✘ Quitar Proxy ✘', callback_data='/deleteproxy ' + username)]
                        )
                    bot.sendMessage(update.message.chat.id,statInfo,reply_markup=reply_markup)
            except:
                bot.sendMessage(update.message.chat.id,'❌Error en el comando /tokenize state❌')
            return

        if '/tokenize_off' in msgText:
            try:
                getUser = user_info
                if getUser:
                    getUser['tokenize'] = 0
                    jdb.save_data_user(username,getUser)
                    jdb.save()
                    statInfo = infos.createStat(username,getUser,jdb.is_admin(username))
                    reply_markup = None
                    if user_info['proxy'] != '':
                        reply_markup = inlineKeyboardMarkup(
                            r1=[inlineKeyboardButton('✘ Quitar Proxy ✘', callback_data='/deleteproxy ' + username)]
                        )
                    bot.sendMessage(update.message.chat.id,statInfo,reply_markup=reply_markup)
            except:
                bot.sendMessage(update.message.chat.id,'❌Error en el comando /tokenize state❌')
            return

        if '/cloud' in msgText:
            try:
                cmd = str(msgText).split(' ',2)
                repoid = cmd[1]
                getUser = user_info
                if getUser:
                    getUser['cloudtype'] = repoid
                    jdb.save_data_user(username,getUser)
                    jdb.save()
                    statInfo = infos.createStat(username,getUser,jdb.is_admin(username))
                    reply_markup = None
                    if user_info['proxy'] != '':
                        reply_markup = inlineKeyboardMarkup(
                            r1=[inlineKeyboardButton('✘ Quitar Proxy ✘', callback_data='/deleteproxy ' + username)]
                        )
                    bot.sendMessage(update.message.chat.id,statInfo,reply_markup=reply_markup)
            except:
                bot.sendMessage(update.message.chat.id,'❌Error en el comando /cloud (moodle or cloud)❌')
            return

        if '/proxy' in msgText:
            try:
                cmd = str(msgText).split(' ',2)
                proxy = cmd[1]
                getUser = user_info
                if getUser:
                    getUser['proxy'] = proxy
                    jdb.save_data_user(username,getUser)
                    jdb.save()
                    statInfo = infos.createStat(username,getUser,jdb.is_admin(username))
                    reply_markup = None
                    if user_info['proxy'] != '':
                        reply_markup = inlineKeyboardMarkup(
                            r1=[inlineKeyboardButton('✘ Quitar Proxy ✘', callback_data='/deleteproxy ' + username)]
                        )
                    bot.sendMessage(update.message.chat.id,statInfo)
            except:
                if user_info:
                    user_info['proxy'] = ''
                    statInfo = infos.createStat(username,user_info,jdb.is_admin(username))
                    reply_markup = None
                    if user_info['proxy'] != '':
                        reply_markup = inlineKeyboardMarkup(
                            r1=[inlineKeyboardButton('✘ Quitar Proxy ✘', callback_data='/deleteproxy ' + username)]
                        )
                    bot.sendMessage(update.message.chat.id,statInfo,reply_markup=reply_markup)
            return

        if '/crypt' in msgText:
            proxy_sms = str(msgText).split(' ')[1]
            proxy = S5Crypto.encrypt(f'{proxy_sms}')
            bot.sendMessage(update.message.chat.id, f'Proxy encryptado:\n{proxy}')
            return

        if '/decrypt' in msgText:
            proxy_sms = str(msgText).split(' ')[1]
            proxy_de = S5Crypto.decrypt(f'{proxy_sms}')
            bot.sendMessage(update.message.chat.id, f'Proxy decryptado:\n{proxy_de}')
            return

        if '/dir' in msgText:
            try:
                cmd = str(msgText).split(' ',2)
                repoid = cmd[1]
                getUser = user_info
                if getUser:
                    getUser['dir'] = repoid + '/'
                    jdb.save_data_user(username,getUser)
                    jdb.save()
                    statInfo = infos.createStat(username,getUser,jdb.is_admin(username))
                    reply_markup = None
                    if user_info['proxy'] != '':
                        reply_markup = inlineKeyboardMarkup(
                            r1=[inlineKeyboardButton('✘ Quitar Proxy ✘', callback_data='/deleteproxy ' + username)]
                        )
                    bot.sendMessage(update.message.chat.id,statInfo,reply_markup=reply_markup)
            except:
                bot.sendMessage(update.message.chat.id,'❌Error en el comando /dir folder❌')
            return
        #end

        message = bot.sendMessage(update.message.chat.id,'⏳Procesando...')

        thread.store('msg',message)

        if '/start' in msgText:
            reply_markup = inlineKeyboardMarkup(
                r1=[inlineKeyboardButton('📂Archivos📂', callback_data='/ls '+username),
                    inlineKeyboardButton('👤Soporte👤', url='https://t.me/diago8888')]
            )
            bot.editMessageText(message,infos.dashboard(),reply_markup=reply_markup)
        elif '/get_token' in msgText:
            message2 = bot.editMessageText(message,'⏳Obteniendo Token...')
            try:
                proxy = ProxyCloud.parse(user_info['proxy'])
                client = MoodleClient(user_info['moodle_user'],
                                      user_info['moodle_password'],
                                      user_info['moodle_host'],
                                      user_info['moodle_repo_id'],proxy=proxy)
                loged = client.login()
                if loged:
                    token = client.userdata
                    modif = token['token']
                    bot.editMessageText(message2,'Su Token es: '+modif)
                    client.logout()
                else:
                    bot.editMessageText(message2,'La Moodle '+client.path+' No tiene Token')
            except Exception as ex:
                bot.editMessageText(message2,'La Moodle '+client.path+' No tiene Token o revise la Cuenta')
        elif '/files' == msgText and user_info['cloudtype']=='moodle':
             proxy = ProxyCloud.parse(user_info['proxy'])
             client = MoodleClient(user_info['moodle_user'],
                                   user_info['moodle_password'],
                                   user_info['moodle_host'],
                                   user_info['moodle_repo_id'],proxy=proxy)
             loged = client.login()
             if loged:
                 files = client.getEvidences()
                 filesInfo = infos.createFilesMsg(files)
                 bot.editMessageText(message,filesInfo)
                 client.logout()
             else:
                bot.editMessageText(message,'❌Error y Causas🧐\n1-Revise su Cuenta\n2-Servidor Desabilitado: '+client.path)
        elif '/txt_' in msgText and user_info['cloudtype']=='moodle':
             findex = str(msgText).split('_')[1]
             findex = int(findex)
             proxy = ProxyCloud.parse(user_info['proxy'])
             client = MoodleClient(user_info['moodle_user'],
                                   user_info['moodle_password'],
                                   user_info['moodle_host'],
                                   user_info['moodle_repo_id'],proxy=proxy)
             loged = client.login()
             if loged:
                 evidences = client.getEvidences()
                 evindex = evidences[findex]
                 txtname = evindex['name']+'.txt'
                 sendTxt(txtname,evindex['files'],update,bot)
                 client.logout()
                 bot.editMessageText(message,'TxT Aqui👇')
             else:
                bot.editMessageText(message,'❌Error y Causas🧐\n1-Revise su Cuenta\n2-Servidor Desabilitado: '+client.path)
             pass
        elif '/del_' in msgText and user_info['cloudtype']=='moodle':
            findex = int(str(msgText).split('_')[1])
            proxy = ProxyCloud.parse(user_info['proxy'])
            client = MoodleClient(user_info['moodle_user'],
                                   user_info['moodle_password'],
                                   user_info['moodle_host'],
                                   user_info['moodle_repo_id'],
                                   proxy=proxy)
            loged = client.login()
            if loged:
                evfile = client.getEvidences()[findex]
                client.deleteEvidence(evfile)
                client.logout()
                bot.editMessageText(message,'Archivo Borrado 🦶')
            else:
                bot.editMessageText(message,'❌Error y Causas🧐\n1-Revise su Cuenta\n2-Servidor Desabilitado: '+client.path)
        elif 'uptodown.com' in msgText:
            try:
                if not os.path.isdir(username):
                    os.mkdir(username)
                url = msgText
                bot.editMessageText(message,'📥 Descargando de uptodown 📥')
                file = uptodown.Download(url, output=path)
                bot.editMessageText(message,'📥 Descarga finalizada 📥')
                user_info = jdb.get_user(username)
                if user_info['autoup'] == 1:
                    processFile(update,bot,message,file,thread=thread,jdb=jdb)
                    os.remove(file)
            except:
                bot.sendMessage(update.message.chat.id,'❌Error al descargar❌')
        elif 'http' in msgText:
            url = msgText
            ddl(update,bot,message,url,file_name='',thread=thread,jdb=jdb)
        elif '/up' in msgText:
            try:
                dir, subdirs, archivos = next(walk(path))
                filenmb = int(msgText.split('_')[1])
                filespl = archivos[filenmb]
                file = path+filespl
                processFile(update,bot,message,file,thread=thread,jdb=jdb)
            except:
                bot.editMessageText(message,'❌Comando mal usado❌\n🔰Ejemplo: /up_0')
            return
    except Exception as ex:
           print(str(ex))
           bot.sendMessage(update.message.chat.id,str(ex))

def atras(update,bot:ObigramClient):
    username = update.data
    reply_markup = inlineKeyboardMarkup(
        r1=[inlineKeyboardButton('📂Archivos📂', callback_data='/ls '+username),
            inlineKeyboardButton('👤Soporte👤', url='https://t.me/diago8888')]
    )
    bot.editMessageText(update.message,infos.dashboard(),reply_markup=reply_markup)

def ls(update,bot:ObigramClient):
    username = update.data
    path = './'+username+'/'
    if not os.path.isdir(username):
        os.mkdir(username)
    files = infos.files(username, path)
    reply_markup = inlineKeyboardMarkup(
        r1=[inlineKeyboardButton('⬅️Atrás⬅️', callback_data='/atras '+username)]
    )
    bot.editMessageText(update.message, files, reply_markup=reply_markup)

def cancel_task(update,bot:ObigramClient):
    try:
        cmd = str(update.data).split(' ', 2)
        tid = cmd[1]
        tcancel = bot.threads[tid]
        msg = tcancel.getStore('msg')
        tcancel.store('stop', True)
        time.sleep(3)
        bot.deleteMessage(update.message)
    except Exception as ex:
        print(str(ex))
    return
    pass

def maketxt(update,bot:ObigramClient):
    data = update.message.reply_markup.inline_keyboard
    urls = []
    for item in data:
        for keyboard in item:
            try:
                name = keyboard.text
                url = keyboard.url
                urls.append({'name':name,'directurl':url})
            except:pass
    txtname = str(update.data).replace(' ','')
    sendTxt(txtname,urls,update,bot)
    pass

def deleteproxy(update,bot:ObigramClient):
    username = update.data
    jdb = JsonDatabase('database')
    jdb.check_create()
    jdb.load()
    userdata = jdb.get_user(username)
    if userdata:
        userdata['proxy'] = ''
        jdb.save_data_user(username, userdata)
        jdb.save()
        statInfo = infos.createStat(username, userdata, jdb.is_admin(username))
        bot.editMessageText(update.message, statInfo)
    pass

def convert2calendar(update,bot:ObigramClient):
    data = update.message.reply_markup.inline_keyboard
    urls = []
    for item in data:
        for keyboard in item:
            try:
                name = keyboard.text
                url = keyboard.url
                urls.append(url)
            except:
                pass
    parserdata = S5Crypto.decrypt(str(update.message.text).split('\n')[1].replace('datacallback: ','')).split('|')
    parser = Draft2Calendar()
    host = parserdata[0]
    user = parserdata[1]
    passw = parserdata[2]
    proxy = None
    if len(parserdata)>3:
        proxy = ProxyCloud.parse(parserdata[3])
    asyncio.run(parser.send_calendar(host,user,passw,urls,proxy))
    while parser.status==0:pass
    if parser.data:
        text = str(update.message.text).replace('draft','calendario')
        markup_array = []
        i = 0
        lastfile = ''
        while i < len(parser.data):
            filename1 = str(parser.data[i]).split('/')[-1]
            bbt = [inlineKeyboardButton(filename1, url=parser.data[i])]
            lastfile = filename1
            if i + 1 < len(parser.data):
                filename2 = str(parser.data[i + 1]).split('/')[-1]
                if filename2!=lastfile:
                    bbt.append(inlineKeyboardButton(filename2, url=parser.data[i + 1]))
                    lastfile = filename2
            markup_array.append(bbt)
            i += 2
        txtname = str(parser.data[0]).split('/')[-1].split('.')[0] + '.txt'
        markup_array.append([inlineKeyboardButton('✎Crear TxT✎',callback_data='/maketxt '+txtname)])
        reply_markup = inlineKeyboardMarkupArray(markup_array)
        bot.editMessageText(update.message, text,reply_markup=reply_markup)
    pass

def main():
    #bot_token = os.environ.get('bot_token')
    print('💢Bot iniciado💢')
    #set in debug
    bot_token = '5497216071:AAHHSiohR73ubpJtCOc2ILZpko43mKP0Qhs'
    bot = ObigramClient(bot_token)
    bot.onMessage(onmessage)
    bot.onCallbackData('/atras ',atras)
    bot.onCallbackData('/ls ',ls)
    bot.onCallbackData('/cancel ',cancel_task)
    bot.onCallbackData('/maketxt ', maketxt)
    bot.onCallbackData('/deleteproxy ',deleteproxy)
    bot.onCallbackData('/convert2calendar ',convert2calendar)
    bot.run()

if __name__ == '__main__':
    try:
        main()
    except:
        main()

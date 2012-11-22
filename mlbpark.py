#!/usr/bin/python
# -*- coding: utf-8 -*-
import urllib
import urllib2
import ClientCookie
import os
import getpass
import re
import cgi
import sys
import BeautifulSoup
import pickle
import MySQLdb
import md5
import dbpass

db = None
def connectDB():
    global db
    db = MySQLdb.connect('localhost', dbpass.id, dbpass.passwd, dbpass.dbname)
    db.query("set character_set_connection=utf8;")
    db.query("set character_set_server=utf8;")
    db.query("set character_set_client=utf8;")
    db.query("set character_set_results=utf8;")
    db.query("set character_set_database=utf8;")
    return db

def getLoginURLDataResponse(url):
    request = urllib2.Request(url)
    request.add_header('Referer', url)
    response = ClientCookie.urlopen(request)
    return response

def extractArticle(board, page):
    d = getLoginURLDataResponse('http://mlbpark.donga.com/mbs/articleL.php?mbsC=%s&cpage=%d'%(board,page))
    html = d.read()
    html = html.decode('cp949')
    soup = BeautifulSoup.BeautifulSoup(html)
    articles = soup.findAll('td' , attrs={'width':45,'class':'A11gray'}) 
    lastid = 0
    for item in articles:
        no = item.text.encode('utf-8')
        if no =='공지':
            continue
        node = item.parent
        anode = node.find('a')  
        title = anode.text.encode('utf-8').replace('&nbsp;','')
        link = anode['href']
        id = anode['title']
        renode = node.find('font', attrs={'color':'FF7F02'})
        re = '0'
        if renode :
            re = renode.text.encode('utf-8').replace('[','').replace(']','')
        name_node = node.find('div')
        name_node = name_node.nextSibling
        name = name_node.text.encode('utf-8')
        read_node = node.find('td', attrs={'width':'40', 'align':'right','class':'A12gray','style':'padding:0 5 0 0px'})
        read = read_node.text
        link = 'http://mlbpark.donga.com%s'%link
        lastid = id
        
        #print title,
        #print link,
        #print name
        #print id
        #print 're:[%s]'%re
        #print 'view:%s'%read
        #print node.prettify()
        r = checkDuplicate(board, id)
        if r > 0 :
            updateRVCount(board, id, re, read)
            continue

        (content ,has_image, has_youtube, has_flash ) = extractContents(board, id)
        print title , name 
        insertArticle(link, board, id, title , content , name, re, read, has_image, has_youtube, has_flash )
    return lastid



def extractContents(board, id) :
    d = getLoginURLDataResponse('http://mlbpark.donga.com/mbs/articleV.php?mbsC=%s&mbsIdx=%s'%(board, id))
    html = d.read()
    try:
        html = html.decode('cp949')
    except:
        pass
    html = html.replace('width:660px','')
    soup = BeautifulSoup.BeautifulSoup(html)
    contents = soup.findAll('body')

    if len(contents) == 2 :
        contents = contents[1]
    elif soup.find('div' , attrs={'align':'justify'}) :
        contents = soup.find('div' , attrs={'align':'justify'})
    else:
        return ['',0,0,0]
    
    img_count = 0;
    flash_count = 0
    youtube_count = 0


    imgs = contents.findAll('img')
    
    
    for img in imgs:
        path = img.get('src')
        new_path = path
        try:
            new_path=path
            new_path = saveImage(board, id, path )
        except:
            print 'error saveImage %s'%path
            continue
        #print path, new_path
        newTag = BeautifulSoup.Tag(soup,"img")
        if new_path.startswith('http') :
            newTag['src']=new_path
        else:
            newTag['src']='http://toors.cafe24.com/service/crawler/%s'%new_path
        img.replaceWith(newTag)
        img_count+=1
    
    embeds = contents.findAll('embed')
    for embed in embeds:
        path = embed.get('src')
        if path and path.find('youtube.com') != -1:
            youtube_count += 1
        else:
            flash_count +=1

    return [contents, img_count , youtube_count, flash_count ]
    

def saveImage(board, id , path):
    if not path :
        return ''
    if path.startswith('/'):
        path = 'http://mlbpark.donga.com%s'%path
    elif not path.startswith('http://') :
        path = 'http://mlbpark.donga.com/mbs/%s'%path
    
    if 1 :
        return path


    try:
        d = getLoginURLDataResponse(path)
    except:
        path = path.encode('utf-8')
        d = getLoginURLDataResponse(path)
        path = path.decode('utf-8')

    path = urllib.unquote(path)

    filename = path.split('/')[-1]
    if( len(filename) > 255 ):
        filename = filename[-100:]
    new_path = 'imgs/mlbpark_%s_%s_%s'%(board, id, filename)
    new_path = new_path.encode('utf-8')
    print new_path
    f = open(new_path , 'w')
    imgdata = d.read()
    f.write(imgdata)
    imgmd5 = md5.new(imgdata).hexdigest()
    insertImageinfo(board,id,new_path,imgmd5)
    try:
        new_path = urllib.quote(new_path)
    except:
        pass
    return new_path.decode('utf-8')

def insertImageinfo(board,id,path,imgmd5):
    cur = db.cursor()
    parent = 'mlbpark/%s/%s'%(board,id)
    cur.execute('insert into crdata_imgs (path,parent,md5) values (%s,%s,%s)', (path, parent, imgmd5))
    cur.close()

def checkDuplicate(board,id):
    cur = db.cursor()
    ret= cur.execute('select * from crdata_article where bbs=%s and no=%s', ('mlbpark/%s'%(board), id))
    cur.close()
    return ret

def updateRVCount(board, id, reply, view ):
    cur = db.cursor()
    cur.execute('update crdata_article set reply_count = %s , view_count = %s where bbs=%s and no=%s', (reply, view, 'mlbpark/%s'%board, id))
    cur.execute('update crdata_popular set reply_count = %s , view_count = %s where bbs=%s and no=%s', (reply, view, 'mlbpark/%s'%board, id))
    cur.close()

def insertArticle(link, board, id, title, content, name, reply_count, view_count, has_image, has_youtube, has_flash ):
    cur = db.cursor()
    cur.execute('insert into crdata_article (link, bbs, no, title, content, name, reply_count, view_count, is_pop, has_image, has_youtube, has_flash ) values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)', (link,'mlbpark/%s'%board, id , title, content, name, reply_count, view_count,0, has_image, has_youtube, has_flash))
    cur.close()

def deleteArticle( board, id ):
    cur = db.cursor()
    cur.execute('select * from crdata_imgs where parent = %s', 'mlbpark/%s/%s'%(board,id))
    r = cur.fetchall()
    for item in r :
        print item[1]
        try:
            os.remove(item[1])
        except:
            pass

    cur.execute('delete from crdata_imgs where parent = %s', 'mlbpark/%s/%s'%(board,id))
    cur.execute('delete from crdata_article where bbs = %s and no = %s', ('mlbpark/%s'%board, id))
    cur.close()

def checkPopularOldDelete( board , oldid ,reply, view):
    cur = db.cursor()
    r = cur.execute('update crdata_article set is_pop = 1, pop_date = CURRENT_TIMESTAMP where is_pop = 0 and bbs = %s and (reply_count > %s or view_count > %s)', ('mlbpark/%s'%board,reply,view) )
    print '%d article is popular'%r
    oldid = int(oldid)
    oldid -= 1000
    cur.execute('select * from crdata_article where is_pop = 0 and bbs = %s and no < %s', ('mlbpark/%s'%board ,oldid))
    r = cur.fetchall()
    for item in r:
        print item[3] , item[4]
        deleteArticle(board,item[3])

if __name__=='__main__':
    connectDB()
    lastid = 0
    for i in range(1,10):
        lastid = extractArticle('bullpen',i)    
    checkPopularOldDelete('bullpen',lastid, 25 , 2700)



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

def ppomppuLogin(userid, passwd):
    values = {'user_id':userid,'password':passwd}
    data = urllib.urlencode(values)
    loginurl = 'http://www.ppomppu.co.kr/zboard/login_check.php'
    request = urllib2.Request(loginurl, data)
    request.add_header('Referer', 'http://www.ppomppu.co.kr/')
    response = ClientCookie.urlopen(request)
    print response.read()

def getLoginURLDataResponse(url):
    request = urllib2.Request(url)
    request.add_header('Referer', url)
    response = ClientCookie.urlopen(request)
    return response

def extractArticle(board, page):
    d = getLoginURLDataResponse('http://www.ppomppu.co.kr/zboard/zboard.php?id=%s&page=%s'%(board,page))
    html = d.read()
    html = html.decode('cp949')
    soup = BeautifulSoup.BeautifulSoup(html)
    articles = soup.findAll('div' , attrs={'style':'width:80px;overflow:hidden;text-overflow:ellipsis', 'class':'list_name'}) 
    lastid = 0
    for item in articles:
        
        node = item.parent.parent
        name = ''
        name_node = node.find('a')
        if name_node.find('img') :
            name = name_node.find('img')['alt'].encode('utf-8')
        else:
            name = name_node.find('span').text.encode('utf-8')
        if name.startswith('관리자'):
            continue
        title = node.find('font', attrs={'class':"list_title"}).text.encode('utf-8')
        reply ='0'
        if node.find('span', attrs={'class':"list_comment2"}) :
            reply = node.find('span', attrs={'class':"list_comment2"}).text.encode('utf-8')
        elif node.find('span', attrs={'class':"list_comment"}) :
            reply = node.find('span', attrs={'class':"list_comment"}).text.encode('utf-8')
        #print reply
        read = node.findAll('td')[-1].text.encode('utf-8')
        link = ''
        no = ''
        links = node.findAll('a')
        for tmp in links :
            href = tmp['href']
            if href.startswith('view.php'):
                link = href
                break
        
        no = href.split('no=')[-1]
        link = 'http://ppomppu.co.kr/zboard/%s'%link

        r = checkDuplicate(board, no)
        lastid = no
        if r > 0 :
            updateRVCount(board, no, reply, read)
            continue
        
        (content ,has_image, has_youtube, has_flash ) = extractContents(board, no)
        print title , name 
        insertArticle(link, board, no, title , content , name, reply, read, has_image, has_youtube, has_flash )
    return lastid

def extractContents(board, id) :
    #d = getLoginURLDataResponse('http://ppomppu.co.kr/zboard/view.php?id=%s&no=%s'%(board, id))
    d = urllib.urlopen('http://ppomppu.co.kr/zboard/view.php?id=%s&no=%s'%(board, id))
    html = d.read()
    try:
        html = html.decode('cp949')
    except:
        pass
    idx = html.find('<!--DCM_BODY-->')
    if idx == -1 :
        return ['', 0 , 0, 0 ]
    html = html[idx+len('<!--DCM_BODY-->'):]
    idx= html.find('<!--/DCM_BODY-->')
    html = html[:idx]

    
    soup = BeautifulSoup.BeautifulSoup(html)
    contents = soup
    #print contents.prettify()
    img_count = 0;
    flash_count = 0
    youtube_count = 0

    
    imgs = contents.findAll('img')
    for img in imgs:
        img_count+=1
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
    
    if path.find('ppomppu') == -1 :
        return path

    try:
        d = getLoginURLDataResponse(path);
    except:
        path = path.encode('utf-8')
        d = getLoginURLDataResponse(path)
        path = path.decode('utf-8')

    path = urllib.unquote(path)

    filename = path.split('/')[-1]
    if( len(filename) > 255 ):
        filename = filename[-100:]
    new_path = 'imgs/ppomppu_%s_%s_%s'%(board, id, filename)
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
        print 'url quote error'
    return new_path.decode('utf-8')

def insertImageinfo(board,id,path,imgmd5):
    cur = db.cursor()
    parent = 'ppomppu/%s/%s'%(board,id)
    cur.execute('insert into crdata_imgs (path,parent,md5) values (%s,%s,%s)', (path, parent, imgmd5))
    cur.close()

def checkDuplicate(board,id):
    cur = db.cursor()
    ret= cur.execute('select * from crdata_article where bbs=%s and no=%s', ('ppomppu/%s'%(board), id))
    cur.close()
    return ret

def updateRVCount(board, id, reply, view ):
    cur = db.cursor()
    cur.execute('update crdata_article set reply_count = %s , view_count = %s where bbs=%s and no=%s', (reply, view, 'ppomppu/%s'%board, id))
    cur.execute('update crdata_popular set reply_count = %s , view_count = %s where bbs=%s and no=%s', (reply, view, 'ppomppu/%s'%board, id))
    cur.close()

def insertArticle(link, board, id, title, content, name, reply_count, view_count, has_image, has_youtube, has_flash ):
    cur = db.cursor()
    cur.execute('insert into crdata_article (link, bbs, no, title, content, name, reply_count, view_count, is_pop, has_image, has_youtube, has_flash ) values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)', (link,'ppomppu/%s'%board, id , title, content, name, reply_count, view_count,0, has_image, has_youtube, has_flash))
    cur.close()

def deleteArticle( board, id ):
    cur = db.cursor()
    cur.execute('select * from crdata_imgs where parent = %s', 'ppomppu/%s/%s'%(board,id))
    r = cur.fetchall()
    for item in r :
        print item[1]
        try:
            os.remove(item[1])
        except:
            pass

    cur.execute('delete from crdata_imgs where parent = %s', 'ppomppu/%s/%s'%(board,id))
    cur.execute('delete from crdata_article where bbs = %s and no = %s', ('ppomppu/%s'%board, id))
    cur.close()

def checkPopularOldDelete( board , oldid ,reply, view):
    cur = db.cursor()
    r = cur.execute('update crdata_article set is_pop = 1, pop_date = CURRENT_TIMESTAMP where is_pop = 0 and bbs = %s and (reply_count > %s or view_count > %s)', ('ppomppu/%s'%board,reply,view) )
    print '%d article is popular'%r
    oldid = int(oldid)
    oldid -= 3000
    cur.execute('select * from crdata_article where is_pop = 0 and bbs = %s and no < %s', ('ppomppu/%s'%board ,oldid))
    r = cur.fetchall()
    for item in r:
        print item[3] , item[4]
        deleteArticle(board,item[3])

if __name__=='__main__':
    connectDB()
    lastid = 0
    for i in range(1,8):
        lastid = extractArticle('freeboard',i)
    checkPopularOldDelete('freeboard', lastid, 25, 2800)
    
    for i in range(1,10):
        lastid = extractArticle('humor',i)
    checkPopularOldDelete('humor', lastid, 28, 3000)
    ppomppuLogin(dbpass.ppomppu['id'],dbpass.ppomppu['passwd'])

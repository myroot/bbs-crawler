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

def extractArticle(board):
    d = getLoginURLDataResponse('http://www.slrclub.com/')
    html = d.read()
    html = html.decode('cp949')
    soup = BeautifulSoup.BeautifulSoup(html)
    articles = soup.find('div',id='issue-free').findAll('li')
    for item in articles:
        title = item.find('a').text
        link = item.find('a')['href']
        item_id = link.split('no=')[1]
        

        r = checkDuplicate(board, item_id)
        if r > 0 :
            continue

        (content ,has_image, has_youtube, has_flash, title, nick) = extractContents(board,item_id)
        #print item_id, title       
        #title = title.encode('utf-8')
        link = 'http://www.slrclub.com'+link
        user = nick
        reply = 0
        read = 0
        #print content
        insertArticle(link, board, item_id, title , content , user, reply, read, has_image, has_youtube, has_flash )


def extractContents(board, no):
    d = getLoginURLDataResponse('http://www.slrclub.com/bbs/vx2.php?id=%s&no=%s'%(board,no))
    html = d.read()
    html = html.decode('cp949')
    soup = BeautifulSoup.BeautifulSoup(html)
    content = soup.find('div', id='userct')
    if content == None :
        return ['error',0,0,0]
    
    title = soup.find('td',{'width':'771','align':'left','colspan':7}).find('b').contents[0]
    #print title
    nick = soup.find('td',{'width':'351','align':'left'}).find('span').contents[0]
    #print nick
    
    content = content.findAll('td')[1]
    imgs = content.findAll('img')
    img_count = 0;
    flash_count = 0
    youtube_count = 0
    for img in imgs:
        img_count+=1
        
        path = img.get('src')


        if path.find('slrclub') == -1 :
            continue

        new_path = saveImage(board, no, path )
        
        newTag = BeautifulSoup.Tag(soup,"img")
        if new_path.startswith('http') :
            newTag['src']=new_path
        else:
            newTag['src']='http://toors.cafe24.com//service/crawler/%s'%new_path
        img.replaceWith(newTag)
    
    embeds = content.findAll('embed')
    for embed in embeds:
        path = embed.get('src')
        print path
        if path and path.find('youtube.com') != -1:
            youtube_count += 1
        else:
            flash_count +=1
    
    return [content, img_count , youtube_count, flash_count, title, nick ]

def saveImage(board, id , path):
    if not path :
        return ''
    try:
        d = getLoginURLDataResponse(path)
    except:
        path = path.encode('utf-8')
        try:
            d = getLoginURLDataResponse(path)
        except :
            return path.decode('utf-8')
        path = path.decode('utf-8')
    path = urllib.unquote(path)
    #print '----saveImage----'
    #print path
    filename = path.split('/')[-1]
    
    if( len(filename) > 20 ):
        filename = filename[-20:]

    #mid_path = 'imgs/slr_%s_%s_%s'.encode('utf-8')
    #new_path = mid_path%(board, id, filename)
    new_path = 'imgs/slr_%s_%s_%s'%(board, id, filename)
    new_path = new_path.encode('utf-8')
    f = open(new_path , 'w')
    imgdata = d.read()
    f.write(imgdata)
    imgmd5 = md5.new(imgdata).hexdigest()
    insertImageinfo(board,id,new_path,imgmd5)
    new_path = urllib.quote(new_path)
    return new_path.decode('utf-8')

def insertImageinfo(board,id,path,imgmd5):
    cur = db.cursor()
    parent = 'slr/%s/%s'%(board,id)
    cur.execute('insert into crdata_imgs (path,parent,md5) values (%s,%s,%s)', (path, parent, imgmd5))
    cur.close()

def checkDuplicate(board,id):
    cur = db.cursor()
    ret= cur.execute('select * from crdata_article where bbs=%s and no=%s', ('slr/%s'%(board), id))
    cur.close()
    return ret

def updateRVCount(board, id, reply, view ):
    cur = db.cursor()
    cur.execute('update crdata_article set reply_count = %s , view_count = %s where bbs=%s and no=%s', (reply, view, 'slr/%s'%board, id))
    cur.execute('update crdata_popular set reply_count = %s , view_count = %s where bbs=%s and no=%s', (reply, view, 'slr/%s'%board, id))
    cur.close()

def insertArticle(link, board, id, title, content, name, reply_count, view_count, has_image, has_youtube, has_flash ):
    cur = db.cursor()
    cur.execute('insert into crdata_article (link, bbs, no, title, content, name, reply_count, view_count, is_pop, has_image, has_youtube, has_flash ) values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)', (link,'slr/%s'%board, id , title, content, name, reply_count, view_count,1, has_image, has_youtube, has_flash))
    cur.close()

def deleteArticle( board, id ):
    cur = db.cursor()
    cur.execute('select * from crdata_imgs where parent = %s', 'slr/%s/%s'%(board,id))
    r = cur.fetchall()
    for item in r :
        print item[1]
        try:
            os.remove(item[1])
        except:
            pass

    cur.execute('delete from crdata_imgs where parent = %s', 'slr/%s/%s'%(board,id))
    cur.execute('delete from crdata_article where bbs = %s and no = %s', ('slr/%s'%board, id))
    cur.close()

def checkPopularOldDelete( board , oldid ,reply, view):
    cur = db.cursor()
    r = cur.execute('update crdata_article set is_pop = 1, pop_date = CURRENT_TIMESTAMP where is_pop = 0 and bbs = %s and (reply_count > %s or view_count > %s)', ('slr/%s'%board,reply,view) )
    print '%d article is popular'%r
    oldid = int(oldid)
    oldid -= 25000
    cur.execute('select * from crdata_article where is_pop = 0 and bbs = %s and no < %s', ('slr/%s'%board ,oldid))
    r = cur.fetchall()
    for item in r:
        print item[3] , item[4]
        deleteArticle(board,item[3])


if __name__=='__main__':
    connectDB()
    extractArticle('free')
    #extractContents('free', '18522997','test')

    #checkPopularOldDelete('free', lastid, 30, 1800)

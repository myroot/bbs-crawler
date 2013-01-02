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

refind = re.compile('\[[^\]]*\]')
stripre = lambda x: refind.sub('', x)

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

def clienLogin(userid, passwd):
    values = {'mb_id':userid,'mb_password':passwd}  
    data = urllib.urlencode(values)
    loginurl = 'http://clien.career.co.kr/cs2/bbs/login_check.php'
    request = urllib2.Request(loginurl, data)
    request.add_header('Referer', 'http://clien.career.co.kr/')
    request.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US) AppleWebKit/525.13 (KHTML, like Gecko) Chrome/0.2.149.29 Safari/525.13')
    response = ClientCookie.urlopen(request)
    #print response.read()

def getLoginURLDataResponse(url):
    request = urllib2.Request(url)
    request.add_header('Referer', url)
    request.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US) AppleWebKit/525.13 (KHTML, like Gecko) Chrome/0.2.149.29 Safari/525.13')
    response = ClientCookie.urlopen(request)
    return response

def extractArticle(board, page):
    #d = getLoginURLDataResponse('http://abyss.jaram.org/wrapper.php?type=txt&url=http://clien.career.co.kr/cs2/bbs/board.php?bo_table=%s&page=%d'%(board,page))
    d = getLoginURLDataResponse('http://relay-request.appspot.com/r?rq=http://clien.career.co.kr/cs2/bbs/board.php?bo_table=%s&page=%d'%(board,page))
    raw = d.read()
    idx = raw.find('<meta property="og:description" content="')
    if idx :
        pre = raw[:idx]
        idx2 = raw[idx+41:].find('>')
        post = raw[idx+41+idx2:]
        raw = pre+post
    soup = BeautifulSoup.BeautifulSoup(raw)
    articles = soup.findAll('tr', attrs={'class':"mytr"})
    lastid = 0
    #print 'extract article %d'%len(articles)
    for item in articles:
        try:
            #title = item.contents[5].contents[1].contents[0]
            title = item.find('td', attrs={'class':'post_subject'}).text.encode('utf-8').replace('&nbsp;','')
            title = stripre(title)
            #link = item.contents[5].contents[1].get('href')
            link = item.find('a')['href']
            link = link.replace('../', 'http://clien.career.co.kr/cs2/')
            #user = item.contents[7].contents[0].get('title')
            #user = item.findAll('a')[1].get('title').encode('utf-8')
            user = item.find('td', attrs={'class':'post_name'})
            if user.find('img') :
                user = user.find('img')
                user['src'] = 'http://clien.career.co.kr/'+user['src']
            else:
                user = user.find('span')
                user = user.text.encode('utf-8')

            id = link.split('wr_id=')[1]
            id = id.split('&')[0]
            lastid = id
            print title, 
            print user
        except :
            print 'error 1'
            continue
        try:
            replyNum = item.find('td', attrs={'class':'post_subject'}).find('span').text
        except:
            replyNum = '[0]'
        readCount = item.findAll('td')[-1].text
        replyNum = replyNum.replace('[','').replace(']','')

        #print title , user 

        r = checkDuplicate(board, id)
        if r > 0 :
            updateRVCount(board, id, replyNum, readCount)
            continue

        (content ,has_image, has_youtube, has_flash ) = extractContents(board, id)
        print title , user 
        insertArticle(link, board, id, title , content , user, replyNum, readCount, has_image, has_youtube, has_flash )
    return lastid

def extractContents(board, id) :
    d = getLoginURLDataResponse('http://abyss.jaram.org/wrapper.php?type=txt&url=http://clien.career.co.kr/cs2/bbs/board.php?bo_table=%s&wr_id=%s'%(board, id))
    raw = d.read()
    idx = raw.find('<meta property="og:description" content="')
    if idx :
        pre = raw[:idx]
        idx2 = raw[idx+41:].find('>')
        post = raw[idx+41+idx2:]
        raw = pre+post
    soup = BeautifulSoup.BeautifulSoup(raw)
    #soup = BeautifulSoup.BeautifulSoup(d)
    contents = soup.find("div" , id="resContents")
    rel = contents.find('div', attrs={'class':"ccl"})
    sig = contents.find('div', attrs={'class':'signature'})
    if sig : sig.extract()
    if rel : rel.extract()
    img_count = 0;
    flash_count = 0
    youtube_count = 0
    
    imgs = contents.findAll('img')
    for img in imgs:
        path = img.get('src')
        new_path = path
        try:
            new_path = saveImage(board, id, path )
        except:
            print 'error saveImage %s'%path
            continue
        print path, new_path
        newTag = BeautifulSoup.Tag(soup,"img")
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
    if path.startswith('../') :
        path = path.replace('../','http://abyss.jaram.org/wrapper.php?type=txt&url=http://clien.career.co.kr/cs2/')
    try:
        d = getLoginURLDataResponse(path);
    except:
        path = path.encode('utf-8')
        d = getLoginURLDataResponse(path);
        path = path.decode('utf-8')
    
    filename = path.split('/')[-1]
    if( len(filename) > 255 ):
        filename = filename[-100:]
    new_path = 'imgs/clien_%s_%s_%s'%(board, id, filename)
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
    parent = 'clien/%s/%s'%(board,id)
    cur.execute('insert into crdata_imgs (path,parent,md5) values (%s,%s,%s)', (path, parent, imgmd5))
    cur.close()

def checkDuplicate(board,id):
    cur = db.cursor()
    ret= cur.execute('select id from crdata_article where bbs=%s and no=%s', ('clien/%s'%(board), id))
    cur.close()
    return ret

def updateRVCount(board, id, reply, view ):
    cur = db.cursor()
    cur.execute('update crdata_article set reply_count = %s , view_count = %s where bbs=%s and no=%s', (reply, view, 'clien/%s'%board, id))
    cur.execute('update crdata_popular set reply_count = %s , view_count = %s where bbs=%s and no=%s', (reply, view, 'clien/%s'%board, id))
    cur.close()

def insertArticle(link, board, id, title, content, name, reply_count, view_count, has_image, has_youtube, has_flash ):
    cur = db.cursor()
    cur.execute('insert into crdata_article (link, bbs, no, title, content, name, reply_count, view_count, is_pop, has_image, has_youtube, has_flash ) values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)', (link,'clien/%s'%board, id , title, content, name, reply_count, view_count,0, has_image, has_youtube, has_flash))
    cur.close()

def deleteArticle( board, id ):
    cur = db.cursor()
    cur.execute('select * from crdata_imgs where parent = %s', 'clien/%s/%s'%(board,id))
    r = cur.fetchall()
    for item in r :
        print item[1]
        try:
            os.remove(item[1])
        except:
            pass

    cur.execute('delete from crdata_imgs where parent = %s', 'clien/%s/%s'%(board,id))
    cur.execute('delete from crdata_article where bbs = %s and no = %s', ('clien/%s'%board, id))
    cur.close()

def checkPopularOldDelete( board , oldid ,reply, view):
    cur = db.cursor()
    r = cur.execute('update crdata_article set is_pop = 1, pop_date = CURRENT_TIMESTAMP where is_pop = 0 and bbs = %s and (reply_count > %s or view_count > %s)', ('clien/%s'%board,reply,view) )
    print '%d article is popular'%r
    oldid = int(oldid)
    oldid -= 5000
    cur.execute('select * from crdata_article where is_pop = 0 and bbs = %s and no < %s', ('clien/%s'%board ,oldid))
    r = cur.fetchall()
    for item in r:
        print item[3] , item[4]
        deleteArticle(board,item[3])

if __name__=='__main__':
    connectDB()
    lastid = 0
    for i in range(1,10):
        try:
            lastid = extractArticle('park',i)
        except:
            pass
    checkPopularOldDelete('park', lastid, 25, 2700)
    lastid = 0
    for i in range(1,3):
        try:
            lastid = extractArticle('news', i);
        except:
            pass
    checkPopularOldDelete('news', lastid, 100, 10000)

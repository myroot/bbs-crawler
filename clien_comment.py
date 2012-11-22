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
#import MySQLdb
import md5

tagfind = re.compile(r'<a[^>]*>')
stripatag = lambda x: tagfind.sub('', x)

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

def test_getComments(board, id):
    #d = getLoginURLDataResponse('http://clien.career.co.kr/cs2/bbs/board.php?bo_table=park&wr_id=6718653&page=5')
    d = getLoginURLDataResponse('http://abyss.jaram.org/wrapper.php?type=txt&url=http://m.clien.career.co.kr/cs3/board?bo_table=%s&bo_style=view&wr_id=%s'%(board,id))
    raw = d.read()
    #print raw
    #chunk = '<body topmargin="0" leftmargin="0" >'
    chunk = '<meta property="og:description" content="'
    idx = raw.find(chunk)
    if idx :
        pre = raw[:idx]
        idx2 = raw[idx+len(chunk):].find('>')
        post = raw[idx+len(chunk)+idx2:]
        raw = pre+post
    chunkstart = '<div class="reply">'
    chunkend = '</section>'
    idx = raw.find(chunkstart)
    if idx == -1 :
        return '삭제된 글입니다'
    raw = raw[idx:]
    idx = raw.find(chunkend)
    raw = raw[:idx]
    raw = raw.replace('/data/member/', 'http://m.clien.career.co.kr/data/member/')
    raw = stripatag(raw)
    raw = raw.replace('</a>','')
    css  ='<style>'
    css +='.reply{margin-top:7px}'
    css +='.reply_txt{font-size:13px;padding:5px 4px}'
    css +='.reply_user{color:#00264f}'
    css +='.reply_hd{height:28px;padding:0 5px;background:-webkit-gradient(linear,left bottom,left top,from(#b4b8bf),color-stop(0.99,#dddee1),to(#fff));border-top:1px solid #eee;border-bottom:1px solid #757f90;line-height:28px;box-shadow:0 1px 0 #666;-webkit-box-shadow:0 1px 0 #ccc}'
    css +='.reply_date{font-size:12px;color:#808ea0}'
    css +='</style>'
    raw = raw.replace('<script','<none')
    return css+raw

if __name__=='__main__':
    print "Content-Type: text/plain\n";
    form = cgi.FieldStorage()
    board= ''
    id = ''
    try:
        board = form['board'].value
        id = form['id'].value
    except:
        print 'error'
    
    print test_getComments(board, id);

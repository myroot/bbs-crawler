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
import json

def slrLogin(userid, passwd):
    values = {'user_id':userid,'password':passwd}   
    data = urllib.urlencode(values)
    loginurl = 'http://www.slrclub.com/login/process.php'
    request = urllib2.Request(loginurl, data)
    request.add_header('Referer', 'http://www.slrclub.com/')
    response = ClientCookie.urlopen(request)
    #print response.read()

def getLoginURLDataResponse(url):
    request = urllib2.Request(url)
    request.add_header('Referer', url)
    request.add_header('User-Agent','Mozilla/4.0 (compatible;)')
    response = ClientCookie.urlopen(request)
    return response

def getArticleCommentID(board, id):
    d = getLoginURLDataResponse('http://www.slrclub.com/bbs/vx2.php?id=%s&no=%s'%(board, id))
    html = d.read()

    idx = html.find('data-cmrno=\"')
    if idx == -1:
        return ''
    html = html[idx+len('data-cmrno=\"'):]
    idx = html.find('\"')
    commentid = html[:idx]
    return commentid

def getComments2(board, id):
    commentid = getArticleCommentID(board,id)
    if commentid == '' :
        return '삭제된글입니다.'
        
    parm = urllib.urlencode({'id':board, 'no':commentid, 'sno':1,'spl':'300', 'mno':'1'})
    request = urllib2.Request('http://www.slrclub.com/bbs/mobile_cmt/load.php', parm)
    request.add_header('Referer', 'http://www.slrclub.com/bbs/vx2.php?id=%s&no=%s'%(board,id))
    d  =  urllib2.urlopen(request)
    soup = BeautifulSoup.BeautifulSoup(d)
    return soup.prettify()
    

def getComments(board, id):
    commentid = getArticleCommentID(board,id)
    #print 'comment id = '+commentid
    if commentid == '' :
        print '삭제된글입니다.'
        return
    parm = urllib.urlencode({'id':board, 'no':commentid, 'sno':1,'spl':'300', 'mno':'1'})
    request = urllib2.Request('http://www.slrclub.com/bbs/comment_db/load.php', parm)
    request.add_header('Referer', 'http://www.slrclub.com/bbs/vx2.php?id=%s&no=%s'%(board,id))
    request.add_header('User-Agent','Mozilla/4.0 (compatible;)')
    d  =  urllib2.urlopen(request)
    comments = json.load(d)
    try:
        for item in comments['c']:
            item['name'] = item['name'].encode('utf-8')
            item['memo'] = item['memo'].encode('utf-8')
            print '<p>'
            print '<b>%s</b>'%item['name']
            print '<br>'
            print item['memo']
            print '</p>'
    except Exception,e:
        print e
    #soup = BeautifulSoup.BeautifulSoup(d)
    #print soup.prettify()
    #comments = soup.findAll('table')
    #for comment in comments:
    #    name = comment.find('span')
    #    if not name :
    #        continue
    #    name = name.text.encode('utf-8')
    #    txt = comment.find('td', attrs={'align':"left", 'class':"cmt_td"})
    #    print '<p>'
    #    print '<b>%s</b>'%name
    #    print '<br>'
    #    print txt
    #    print '</p>'

        

if __name__=='__main__':
    print "Content-Type: text/plain\n";
    form = cgi.FieldStorage()
    board= 'free'
    id = '15533022'
    id = '25017117'
    try:
        board = form['board'].value
        id = form['id'].value
    except:
        print 'error'

    getComments(board, id);
    

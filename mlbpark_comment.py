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
import md5

def getLoginURLDataResponse(url):
    request = urllib2.Request(url)
    request.add_header('Referer', url)
    response = ClientCookie.urlopen(request)
    return response

def getComments(board, id):
    #url = 'http://ppomppu.co.kr/zboard/list_comment.php?id=%s&no=%s'%(board,id)
    url = 'http://mlbpark.donga.com/mbs/articleV.php?mbsC=%s&mbsIdx=%s'%(board,id)
    html = urllib.urlopen(url)
    html = html.read()
    html = html.decode('cp949')
    soup = BeautifulSoup.BeautifulSoup(html)
    
    comment = soup.find('div', id='myArea')
    if not comment :
        print '삭제된 글입니다.'
        return
    comment = comment.find('table')
    comments = comment.findAll('table', attrs={'width':'97%', 'border':'0', 'cellspacing':'0', 'cellpadding':'0', 'style':'word-break:break-all'})
    for item in comments:
        print '<p>'
        print item.contents[1].contents[1].find('a').text.encode('utf-8')
        print '<br>'
        print item.contents[1].contents[3].findAll('td')[1]
        #for text in item.contents[1].contents[3].findAll('td')[1].contents:
        #   try:
        #       print text.encode('utf-8').strip()
        #   except:
        #       pass
        print '</p>'

if __name__=='__main__':
    print "Content-Type: text/plain\n";
    form = cgi.FieldStorage()
    board= 'bullpen'
    id = '41705'
    try:
        board = form['board'].value
        id = form['id'].value
    except:
        print 'error'
    

    getComments(board, id);
    

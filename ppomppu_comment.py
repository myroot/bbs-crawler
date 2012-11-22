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
	url = 'http://m.ppomppu.co.kr/new/bbs_view.php?id=%s&no=%s'%(board,id)
	html = urllib.urlopen(url)
	html = html.read()
	html = html.decode('cp949')
	soup = BeautifulSoup.BeautifulSoup(html)
	comments = soup.find('div', attrs={'class':"cmAr"})
	if not comments :
		return '삭제된 글입니다.'
	comment = comments.findAll('div', attrs={'class':'sect'})
	for item in comment:
		item.find('a')['href'] = '#'
		
	return comments #.replace('/new/asset/', 'http://m.ppomppu.co.kr/new/asset/').replace('/images/', 'http://m.ppomppu.co.kr/images/')
if __name__=='__main__':
	print "Content-Type: text/plain\n";
	form = cgi.FieldStorage()
	board= 'free'
	id = '15533022'
	try:
		board = form['board'].value
		id = form['id'].value
	except:
		print 'error'

	print str(getComments(board, id)).replace('/new/asset/', 'http://m.ppomppu.co.kr/new/asset/').replace('/images/reply_new_head.gif', 'http://m.ppomppu.co.kr/images/reply_new_head.gif')
	

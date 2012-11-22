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

def copyPopularArticle( ) :
    cur = db.cursor()
    cur.execute('select * from crdata_article where is_pop = 1 and is_copied = 0 order by date asc')
    r = cur.fetchall()
    for item in r :
        #print item[4]
        copyArticle(item[0], item[1],item[2],item[3],item[4],item[5],item[6],item[7], item[8],item[10],item[11],item[12],item[14])

    cur.close()

def copyArticle(originid,link,bbs,no,title,content,name,reply_count,view_count,has_image,has_youtube,has_flash,origin_date ):
    cur = db.cursor()
    cur.execute('update crdata_article set is_copied = 1 where id = %s', originid)
    cur.execute('insert into crdata_popular (origin_id,link, bbs, no, title, content, name, reply_count, view_count, has_image, has_youtube, has_flash, origin_date ) values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)', (originid,link,bbs,no,title,content,name, reply_count, view_count,has_image, has_youtube, has_flash, origin_date))
    cur.close()

def temp():
    cur = db.cursor()
    cur.execute('SELECT count(*) as cnt , md5,parent FROM `crdata_imgs` group by md5 having cnt > 1 ORDER BY `cnt`  DESC');
    r = cur.fetchall()
    for item in r:
        #print item[0],item[1],item[2]
        ret = cur.execute('select * from crdata_imgs where parent like %s and md5 like %s',(item[2],item[1]))
        if ret > 1 :
            cur.execute('delete from crdata_imgs where parent like %s and md5 like %s limit %s',(item[2],item[1],ret-1))


if __name__=='__main__':
    connectDB()
    copyPopularArticle()
    #temp()

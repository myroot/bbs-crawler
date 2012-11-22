#!/usr/bin/python
# -*- coding: utf-8 -*-
import time
import MySQLdb
import os
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


def deleteArticle( bbs, id , no):
    cur = db.cursor()
    cur.execute('select * from crdata_imgs where parent = %s', '%s/%s'%(bbs,no))
    r = cur.fetchall()
    for item in r :
        print item[1]
        try:
            os.remove(item[1])
        except:
            pass

    cur.execute('delete from crdata_imgs where parent = %s', '%s/%s'%(bbs,no))
    cur.execute('delete from crdata_article where id = %s', id )
    cur.execute('delete from crdata_popular where origin_id = %s', id )
    cur.close()


def delete_old_img():
    tm = time.localtime(time.time()-(60*60*24*30))
    cur = db.cursor()
    cur.execute('select * from crdata_imgs where date < %s', ('%d-%d-%d'%(tm[0],tm[1],tm[2])))
    r = cur.fetchall()
    for item in r:
        print item[1]
        try:
            os.remove(item[1])
        except:
            pass
    cur.execute('delete from crdata_imgs where date < %s', ('%d-%d-%d'%(tm[0],tm[1],tm[2])))
    

def delete_oldpop():
    tm = time.localtime(time.time()-(60*60*24*30))
    cur = db.cursor()
    cur.execute('select * from crdata_article where date < %s', ('%d-%d-%d'%(tm[0],tm[1],tm[2])))
    r = cur.fetchall()
    for item in r:
        print item[0], item[2], item[3] , item[4], item[14]
        deleteArticle(item[2],item[0],item[3]) 


if __name__ == '__main__':
    connectDB()
    delete_oldpop()
    delete_old_img()


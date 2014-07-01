#import urllib
import urllib2
import MySQLdb
import json
import pdb
import urllib
import subprocess
import time
from bs4 import BeautifulSoup

class NailShopCrawler():
    def __init__(self):
        self.init_database()

    def init_database(self):
        mysqlHost = '127.0.0.1'
        UserName = 'root'
        mysqlPassword = 'demitase'
        DBName = 'girlsday'
        self.db = MySQLdb.connect(host=mysqlHost, user=UserName, passwd=mysqlPassword, db=DBName)
        self.db.set_character_set('utf8')
        charset = self.db.character_set_name()
        self.cursor = self.db.cursor(MySQLdb.cursors.DictCursor)

    def get_store_num(self,code):
        query = "select num from t_store where ucode='%s'" % code
        self.cursor.execute(query)
        row = self.cursor.fetchone()
        global store_num
        if row:
            store_num = row['num']
        else:
            store_num = 0

    def crawling(self):
        #query = "insert into t_store(ucode,store_name,address,tel,homepage,latitude,longitude,review_count,review_average) value('%s','%s','%s','%s','%s','%s','%s','%s','%s')"
        query = "insert into t_store(ucode,store_name,address,tel,homepage,latitude,longitude,review_count,review_average) value('%s','%s','%s','%s','%s','%f','%f','%d','%f')"
        thum_query = "insert into t_store_photo(store_num,photo_url) value('%s','%s')"
        url = "http://map.naver.com/search2/local.nhn?query=%EB%84%A4%EC%9D%BC%EC%95%84%ED%8A%B8&page="
        user_agent = 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)'
        headers = { 'User-Agent' : user_agent }
        for i in range(1,500):
            seed = url + str(i)
#            pdb.set_trace()
            r = urllib2.Request(seed, headers=headers)
            j_data = json.loads(urllib2.urlopen(r,timeout = 10).read())
#            j_data = json.loads(urllib.urlopen(seed).read())
            for list_j in j_data['result']['site']['list']:
                print list_j['id']
                print list_j['name'].encode('utf-8')
                print list_j['tel']
                print list_j['address'].encode('utf-8')
                print list_j['review']
                print list_j['reviewScore']
                print list_j['thumUrl']
                print list_j['x']
                print list_j['y']
                print list_j['homePage']
                try:
#                    self.cursor.execute(query,(list_j['id'],list_j['name'],list_j['address'],list_j['tel'],list_j['homePage'],float(list_j['x']),float(list_j['y']),int(list_j['review']),float(list_j['reviewScore'])))
                    self.cursor.execute(query % (list_j['id'],list_j['name'],list_j['address'],list_j['tel'],list_j['homePage'],float(list_j['x']),float(list_j['y']),int(list_j['review']),float(list_j['reviewScore'])))

                    self.db.commit()
                    self.get_store_num(list_j['id'])
                    if list_j['thumUrl']:
                        self.cursor.execute(thum_query % (store_num,list_j['thumUrl']))
                        self.db.commit()
                    self.viewshop(list_j['id'].split('s')[1])
                except Exception:
                    continue
            
    def viewshop(self,code):
        query = "insert t_review(store_num,content,review_point) values('%s','%s',%f)"
        referer_url = 'http://map.naver.com/local/siteview.nhn?code='
#        comment_url = 'http://map.naver.com/comments/list_comment.nhn'
        form_data = 'ticket=map1&object_id=%s&_ts=1404105309078&page_no=1'
#        form_data = urllib.urlencode({'ticket': 'map1','object_id':'11816153','_ts':'1404105309078','page_no':'1'})
#        header = {"Referer" : referer_url + code}
#        req = urllib2.Request(comment_url, form_data, header)

        proc = subprocess.Popen(["curl","--referer",referer_url + code,"http://map.naver.com/comments/list_comment.nhn","-XPOST","-d",form_data % code],stdout=subprocess.PIPE)
        (out, err) = proc.communicate()
        try:
            review_data = json.loads(out)
        except Exception:
            return

        for rd in review_data['comment_list']:
            try:
                self.cursor.execute(query %(store_num,rd['contents'],float(rd['object_score'])))
                self.db.commit()
            except Exception:
                continue

        self.crawl_thumbnail(referer_url + code)

    def crawl_thumbnail(self, s_url):
        thum_query = "insert into t_store_photo(store_num,photo_url) value('%s','%s')"
        headers = { 'User-Agent' : 'Mozilla/5.0' }
        req = urllib2.Request(s_url, None, headers)
        html = urllib2.urlopen(req).read()
        soup = BeautifulSoup(html) 
        if soup.find('a',{'class':'_thumbImg'}):
            for th_img in soup.findAll('a',{'class':'_thumbImg'}):
                try:
                    self.cursor.execute(thum_query % (store_num,th_img.find('img')['src']))
                    self.db.commit()
                except Exception:
                    continue
        

if __name__ == "__main__":
    mycrawler = NailShopCrawler()
    mycrawler.crawling()


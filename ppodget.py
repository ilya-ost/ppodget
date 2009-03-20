#! /usr/bin/env python2.5
# -*- coding: utf-8 -*- 

from __future__ import with_statement
import feedparser
import sys
import os
import string
import urllib
import re
import codecs
from mutagen.easyid3 import EasyID3
import cPickle as pickle

feed_file_name = os.path.expanduser(u"~/.ppodget/feeds.urls")
base_file_name = os.path.expanduser(u"~/.ppodget/ppodbase")
downdir = os.path.expanduser(u"~/audio/podcasts/")

def download(pod, base):
    directory = downdir + pod['name'].replace('"', '')
    # print pod['type']
    if pod['type'] == u'audio/mpeg':
        extension = u'.mp3'
    elif pod['type'] == 'application/ogg':
        extension = u'.ogg'
    elif pod['type'] == 'audio/x-mp3':
        extension = u'.mp3'
    elif pod['type'] == 'video/quicktime':
        extension = u'.mov'
    else:
        extension = u'.void'
    try:
        os.mkdir(downdir)
    except:
        pass
    try:
        os.mkdir(directory)
    except:
        pass
    if pod['url'][len(pod['url'])-4:] in ['.mp3','.ogg','m4a']:
        extension = pod['url'][len(pod['url'])-4:]
    filename = directory + u"/" + pod['title'].replace('"', '').replace('/', '') + extension
    try:
        print filename
        
        class Rep(object):
            def __init__(self):
                self.count = 0
                
            def report(self, count, blksize, totalsize):
                if  int(100 * count * blksize / float(totalsize)) - self.count >= 10:
                    print str(int (100 * count * blksize / float(totalsize))) + "%",
                    sys.stdout.flush()
                    self.count = int (100 * count * blksize / float(totalsize))
                    
        urllib.urlretrieve(pod['url'], filename, Rep().report)
        if extension == '.mp3':
            tag = EasyID3(filename)
            tag["title"] = filename[:-4]
            tag["album"] = directory
            tag["artist"] = directory
            tag.save()

        base.append(pod['id'])
    except Exception, ex:
        print ex
        print filename + ": error"
            
def update(pod, base):
    base.append(pod['id'])

def show_pod(pod):
    print "-" * 50
    print pod['title']
    print pod['id']

def getpods(feeds, base, podcast_id):
    for name, url in feeds:
        d = feedparser.parse(url)
        for entry in d.entries:
            if 'id' in entry:
                p_id = entry.id
            else:
                p_id = entry.link
            if 'enclosures' in entry:
                for e in entry.enclosures:
                    if not p_id in base and (podcast_id == 'all' or podcast_id == p_id):
                        yield {'name': name,
                               'title': entry.title,
                               'id': p_id,
                               'url': e['href'],
                               'type': e['type']}

usage_message = 'usage: ppodget.py update podcast_number | all\n\
                  download podcast_id | all\n\
                  download_feed feed_number\n\
                  show_new\n\
                  show_feeds\n\
                  del_feed feed_number | all\n\
                  add_feed name url'

def show_feeds(feeds):
    if len(feeds) == 0:
        print "No feeds"
    else:
        for i, f in enumerate(feeds):
            print "-" * 50
            print "%d\t%s" % (i + 1, f[0])
            print "\t%s" % (f[1])

if __name__ == "__main__":
    args = ('update', 'download', 'show_new',
            'add_feed', 'show_feeds', 'del_feed',
            'download_feed')

    if len(sys.argv) < 2:
        print usage_message
        sys.exit()
    else:
        if sys.argv[1] in args:
            op = sys.argv[1]
        else:
            print usage_message
            sys.exit()
    feeds = []
    if os.path.exists(feed_file_name):
        with open(feed_file_name) as f:
            feeds = pickle.load(f)
    if op == 'add_feed':
        if len(sys.argv) == 4:
            feeds.append((unicode(sys.argv[2]),sys.argv[3])) # name, url
            with open(feed_file_name, 'w') as f:
                pickle.dump(feeds, f)
            show_feeds(feeds)
            sys.exit()
        else:
            print usage_message
            sys.exit()
    if op == 'del_feed':
        if len(sys.argv) < 3:
            print usage_message
            sys.exit()
        else:
            if sys.argv[2] == 'all':
                feeds = []
            else:
                feed_number = int(sys.argv[2])
                if len(feeds) >= feed_number > 0:
                    del feeds[feed_number - 1]
                    show_feeds(feeds)
                else:
                    print "No feed N " + str(feed_number)
                    show_feeds(feeds)
            with open(feed_file_name, 'w') as f:
                pickle.dump(feeds, f)
            sys.exit()
    if op == 'show_feeds':
        show_feeds(feeds)
        sys.exit()
    if op in ('update', 'download', 'show_new', 'download_feed'):
        if len(sys.argv) == 3:
            if op == 'download_feed':
                feed_number = int(sys.argv[2])
            else:
                podcast_id = sys.argv[2]
        elif op == 'show_new':
            podcast_id = 'all'
        else:
            print usage_message
            sys.exit()
        base = []
        if os.path.exists(base_file_name):
            with open(base_file_name) as f:
                base = pickle.load(f)
        if op == 'download_feed':
            for pod in getpods(feeds[(feed_number - 1):feed_number], base, 'all'):
                download(pod, base)
        if op == 'update':
            for pod in getpods(feeds, base, podcast_id):
                update(pod, base)
        elif op == 'download':
            for pod in getpods(feeds, base, podcast_id):
                download(pod, base)
        elif op == 'show_new':
            for pod in getpods(feeds, base, podcast_id):
                show_pod(pod)
        with open(base_file_name, 'w') as f:
            pickle.dump(base, f)

#!/usr/bin/env python
# -*- coding: utf-8 -*-

import tweepy
import Queue
import time
import auth
from HTMLParser import HTMLParser

import logging
import re
from oyoyo.client import IRCClient
from oyoyo.cmdhandler import DefaultCommandHandler
from oyoyo import helpers

##CUSTOMIZE_THIS_START
HOST = 'irc.freenode.net'
PORT = 6667
NICK = 'Jtwitt'
CHANNEL = '#Jeanne_D\'Hack'

WHITELIST = [ "moebius_eye", "Mydym", "skelkey", "sybix", "Vigdis", "xoomed", "y0no", "Lotto", "chiropter", "grab", "Trium" ]
RELAYBOT_NAMES = ['RelayB','RelayB`','RelayB_']
##CUSTOMIZE_THIS_END

def twitt ( nick, chan, to_say ) :
    global api
    global cli
    ## Si on a la place d'ajouter une signature, on le fait.
    if len(to_say) > 0 and len( "%s -- %s" % (to_say , nick) ) <= 140 :
      to_say = "%s -- %s" % (to_say , nick)
      
    ## Si le message est à la bonne taille
    if  0 < len(to_say) and len(to_say) <= 140 :
      ## Envoyer le twitt et confirmer sur le canal
      try:
        api.update_status(to_say)
        print('Saying, "%s"' % to_say)
        helpers.msg(cli, chan, '>%s > Twitt envoyé' % nick )
        return True
      except:
        helpers.msg(cli, chan, '>%s > Erreur non prévisible. Ooops.' % nick )
      
    ## Sinon, signaler l'erreur
    elif len(to_say) > 140:
      helpers.msg(cli, chan, '>%s > Twitt trop long (%d char)' % ( nick, len(to_say) ) )
    elif len(to_say) <= 0:
      helpers.msg(cli, chan, '>%s > Syntax: !say <message> | Interdiction d\'envoyer un twitt vide.' % nick )



class StreamWatcherListener(tweepy.StreamListener):

    def __init__(self, status_queue):
        super( StreamWatcherListener, self ).__init__()
        self.status_queue = status_queue

    def on_status(self, status):
        try:
            print 'new tweet'
            print status.text
            self.status_queue.put(status)
        except:
            ## Catch any unicode errors while printing to console
            ## and just ignore them to avoid breaking application.
            pass

    def on_error(self, status_code):
        print 'An error has occured! Status code = %s' % status_code
        if status_code == '420':
            time.sleep(5)
            return False
        return True  # keep stream alive

    def on_timeout(self):
        print 'Snoozing Zzzzzz'



class MyHandler(DefaultCommandHandler):
    def privmsg(self, nick_extended, chan, msg):
        global api
        global cli
        global denied_cmd
        global respond_to
        
        ## Getting "nick" from "nick!user@domain" string
        nick = re.match('(.*)\!', nick_extended).group(1).strip()
        
        ## Making sure the user is in the whitelist
        ## by (1) : checking that the user is in the list
        if nick not in RELAYBOT_NAMES:
          
          match = re.match('\!([a-z]*)(.*)', msg)
          if match:
            cmd = match.group(1).strip()
            to_say = match.group(2).strip()
            print cmd, nick, to_say
            
        else:
        
          ## or by (2) : checking that the relayed user is in the list
          match = re.match('<(.*)\@.*> \!([a-z]*)(.*)', msg)
          if match:
            cmd = match.group(1).strip()
            nick = match.group(2).strip()
            to_say = match.group(3).strip()
            print cmd, nick, to_say
            
        if match and cmd in ["say","accept","respond"] and nick not in WHITELIST and nick not in RELAYBOT_NAMES:
          match = False
          denied_cmd = msg
          helpers.msg(cli, chan, u">%s > Vous n\'ètes pas dans la liste blanche. Une whitelisté peut !accept votre commande." % nick )
        
        ## Si la commande a été comprise
        if match:
          if cmd == "say":
              twitt( nick, chan, to_say )
          elif cmd == "accept":
              try:
                self.privmsg( nick_extended, chan, denied_cmd )
              except:
                helpers.msg(cli, chan, u">%s > Rien à accepter " % nick )
          elif cmd == "respond":
              twitt( nick, chan, "@%s %s" % ( respond_to ,to_say ) )
          else:
              helpers.msg(cli, chan, u">%s > commandes prises en charge: !say <msg> | !respond <msg> | !accept " % nick)
        else:
          print "Parsing error"
          
    def kick( self, kickernick, chan, mynick, reason ):
        print "kick: %s " % reason
        if reason not in ["perma","permanent","perm","flood","flooding"] :
          time.sleep(2)
          helpers.join(cli, CHANNEL)

    def error( self, nick, reason ):
        print "error: %s " % reason
        try:
          time.sleep(2)
          helpers.join(cli, CHANNEL)
        except:
          main()

    def quit( self, nick, reason ):
        try:
          try:
            ircinit()
            print "ircinit success"
            main()
          except:
            print "ircinit or main failure"
            try:
              main()
            except:
              print "\"You get nothing done\" -- Axl' Rose"
              pass
        except:
          print "something went wrong."
        helpers.join(cli, CHANNEL)

def connect_cb(cli):
    helpers.join(cli, CHANNEL)


def main():
    global conn
    global respond_to
    i = 0
    old_id = 0
    start = time.time()
    while True:
        time.sleep(0.1)
        if i < 200:
            i+=1
        if i == 100:
            print 'joining'
            helpers.join(cli, CHANNEL)
        if i == 200:
            print 'joining'
            helpers.join(cli, CHANNEL)
            i+=1
        if i > 200:
            mentions = []
            if time.time() - start > 10 :
              start = time.time()
              print "getting goodies"
              try:
                mentions = api.mentions()
                mentions = mentions[:1] ## Get only the last mention
              except:
                mentions = []
                pass
            mentions.reverse()
            for mention in mentions:
                if mention.id > old_id :
                  text = HTMLParser().unescape(mention.text)
                  helpers.msg(cli, CHANNEL, '@%s nous dis : %s' % (mention.author.screen_name , text) )
                  respond_to = mention.author.screen_name
                  old_id = mention.id + 1
        try:
            item = status_queue.get(False)
            print str(item.author.screen_name)
            if str(item.author.screen_name) != NICK:
                helpers.msg(cli, CHANNEL, str(item.author.screen_name)+' -- '+str(item.text))
                api.update_status(str(item.author.screen_name)+' -- '+str(item.text))
        except KeyboardInterrupt:
          print "Interrupted"
          exit()
        except:
            pass
        conn.next()      ## python 2


def ircinit():
    global conn
    global cli
    ## Setting IRC cli.
    logging.basicConfig(level=logging.DEBUG)
    cli = IRCClient(MyHandler, host=HOST, port=PORT, nick=NICK)#,connect_cb=connect_cb)
    conn = cli.connect()


if __name__ == '__main__':
    status_queue = Queue.Queue()

    ##CUSTOMIZE_THIS_START
    consumer_key    = auth.consumer_key    
    consumer_secret = auth.consumer_secret 
    key             = auth.key             
    secret          = auth.secret          
    ##CUSTOMIZE_THIS_END

    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(key, secret)
    api = tweepy.API(auth)
    stream = tweepy.Stream(auth=auth, listener=StreamWatcherListener(status_queue))

    ##CUSTOMIZE_THIS_START
    follow_list = ['jeanne_DHack']
    ##CUSTOMIZE_THIS_END


    ## Setting IRC cli.
    ircinit()
    
    track_list = []
    stream.filter(follow_list, track_list, True)
    try:
      main()
    except KeyboardInterrupt:
      print "Interrupted"
      exit()





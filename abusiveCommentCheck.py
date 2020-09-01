import praw
from profanity import profanity
import sqlite3
import os
from datetime import datetime
import math
import logging
try:
    import profanity_check as pc
except Exception as e:
    logging.warning(e, 'Couldn\'t import profanity-check')

class abusiveCommentBot:

    def __init__(self):
        self.reddit = None
        self.subreddit = None
        
        self.database_name = 'reddit'
        self.table_name = 'comments'
        
        self.set_reply = "This contains abuse, so your comment has been deleted, child-safe : "
        self.set_replyV2 = "This contains abuse, but we don't have a child-safe version, better to skip this comment\n\n"
        self.confidence = "We can say this with a confidence of {}\n\n"
        self.new_line_reply = "If you still want to read it as it is, do it at your own discretion : "
        self.insert_sql = "insert into " + self.table_name + " values(?,?,?) "
        self.select_idw_sql = "select * from " + self.table_name + " where id= ?"
        self.update_idwpc_sql = "update " + self.table_name + " set processedCount = ? " + " where id = ?" 
        
        
        self.conn = sqlite3.connect(self.database_name)
        self.c = self.conn.cursor()

        self.create_table = 'create table if not exists ' + self.table_name + ' (id text primary key, time timestamp, processedCount integer)'
        self.c.execute(self.create_table)
    
    def getCredentials(self, credentialFile = 'credentials.txt'):
        '''
        Obtaining credentials from credentials.txt and sending them back
        for login
        '''
        f = open(credentialFile)
        self.client_id, self.client_secret, self.username, \
            self.password, self.user_agent = f.readline().split(',')
        f.close()

    def login(self):
        '''
        Login function
        '''
        self.reddit = praw.Reddit(client_id=self.client_id,
                                  client_secret=self.client_secret,
                                  username=self.username,
                                  password=self.password,
                                  user_agent=self.user_agent)

        if self.reddit is not None:
            logging.debug('Reddit Object created successfully')

    def truncate(self,num, ndigits):
        return math.floor(num * 10 ** ndigits) / 10 ** ndigits
    
    def chosenSubreddits(self):
        '''
        These subreddits have the bot running
        '''
        self.subreddit = self.reddit.subreddit('ReportAbuseBot')  
        logging.debug('Subreddit chosen')

    def streamComments(self):
        '''
        Checking comments
        '''
        me = self.reddit.user.me()
        for comment in self.subreddit.stream.comments():
            pred, prob = None, None
            try:
                pred = pc.predict([comment.body])
                prob = pc.predict_prob([comment.body])
            except Exception as e:
                logging.info(e + '\n\nError with profanity-check')
            if profanity.contains_profanity(comment.body) and comment.author != me:
                self.c.execute(self.select_idw_sql,(comment.id,))
                data = self.c.fetchall()
                if len(data) == 0:
                    multiline = comment.body.split('\n')
                    if len(multiline) > 1:
                        try:
                            multiline = list(filter(('').__ne__, multiline))
                        except:
                            pass
                        for i in range(len(multiline)-1):
                            multiline[i] = multiline[i] + '  \n'
                        com = ''.join(multiline) 
                        if prob is not None:
                            comment.reply(self.set_reply + '\n\n' + str(profanity.censor(comment.body)) + '\n\n' + self.confidence.format(self.truncate(prob[0],3)) + self.new_line_reply + '\n\n>!' + com + '!<')
                        else:
                            comment.reply(self.set_reply + '\n\n' + str(profanity.censor(comment.body)) + '\n\n' + self.new_line_reply + '\n\n>!' + com + '!<')
                    else:
                        if prob is not None:
                            comment.reply(self.set_reply + str(profanity.censor(comment.body)) + '\n\n' + self.confidence.format(self.truncate(prob[0],3)) + self.new_line_reply + '>!' + comment.body + '!<')
                        else:
                            comment.reply(self.set_reply + str(profanity.censor(comment.body)) + '\n\n' + self.new_line_reply + '>!' + comment.body + '!<')
                    self.c.execute(self.insert_sql,(comment.id, datetime.now(),1))
                    comment.mod.remove(mod_note = "This is a censored comment")            
                    logging.debug("Detected by profanity: " + str(comment.body) + str(pred) + str(prob))

                else:
                    self.c.execute(self.update_idwpc_sql,(data[0][2]+1,comment.id,))
                    
            elif pred and pred[0] > 0.9 and comment.author != me:
                self.c.execute(self.select_idw_sql,(comment.id,))
                data = self.c.fetchall()
                if len(data) == 0:
                    multiline = comment.body.split('\n')
                    if len(multiline) > 1:
                        try:
                            multiline = list(filter(('').__ne__, multiline))
                        except:
                            pass
                        for i in range(len(multiline)-1):
                            multiline[i] = multiline[i] + '  \n'
                        com = ''.join(multiline) 
                        if prob is not None:
                            comment.reply(self.set_replyV2 + '\n\n' + self.confidence.format(self.truncate(prob[0],3)) + self.new_line_reply + '\n\n>!' + com + '!<')
                        else:
                            comment.reply(self.set_replyV2 + '\n\n' + self.new_line_reply + '\n\n>!' + com + '!<')
                    else:
                        if prob is not None:
                            comment.reply(self.set_replyV2 + '\n\n' + self.confidence.format(self.truncate(prob[0],3)) + self.new_line_reply + '>!' + comment.body + '!<')
                        else:
                            comment.reply(self.set_replyV2 + '\n\n' + self.new_line_reply + '>!' + comment.body + '!<')
                    self.c.execute(self.insert_sql,(comment.id, datetime.now(),1))
                    comment.mod.remove(mod_note = "This is a protected comment")            
                    logging.debug("Detected by profanity-check: " + str(comment.body) + str(pred) + str(prob))

                else:
                    self.c.execute(self.update_idwpc_sql,(data[0][2]+1,comment.id,))

            self.conn.commit()

        self.conn.commit()
        self.c.close()

if __name__ == "__main__":
    # Setting up logger
    logFile = 'abusiveCommentBot.log'
    os.remove(logFile)
    logForm = '%(asctime)s.%(msecs)03d %(levelname)s %(module)s -\
%(funcName)s: %(message)s'

    logging.basicConfig(filename=logFile,
                        filemode='a',
                        format=logForm,
                        datefmt='%Y-%m-%d %H:%M:%S',
                        level=logging.DEBUG)

    BOT = abusiveCommentBot()

    BOT.getCredentials()
    BOT.login()
    BOT.chosenSubreddits()
    BOT.streamComments()

import praw
from profanity import profanity
import sqlite3
import os
from datetime import datetime

f = open('credentials.txt')
client_id, client_secret, username, password, user_agent = f.readline().split(',')
f.close()

database_name = 'reddit'
table_name = 'comments'

conn = sqlite3.connect(database_name)
c = conn.cursor()

create_table = 'create table if not exists ' + table_name + ' (id text primary key, time timestamp, processedCount integer)'
c.execute(create_table)

reddit = praw.Reddit(client_id = client_id, client_secret = client_secret, username = username, password = password, user_agent = user_agent)

subreddit = reddit.subreddit('ReportAbuseBot')

print(subreddit)

me = reddit.user.me()

set_reply = "This contains abuse, so your comment has been deleted, child-safe : "
new_line_reply = "If you still want to read it as it is, do it at your own discretion : "
insert_sql = "insert into " + table_name + " values(?,?,?) "
select_idw_sql = "select * from " + table_name + " where id= ?"
update_idwpc_sql = "update " + table_name + " set processedCount = ? " + " where id = ?" 

for comment in subreddit.stream.comments():
    if profanity.contains_profanity(comment.body) and comment.author != me:
        c.execute(select_idw_sql,(comment.id,))
        data = c.fetchall()
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
                comment.reply(set_reply + '\n\n' + str(profanity.censor(comment.body)) + '\n\n' + new_line_reply + '\n\n>!' + com + '!<')
            else:
                comment.reply(set_reply + str(profanity.censor(comment.body)) + '\n\n' + new_line_reply + '>!' + comment.body + '!<')
            c.execute(insert_sql,(comment.id, datetime.now(),1))
            comment.mod.remove(mod_note = "This is a censored comment") 
            print("Done")
        else:
            c.execute(update_idwpc_sql,(data[0][2]+1,comment.id,))
            print("Comment already processed ", data)
    else:
        pass
    conn.commit()

conn.commit()
c.close()
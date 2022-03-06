import pymysql
from itertools import chain

scope_list = {'banking':['transaction_data', 'financial_data'],
                'public':['Public_data'],
                'medical':['medical_data']}

schema = {'transaction_data':[('transaction_data', 'varchar(30)', ''),
                        ('financial_SSN', 'int', 'UNIQUE NOT NULL'),
                        ('deposit_amount', 'int', ''),
                        ('withdrawal_amount', 'int', '')], 
            'financial_data':[('financial_SSN', 'int', 'UNIQUE NOT NULL'),
                        ('Account', 'int', ''),
                        ('balance', 'int', '')], 
            'Public_data':[('Public_SSN', 'int', 'UNIQUE NOT NULL'),
                        ('Relation', 'varchar(30)', ''), 
                        ('Relation_name', 'varchar(30)', ''), 
                        ('Relation_DOB', 'varchar(30)', ''), 
                        ('relation_SSN', 'int', ''), 
                        ('SEX', 'varchar(30)', '')], 
            'medical_data':[('medical_SSN', 'varchar(30)', 'UNIQUE NOT NULL'), 
                        ('data_time', 'varchar(30)', ''), 
                        ('image_path', 'varchar(30)', '')]}

table_list = list(chain(*scope_list.values()))
assert(table_list == list(schema.keys()))

class Control:
    def __init__(self, db, cur):
        self.db = db
        self.cur = cur

    def add_user(self, new_id, new_pw):
        sql  = "INSERT INTO user (id, pw) "
        sql += "VALUES ('%s', '%s')"%(new_id, new_pw)
        self.cur.execute(sql)

        sql  = "INSERT INTO token (id) "
        sql += "VALUES ('%s')"%(new_id)
        self.cur.execute(sql)

        self.db.commit()

    def get_user(self, id, pw):
        sql  = "SELECT id FROM user WHERE "
        sql += "id = '%s' AND pw = '%s'"%(id, pw)
        count = self.cur.execute(sql)
        result = self.cur.fetchall()
        if count == 1:
            return result[0][0]
        else:
            return None

    def add_token(self, id, scope, token, expire):
        sql  = "UPDATE token "
        sql += "SET %s_token = '%s', "%(scope, token)
        sql += "%s_expire = %d "%(scope, expire)
        sql += "WHERE id = '%s'"%(id)
        self.cur.execute(sql)
        self.db.commit()
    
    def del_token(self, id, scope):
        pass
    
    def get_data(self, id, scope):
        pass

def init_db():
    # create database operator;
    # create user operator@localhost identified by 'mysql_pw';
    # grant all on operator.* to operator@localhost;

    ### connect db
    db = pymysql.connect(host='localhost', user='operator', passwd='mysql_pw', db='operator', charset='utf8')
    cur = db.cursor()

    ### creat table "user"
    sql  = "CREATE TABLE IF NOT EXISTS user ("
    sql += "id varchar(20) UNIQUE NOT NULL, "
    sql += "pw varchar(20) NOT NULL)"
    cur.execute(sql)

    ### create table "token"
    sql  = "CREATE TABLE IF NOT EXISTS token ("
    sql += "id varchar(20) UNIQUE NOT NULL, "
    for scope in scope_list.keys():
        sql += "%s_token char(22), %s_expire int, "%(scope, scope)
    sql = sql[:-2] + ')'
    cur.execute(sql)

    ### create data tables as specified by "schema"
    for table_name in table_list:
        sql  = "CREATE TABLE IF NOT EXISTS %s ("%(table_name)
        for column, type, option in schema[table_name]:
            sql += "%s %s %s, "%(column, type, option)
        sql = sql[:-2] + ')'
        cur.execute(sql)

    db.commit()

    return Control(db, cur)
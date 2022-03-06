import pymysql

scope_list = {'banking':[], 
            'public':[], 
            'medical':[]}

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
        scope_prefix = scope[0] + '_'  # ex) 'banking' -> 'b_'
        sql  = "UPDATE token "
        sql += "SET %stoken = '%s', "%(scope_prefix, token)
        sql += "%sexpire = %d "%(scope_prefix, expire)
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
    sql += "b_token char(22), b_expire int, "
    sql += "p_token char(22), p_expire int, "
    sql += "m_token char(22), m_expire int)"
    cur.execute(sql)

    db.commit()

    return Control(db, cur)
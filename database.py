import pymysql
from itertools import chain
import time

scope_list = {'financial_data':['transaction_data', 'financial_data'],
                'public_data':['public_data'],
                'medical_data':['medical_data']}

url_list_front = {'financial_data':'http://163.152.30.239:8080/financial',
                'public_data':'http://163.152.30.239:8080/public',
                'medical_data':'http://163.152.30.239:8080/medical'}

url_list_back = {'financial_data':'http://163.152.30.239:3000/api/financial',
                'public_data':'http://163.152.30.239:3000/api/public',
                'medical_data':'http://163.152.30.239:3000/api/medical'}

schema = {'public_data':[('user_id', 'varchar(50)', ''),
                        ('name', 'varchar(20)', ''),
                        ('relation', 'varchar(10)', ''),
                        ('birth', 'date', ''),
                        ('ssn', 'varchar(15)', ''),
                        ('sex', 'enum(\'F\',\'M\')', '')],
            'financial_data':[('user_id', 'varchar(50)', ''),
                        ('account', 'varchar(20)', ''),
                        ('balance', 'bigint', '')],
            'transaction_data':[('user_id', 'varchar(50)', ''),
                        ('date_time', 'varchar(50)', ''),
                        ('deposit_amount', 'bigint', ''),
                        ('withdrawal_amount', 'bigint', '')], 
            'medical_data':[('user_id', 'varchar(50)', ''), 
                        ('date_time', 'varchar(50)', ''), 
                        ('image_path', 'varchar(200)', '')]}

table_list = set(chain(*scope_list.values()))
assert(table_list == set(schema.keys()))
assert(set(url_list_front.keys()) == set(scope_list.keys()))
assert(set(url_list_back.keys()) == set(scope_list.keys()))

class Control:
    def __init__(self, db, cur):
        self.db = db
        self.cur = cur

    def add_user(self, new_id, new_pw):
        ### add user info into db
        sql  = "INSERT INTO user (id, pw) "
        sql += "VALUES ('%s', '%s')"%(new_id, new_pw)
        self.cur.execute(sql)

        self.db.commit()
        
        return "success"

    def get_user(self, id, pw):
        ### get user id from db
        sql  = "SELECT id FROM user WHERE "
        sql += "id = '%s' AND pw = '%s'"%(id, pw)
        count = self.cur.execute(sql)
        result = self.cur.fetchall()
        if count == 1:
            return result[0][0]
        else:
            return None

    def add_token(self, id, scope, token, expire):
        ### delete old token
        self.del_token(id, scope)

        ### add token into db
        sql  = "INSERT INTO token (id, scope, token, expire) "
        sql += "VALUES ('%s', '%s', '%s', %d)"%(id, scope, token, expire)
        self.cur.execute(sql)
        self.db.commit()
        return "success"
    
    def get_token(self, id, scope):
        ### get token from db if exists & not expired
        sql  = "SELECT token, expire "
        sql += "FROM token "
        sql += "WHERE id = '%s' and scope = '%s'"%(id, scope)
        count = self.cur.execute(sql)
        result = self.cur.fetchall()
        
        if count == 1:
            token = result[0][0]
            expire = result[0][1]
            if int(time.time()) <= expire:
                return token
            else:
                return "token expired"
        else:
            return None
    
    def del_token(self, id, scope):
        ### delete token from db
        sql  = "DELETE FROM token "
        sql += "WHERE id='%s' AND scope='%s'"%(id, scope)
        count = self.cur.execute(sql)
        self.db.commit()
        
        return count

    def add_data(self, id, scope, data):
        ### delete old data
        self.del_data(id, scope)

        ### add data into db
        table_names = list(data)
        for table_name in table_names:
            for d in data[table_name]:
                columns = list(d)
                vals = [d[x] for x in columns]
                sql  = "INSERT INTO %s "%(table_name)
                sql += "(id, " + ", ".join(columns) + ") "
                sql += "VALUES ('%s',"%(id) + str(vals)[1:-1] + ")"
                print(sql)
                self.cur.execute(sql)
        
        self.db.commit()
        
        return "success"
    
    def get_data(self, id, scope):
        ### get data from db
        data = {}
        for table_name in scope_list[scope]:
            print(table_name)
            columns = [x[0] for x in schema[table_name]]
            sql  = "SELECT " + ', '.join(columns) + ' '
            sql += "FROM %s "%(table_name)
            sql += "WHERE id = '%s'"%(id)
            count = self.cur.execute(sql)
            result = self.cur.fetchall()

            data[table_name] = []
            for i in range(count):
                d = {}
                for j in range(len(columns)):
                    d[columns[j]] = result[i][j]
                data[table_name].append(d)
            
        return data
    
    def del_data(self, id, scope):
        ### delete data from db
        count = 0
        for table_name in scope_list[scope]:
            sql  = "DELETE FROM %s "%(table_name)
            sql += "WHERE id = '%s'"%(id)
            count += self.cur.execute(sql)

        self.db.commit()

        return count

    def __del__(self):
        self.db.close()

def init_db():
    # create database operator;
    # create user operator@localhost identified by 'mysql_pw';
    # grant all on operator.* to operator@localhost;

    ### connect db
    db = pymysql.connect(host='localhost', user='operator', passwd='mysql_pw', db='operator', charset='utf8')
    cur = db.cursor()

    ### creat table "user"
    sql  = "CREATE TABLE IF NOT EXISTS user ("
    sql += "id varchar(50) UNIQUE NOT NULL, "
    sql += "pw varchar(50) NOT NULL)"
    cur.execute(sql)

    ### create table "token"
    sql  = "CREATE TABLE IF NOT EXISTS token ("
    sql += "id varchar(50) NOT NULL, "
    sql += "scope varchar(20), "
    sql += "token char(22), "
    sql += "expire int )"
    cur.execute(sql)

    ### create data tables as specified by "schema"
    for table_name in table_list:
        sql  = "CREATE TABLE IF NOT EXISTS %s ("%(table_name)
        sql += "id varchar(50) NOT NULL, "
        for column, type, option in schema[table_name]:
            sql += "%s %s %s, "%(column, type, option)
        sql = sql[:-2] + ')'
        cur.execute(sql)

    db.commit()

    return Control(db, cur)

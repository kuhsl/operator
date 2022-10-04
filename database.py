import pymysql
from itertools import chain
import time
from logging.config import dictConfig



dictConfig({
    'version': 1,
    'formatters': {
        'default': {
            'format': '[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
        }
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'test_error.log',
            'maxBytes': 1024 * 1024 * 5,  # 5 MB
            'backupCount': 5,
            'formatter': 'default',
        },
    },
    'root': {
        'level': 'INFO',
        'handlers': ['file']
    }
})


scope_list = {'financial_data':['transaction_data', 'financial_data'],
                'public_data':['public_data'],
                'medical_data':['medical_data']}

url_list_front = {'financial_data':'http://163.152.71.223:8000/financial',
                'public_data':'http://163.152.71.223:8000/public',
                'medical_data':'http://163.152.71.223:8000/medical'}

url_list_back = {'financial_data':'https://163.152.71.223/api/financial',
                'public_data':'https://163.152.71.223/api/public',
                'medical_data':'https://163.152.71.223/api/medical'}

schema = {'public_data':[('user_id', 'varchar(50)', ''),
                        ('name', 'varchar(20)', ''),
                        ('relations', 'varchar(200)', ''),
                        ('address', 'varchar(50)', ''),
                        ('birth', 'date', ''),
                        ('ssn', 'varchar(15)', ''),
                        ('sex', 'enum(\'F\',\'M\')', '')],
            'financial_data':[('user_id', 'varchar(50)', ''),
                        ('account', 'varchar(20)', ''),
                        ('balance', 'bigint', ''),
                        ('ssn', 'varchar(15)', '')],
            'transaction_data':[('user_id', 'varchar(50)', ''),
                        ('date_time', 'varchar(50)', ''),
                        ('deposit_amount', 'bigint', ''),
                        ('withdrawal_amount', 'bigint', '')],
            'medical_data':[('user_id', 'varchar(50)', ''),
                        ('name', 'varchar(20)', ''),
                        ('sex', 'enum(\'F\',\'M\')', ''),
                        ('ssn', 'varchar(15)', ''),
                        ('date_time', 'varchar(50)', ''),
                        ('recovered', 'enum(\'Y\',\'N\')', ''),
                        ('disease_name', 'varchar(30)', ''),
                        ('disease_num', 'varchar(30)', ''),
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

    def add_pubkey(self, id, pkey):
        ### add pubkey into db

        sql  = "SELECT id FROM user WHERE "
        sql += "id = '%s'"%id
        count = self.cur.execute(sql)
        if count != 1: #when id doesn't exist in db
            return

        sql  = "UPDATE user SET pubkey = '%s' "%pkey
        sql += "WHERE id = '%s'"%id
        self.cur.execute(sql)
        self.db.commit()

        return "success"

    def get_pubkey(self, id):
        ### get pubkey from db
        sql = "SELECT pubkey FROM user WHERE "
        sql += "id = '%s'"%id
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
                self.cur.execute(sql)

        self.db.commit()

        return "success"

    def get_data(self, id, scope):
        ### get data from db

        ### data format ###
        # {
        #     'table1' : [
        #         { 'attribute1':'data11',
        #             'attribute2':'data12',
        #             'attribute3':'data13' },
        #         { 'attribute1':'data21',
        #             'attribute2':'data22',
        #             'attribute3':'data23' } ],
        #     'table2' : [
        #         { 'attribute4':'data41',
        #             'attribute5':'data42' } ]
        # }

        data = {}
        for table_name in scope_list[scope]:
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
    # CREATE DATABASE operator_platform;
    # CREATE USER admin@localhost IDENTIFIED BY 'mysql_pw' with grant option;
    # GRANT ALL ON operator_platfom.* TO admin@localhost;

    ## CREATE USER operator@localhost IDENTIFIED BY 'mysql_pw';
    ## CREATE USER middleware@localhost IDENTIFIED BY 'mysql_pw';

    ### connect db
    db = pymysql.connect(host='localhost', user='admin', passwd='mysql_pw', db='operator_platform', charset='utf8')
    cur = db.cursor()

    ### creat table "user"
    sql  = "CREATE TABLE IF NOT EXISTS user ("
    sql += "id varchar(50) UNIQUE NOT NULL, "
    sql += "pw varchar(200) NOT NULL, "
    sql += "pubkey varchar(1024) )"
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
        sql  = "CREATE TABLE IF NOT EXISTS %s ("%table_name
        sql += "id varchar(50) NOT NULL, "
        sql += "enc_data text, "
        sql += "idx int )"                                ## idx : not for use // use if len(enc_data) > 1000
        cur.execute(sql)

    db.commit()

    ## GRANT SELECT, INSERT, DELETE ON operator_platform.user TO operator@localhost;
    ## GRANT SELECT ON operator_platform.user TO operator@localhost;
    ## GRANT SELECT, INSERT, DELETE ON operator_platform.user TO middleware@localhost;

    ### grant priv to operator
    cur.execute("GRANT SELECT, INSERT, DELETE ON operator_platform.user TO operator@localhost")
    for table_name in table_list:
        cur.execute("GRANT SELECT ON operator_platform.%s TO operator@localhost"%table_name)

    ### grant priv to middleware
    cur.execute("GRANT SELECT, INSERT, DELETE ON operator_platform.user TO middleware@localhost")
    for table_name in table_list:
        cur.execute("GRANT SELECT, INSERT, DELETE ON operator_platform.%s TO middleware@localhost"%table_name)
    cur.execute("GRANT SELECT, INSERT, DELETE ON operator_platform.token TO middleware@localhost")

    db.commit()
    
    ### connect db (operator, middleware)
    app_db = pymysql.connect(host='localhost', user='operator', passwd='mysql_pw', db='operator_platform', charset='utf8')
    app_cur = app_db.cursor()
    mid_db = pymysql.connect(host='localhost', user='middleware', passwd='mysql_pw', db='operator_platform', charset='utf8')
    mid_cur = mid_db.cursor()

    return Control(app_db, app_cur), Control(mid_db, mid_cur)

 
    

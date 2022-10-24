from flask import Flask, request, redirect, jsonify, make_response
import pymysql
import pandas as pd
import numpy as np
from IPython.display import display 
import warnings

warnings.filterwarnings(action='ignore')

disease_list=['I10','R81','E66']

app = Flask(__name__)

### connect db
#conn = pymysql.connect(host='163.152.71.223', user='localhost', passwd='mysql_pw', db='operator', charset='utf8')
#conn = pymysql.connect(host='localhost', user='root', passwd='hw147258369!', db='db-server', charset='utf8')
conn = pymysql.connect(host='localhost', user='operator', passwd='mysql_pw', db='operator', charset='utf8')

def refresh_data():
    
    pass

def engine1_internal(disease_num):

    refresh_data()

    sql="SELECT a.name, a.ssn, relations, FLOOR((CHAR_LENGTH(relations)-CHAR_LENGTH(REPLACE(relations, 'c:','')))/2) AS child_cnt, disease_num FROM public_data a JOIN medical_data b ON a.ssn=b.ssn WHERE disease_num='"+disease_num+"' ORDER BY BIRTH ASC"

    df=pd.read_sql(sql, con=conn)

    #display(df)
    
    cnt=0
    total=0
    for index, row in df.iterrows():
        #check if he or she has any child
        if(row.child_cnt==0) :
            continue

        total+=1
        #parse person
        parsed=row.relations.split(';')
        #exclude spouse
        parsed=parsed[1:-1]

        #filter ssn
        child_ssn_list=[]  
        for child in parsed :
            child_ssn_list.append(child.split(':')[1])
        #print(child_ssn_list)

        #check each child's medical factors
        for ssn in child_ssn_list:
            total+=1
            cnt += check_child(ssn,conn,disease_num)
    
    if(total==0) :
        #print('No data for disease(',disease_num,') : Can not proceed analysis')
        res = -1
    else : 
        #print('Analysis of disease(',disease_num,')has been finished successfully. \nTotal :',total,' cnt : ',cnt,' ',(cnt/total)*100,'%')
        res = round((cnt/total)*100, 2)

    #print(res)
    
    return res

def check_child(ssn,conn,disease_num):

    sql="SELECT a.name, a.ssn, relations, FLOOR((CHAR_LENGTH(relations)-CHAR_LENGTH(REPLACE(relations, 'c:','')))/2) AS child_cnt FROM public_data a JOIN medical_data b ON a.ssn=b.ssn WHERE disease_num='"+disease_num+"' and a.ssn='"+ssn+"'"
    df=pd.read_sql(sql, con=conn)

    #check whether he has the same disease
    if(len(df)>0) :
        return 1
    else:
        return 0

def engine1():
    result = {}
    for disease_num in disease_list :
        result[disease_num] = engine1_internal(disease_num)

    return result

@app.get('/')
def run():
    return make_response(json.dumps(engine1(), ensure_ascii = False))

if __name__ == '__main__':
    try:
        app.run(host='0.0.0.0', port=80, debug=False)
    finally:
        conn.close()

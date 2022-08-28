import pymysql
import pandas as pd
import numpy as np
from IPython.display import display 
import warnings

warnings.filterwarnings(action='ignore')

def engine3():
    ### connect db
    conn = pymysql.connect(host='163.152.30.239', user='root', passwd='hw147258369!', db='db-server', charset='utf8')
    cur = conn.cursor()

    #sql="SELECT name, a.ssn, FLOOR((CHAR_LENGTH(relations)-CHAR_LENGTH(REPLACE(relations, 'c:','')))/2) as child_cnt, balance FROM public_data a JOIN financial_data b ON a.ssn=b.ssn"
    sql="SELECT FLOOR((CHAR_LENGTH(relations)-CHAR_LENGTH(REPLACE(relations, 'c:','')))/2) as child_cnt, balance FROM public_data a JOIN financial_data b ON a.ssn=b.ssn"

    df=pd.read_sql(sql, con=conn)
    df=df.set_index('balance')

    display(df)
    print(df.to_dict())
    return df.to_dict()

def run():
    engine3()

if __name__ == '__main__':
    run()
import pymysql
import pandas as pd
import numpy as np
from IPython.display import display
import warnings

warnings.filterwarnings(action='ignore')

labels=['label1','label2','label3']

def engine2():
    result={}
    ### connect db
    #conn = pymysql.connect(host='163.152.71.223', user='root', passwd='hw147258369!', db='db-server', charset='utf8')
    conn = pymysql.connect(host='localhost', user='operator', passwd='mysql_pw', db='operator', charset='utf8')
    #conn = pymysql.connect(host='localhost', user='root', passwd='hw147258369!', db='db-server', charset='utf8')
    cur = conn.cursor()

    sql="SELECT balance, disease_num FROM financial_data a LEFT OUTER JOIN medical_data b ON a.ssn=b.ssn ORDER BY balance ASC"
    #sql="SELECT balance, disease_num FROM financial_data a JOIN medical_data b ON a.ssn=b.ssn WHERE disease_num IN ('I10','R81','E66') ORDER BY balance ASC"

    df=pd.read_sql(sql, con=conn)
    #display(df)

    df['label']=pd.cut(df['balance'],
                        bins=3,
                        labels=labels,
                        include_lowest=True)

    #print(df)

    for label in labels:

        condition1=(df['label']==label)
        condition2=((df['disease_num']=='I10') | (df['disease_num']=='R81') | (df['disease_num'] =='E66'))

        tot_cnt = len(df.loc[condition1])
        patient_cnt = len(df.loc[condition1 & condition2])

        if(tot_cnt == 0) :
            #print('No Data for ('+label+') : Can not proceed analysis')
            result[label]=-1
            continue

        ret=(patient_cnt/tot_cnt)*100

        #print(ret)
        result[label]=ret

    return result

def run():
    return engine2()

#if __name__ == '__main__':

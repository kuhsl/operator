import pymysql
import pandas as pd
import numpy as np
from IPython.display import display 
import warnings

warnings.filterwarnings(action='ignore')

labels=['label1','label2','label3']

app = Flask(__name__)

### connect db
#conn = pymysql.connect(host='163.152.30.239', user='root', passwd='hw147258369!', db='db-server', charset='utf8')
conn = pymysql.connect(host='localhost', user='operator', passwd='mysql_pw', db='operator', charset='utf8')
cur = conn.cursor()

def engine2():

    result={}

    sql="SELECT balance, disease_num FROM financial_data a LEFT OUTER JOIN medical_data b ON a.ssn=b.ssn ORDER BY balance ASC"
    #sql="SELECT balance, disease_num FROM financial_data a JOIN medical_data b ON a.ssn=b.ssn WHERE disease_num IN ('I10','R81','E66') ORDER BY balance ASC"

    df=pd.read_sql(sql, con=conn)
    display(df)

    bins=[df['balance'].min(), 3584756, 7681620,df['balance'].max()]

    df['label']=pd.cut(df['balance'],
                        bins=bins,
                        labels=labels,
                        include_lowest=True)


    print(df)
    
    for label in labels:

        condition1=(df['label']==label)
        condition2=((df['disease_num']=='I10') | (df['disease_num']=='R81') | (df['disease_num'] =='E66'))

        tot_cnt = len(df.loc[condition1])
        patient_cnt = len(df.loc[condition1 & condition2])

        if(tot_cnt == 0) :
            print('No Data for ('+label+') : Can not proceed analysis')
            result[label]=-1
            continue
        
        ret= round((patient_cnt/tot_cnt)*100, 2)
        
        print(ret)
        result[label]=ret

    print(result)
    return result

@app.get('/')
def run():
    return make_response(json.dumps(engine2(), ensure_ascii = False)

if __name__ == '__main__':
    try:
        app.run(host='0.0.0.0', port=80, debug=False)
    finally:
        conn.close()
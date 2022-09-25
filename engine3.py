import pymysql
import pandas as pd
import numpy as np
from IPython.display import display 
import warnings

import matplotlib
import matplotlib.pyplot as plt
from datetime import datetime as dt
from base64 import b64encode

matplotlib.use('agg')

warnings.filterwarnings(action='ignore')

dir = 'img/'

def engine3():
    ### connect db
    #conn = pymysql.connect(host='163.152.71.223', user='root', passwd='hw147258369!', db='db-server', charset='utf8')
    conn = pymysql.connect(host='localhost', user='operator', passwd='mysql_pw', db='operator', charset='utf8')
    #conn = pymysql.connect(host='localhost', user='root', passwd='hw147258369!', db='db-server', charset='utf8')
    cur = conn.cursor()

    #sql="SELECT name, a.ssn, FLOOR((CHAR_LENGTH(relations)-CHAR_LENGTH(REPLACE(relations, 'c:','')))/2) as child_cnt, balance FROM public_data a JOIN financial_data b ON a.ssn=b.ssn"
    sql="SELECT FLOOR((CHAR_LENGTH(relations)-CHAR_LENGTH(REPLACE(relations, 'c:','')))/2) as child_cnt, balance FROM public_data a JOIN financial_data b ON a.ssn=b.ssn"

    df=pd.read_sql(sql, con=conn)
    df=df.set_index('balance')
    
    #display(df['child_cnt'])
    result_dict = df['child_cnt'].to_dict()
    #print(result_dict)

    list_x_values = result_dict.keys()
    list_y_values = list(map(int, result_dict.values()))

    #print(list_x_values)
    #print(list_y_values)
    
    plt.scatter(list_x_values, list_y_values, s=1)
    plt.xscale('log')

    plt.title('Test graph')
    plt.xlabel('balance')
    plt.ylabel('children count')

    #filename = dir + dt.now().strftime("%Y-%m-%d_%H%M%S") + ".png"
    filename = dir + "result_image.png"

    plt.savefig(filename,
                facecolor='#eeeeee',
                edgecolor='black',
                format='png', dpi=200)
    
    with open(filename, 'rb') as f:
        img = f.read()
        b64 = b64encode(img).decode()

    return b64

def run():
    return engine3()

if __name__ == '__main__':
   run()

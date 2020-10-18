##LIBRERIAS
import os
import numpy as np
import time
import pandas as pd
import datetime
import re
import boto3
import matplotlib.pyplot as plt
import cv2
#import spacy
from unicodedata import normalize
import boto3

##FUNCIONES PRIMARIAS
#***************************TUPLA DE (AÑO,COLUMNA)***********************
def extract_column_year(df):
    try:
        ##limpiar del df
        df = df.applymap(str)
        ##5 limite de renglones a revisar
        tupl = year_loc(df,5)
        return tupl
    except:
        return -1





##FUNCIONES SECUNDARIAS
def year_loc(df,num_renglones):
    for i in range(num_renglones):
        l_years_row = [] ## lista de los años que encuentre en las celdas
        
        for col in range(df.shape[1]):
            #print(col)
            if col == 0:
                pass
            else:
                s = df.iloc[i,col]
                #print(s,':',col)
                year = extract_year(s)
                if year:
                    l_years_row.append((year,col))
                    #print(tuple(year,col))

        if len(l_years_row)>0:
            years_columns = pd.DataFrame(l_years_row)
            #print(years_columns)
            years_columns = years_columns.groupby(0).min()
            y_max = max(years_columns.index.to_list())
            columna = years_columns.loc[y_max][1]
            #display(df.head(5))######
            
            #print(l_years)
            return (y_max,columna)

def extract_year(s):
    ##re para 00's y 90's
    year = re.search('(([2]{1}[0][0-2]{1}[0-9]{1}|[1]{1}[9][7-9]{1}[0-9]{1}))',s)
    if year:
        return year.group()
    else:
        years = re.findall('(([0-2]{1}|[8-9]{1})[0-9]{1})',s)
        try:
            year = years[-1][0]
            if (year[0]=='1') or (year[0]=='2') or (year[0]=='0') :
                year = '20'+year
            else:
                year = '19'+year
            return year
        except:
            return None
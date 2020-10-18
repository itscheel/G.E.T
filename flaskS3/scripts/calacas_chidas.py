import numpy as np
import pandas as pd

import boto3
import cv2
import re
import difflib
import enchant

import datetime
import time
import os
import sys


from unicodedata import normalize
from scripts.extract_key_value import extract_column_year
from scripts.text_detection import get_aws_analyze_document

def clean_text(s):
    s = str(s)
    s = re.sub(
        r"([^n\u0300-\u036f]|n(?!\u0303(?![\u0300-\u036f])))[\u0300-\u036f]+", r"\1", 
        normalize( "NFD", s), 0, re.I
    )
    s = normalize('NFC', s)
    minus = s.lower()
    punctuations = '''!()-[]{};:'"\,<>./?@#$%^&*_~'''
    no_punct = ""
    for char in minus:
        if char not in punctuations:
            no_punct = no_punct + char
    return no_punct

def clean_text_numerico(s):
    s = str(s)
    s = re.sub(
        r"([^n\u0300-\u036f]|n(?!\u0303(?![\u0300-\u036f])))[\u0300-\u036f]+", r"\1", 
        normalize( "NFD", s), 0, re.I
    )
    s = normalize('NFC', s)
    minus = s.lower()
    punctuations = '''![]{};:'"\,<>./?@#$%^&*_~'''
    no_punct = ""
    for char in minus:
        if char not in punctuations:
            no_punct = no_punct + char
    return no_punct

def dates_in_tables_f(list_df_tables):
    dates_in_tables =[]
    for df_tables in list_df_tables:
        s = df_text_to_string(df_tables)
        date = extract_dates(s)    
        dates_in_tables.append(date)
    dates_in_tables = [x for x in dates_in_tables if x]
    dates_in_tables.sort()
    date = None
    if len(dates_in_tables) > 0:
        date = dates_in_tables[-1]
    return date

def extract_dates(s):
    try:
        mesesDic = {
            'enero': '01',
            'febrero': '02',
            'marzo': '03',
            'abril': '04',
            'mayo': '05',
            'junio': '06',
            'julio': '07',
            'agosto': '08',
            'septiembre': '09',
            'octubre': '10',
            'noviembre': '11',
            'diciembre': '12'
        }
        dates = re.finditer('(?P<day>[0-9]{2}) (de) (?P<month>[a-zA-Z]+) (de|del) (?P<year>[0-9]{4})',s)
        list_dates = []
        for x in dates:
            day = x.group('day')
            month = mesesDic[x.group('month')]
            year = x.group('year')
            fecha = datetime.date(int(year),int(month),int(day))
            list_dates.append(fecha)
        list_dates.sort(reverse=True)
        list_dates = [y.strftime('%d-%m-%Y') for y in list_dates]
        return(list_dates[0])
    except:
        return None

def extract_units(s):
    try:
        unidades = re.finditer('((miles|millones) (de) (?P<moneda>(dolares|pesos|usd) (colombianos|chilenos|mexicanos|americanos)?))',s,flags=2)
        #print(unidades)
        for x in unidades:
            if x.group().find('usd'):
                return(x.group())
        return(x.group())
    except:
        return None

def df_text_to_string(df_text):
    df_text = df_text.applymap(str)
    string= ''
    for i, row in df_text.iterrows():
        line_text = ''.join(row)
        string += line_text +'\n'
    return string

def list_dfs_to_string(list_df_text):
    String = ' '.join([df_text_to_string(x) for x in list_df_text])
    return String

def get_output_indexes(v_contables_dict,list_words):
    output_indexes = {}
    for v_contables_key in v_contables_dict.keys():
        row = -1
        all_close_matches = {}
        for similar_word in v_contables_dict[v_contables_key]:
            close_matches = difflib.get_close_matches(similar_word, list_words, n=3)
            for match in close_matches:
                distance = enchant.utils.levenshtein(similar_word, match)
                # parche 
                if 'costo' in v_contables_key.lower() and 'gasto' in match:
                    continue
                if distance < int(len(similar_word)*0.5):
                    if match in all_close_matches:
                        if all_close_matches[match] > distance:
                            all_close_matches[match] = distance
                    else:
                        all_close_matches[match] = distance

        matches_len = len(all_close_matches)
        if matches_len > 0:
            all_close_matches = sorted(all_close_matches.items(), key=lambda x: x[1])
            row = list_words.index(all_close_matches[0][0])
            # Get unused row
            index = 1
            while index < matches_len and row in output_indexes.values():
                row = list_words.index(all_close_matches[index][0])
                index += 1
            if row in output_indexes.values():
                row = -1

        output_indexes[v_contables_key] = row
    return output_indexes

def Calacas_chidas_AI(v_contables_dict,bucket, bucket_file):
    file_path = os.path.join('DownTest', bucket_file)
    print(file_path)
    if bucket_file not in os.listdir('scripts/DownTest'):
        boto3.client('s3').download_file(
            bucket, 
            file_path, 
            'scripts/'+file_path
        )
    list_df_tables, list_df_text = get_aws_analyze_document('scripts/'+file_path)
    list_df_tables = [a for a in list_df_tables if a is not None]
    list_df_text = [a for a in list_df_text if a is not None]

    Text = clean_text(list_dfs_to_string(list_df_text))
    Unidades = extract_units(Text)
    Fecha = extract_dates(Text)
    if not Fecha:
        Fecha = dates_in_tables_f(list_df_tables)
    
    """
    for x in range(len(list_df_tables)):
        list_df_tables[x] = list_df_tables[x].applymap(clean_text)
    """    
    l=[]
    for x in range(len(list_df_tables)):
        clave = extract_column_year(list_df_tables[x])
        l.append(list_df_tables[x].rename(columns={1:'Clave',clave[1]:'Valor'})[['Clave','Valor']])
    
    df = pd.concat(l,axis=0, ignore_index=True)
    df['Clave'] = df['Clave'].map(lambda x:str(x).lower())
    df.replace({'':np.nan},inplace=True)
    df.dropna(inplace=True)
    
    ids_campos = get_output_indexes(v_contables_dict,df['Clave'].to_list())
    claves = ids_campos.keys()
    
    aux = []
    aux.append(['Archivo',bucket_file])
    aux.append(['Fecha',Fecha])
    aux.append(['Unidades en las que se mide',Unidades])
    for i in claves:
        if ids_campos[i] == -1:
            aux.append([i,np.nan])
        else:
            aux.append([i,df.iloc[ids_campos[i]]['Valor']])
    df = pd.DataFrame(aux)
    df.replace({np.nan:'0',None:'0'},inplace=True)
    df[1] = df[1].map(lambda x:clean_text_numerico(str(x)))
    
    return(df)


def modelo(documentos):
    v_contables_dict = {
        'Caja y bancos':[
            'caja y bancos', 
            'efectivo y equivalentes en efectivo',
            'efectivo y equivalentes de efectivo',
        ],
        'Total activo':[
            'total activo',
            'suma de los activos', 
            'activo total',
        ],
        'Total pasivo':[
            'total pasivo',
            'suma de los pasivos',
            'pasivo total',
            'total pasivos',
        ],
        'Total patrimonio':[
            'total patrimonio',
            'suma de los patrimonios',
            'patrimonio total',
            'patrimonio',
            'suma del capital contable',
            'total capital contable', 
            'total capital', 
            'patrimonio de los accionistas',
        ],
        'Ventas':[
            'ventas',  
            'ventas por operacion ordinaria',
            'ingresos por operacion',
            'ingresos por operacion ordinaria', 
            'ingresos operacionales', 
            'ventas brutas', 
            'ingreso por actividades ordinarias',
            'ingresos de actividades ordinarias'
            'total ingresos operacionales',
            'ingresos por ventas',
            'ingresos de actividades ordinarias procedentes de contratos con clientes',
        ],
        'Costo de ventas':[
            'costos de ventas', 
            'costos por ventas', 
            'costo de actividades ordinarias',
            'costo por venta de bienes y prestacion de servicios',
        ],
        'Utilidad bruta':[
            'utilidad bruta',
            'perdida bruta',
            'ganancia bruta',
        ],
        'Utilidad operacional': [
            'utilidad operacional', 
            'perdida operacional',
            'ganancia por actividades de operacion',
            'ganancias de actividades operacionales',
        ],
        'Utilidad antes de impuestos': [
            'utilidad antes de impuestos', 
            'perdida antes de impuestos',
            'utilidad antes de impuesto a las ganancias',
            'utilidad antes del impuesto sobre la renta',
            'ganancia por operaciones continuadas antes del impuesto a las ganancias',
        ],
        'Utilidad neta': [
            'utilidad neta', 
            'perdida neta',
            'utilidad neta del periodo',
            'resultado del ejercicio',
            'ganancia (perdida)'
            'ventas netas'
        ],
    }

    bucket = 'calacaschidas'
    lst = []
    for doc in documentos:
        print(doc)
        bucket_file = str(doc)
        output = Calacas_chidas_AI(v_contables_dict,bucket, bucket_file)
        final_df = output.set_index(0).T
        final_df['Archivo'] = bucket_file
        lst.append(final_df)
    final = pd.concat(lst,ignore_index=True)
    print('**************************************************')
    final.to_csv('static/csv/ETL.csv',index=False)
    print('**************************************************',final)
    print(final)
    return(final)
    
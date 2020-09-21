from alamala import obtenertokenconnect
from crearplaylist import crearplaylist
import spotipy
import spotipy.util as util
import sqlite3
import requests
import keyboard 
import pandas as pd
from surprise import Dataset
from surprise import Reader
from surprise import KNNWithMeans
from surprise import SVD
from surprise.model_selection import cross_validate
from surprise.model_selection import GridSearchCV
import csv
import numpy as np
from datetime import date, time
from caracteristicascancion import ObtenerCaracteristicas
import spotipy.oauth2 as oauth2
import os
import json
import random

#client_id = os.getenv('SPOTIPY_CLIENT_ID')
#client_secret = os.getenv('SPOTIPY_CLIENT_SECRET')
#redirect_uri = os.getenv('SPOTIPY_REDIRECT_URI')

def split_list (list, tamano):
   return [list[i:i+tamano] for i in range(0, len(list), tamano)]


def fn_database(sql, params=None):
    conn = sqlite3.connect('spotify.db')
    c = conn.cursor()

    df = pd.read_sql_query(sql, conn, params=params)

    conn.commit()
    conn.close()

    return df

def elrating(row):
    
    if (row.time_range == 'short_term'):
        reciente = .8
    elif (row.time_range == 'medium_term'):
        reciente = 1
    elif (row['time_range'] == 'long_term'):
        reciente = .6
    
    importancia = (200 - row.position)/200
    
    rating = importancia * reciente * 5

    return rating

def lafiesticidad(row):
    if (row['fiesticidad'] >= .4):
        puntaje_final = 1
    
    return puntaje_final


def is_token_expired(token_info):
    now = int(time.time())
    return token_info["expires_at"] - now < 60



def iniciarfiesta(fiesta_id, nombre_fiesta):

    conn = sqlite3.connect('spotify.db')


    sql = '''SELECT * FROM CancionUsuario'''

    fecha = str(date.today())
    uri_usuarios = []

    c = conn.cursor()

    sqlselectusers = ''' SELECT uri_usuario FROM FiestaUsuario where fiesta_id = ? '''
    cur = conn.cursor()
    cur.execute(sqlselectusers,(str(fiesta_id),))
    conn.commit()
    
    select_invitados = cur.fetchall()

    for uri_usuario in select_invitados:
        uri_usuarios.append(uri_usuario[0])
    
    conn.close()

    invitado_para_sacar_info = uri_usuarios[0][13:]

    scope = 'user-library-read,user-top-read,playlist-modify-public'

    token_info = util.prompt_for_user_token(username=invitado_para_sacar_info, scope=scope)


    playlistid = crearplaylist(token_info, invitado_para_sacar_info, nombre_fiesta)
    playlisturi = 'spotify:playlist:{}'.format(playlistid)

    
    df = fn_database(sql)


    df = df.loc[df['uri_usuario'].isin(uri_usuarios)]
    df_mas_recientes = df.groupby(['uri_usuario'],as_index=False)['date'].max()

    df = df.merge(df_mas_recientes, on='uri_usuario', how='left')


    df = df.loc[df['date_x']==df['date_y']]

    print(token_info)

    uri_canciones = []
    for index, row in df.iterrows():
        print(row['uri_cancion'])
        uri_canciones.append(row['uri_cancion'])
    

    ObtenerCaracteristicas(uri_canciones,token_info)
    
    sqlcaracteristicas = '''SELECT uri AS uri_cancion, danceability*energy*5 AS fiesticidad, duration_ms
        FROM CancionCaracteristicas'''

    df_caracteristicas = fn_database(sqlcaracteristicas)
    print (df_caracteristicas)

    df['rating'] = df.apply(lambda row: elrating(row), axis=1)


    dfmodelo = df.groupby(['uri_cancion','uri_usuario'],as_index=False)['rating'].max()

    dfsimple = dfmodelo.groupby(['uri_cancion'],as_index=False)['rating'].sum()

    dfrecommender = dfmodelo[['uri_usuario', 'uri_cancion', 'rating']].copy()


    reader = Reader(rating_scale=(0, 5))

    data = Dataset.load_from_df(dfrecommender[['uri_usuario', 'uri_cancion', 'rating']], reader)

    algo = SVD()

    cross_validate(algo, data, measures=['RMSE', 'MAE'], cv=5, verbose=True)


    param_grid = {'n_factors':[5,10,15,20],'n_epochs':[5,10,20,25,30],  'lr_all':[0.001,0.005,0.01],'reg_all':[0.02,0.1,0.2,0.3]}
    #param_grid = {'n_factors':[1],'n_epochs':[5,10,20,25,30],  'lr_all':[0.001,0.005,0.007,0.01],'reg_all':[0.02,0.1,0.2,0.3]}
    gs = GridSearchCV(SVD, param_grid, measures=['rmse'], cv=3)
    gs.fit(data)
    params = gs.best_params['rmse']
    print (params)
    svdtuned = SVD(n_factors=params['n_factors'], n_epochs=params['n_epochs'],lr_all=params['lr_all'], reg_all=params['reg_all'])
    #svdtuned = SVD(n_factors=20, n_epochs=params['n_epochs'],lr_all=params['lr_all'], reg_all=params['reg_all'])
    trainingSet = data.build_full_trainset()

    algo = svdtuned
    print 
    print (algo.n_epochs)

    #sp = spotipy.Spotify(auth=token_info['access_token'])
    sp = spotipy.Spotify(auth=token_info)

    #descripcion_anterior = sp.user_playlist(user=token[1],playlist_id=playlistid,fields='description')
    descripcion_anterior = sp.user_playlist(user=invitado_para_sacar_info,playlist_id=playlistid,fields='description')

    descripcion = descripcion_anterior['description'] + ' ' + str(params)

    sp.user_playlist_change_details(user=invitado_para_sacar_info,playlist_id=playlistid,description=descripcion)
 
    algo.fit(trainingSet)

    prediction = algo.predict('spotify:user:jorged_94', 'spotify:track:0aZ5EsW90SpCbsYfMQ7HRf', r_ui =0.995, verbose=True)

    folder_path = r'Matrix\{}'.format(nombre_fiesta)
    #os.makedirs(os.path.dirname(filename_inputSI), exist_ok=True)
    os.makedirs(folder_path, exist_ok=True)

    rm = np.dot(algo.pu, algo.qi.T)

    np.savetxt(r'{}\algo.pu.csv'.format(folder_path), algo.pu, delimiter=',')
    np.savetxt(r'{}\algo.qi.csv'.format(folder_path), algo.qi, delimiter=',')
    np.savetxt(r'{}\rm.csv'.format(folder_path), rm, delimiter=',')

    #pu: User factors
    #qi: Item factors
    #bu: User bias
    #bi: Item bias

    group_pu = algo.pu.mean(axis=0)
    latent_factors = np.dot(group_pu, algo.qi.T)

    np.savetxt('{}\latent_factors.csv'.format(folder_path), latent_factors, delimiter=',')

    #print(algo.bu)
    #print(algo.bu.mean())

    numero_de_canciones = algo.qi.shape[0]

    recomendacion_grupal = []

    for i_iid in range(numero_de_canciones):
        group_estimacion = latent_factors[i_iid]+ algo.bi[i_iid]+dfrecommender['rating'].mean()
        cancion = trainingSet.to_raw_iid(i_iid)
        #print (cancion,group_estimacion)
        recomendacion_grupal.append([cancion,group_estimacion])

    def Sort(sub_li): 
  
        # reverse = None (Sorts in Ascending order) 
        # key is set to sort using second element of  
        # sublist lambda has been used 
        sub_li.sort(key = lambda x: x[1],reverse=True) 
        return sub_li 
  
    # Driver Code 
    recomendacion_grupal_ordenada = Sort(recomendacion_grupal)

    df_final = pd.DataFrame(recomendacion_grupal_ordenada, columns =['uri_cancion', 'estimacion'])
    print (df_final)

    #df_final.join(other.set_index('key'), on='key')

    #df_final.merge(df_caracteristicas, left_on='uri',right_on='uri_cancion', how='left')
    df_final = df_final.merge(df_caracteristicas, on='uri_cancion', how='left')
    print (df_final)


    #df_final['puntaje_final']=(50*df_final['estimacion']+df_final['fiesticidad'])/3

    fiesticidad_threshold = 2

    df_final.loc[df_final['fiesticidad'] <= fiesticidad_threshold, 'puntaje_final'] = 0
    df_final.loc[df_final['fiesticidad'] > fiesticidad_threshold, 'puntaje_final'] = df_final['estimacion']  

    #df_final['puntaje_final'] = df_final['set_of_numbers'].apply(lambda x: 'True' if x <= 4 else 'False')

    print (df_final)

    #df.loc[['viper', 'sidewinder'], ['shield']] = 50
    
    #df_final.loc[df_final['duration_ms'] > 420000, 'puntaje_final'] = 0

    df_final.loc[df_final.duration_ms > 420000, 'puntaje_final'] = 0


    df_final = df_final.sort_values(by='puntaje_final', ascending=False)
    print (df_final)

    df_final.to_csv (r'{}\estimacion_final.csv'.format(folder_path), index = False, header=True)
    

    dfsimple = dfsimple.sort_values(by='rating',ascending=False)

    dfsimple.to_csv(r'{}\estimacion_simple.csv'.format(folder_path),index=False, header=True)

    aleatorio =  random.choice([1, 2])
    #aleatorio = 1
    if (aleatorio == 1):
        cancionesasonar = df_final
    elif (aleatorio == 2):
        cancionesasonar = dfsimple


    canciones = []

    for index, row in cancionesasonar.iterrows():
        #print(row['uri_cancion'])
        canciones.append(row['uri_cancion'])

    print(canciones)
    
    #for a,b in recomendacion_grupal_ordenada:
    
        #canciones.append(a)
    canciones_seccionado = split_list(canciones,100)
    
    #canciones = canciones[:100]
    #print (canciones)
    sp = spotipy.Spotify(auth=token_info)
    for seccion in canciones_seccionado:
        snapshot = sp.user_playlist_add_tracks(user=invitado_para_sacar_info,playlist_id=playlistid,tracks=seccion)

    #sp.start_playback(devi)    
    sp.shuffle(state=False)

    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'Authorization': 'Bearer {}'.format(token[0]),
    }

    data = '{{"context_uri":"{}","offset":{{"position":{}}},"position_ms":0}}'.format(playlisturi,0)

    response = requests.put('https://api.spotify.com/v1/me/player/play', headers=headers, data=data)

    if response:
        print('Se reprodujo la playlist')
    else:
        print(response,response.text)

    
    conn = sqlite3.connect('spotify.db')
    while True:  # making a loop
        try:  # used try so that if user pressed other than the given key error will not be shown
            if keyboard.is_pressed('n'):  # if key 'q' is pressed 
                print('Next song!')
                
                headers = {
                    'Accept': 'application/json',
                    'Content-Type': 'application/json',
                    'Authorization': 'Bearer {}'.format(token[0]),
                }
               
                responsecancion = requests.get('https://api.spotify.com/v1/me/player/currently-playing', headers=headers)

                #print(responsecancion.json()['progress_ms'],responsecancion.json()['item']['duration_ms'])

                sql = ''' INSERT INTO Salto(uri,porcentaje)
                            VALUES(?,?) '''
                cur = conn.cursor()

                porce =  responsecancion.json()['progress_ms']/responsecancion.json()['item']['duration_ms']

                t=(responsecancion.json()['item']['uri'],porce)
                cur.execute(sql, t)

                conn.commit()
                #conn.close()

                response = requests.post('https://api.spotify.com/v1/me/player/next', headers=headers)
               
   
                #break  # finishing the loop
        except Exception as e:
            print (e)
            break  # if user pressed a key other than the given key the loop will break
    
    print('Bien hecho campeón')
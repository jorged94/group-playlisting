import sys
import spotipy
#import spotipy.util as util
import utilmejorado as util
import sqlite3

#subida a git

def split_list (list, tamano):
   return [list[i:i+tamano] for i in range(0, len(list), tamano)]


def ObtenerCaracteristicas (uri,token):
    #scope = 'user-library-read,user-top-read'
   
    conn = sqlite3.connect('spotify.db')

    uri_seccionado = split_list(uri,100)



    if token:
        sp = spotipy.Spotify(auth=token)
        #audio = sp.audio_features('spotify:track:1ndyl3wJCFs872XZ3ztPk6')
        for seccion in uri_seccionado:
            audio = sp.audio_features(seccion)

            for cancion in audio:
                print(cancion)

                sql = ''' INSERT OR IGNORE INTO CancionCaracteristicas(uri,danceability,energy,key,loudness,mode,speechiness,acousticness,instrumentalness,liveness,valence,tempo,duration_ms,time_signature)
                    VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?) '''
                cur = conn.cursor()
                
                cur.execute(sql,
                (cancion['uri'],
                cancion['danceability'],
                cancion['energy'],
                cancion['key'],
                cancion['loudness'],
                cancion['mode'],
                cancion['speechiness'],
                cancion['acousticness'],
                cancion['instrumentalness'],
                cancion['liveness'],
                cancion['valence'],
                cancion['tempo'],
                cancion['duration_ms'],
                cancion['time_signature']
                ))

                conn.commit()
                

            #print (dir(audio))
            #print (type(audio))
            #print (audio)

            #for item in audio['items']:
                #print (item)

            #for p_info, key in audio[0].items():
                
                #print('{}: {}'.format(p_info,key))
                
            '''for item in audio[0]:
                cur.execute(sql,
                (item['uri'],
                item['album']['uri'],
                item['track_number'],
                item['danceability'],
                item['energy'],
                item['key'],
                item['loudness'],
                item['mode'],
                item['speechiness'],
                item['acousticness'],
                item['instrumentalness'],
                item['liveness'],
                item['valence'],
                item['tempo'],
                item['duration_ms'],
                item['time_signature']
                ))
                #print(item)'''

            
        conn.close()
            
            #print (type(audio[0]))
            #print (audio[0]['mode'])

              

    else:
        print ("Can't get token for", username)


if __name__ == "__main__":
    token = ''
    ObtenerCaracteristicas('spotify:track:0Cn8NxJZz7zUlsaA3rXoIU',token)


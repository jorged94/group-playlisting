from elparty import iniciarfiesta
from caracteristicasUsuario import registrarusuario
from datetime import date
import sqlite3
import os

os.environ["SPOTIPY_CLIENT_ID"] =""
os.environ["SPOTIPY_CLIENT_SECRET"] = ""
os.environ["SPOTIPY_REDIRECT_URI"] = "http://localhost/"


if __name__ == "__main__":

    fecha = str(date.today())

    nombre_fiesta = input ("Ingrese nombre de la fiesta: ")
    nombre_fiesta = nombre_fiesta + " " + fecha
    conn = sqlite3.connect('spotify.db')
    c = conn.cursor()

    sqlfiesta = ''' INSERT OR IGNORE INTO Fiesta(nombre_fiesta) VALUES(?) '''
    cur = conn.cursor()
    cur.execute(sqlfiesta,(nombre_fiesta,))
    conn.commit()
    sqlselectfiesta = ''' SELECT fiesta_id FROM Fiesta WHERE nombre_fiesta = ? '''
    cur.execute(sqlselectfiesta,(nombre_fiesta,))


    rows = cur.fetchone()
 
    fiesta_id = rows[0]


    conn.commit()

    fiesta_id = 42



    while 1:
        seleccion = '0'
        
        print ('''\nBienvenido a la mejor fiesta de su vida
        Para agregar un invitado, seleccione 1
        Para listar los invitados, seleccione 2
        Para comenzar la fiesta, seleccione 3
        Para salir, seleccione 4''')
        
        seleccion = input ("Ingrese su opcion: ")
        if seleccion == '1':
            print ('Ingrese invitado')
            #invitados.append(registrarusuario())
            uri_usuario = registrarusuario()[2]

            sqlfiestausuario = ''' INSERT OR IGNORE INTO FiestaUsuario(fiesta_id,uri_usuario) VALUES(?,?) '''
            cur = conn.cursor()
            cur.execute(sqlfiestausuario,(str(fiesta_id),uri_usuario))
            conn.commit()
            #conn.close()
            
        elif seleccion == '2':
            print ('Estos son los invitados:')
            sqlselectinvitados = ''' SELECT uri_usuario FROM FiestaUsuario WHERE fiesta_id = ? '''
            cur.execute(sqlselectinvitados,(fiesta_id,))

            #print("'{}'".format(nombre_fiesta))

            invitados = cur.fetchall()

            for invitado in invitados:
                print (invitado[0][13:])
 
            #fiesta_id = rows[0]

            #for invitado in invitados:
                #print (invitado)
            
        elif seleccion == '3':
            print ('Welcome to the jungle')
            iniciarfiesta(fiesta_id, nombre_fiesta)
            #iniciarfiesta(15, 'pruebaza')
        elif seleccion == '4':
            print('Gracias por participar')
            break


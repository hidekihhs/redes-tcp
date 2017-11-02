import socket                   # Import socket module
import os
import binascii
import datetime
from python_arptable import *

def stringToBin(msg):
    data_binary = bin(int(binascii.hexlify(msg),16)).split('b')
    return data_binary

def binToString(data_binary):
    n = int(data_binary,2)
    data_hex = binascii.unhexlify('%x' %n)
    return data_hex

def exibePDU(pdu):
    print "Preambulo: " + str(int(pdu[0],2))
    print "Start_frame: " +  str(int(pdu[1],2))
    print "MAC ORIGEM: " +  binToString(pdu[2])
    print "MAC DESTINO: " +  binToString(pdu[3])
    print "TIPO: " +  str(int(pdu[4],2))

def criaFrame(msg):
    preambulo = '10101010101010101010101010101010101010101010101010101010'
    start_frame = '10101011'
    mac_orig = stringToBin(''.join(get_arp_table()[0]['HW address'].split(':')))
    mac_dest = stringToBin(''.join(get_arp_table()[0]['HW address'].split(':')))
    tipo = '0000000011111111'
    frame = ""
    frame += preambulo + '\n' + start_frame + '\n' + mac_orig[1] + '\n' + mac_dest[1] + '\n' + tipo + '\n' + msg[1] + '\n'
    exibePDU(frame.split('\n'))
    return frame

def recebeMensagem():
    filename = 'mensagem.txt'
    f = open(filename,'rb')
    msg = f.read()
    f.close()
    return msg

# configurando socket para ouvir camada superior 
port_superior = 10000                  # Reserve a port for your service.
s_superior = socket.socket()             # Create a socket object
host = 'localhost'     # Get local machine name
                
    
s_superior.bind((host, port_superior))            # Bind to the port
s_superior.listen(5)                     # Escutando camada superior.
   

while True:
    # Comunicacao camada superior -> fisica -> servidor fisica
    g = open('log_c.txt', 'a')
 #   g.write('Arquivo aberto [' + str(datetime.datetime.now()) + ']' + '\n')
   
    g.write('Esperando conexao com a camada superior [' + str(datetime.datetime.now()) + ']' + '\n')
       
    # estabelece conexao com camada superior
    conn_superior, addr_superior = s_superior.accept()     # Establish connection with client.
    g.write('Estabeleceu conexao com a camada superior ' + str(addr_superior) + '[' + str(datetime.datetime.now()) + ']' + '\n')
          
    msg = conn_superior.recv(40) # recebendo mensagem da camada superior
    print "msg da camada superior:" + msg
        
    # converte para binario
    msg_bin = stringToBin(msg)

    # cria Frame Ethernet
    frame = criaFrame(msg_bin)
    with open('frameEnvio1.txt', 'w') as f:
        print 'file opened'
        f.write(frame)
        f.write('')
    f.close()

    # configurando socket para enviar mensagem para o servidor da fisica
    s = socket.socket()             # Create a socket object
    host = socket.gethostname()     # Get local machine name
    port = 10200                     # Reserve a port for your service.

    s.connect((host, port))

    g.write('Estabelece conexao com Servidor da Fisica [' + str(datetime.datetime.now()) + ']' + '\n')

    # Pergunta TMQ
    s.send('TMQ?')
    g.write('Pergunta TMQ [' + str(datetime.datetime.now()) + ']' + '\n')
    print 'recebendo TMQ'
    TMQ = s.recv(10)
    g.write('Recebe TMQ [' + str(datetime.datetime.now()) + ']' + '\n')

    # Envia frame para servidor
    filename = 'frameEnvio1.txt'
    file = open(filename,'rb')
    l = file.read(int(TMQ))
    while (l):
        s.send(l)
        g.write('Envia quadro para servidor [' + str(datetime.datetime.now()) + ']' + '\n')
        #print('Sent ',repr(l))
        l = file.read(int(TMQ))
    g.write('Arquivo enviado [' + str(datetime.datetime.now()) + ']' + '\n')
    print('Arquivo enviado')

    # Envia TMQ para servidor da fisica
    message = s.recv(10)
    s.send(TMQ)
    g.write('Enviou TMQ [' + str(datetime.datetime.now()) + ']' + '\n')
    frame = ""
    
    # Recebendo resposta do servidor
    while True:
        print('recebendo dados...')
        part = s.recv(int(TMQ))
        g.write('Recebeu dados [' + str(datetime.datetime.now()) + ']' + '\n')
        frame += part
        if not part or part == '':
            break
    g.write('Quadro recebido [' + str(datetime.datetime.now()) + ']' + '\n')
    print('Recebido frame com sucesso')

    s.close()
    g.write('Conexao com Servidor da Fisica encerrada [' + str(datetime.datetime.now()) + ']' + '\n\n')
    print ("Conexao encerrada do servidor se comunicando com cliente")

   
    # separar frame (PREAMBULO, START_DELIMITER, MAC_ORIG, MAC_DEST)
    data = frame.split('\n')

    # exibir PDU
    print "Processando PDU da camada Fisica"
    exibePDU(data[:5])
    
    msg_bin = data[5]
    msg = binToString(msg_bin)
    with open('rf.txt', 'wb') as f:
        f.write(msg)
       # print msg

    # envia mensagem para camada superior
    conn_superior.send(msg)

    g.close()
    
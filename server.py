#ON START SERVER SHOULD BE SUPPLIED WITH CONTROL PORT NUMBER
from socket import *
from threading import Thread
import sys
import os
import shutil
import json
import getpass
import glob
global pam_import
try:
    import pam
    pam_import = 0
except ImportError:
    pam_import = 1

global control_port
class State:
    '''
    This class contains the following variables
    Hidden: self.command, self.dirlist, self.data, self.data_addr,
            self.user_name
    '''
    def __init__(self, connectionSocket, addr, count):
        global control_port
        self.cwd = os.getcwd()
        self.folder = os.path.basename(self.cwd)
        self.control = connectionSocket
        self.control_addr = addr
        self.data_port = control_port + count
        self.data_socket = socket(AF_INET, SOCK_STREAM)
        self.data_socket.bind(('', self.data_port))
        self.glob = False


def ls(state):
    d = {}
    dirlist = os.scandir()
    for entry in dirlist:
        if entry.is_dir():
            d[entry.name] = "d"
        else:
            d[entry.name] = "f"
    state.control.send(json.dumps(d).encode('ascii'))

def cd(state):
    target = state.command[3:]
    try:
        os.chdir(target)
        state.cwd = os.getcwd()
        state.folder = target
        state.control.send('OK'.encode('ascii'))
    except Exception as e:
        state.control.send(str(e).encode('ascii'))

def pwd(state):
    state.control.send(state.cwd.encode('ascii'))

def data_connection(state):
    state.control.send(str(state.data_port).encode('ascii'))
    state.data_socket.listen(1)
    state.data, state.data_addr = state.data_socket.accept()

def put(state):
    target = state.command[4:]
    state.control.send('200'.encode('ascii'))
    response = state.control.recv(8).decode('ascii')
    if(response == '201'):
        return
    elif(response == 'file'):
        put_file(state, target)
    elif(response == 'dir'):
        put_dir(state, target)

def put_file(state, target):
    try:
        data_connection(state)
        f = open(target, 'wb+')
        data = state.data.recv(1024)
        while data:
            f.write(data)
            data = state.data.recv(1024)
    except Exception as e:
        state.data.send(str(e).encode('ascii'))
    finally:
        state.data.close()

def put_dir(state, target):
    try:
        cwd = os.getcwd()
        os.mkdir(target)
        os.chdir(target)
        list_files = state.control.recv(2048).decode('ascii')
        l = json.loads(list_files)
        if(l == '201'):
            os.chdir(cwd)
            return
        else:
            for target in l:
                put_file(state, target)
    except Exception as e:
        print(e)
    finally:
        os.chdir(cwd)

def get(state):
    target = state.command[4:]
    if os.path.isfile(target):
        state.control.send("file".encode('ascii'))
        response = state.control.recv(4).decode('ascii')
        get_file(state, target)
    elif os.path.isdir(target):
        state.control.send("dir".encode('ascii'))
        response = state.control.recv(4).decode('ascii')
        get_dir(state, target)

def rename(state):
    target = state.command.split()
    if os.path.isfile(target[1]):
        if os.path.isfile(target[2]):
            state.control.send("file2exist".encode('ascii'))
        else:
            os.renames(target[1], target[2])
            state.control.send("success".encode('ascii'))
    else:
        state.control.send("!file1".encode('ascii'))


def get_dir(state, target):
    try:
        cwd = os.getcwd()
        os.chdir(target)
        d = {}
        dirlist = os.scandir()
        for entry in dirlist:
            if entry.is_dir():
                state.control.send(json.dumps('NESTED').encode('ascii'))
                os.chdir(cwd)
                return
                d[entry.name] = "d"
            else:
                d[entry.name] = "f"
        state.control.send(json.dumps(d).encode('ascii'))
        for key, value in d.items():
            print('Attempting to transfer ' + key + ' of type ' + value)
            if value == 'f':
                get_file(state, key)
            else:
                get_dir(state, key)
    except Exception as e:
        print(e)
        state.control.send(str(e).encode('ascii'))
    finally:
        os.chdir(cwd)

def get_file(state, target):
    try:
        data_connection(state)
        f = open(target, 'rb+')
        l = f.read(1024)
        while(l):
            state.data.send(l)
            l = f.read(1024)
    except Exception as e:
        state.data.send(str(e).encode('ascii'))
    finally:
        state.data.close()

def mget(state):
    line = state.command[5:]
    targets = line.split(" ")
    l = []
    if(state.glob == False):
        for target in targets:
            if(os.path.isfile(target)):
                l.append(target)
            else:
                state.control.send('201'.encode('ascii'))
                return
    else:
        for pattern in targets:
            list = glob.glob(pattern)
            for target in list:
                l.append(target)
        if(len(l) == 0):
            state.control.send('202'.encode('ascii'))
            return
    state.control.send('200'.encode('ascii'))
    response = state.control.recv(1024).decode('ascii')
    state.control.send(json.dumps(l).encode('ascii'))
    response = state.control.recv(1024).decode('ascii')
    for target in l:
        get_file(state, target)

def mput(state):
    state.control.send('200'.encode('ascii'))
    response = state.control.recv(8).decode('ascii')
    if(response == '201'):
        return
    else:
        state.control.send('200'.encode('ascii'))
        text = state.control.recv(2048).decode('ascii')
        l = json.loads(text)
        for target in l:
            put_file(state, target)


def mkdir(state):
    target = state.command[6:]
    try:
        os.mkdir(target)
        state.control.send('OK'.encode('ascii'))
    except Exception as e:
        state.control.send(str(e).encode('ascii'))

def rm(state):
    target = state.command[3:]
    try:
        if os.path.isfile(target):
            os.remove(target)
            state.control.send('OK'.encode('ascii'))
        else:
            shutil.rmtree(target)
            state.control.send('OK'.encode('ascii'))
    except Exception as e:
        state.control.send(str(e).encode('ascii'))

def toggle_glob(state):
    if(state.glob == True):
        state.glob = False
    else:
        state.glob = True

def system(state):
    state.control.send(str(sys.platform).encode('ascii'))

def user(state):
    authenticate_user(state, 1)

def authenticate_user(state, control_code):
    state.user_name = getpass.getuser()
    if control_code == 'new':
        state.control.send(str(state.user_name).encode('ascii'))
    user_name = state.control.recv(1024).decode('ascii')
    user_pass = state.control.recv(1024).decode('ascii')
    result = 'pass'
    if pam.authenticate(user_name, user_pass):
        state.control.send(str(result).encode('ascii'))
    else:
        result = 'fail'
        state.control.send(str(result).encode('ascii'))

def connection(state):
    print("New connection to client {}".format(state.control_addr))
    state.control.send(str(pam_import).encode('ascii'))
    if pam_import == 0:
    	authenticate_user(state, 'new')

    try:
        while True:
            state.command = state.control.recv(1024).decode('ascii')
            os.chdir(state.cwd)
            #SWITCH BASED ON command
            if(state.command == "bye"):
                break
            elif(state.command == "ls"):
                ls(state)
            elif(state.command[0:3] == "cd "):
                cd(state)
            elif(state.command == "pwd"):
                pwd(state)
            elif(state.command[0:4] == "get "):
                get(state)
            elif(state.command[0:6] == "mkdir "):
                mkdir(state)
            elif(state.command[0:3] == "rm "):
                rm(state)
            elif(state.command == "sys"):
                system(state)
            elif(state.command == "user"):
                user(state)
            elif(state.command[0:5] == "mget "):
                mget(state)
            elif(state.command == "glob"):
                toggle_glob(state)
            elif (state.command[0:7] == "rename "):
                rename(state)
            elif(state.command[0:4] == "put "):
                put(state)
            elif(state.command[0:5] == "mput "):
                mput(state)

        print('Connection closed to client {}'.format(state.control_addr))
        state.control.close()
    except Exception as e:
        print(e)

if __name__ == '__main__':
    global control_port
    control_port = int(sys.argv[1])
    control_socket = socket(AF_INET, SOCK_STREAM)
    control_socket.bind(('', control_port))
    control_socket.listen(10)
    count = 1

    while True:
        connectionSocket, addr = control_socket.accept()
        state = State(connectionSocket, addr, count)
        t = Thread(target=connection, args=(state,))
        t.start()
        count += 1

    control_socket.close()

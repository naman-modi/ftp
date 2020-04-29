#ON START CLIENT SHOULD BE SUPPLIED WITH SERVER IP AND CONTROL PORT NUMBER
from socket import *
import sys
import os
import shutil
import json
import getpass
import glob

if os.name == 'nt':
    os.system('color')

global control_port

class State:
    def __init__(self, client, server):
        self.cwd = os.getcwd()
        self.folder = os.path.basename(self.cwd)
        self.control = client
        self.server = server
        self.glob = False

def rls(state):
    state.control.send("ls".encode('ascii'))
    dir = state.control.recv(1024).decode('ascii')
    try:
        dirlist = json.loads(dir)
        for key, value in dirlist.items():
            if ' ' not in key:
                if value == 'f':
                    print(key, end='    ')
                else:
                    CRED = '\033[91m'
                    CEND = '\033[0m'
                    print(CRED + key + CEND, end='    ')
            else:
                if value == 'f':
                    print('\'' + key + '\'', end='    ')
                else:
                    CRED = '\033[91m'
                    CEND = '\033[0m'
                    print(CRED + '\'' + key + '\'' + CEND, end='    ')
        print()
    except Exception as e:
        print(e)

def lls(state):
    dirlist = os.listdir(state.cwd)
    for l in dirlist:
        if ' ' not in l:
            if os.path.isfile(l):
                print(l, end='    ')
            else:
                CRED = '\033[91m'
                CEND = '\033[0m'
                print(CRED + l + CEND, end='    ')
        else:
            if os.path.isfile(l):
                print('\'' + l + '\'', end='    ')
            else:
                CRED = '\033[91m'
                CEND = '\033[0m'
                print(CRED + '\'' + l + '\'' + CEND, end='    ')
    print()

def rcd(state):
    state.control.send(state.command.encode('ascii'))
    print(state.control.recv(1024).decode('ascii'))

def lcd(state):
    target = state.command[4:]
    try:
        os.chdir(target)
        state.cwd = os.getcwd()
        state.folder = target
        print('OK')
    except Exception as e:
        print(e)

def rpwd(state):
    state.control.send(state.command.encode('ascii'))
    print(state.control.recv(1024).decode('ascii'))

def lpwd(state):
    print(state.cwd)

def data_connection(state):
    data_port = int(state.control.recv(1024).decode('ascii'))
    state.data = socket(AF_INET, SOCK_STREAM)
    state.data.connect((state.server, data_port))

def put(state):
    target = state.command[4:]
    state.control.send(state.command.encode('ascii'))
    response = state.control.recv(8).decode('ascii')
    if os.path.isfile(target):
        state.control.send("file".encode('ascii'))
        put_file(state, target)
    elif os.path.isdir(target):
        state.control.send("dir".encode('ascii'))
        put_dir(state, target)
    else:
        print('Target does not exist.')
        state.control.send('201'.encode('ascii'))

def put_file(state, target):
    try:
        data_connection(state)
        f = open(target, 'rb+')
        l = f.read(1024)
        while(l):
            state.data.send(l)
            l = f.read(1024)
        print('OK')
    except Exception as e:
        print(e)
    finally:
        state.data.close()

def put_dir(state, target):
    try:
        cwd = os.getcwd()
        os.chdir(target)
        l = []
        dirlist = os.scandir()
        for entry in dirlist:
            if entry.is_dir():
                print('The directory is nested. Operation terminated.')
                state.control.send(json.dumps('201').encode('ascii'))
                os.chdir(cwd)
                return
            else:
                l.append(entry.name)
        state.control.send(json.dumps(l).encode('ascii'))
        for target in l:
            put_file(state, target)
    except Exception as e:
        print(e)
    finally:
        os.chdir(cwd)

def rename(state):
    state.control.send(state.command.encode('ascii'))
    response = state.control.recv(1024).decode('ascii')
    if(response == "file2exist"):
        print("File with same name exists. Unsuccessful")
    elif(response == "!file1"):
        print("File 1 does not exist.")
    elif(response == "success"):
        print("OK")

def get(state):
    state.control.send(state.command.encode('ascii'))
    target = state.command[4:]
    type = state.control.recv(1024).decode('ascii')
    if(type == 'file'):
        state.control.send('200'.encode('ascii'))
        get_file(state, target)
    else:
        state.control.send('200'.encode('ascii'))
        get_dir(state, target)

def get_file(state, target):
    try:
        data_connection(state)
        f = open(target, 'wb+')
        data = state.data.recv(1024)
        while data:
            f.write(data)
            data = state.data.recv(1024)
        print('OK')
    except Exception as e:
        print(e)
    finally:
        state.data.close()

def get_dir(state, target):
    try:
        cwd = os.getcwd()
        os.mkdir(target)
        os.chdir(target)
        dir = state.control.recv(2048).decode('ascii')
        d = json.loads(dir)
        if(d == 'NESTED'):
            print('The directory is nested. Operation terminated.')
            os.chdir(cwd)
            return
        print(str(d))
        for key, value in d.items():
            print('Attempting to receive ' + key + ' of type ' + value)
            if value == 'f':
                get_file(state, key)
            else:
                get_dir(state, key)
    except Exception as e:
        print(e)
    finally:
        os.chdir(cwd)

def mget(state):
    state.control.send(state.command.encode('ascii'))
    response = state.control.recv(8).decode('ascii')
    if(response == '201'):
        print('One or more of the specified target files do not exist.\nNote: Toggle file globbing with \'glob\'')
        return
    elif(response == '202'):
        print('No files matching the wildcard expression were found.\nNote: Toggle file globbing with \'glob\'')
        return
    elif(response == '200'):
        state.control.send('200'.encode('ascii'))
        text = state.control.recv(2048).decode('ascii')
        l = json.loads(text)
        state.control.send('200'.encode('ascii'))
        for target in l:
            get_file(state, target)

def mput(state):
    state.control.send(state.command.encode('ascii'))
    response = state.control.recv(8).decode('ascii')
    targets = state.command[5:].split(" ")
    l = []
    if(state.glob == False):
        for target in targets:
            if(os.path.isfile(target)):
                l.append(target)
            else:
                state.control.send('201'.encode('ascii'))
                print('One or more of the specified target files do not exist.\nNote: Toggle file globbing with \'glob\'')
                return
    else:
        for pattern in targets:
            list = glob.glob(pattern)
            for target in list:
                l.append(target)
        if(len(l) == 0):
            state.control.send('201'.encode('ascii'))
            print('No files matching the wildcard expression were found.\nNote: Toggle file globbing with \'glob\'')
            return
    state.control.send('200'.encode('ascii'))
    response = state.control.recv(8).decode('ascii')
    state.control.send(json.dumps(l).encode('ascii'))
    for target in l:
        put_file(state, target)

def rmkdir(state):
    state.control.send(state.command.encode('ascii'))
    print(state.control.recv(1024).decode('ascii'))

def lmkdir(state):
    target = state.command[7:]
    try:
        os.mkdir(target)
        print('OK')
    except Exception as e:
        print(e)

def rrm(state):
    state.control.send(state.command.encode('ascii'))
    print(state.control.recv(1024).decode('ascii'))

def lrm(state):
    target = state.command[4:]
    try:
        if os.path.isfile(target):
            os.remove(target)
            print('OK')
        else:
            shutil.rmtree(target)
            print('OK')
    except Exception as e:
        print(e)

def rsystem(state):
    state.control.send(state.command.encode('ascii'))
    print(state.control.recv(1024).decode('ascii'))

def lsystem(state):
    print(sys.platform)

def toggle_glob(state):
    state.control.send(state.command.encode('ascii'))
    if(state.glob == True):
        state.glob = False
    else:
        state.glob = True
    print(state.glob)

def authenticate_user(state, control_code):
    print('Welcome to FTP')
    if control_code == 'new':
        server_user = state.control.recv(1024).decode('ascii')
        server_client_user = input('Name ({}:{}):'.format(server, server_user))
    elif control_code == 'again':
        server_client_user = input('User: ')
    user_pass = getpass.getpass('Password: ')
    state.control.send(server_client_user.encode('ascii'))
    state.control.send(str(user_pass).encode('ascii'))
    auth_result = state.control.recv(1024).decode('ascii')
    if auth_result == 'pass':
        return
    else:
        state.command = input('ftp> ')
        while state.command != 'user':
            print('No connection')
            state.command = input('ftp> ')
        authenticate_user(state, 'again')

def bye(state):
    state.control.send(state.command.encode('ascii'))

if __name__ == '__main__':
    global control_port
    server = "127.0.0.1"
    #server = sys.argv[1]
    control_port = int(sys.argv[1])
    #control_port = int(sys.argv[2])

    client = socket(AF_INET, SOCK_STREAM)
    client.connect((server, control_port))
    state = State(client, server)
    pam_import = state.control.recv(1024).decode('ascii')
    if pam_import == '0':
    	authenticate_user(state, 'new')

    while True:
        temp_command = input('ftp> ')
        state.command = " ".join(temp_command.split())
        #SWITCH BASED ON COMMAND
        if(state.command == "bye" or state.command == "close" or state.command == "disconnect" or state.command == "quit"):
            bye(state)
            break
        elif(state.command == "ls"):
            rls(state)
        elif (state.command == "dir"):
            rls(state)
        elif(state.command == "!ls"):
            lls(state)
        elif(state.command == "cdup"):
            state.command = "cd .."
            rcd(state)
        elif(state.command[0:3] == "cd "):
            rcd(state)
        elif(state.command[0:4] == "!cd "):
            lcd(state)
        elif(state.command == "pwd"):
            rpwd(state)
        elif(state.command == "!pwd"):
            lpwd(state)
        elif(state.command[0:4] == "get "):
            get(state)
        elif(state.command[0:4] == "put "):
            put(state)
        elif(state.command[0:6] == "mkdir "):
            rmkdir(state)
        elif(state.command[0:7] == "!mkdir "):
            lmkdir(state)
        elif(state.command[0:3] == "rm "):
            rrm(state)
        elif(state.command[0:4] == "!rm "):
            lrm(state)
        elif(state.command == "sys"):
            rsystem(state)
        elif(state.command == "!sys"):
            lsystem(state)
        elif(state.command[0:5] == "mget "):
            mget(state)
        elif(state.command[0:5] == "mput "):
            mput(state)
        elif(state.command == "glob"):
            toggle_glob(state)
        elif(state.command[0:7] == "rename "):
            rename(state)
        elif(state.command == ""):
            continue
        else:
            print("Incorrect command!")

    state.control.close()

# ftp
Implemented the File Transfer Protocol from scratch using Python

<strong>USAGE: </strong>
1. In one terminal(of the server, which can be anything) run: python3 server.py
2. You can now start as many clients as you want by running: python3 client.py

<strong>NOTE:</strong>
1. It is multi threaded
2. Few of the commands: <br>
ls: Run ls on server <br>
!ls: Run ls on client<br>
cd: Navigate on server<br>
!cd: Navigate on client<br>
pwd: Print working directory on server<br>
!pwd: Print working directory on client<br>
get: Transfer file from server to client<br>
mkdir: Create a directory on server<br>
!mkdir: Create a directory on client<br>
rm: Remove a file or directory on server<br>
!rm: Remove a file or directory on client<br>
sys: Print system running on server<br>
!sys: Print system running on client<br>
user: Authenticating user (username, and password)<br>

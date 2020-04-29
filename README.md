# ftp
Implemented the File Transfer Protocol from scratch using Python

<strong>USAGE: </strong>
1. For SERVER: python3 server.py {port number}
2. For CLIENT: python3 client.py {same port number as server}

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
mget: Transfer files from server to client<br>
put: Transfer file from client to server<br>
mput: Transfer files from client to server<br>
mkdir: Create a directory on server<br>
!mkdir: Create a directory on client<br>
rm: Remove a file or directory on server<br>
!rm: Remove a file or directory on client<br>
sys: Print system running on server<br>
!sys: Print system running on client<br>
user: Authenticating user (username, and password)<br>

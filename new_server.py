import multiprocessing
from threading import Thread,Lock
from user import User
from game_room import *
import socket
import game_room
class Server:
    #创建主套接字
    @staticmethod
    def __main_socket(host,port):
        addr = (host,port)
        sockfd = socket.socket()
        sockfd.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
        sockfd.bind(addr)
        sockfd.listen(100)
        return sockfd

    #初始化服务器
    def __init__(self,host,port,pool):
        self.recvUserOutMsg,self.sendUserOutMsg=multiprocessing.Pipe()
        self.__host = host
        self.__port = port
        self.__sockfd = self.__main_socket(host,port)
        self.pool = pool
        self.game_num = {x: {'Users': [], 'Process': None,'UserExit':self.sendUserOutMsg,
                             'Communication':multiprocessing.Pipe(False)} for x in range(pool)}
        self.__addr = (host, port)
        self.lock  = Lock()


    #创建新的线程来处理新连接
    def newThread(self,connfd):
        t = Thread(target=self.handler, args=(connfd,))
        t.setDaemon(True)
        t.start()

    #开始服务器处理新加入的连接
    def serve_forever(self):
        t=Thread(target=self.gameCommand)
        t1=Thread(target=self.clearGameDesk)
        t.setDaemon(True)
        t1.setDaemon(True)
        t.start()
        t1.start()
        while True:
            connfd, addr = self.__sockfd.accept()
            self.newThread(connfd)
            connfd.close()

    #处理客户请求
    def handler(self,connfd):
        userInfo = User(connfd)
        data =eval(userInfo.getMessage().decode())
        if data['title'] == 'register':
            userInfo.register(data['data'])   #注册用户
        elif data['title'] == 'login':
            userInfo.setUserPwd(userInfo.splitUserPwd(data['data']))
            self.login(userInfo)#登录游戏
        else:
            userInfo.closeSockfd()

    #退出游戏时清理该桌的信息
    def clearGameDesk(self):
        while True:
            user_fileno = self.recvUserOutMsg.recv()
            pool = self.pool
            for i in self.game_num:
                for user in self.game_num[i]['Users']:
                    if user_fileno == user.fileno:
                        print('玩家来自', user.addr, '退出', end='\n请输入要执行的命令>')
                        self.pool += 1
                        del self.game_num[i]['Users'][self.game_num[i]['Users'].index(user)]
                        if len(self.game_num[i]['Users']) == 0:  #重置该桌的状态
                            self.game_num[i]['Users'] =[]
                            self.game_num[i]['Process']=None
                            # {'Users':[],'Process':None,'UserExit':self.sendUserOutMsg}
                        break
                if pool < self.pool: #完成信息清理 退出循环
                    break
    #用户登陆
    def login(self,userInfo):
        if userInfo.checkAuth(self.game_num) and self.pool != 0:  # 认证用户 #检测玩家是否满员
            self.lock.acquire() #添加锁
            userInfo.sendMessage(userInfo.convert('login','ok'))
        else:
            userInfo.sendMessage(userInfo.convert('login','error'))
            return
        for i in self.game_num: #安排座位
            if len(self.game_num[i]['Users']) < 3:
                self.pool-=1
                self.game_num[i]['Users'].append(userInfo)
                print('玩家来自',userInfo.addr,'登录',end='\n请输入要执行的命令>')
                if self.game_num[i]['Process']==None:
                    # 创建新的进程来管理这桌游戏
                    p = multiprocessing.Process(target=self.start_game, args=(self.game_num[i], i))
                    p.start()
                    self.game_num[i]['Process'] = p.pid
                else:
                    #当人数不满３人时，已经有新的进程的时候，使新人加入该桌游戏
                    self.game_num[i]['Communication'][1].send(userInfo)
                break
        self.lock.release()  #解锁

    #开始这桌的游戏
    @staticmethod
    def start_game(d_msg,num):
        room = game_room.Game(d_msg,num)
        while True:
            #主流程
            if len(d_msg['Users']) == 3:
                #发送开始游戏信息
                room.startGame()
            elif len(d_msg['Users']) == 0:
                return #没有玩家时结束这个进程
            else:
                time.sleep(1)

    #GM命令
    def gameCommand(self):
        while True:
            command=input('请输入要执行的命令>')
            try:
                if command=='game_list':
                    print(self.game_num)
                else:
                    eval(command)
            except Exception:
                print('没有此命令')

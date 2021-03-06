import pygame
from settings import Settings
import sys
from gamefunction import *
import math
from threading import Thread
import time

class Main:
    def __init__(self,user):
        pygame.init()
        self.user = user  #用户类
        self.Set = Settings() #加载设置
        self.screen = pygame.display.set_mode((self.Set.screenWidth,self.Set.screenHeight))  #设置窗口
        self.packge = self.loadPackge()  # 加载资源包
        pygame.display.set_caption('斗地主') #设置标题
        pygame.event.set_blocked(pygame.MOUSEMOTION | pygame.MOUSEBUTTONDOWN | pygame.QUIT) #设置监听事件 测试用
        self.events = {'touch':[],'display':{'selectDiZhu':None,'upDate':None,'prompt':None,'push':None},
                       'now':None} #事件处理
        #初始化要绘制的信息

        self.mySelf = self.drawSelf()  # 绘制自己
        self.leftUser = self.drawLeftUser() #绘制左边玩家
        self.rightUser = self.drawRightUser() #绘制右边玩家
        self.mouse = Mouse(self.screen) #鼠标点击点绘制 用来判断精灵是否碰撞
        self.players = [self.mySelf,self.leftUser,self.rightUser]
        self.t =Thread(target=self.getMessage)
        self.t.setDaemon(True)
        self.t.start()

    def drawBackGroundImage(self):
        '''绘制背景图片'''
        self.screen.blit(self.packge.backgroundImg, (0, -24))  # 绘制背景图片

    def getMessage(self):
        while True:
            msg = self.user.getMessage(True)
            print(msg)
            if self.events['now']:
                self.events['now'](msg)
                self.events['now']=None
                continue
            # msg={'data':'选地主','title':'start'}
            if msg['title'] =='xszf_jdz': #选地主
                self.events['display']['prompt'] = None
                self.appendDisplayEvents(self.mySelf.selectDiZhu,title='selectDiZhu')
                self.appendTouchEvents(self.mySelf.getPointGroup(),self.getPoint,True)
            elif msg['title'] =='up_screen':  #更新屏幕
                self.appendDisplayEvents(self.screen_update,eval(msg['data']),'upDate')
            elif msg['title'] =='start': #出牌
                self.events['touch']=[]
                myHandCard = self.dataToPoker(self.user.getPoker())
                self.appendDisplayEvents(self.mySelf.showCard,myHandCard,'upDate')
                self.appendDisplayEvents(self.mySelf.pushCard,title='push')
                self.appendTouchEvents(self.mySelf.getPokerGroup(),self.popPoker,False)
                self.appendTouchEvents(self.mySelf.getButtonGroup(),self.pushCard,True)
            elif msg['title'] =='xszf_end': #结束
                self.appendDisplayEvents(self.playerWin,msg['data'],title='prompt')
            elif msg['title'] == 'xszf_num': #改变图片
                # self.changeImage(eval(msg['data']))
                # self.changeImage([1,1,2])
                pass
            elif msg['title'] == 'xszf_pass':
                pass
            # elif msg['title'] =='msg': #提示信息
            #     self.appendDisplayEvents(self.playerWin,msg['data'])

    def changeImage(self,data):
        for i in data:
            if i == 2:
                index = data.index(i)
                self.players[index].changeImage(self.packge.otherDizhu)
                break

    def screen_update(self,data):
        myHandCards = data[0]
        bottomCards = data[1]
        putCards = data[2]
        frontPlayer = data[3][1]
        nextPlayer = data[3][0]

        self.user.setPoker(data[0]) #原始列表
        myHandCards = self.dataToPoker(myHandCards) #转换为标准手牌
        bottomCards = self.dataToPoker(bottomCards) #底牌转换为标准牌
        putCards = self.dataToPoker(putCards)
        # process = [myHandCards,frontPlayer,nextPlayer]
        # list(map(lambda x,y:x(y),self.players,process))
        self.leftUser.showCard(range(frontPlayer)) #显示上家手牌
        self.rightUser.showCard(range(nextPlayer)) #显示下家手牌
        self.mySelf.showCard(myHandCards) #显示自己的手牌
        self.drawOutPokerArea(putCards) #显示出牌区域
        self.appendDisplayEvents(self.drawBottomCardsArea,bottomCards,'prompt')#显示底牌

    def dataToPoker(self,data):
        #解析
        cards = []
        for poker in self.packge.poker:
            if poker.ID in data:
                cards.append(poker)
        return cards[::-1]

    def playerWin(self,msg):
        font = self.packge.promptFont  # 字体
        text = font.render(u'%s' % msg, True, (0, 0, 0))
        self.screen.blit(text, (300, 230))  # 绘制到屏幕上
        for player in self.players:
            player.changeImage(self.packge.otherNongmin) #全部初始化


    def pushCard(self,sprite):
        if sprite.putCard:
            poker = [] #把弹出的都添加到列表中
            for i in self.packge.poker:
                if i.pop:
                    i.pop=False #弹回去
                    print(i.ID,'牌大小')
                    poker.append(i.ID)
            #转换为对应的列表发送出去
            sendIndex = list(map(lambda x:self.user.getPoker().index(x),poker))
            sendIndex=sendIndex[::-1]
            for i in sendIndex:
                msg = self.user.convert(repr(i),'fasongpai')#发送牌
                print(msg)
                time.sleep(0.1)
                self.user.sendMessage(msg)
            msg = self.user.convert('20', 'jieshuchupai')#结束出牌
            self.user.sendMessage(msg)
            def event(msg):
                if msg['title'] =='ok' :
                    del self.events['touch'][0] #删除扑克牌点击事件
                    self.events['display']['push']=None
                else:
                    self.appendTouchEvents(self.mySelf.getButtonGroup(), self.pushCard, True) #重新出牌
            self.events['now']=event # 推入立即要处理的事件
        else:
            msg = self.user.convert('40','guo')#过
            self.user.sendMessage(msg)
            self.events['display']['push'] = None
            del self.events['touch'][0]  # 删除扑克牌点击事件

    def getPoint(self,sprite):
        point = sprite.point
        if point == 0:
            msg =self.user.convert('n','yaodizhu')#要地主
        else:
            msg = self.user.convert('y', 'yaodizhu')#要地主
        self.events['display']['selectDiZhu'] = None
        self.user.sendMessage(msg)

    def popPoker(self,sprite):
        if sprite.pop ==True:
            sprite.pop =False
        else:
            sprite.pop = True

    def appendTouchEvents(self,spritesGroup,fun,delete=True):
        '''spritesGroup = 精灵组 fun = 要执行的函数 delete事件执行完后是否删除 会将相撞的精灵对象放入到函数中，
        使用函数进行处理即可'''
        def append():
            rect = pygame.sprite.spritecollideany(self.mouse,spritesGroup)
            for sprite in spritesGroup.sprites():
                if rect == sprite.rect:
                    fun(sprite)
                    return delete
        self.events['touch'].append(append)

    def appendDisplayEvents(self,fn,data=None,title=None):
        def append():
            if data == None:
                fn()
            else:
                fn(data)
        self.events['display'][title]=append

    def gameEvent(self):
        '''处理事件
        '''
        for event in self.events['display']:
            if self.events['display'][event] !=None:
                self.events['display'][event]()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.user.closeSockfd()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                self.mouse.drawPoint()
                # try:
                for i in self.events['touch']:
                    time.sleep(0.1)
                    if i():
                        del self.events['touch'][self.events['touch'].index(i)]
                # except:
                #     self.events['touch'] =[]

    def main_loop(self):
        '''流程主循环
        '''
        while True: #主事件循环
            self.drawBackGroundImage() #背景覆盖
            # self.events.append(self.eventsAppend(self.mySelf.getPokerGroup(),self.fn,True)) #事件添加
            # self.drawOutPokerArea(self.packge.poker[:20])  # 绘制出牌区域
            # self.mySelf.showCard(self.packge.poker[:10])  # 绘制手牌
            # self.rightUser.showCard((self.packge.poker[1:])) # 绘制手牌
            # self.leftUser.showCard((self.packge.poker[1:]))  # 绘制手牌
            # self.mySelf.pushCard()
            # self.mySelf.selectDiZhu()
            # self.rightUser.selectDiZhu()
            # self.leftUser.selectDiZhu()
            # self.drawBottomCardsArea(self.packge.poker[1:4])
            self.gameEvent()  #处理事件
            self.mySelf.blit() #绘制自己
            self.leftUser.blit() #绘制左边玩家
            self.rightUser.blit() #绘制右边玩家
            pygame.display.flip()

    def drawSelf(self): #初始化绘制自己
        '''绘制自己'''
        player = PSelf(pygame, self.packge, self.screen)
        player.changeImage(self.packge.nongmin)
        return player

    def drawRightUser(self):
        '''绘制右边玩家'''
        return PRight(pygame, self.packge,self.screen)

    def drawLeftUser(self):
        '''绘制左边玩家'''
        return PLeft(pygame, self.packge,self.screen)

    def drawBottomCardsArea(self,poker):
        x=self.Set.bottomCardsX
        for i in poker:
            x+=self.Set.pokerInterval
            self.screen.blit(i.image,(x,self.Set.bottomCardsY))

    def drawOutPokerArea(self,poker=None):
        '''绘制出牌区域'''
        #############计算绘制位置 ###############
        if poker:
            width = self.Set.outPokerAreaWidth
            # height = 150
            # area = pygame.Surface((width,height))  #创建矩形
            # area.fill((0,0,255))  #填充矩形
            # area.set_colorkey((0,0,255)) #设置透明颜色
            if len(poker)*self.Set.pokerWidth >width:  #判断牌数量是否能存放下完整大小
                lenght = math.floor(width / (len(poker)+1))
            else:
                lenght = self.Set.pokerInterval;
        #########################################
            x =self.Set.outPokerCardsX
            #把要绘制的扑克牌绘制出来
            for i in poker:
                x +=lenght
                self.screen.blit(i.image,(x,self.Set.outPokerCardsY)) #绘制到屏幕上

    def loadPackge(self):
        '''加载资源包'''
        class packge:
            def __init__(self,pygame,settings):
                self.pygame =pygame
                self.settings = settings
                self.poker = [Poker('%s\\%s.jpg' % (self.settings.poker, i), i) for i in range(1, 55)] #加载扑克牌
                self.backgroundImg = pygame.image.load(self.settings.backgroundImage)  # 设置背景
                self.font = pygame.font.Font(self.settings.font, 16)  # 加载字体
                self.promptFont = pygame.font.Font(self.settings.font, 80)  # 加载字体
                self.cardBackGround = pygame.image.load(self.settings.cardBackGround)  # 加载卡牌背景
                self.cardBackGround = pygame.transform.scale(self.cardBackGround, (40, 50))  # 缩放提示牌大小
                point = [self.settings.point0,self.settings.point1,self.settings.point2,self.settings.point3]
                self.points = [Point(point[x],x) for x in range(2)] # 加载叫分图片
                self.pass1 = Buttons(self.settings.pass1,600,360,False) #过图片 精灵类
                self.put = Buttons(self.settings.put,300,360,True)  #出牌 精灵类
                self.putError = pygame.image.load(self.settings.putError) #出牌错误 图片 未用到
                self.putNoCards = pygame.image.load(self.settings.putNoCards)  #没有牌能出 未用到
                self.nongmin = pygame.image.load(self.settings.nongmin) #农民图片
                self.otherDizhu = pygame.image.load(self.settings.otherDizhu) #其他玩家地主图片
                self.otherNongmin = pygame.image.load(self.settings.otherNongmin) #其他玩家农民图片
        print('加载资源包完成')
        return packge(pygame,self.Set)
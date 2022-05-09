from random import randint
from tabnanny import check
from webbrowser import get
from playwright.sync_api import sync_playwright
import sys,time,os,re,json
from pathlib import Path
from playwright.sync_api import expect
from  socket import gethostname

hostname=gethostname()
headless=not(hostname in['B550M-K','localhost'])
if os.getenv('headless')=='True':
    headless=True

url={'login':'http://pt.hxpxw.net/login/login.init.do?otherPageName=sanming.html',
     'hxpx':'http://pt.hxpxw.net',
    'home':'http://pt.hxpxw.net',
    'menu':'http://pt.hxpxw.net/els/html/learnroadmap/learnroadmap.viewRoadMapDetail.do?roadMapId=3f22c03df58d40f9860c7a397c1f033b&projectId=9000ef53519f44a4bb9803d9dc4598d6#',
}

playwright=sync_playwright().start()
browser=playwright.chromium.launch(headless=headless,channel="msedge")
context=browser.new_context(accept_downloads=True)

def find_focused_node(node):
    if (node.get("focused")):
        return node
    for child in (node.get("children") or []):
        found_node = find_focused_node(child)
        return found_node
    return None


def login(page,sfzh):
    password=os.getenv("password")
    if not password:
        password='000000'
    page.goto(url['login'])
    page.fill('input[name="loginName"]',sfzh)
    page.fill('input[name="password"]',password)  
    page.click('input[type="submit"]')
    time.sleep(8)
    print(page.title())
    assert '海峡人才培训平台' in page.title()
    context.storage_state(path=sfzh+'_login_hxpx.json')
    return page

def open_gxkm(page):
    with page.expect_popup() as popup_info:
        page.click('text=公需课目（公共课）')
        page1 = popup_info.value
    assert '课程中心' in page1.title()        
    return page1

def open_popup_text(page,text):
    with page.expect_popup() as popup_info:
        page.click('text='+text)
        page1 = popup_info.value
    return page1

def login_storage(browser,sfzh):   
    context = browser.new_context(
            storage_state=sfzh+'_login_hxpx.json',
            accept_downloads=True)
    page = context.new_page()
    page.goto(url['home'])
    time.sleep(2)
    assert '海峡人才培训平台' in page.title()
    return page

def list_card(page):
    arr=page.locator('ul.nc-course-list').text_content().split('学时')
    a=[]
    for i in arr:
        a.append(i.split()[-1])
    return a[:-1]



def open_card(page,text):    
    with page.expect_popup() as popup_info:
        page.click('text='+text)
        page1 = popup_info.value
    assert text in page1.title()        
    return page1

def checkcode(id_number_str):
    id_number_last= id_number_str.strip()[-1]
    id_number_str = id_number_str.strip()[:-1]   
    # 判断长度，如果不是 17 位，直接返回失败
    if len(id_number_str) != 17:
        return False
    id_regex = '[1-9][0-9]{14}([0-9]{2}[0-9X])?'
    if not re.match(id_regex, id_number_str):
        return False
    items = [int(item) for item in id_number_str]
    # 加权因子表
    factors = (7, 9, 10, 5, 8, 4, 2, 1, 6, 3, 7, 9, 10, 5, 8, 4, 2)
    # 计算17位数字各位数字与对应的加权因子的乘积
    copulas = sum([a * b for a, b in zip(factors, items)])
    # 校验码表
    check_codes = ('1', '0', 'X', '9', '8', '7', '6', '5', '4', '3', '2')
    checkcode = check_codes[copulas % 11].upper()
    if id_number_last.upper() == checkcode:
        return True
    else:
        return False
    
def get_datetime():
    res= time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))
    return res

def do_learn(page):
    page1=page
    a=list_card(page1)
    for i in a:
        a_idx=a.index(i)
        try:
            isok=page.locator('span.done-txt').nth(a_idx).text_content()
        except:
            isok=''
        print(i,isok)
        if isok=='完成':            
            continue
        page3=open_popup_text(page1,i)
        if '2022' in page3.title():
            pass
        else:
            print('跳过',i,end='')
            continue
        print(get_datetime(),page3.title())
        time.sleep(0.5)
        try:
            page3.click('text='+'进入学习')
            time.sleep(1)
            print(get_datetime(),page3.title())
            #print(page3.locator('div.nano-content').text_content())                    
        except:
            print(get_datetime(),'没有进入学习，继续未完成的课程：',page3.title(),end='')
            continue
            #print(page3.locator('div.main-body').text_content())  
        try:
            page3.click('text='+'进入该课程')
            print(get_datetime(),page3.title())
        except:
            print(get_datetime(),'没有进入该课程，选择新课程：',page3.title(),end='')
            #print(page3.locator('div.main-body').text_content())      
        try:
            page3.click('text='+'选择课程')
            print(get_datetime(),page3.title())
        except:
            print(get_datetime(),'没有选择课程',page3.title(),end='') 
        page3.on("dialog", lambda dialog: dialog.accept())
        time.sleep(60*9+5)
        page3.close()

def get_dialog_inner_list(page):
    a=[]
    #a=page.frame_locator("iframe").first.locator('ul.track-dialog-ctt').text_content().split('\n')  
    obj=page.frame_locator("iframe").first.locator('li.innercan.track-course-item')
    obj.last.text_content().strip()   
    for i in range(obj.count()):
        a.append(obj.nth(i).text_content().strip())   
    return a

def answer_page(page1):
    # Check input[name="score"] >> nth=4
    page1.locator("input[name=\"score\"]").nth(4).check()
    # Click .cs-option-radio >> nth=0
    page1.locator(".cs-option-radio").first.click()
    # Click li:nth-child(2) div .cs-option-cell span >> nth=0
    page1.locator("li:nth-child(2) div .cs-option-cell span").first.click()
    # Click li:nth-child(3) div .cs-option-cell span >> nth=0
    page1.locator("li:nth-child(3) div .cs-option-cell span").first.click()
    # Click li:nth-child(4) div .cs-option-cell span >> nth=0
    page1.locator("li:nth-child(4) div .cs-option-cell span").first.click()
    # Click li:nth-child(5) div .cs-option-cell span >> nth=0
    page1.locator("li:nth-child(5) div .cs-option-cell span").first.click()
    # Click li:nth-child(6) div .cs-option-cell span >> nth=0
    page1.locator("li:nth-child(6) div .cs-option-cell span").first.click()
    # Click textarea[name="\38 2dbc29d6fe948529895f33e46f9d068"]
    page1.locator("textarea >> nth=0").click()
    page1.locator("textarea >> nth=0").fill("无")
    time.sleep(2)    
    page1.locator("input[name=\"score\"]").nth(4).check()
    page1.locator("text=提交").click()
    time.sleep(1)
    # Click a:has-text("确定")
    page1.locator("a:has-text(\"确定\")").click()
    time.sleep(1)
    with page1.expect_navigation():
        page1.locator("text=查看结果").click()
    # Click text=关闭

def answer2(page2):
    # 选择答案 1-5
    page2.locator("text=✔ D 中心化业务处理系统 >> span").click()    
    page2.locator("text=✔ B 不可逆转性 >> span").click()   
    page2.locator("text=✔ A 比特币 >> span").click()   
    page2.locator("text=✔ B 中本聪 >> span").click()
    page2.locator("text=✔ B 中国 >> span").click()
    # 选择答案 6-10
    page2.locator("text=✔ A 正反馈 >> span").click()    
    page2.locator("text=✔ D 2020年 >> span").click()    
    page2.locator("text=✔ A 16亿 >> span").click()    
    page2.locator("text=✔ C 苹果公司 >> span").click()   
    page2.locator("text=✔ B 二进制 >> span").click()   
    # 11-15
    page2.locator("text=✔ D 生物医药 >> span").click() 
    page2.locator("text=✔ B 小分子药物 >> span").click()  
    page2.locator("text=✔ A 分子水平 >> span").click()   
    page2.locator("text=✔ A 感冒 >> span").click()    
    page2.locator("text=✔ A 产业结构和产业组织模式 >> span").click() 
    #16-20
    page2.locator("text=✔ B 服务 >> span").click()   
    page2.locator("text=✔ C 锁定效应 >> span").click()   
    page2.locator("text=✔ C 供给侧结构性改革 >> span").click()   
    page2.locator("text=✔ D 制造业 >> span").click()    
    page2.locator("text=✔ A 人才 >> span").click()
    # 多选题1
    page2.locator("text=A 密码技术 >> span").click()  
    page2.locator("text=B 共识算法 >> span").click()    
    page2.locator("text=C 嵌入式数据库 >> span").click()   
    page2.locator("text=D 智能合约 >> span").click()   
    page2.locator("text=E P2P网络 >> span").click()
    # 多选题2
    page2.locator("text=A 默克尔根 >> span").click()   
    page2.locator("text=B 哈希值 >> span").click()    
    page2.locator("text=C 时间戳 >> span").click()   
    page2.locator("text=D 随机数 >> span").click()   
    page2.locator("text=E 目标哈希函数 >> span").click()
    #  多选题3
    page2.locator("text=A 去中心化 >> span").click()    
    page2.locator("text=B 高度透明 >> span").click()    
    page2.locator("text=C 集体维护 >> span").click()   
    page2.locator("text=D 不可篡改 >> span").click()    
    page2.locator("text=E 安全可信 >> span").click()
    #  多选题4
    page2.locator("text=A 网络管理 >> span").click()   
    page2.locator("text=B P2P网络 >> span").click()    
    page2.locator("text=C DHT >> span").click()
    page2.locator("text=D 发现节点 >> span").click()   
    page2.locator("text=E 心跳服务 >> span").click()
    # 多选题5
    page2.locator("text=B 房产 >> span").click()   
    page2.locator("text=D 机器 >> span").click()
    # 多选题6
    page2.locator("text=A 5G的带宽非常宽 >> span").click()   
    page2.locator("text=B 5G能够提供高上100倍的链接密度 >> span").click()    
    page2.locator("text=C 5G具有低延时特点 >> span").click()
    # 多选题7  
    page2.locator("text=A 商汤科技 >> span").click()  
    page2.locator("text=B 旷视科技 >> span").click()     
    page2.locator("text=C 依图 >> span").click()    
    page2.locator("text=D 云从 >> span").click()
    # 多选题8 
    page2.locator("text=A 科技和产业步入近现代，实际上是追求在“极大和极小”上认识世界、改造世界 >> span").click()   
    page2.locator("text=B 想要在“极小”这个尺度上认识、改造世界，就离不开纳米技术 >> span").click()
    page2.locator("text=C 纳米技术具有变革性 >> span").click()
    page2.locator("text=E 纳米技术具有带动性 >> span").click()
    # 多选题9 
    page2.locator("text=A 传感器的核心是微纳加工技术、敏感材料 >> span").click()
    page2.locator("text=B 传感是智慧社会、智能社会、智慧城市最核心的技术 >> span").click()
    page2.locator("text=D 纳米技术是传感器的核心 >> span").click()
    # 多选题10    
    page2.locator("text=A 平台型 >> span").click()    
    page2.locator("text=B 交叉型 >> span").click()
    page2.locator("text=C 融合型 >> span").click()     
    page2.locator("text=E 普适型 >> span").click()
    
    # Click text=1、区块链是用密码技术将共识确认的区块按顺序追加形成的分布式账本。（2.5 分） ✔ A 正确 ✔ B 错误 >> span >> nth=2
    page2.locator("text=1、区块链是用密码技术将共识确认的区块按顺序追加形成的分布式账本。（2.5 分） ✔ A 正确 ✔ B 错误 >> span").nth(2).click()
    # Click text=2、数字签名算法主要用于构成默克尔树。（2.5 分） ✔ A 正确 ✔ B 错误 >> span >> nth=3
    page2.locator("text=2、数字签名算法主要用于构成默克尔树。（2.5 分） ✔ A 正确 ✔ B 错误 >> span").nth(3).click()
    # Click text=3、共识由多个参与节点按照一定机制确认或验证数据，确保数据在账本中具备正确性和一致性。（2.5 分） ✔ A 正确 ✔ B 错误 >> span >> nth=2
    page2.locator("text=3、共识由多个参与节点按照一定机制确认或验证数据，确保数据在账本中具备正确性和一致性。（2.5 分） ✔ A 正确 ✔ B 错误 >> span").nth(2).click()
    # Click text=4、嵌入式数据库消除了与客户机服务器配置相关的开销，需要较大的内存开销。（2.5 分） ✔ A 正确 ✔ B 错误 >> span >> nth=3
    page2.locator("text=4、嵌入式数据库消除了与客户机服务器配置相关的开销，需要较大的内存开销。（2.5 分） ✔ A 正确 ✔ B 错误 >> span").nth(3).click()
    # Click text=5、区块链的本质价值在于分布式的协同信任。（2.5 分） ✔ A 正确 ✔ B 错误 >> span >> nth=2
    page2.locator("text=5、区块链的本质价值在于分布式的协同信任。（2.5 分） ✔ A 正确 ✔ B 错误 >> span").nth(2).click()
    # Click text=6、我国央行数字货币第一期试点在雄安新区。（2.5 分） ✔ A 正确 ✔ B 错误 >> span >> nth=3
    page2.locator("text=6、我国央行数字货币第一期试点在雄安新区。（2.5 分） ✔ A 正确 ✔ B 错误 >> span").nth(3).click()
    # Click text=7、大数据是基于分布式网络的共享账本系统。（2.5 分） ✔ A 正确 ✔ B 错误 >> span >> nth=3
    page2.locator("text=7、大数据是基于分布式网络的共享账本系统。（2.5 分） ✔ A 正确 ✔ B 错误 >> span").nth(3).click()
    # Click text=8、一旦拥有无处不在的算力，智慧交通、智慧城市、智慧天气等全都有可能会发生改变。（2.5 分） ✔ A 正确 ✔ B 错误 >> span >> nth=2
    page2.locator("text=8、一旦拥有无处不在的算力，智慧交通、智慧城市、智慧天气等全都有可能会发生改变。（2.5 分） ✔ A 正确 ✔ B 错误 >> span").nth(2).click()
    # Click text=9、Siri是语音识别与信息聚合两项技术的一个综合体，但是逻辑仍旧比较简单。（2.5 分） ✔ A 正确 ✔ B 错误 >> span >> nth=3
    page2.locator("text=9、Siri是语音识别与信息聚合两项技术的一个综合体，但是逻辑仍旧比较简单。（2.5 分） ✔ A 正确 ✔ B 错误 >> span").nth(3).click()
    # Click text=10、根据本讲，与美国相比，中国在纳米科技论文总量、高引论文和专利授权方面在世界上处于落后地位。（2.5分） ✔ A 正确 ✔ B 错误 >> span >> nth=3
    page2.locator("text=10、根据本讲，与美国相比，中国在纳米科技论文总量、高引论文和专利授权方面在世界上处于落后地位。（2.5分） ✔ A 正确 ✔ B 错误 >> span").nth(3).click()   
    
    # Click text=提交
    page2.locator("text=提交").click()
    # Click a:has-text("确定")
    page2.locator("a:has-text(\"确定\")").click()
    # Click text=查看结果
    page2.locator("text=查看结果").click()
   

def get_catalog_playing(page):
    #'class="scormItem-no cl-catalog-link cl-catalog-link-sub item-no cl-catalog-playing"
    print(page.locator("a > cl-catalog-playing").last.text_content())    
    count=page.locator("div.cl-catalog-item-sub").count()
    a=[]
    for i in range(count):
        a.append(page.locator("div.cl-catalog-item-sub").nth(i).text_content().strip())
    return a
    
def playing_catalog_item_no(page):
    print('本节课题数：',page.locator('div.cl-catalog-item-sub').count()) 
    item_count=page.locator("a.scormItem-no.cl-catalog-link.cl-catalog-link-sub.item-no").count()
    print('本节未完成课题数：',item_count)
    for j in range(item_count):
        print(page.locator("a.scormItem-no.cl-catalog-link.cl-catalog-link-sub.item-no").first.text_content(),get_datetime())  #未完成课题
        page.locator("a.scormItem-no.cl-catalog-link.cl-catalog-link-sub.item-no").first.click()
        headertext=page.locator("div >>nth=0").text_content().replace('（','').split()
        if len(headertext)>1:
            times=re.findall('\d+',headertext[1])
        else:
            times=[100,0]        
        sec=(int(times[0])-int(times[1]))*60+30
        print('延时',sec)            
        delay_play(sec)  


def learn_dialog_inner_list(page):
    a=get_dialog_inner_list(page)
    print(len(a))
    for i in a:  
        print(i)      
        #page1=open_popup_text(page,i)
        with page.expect_popup() as popup_info:
            page.frame_locator("iframe").first.locator("text="+i).click()            
        page1 = popup_info.value
        #print(get_datetime(),page1.locator('body').inner_html())
        time.sleep(2)  
        
        if not page1.title()==i:
            page1.click('text='+'进入该课程')
            time.sleep(5)
        try:
            scormItem=get_catalog_playing(page1)
            print(scormItem)
        except:
            pass
        #print(get_section_list(page1))
        #current_time=page1.frame_locator("#aliPlayerFrame").locator('span.current-time').text_content()
        #print(current_time)
        headertext=page1.locator("div >>nth=0").text_content().replace('（','').split()
        print(headertext[:2])
        if headertext[0]=='关闭':
            try:
                answer_page(page1)
            except:
                answer2(page1)
            page1.close()
            time.sleep(2)
            continue
        #print(page1.locator('id=goNextStep').inner_html())
        playing_catalog_item_no(page1)
                             
        if len(headertext)>1:
            times=re.findall('\d+',headertext[1])
        else:
            times=[100,0]
        if len(times)==1:
            times=[100,int(times[0])]
        else:      
            sec=(int(times[0])-int(times[1]))*60+30
            print('延时',sec)            
            delay_play(sec)                     
            page1.close()
            continue                   
        #print(times,headertext)
        if times[0]==times[1]:            
            print("已经完成",end='\n')           
            #page1.frame_locator("iframe").first.locator("text=关闭").click()
            page1.close()
            continue       
        section=get_section_list(page1)        
        for sect in section:
            do_play_section(page1,sect)
        page1.close()

def do_play_section(page,sect=None):
    if sect:
        page.frame_locator("iframe").first.locator('div.section >> text='+sect[0]).last.click()
        time.sleep(2)
    do_playing(page)

def delay_play(sec):
    while sec>0:
        sec-=1
        time.sleep(1)
        print('倒计时',sec,'秒',end='\r')

def do_playing(page):
        plaing=True
        while plaing:
            time.sleep(1)
            if '100%' in page.locator("div >>nth=0").text_content():
                plaing=False
                break
            current_time=page.frame_locator("#aliPlayerFrame").locator('span.current-time').text_content()
            duration_time=page.frame_locator("#aliPlayerFrame").locator('span.duration').text_content()
            if  current_time==duration_time and current_time!='00:00':
                print(get_datetime(),page.title(),'——>已经完成')
                plaing=False
                break
            else:
                print(current_time,end='\r')
        return 
            
        #time.sleep(waite_time+10)
        
def get_section_list(page):
    res=[]     
    section_obj=page.frame_locator("iframe").first.locator('li.section-item')
    for i in range(section_obj.count()):
        section_title=section_obj.nth(i).locator('span.section-title').text_content().strip()
        second_line=section_obj.nth(i).locator('div.second-line').text_content().strip()
        res.append([section_title,second_line])       
    print(res)
    return res

def print_(page):
    print(page.title(),"正在打印")
    with page.expect_popup() as popup_info:
        page.locator('text=证书打印').click()            
    page_print1 = popup_info.value    
    time.sleep(10)
    for row in range(page_print1.locator('text=打印证书').count()):
        with page_print1.expect_popup() as popup_info:
            page_print1.locator('text=打印证书').nth(row).click()            
        page_print2 = popup_info.value    
        page_print2.locator('text=打印').click()
        time.sleep(30)
        page_print2.close()
    page_print1.close()
    print(page.title(),"打印完成")

if __name__ == '__main__':
    cwd=Path.cwd().name
    print(cwd,end='')
    if checkcode(cwd):
        os.environ.setdefault('sfzh',cwd)
        print('有效身份证号,设置环境变量sfzh',end='\n')        
    sfzh=os.getenv('sfzh')
    if len(sys.argv)==1 and sfzh==None:
        print('请输入身份证号')
        sys.exit()
    else:
        if len(sys.argv)==2:
            sfzh=sys.argv[1]            
            if checkcode(sfzh):
                os.environ.setdefault('sfzh',sfzh)
            else:
                if sfzh.upper()=='ALL':
                    import  pandas as pd
                    df=pd.read_excel(Path('..','教育局人员.xlsx'))
                    df=df[df['标记']=='是']
                    sfzh=df['身份证号'].tolist()[randint(0,len(df)-1)]
                    print('随机身份证号为',sfzh,df[df['身份证号']==sfzh]['姓名'],'\n')
                    os.environ.setdefault('sfzh',sfzh)
                else:
                    print('身份证号不正确')
                    sys.exit()
    login_storage_file=os.environ['sfzh']+'_login_hxpx.json'
    if Path(login_storage_file).exists():
        page2=login_storage(browser,sfzh)
    else:
        page=context.new_page()
        page2=login(page,sfzh)
    #问候语 及完成学时数
    tips_title=page2.locator('div.tips-title.line-over').text_content()
    print(tips_title)    
    print(page2.locator("a.desc-wrap").last.text_content()) 
    line_over=page2.locator("h4.line-over").count()
    for row in range(line_over):
        text=page2.locator("h4.line-over").first.text_content()
        print(text)
        if '2022' in text:
            page2.locator("h4.line-over ").first.click()
            learn_dialog_inner_list(page2)
    page2.goto(url['hxpx'])
    print_(page2)

    
    page2.close()
    browser.close()
    '''
     # Click text=推动新时代基础教育高水平高质量普及
    with page2.expect_popup() as popup_info:
        page2.frame_locator("iframe").first.locator("text=推动新时代基础教育高水平高质量普及").click()
    page1 = popup_info.value
    time.sleep(60)
    page1=open_gxkm(page2)
    for times_ in range(3):
        do_learn(page1)
    page1.close()
    '''
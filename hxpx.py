from random import randint
from tabnanny import check
from webbrowser import get
from playwright.sync_api import sync_playwright
import sys,time,os,re,json
from pathlib import Path
from playwright.sync_api import expect
from  socket import gethostname
import  pandas as pd

f_md=Path("C:","Users","qllwx","Documents","人员名单dafd.xlsx")
if not f_md.exists():
    f_md="人员名单.xlsx"


hostname=gethostname()
headless=not(hostname in['B550M-K','localhost','qllwx-PowerEdge-R730'])
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
    #page.on('系统提示', lambda dialog: dialog.accept())
    try:
        with page.expect_navigation():
            page.locator("text=继续登录").click()
    except:
        pass
    time.sleep(8)
    print(page.title(),sfzh)
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
    time.sleep(1)
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
    if len(id_number_str) != 18:
        return False
    id_number_last= id_number_str.strip()[-1]
    id_number_str = id_number_str.strip()[:-1]   
    # 判断长度，如果不是 17 位，直接返回失败
    
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
    time.sleep(3)
    #a=page.frame_locator("iframe").first.locator('ul.track-dialog-ctt').text_content().split('\n')  
    obj=page.frame_locator("iframe").first.locator('li.innercan.track-course-item')
    #obj.last.text_content().strip()   
    for i in range(obj.count()):
        a.append(obj.nth(i).text_content().strip())   
    return a

def answer_yc(page2):
     # 1
    page2.locator("text=✔ B 以人为核心 >> span").click()    
    page2.locator("text=✔ D 绿色循环低碳发展 >> span").click()    
    page2.locator("text=✔ D 共商共建共享 >> span").click()   
    page2.locator("text=✔ A 二 >> span").click()    
    page2.locator("text=✔ B 二 >> span").click()
    #6 Click text=✔ C 开放包容 >> span
    page2.locator("text=✔ C 开放包容 >> span").click()   
    page2.locator("text=✔ D 专业化 >> span").click()  
    page2.locator("text=✔ C 2035 >> span").click()    
    page2.locator("text=✔ C 和平与发展 >> span").click()   
    page2.locator("text=✔ D 改革创新 >> span").click()
    # 11Click text=✔ B 1，1.5 >> span
    page2.locator("text=✔ B 1，1.5 >> span").click()    
    page2.locator("text=✔ A 概念验证阶段 >> span").click()   
    page2.locator("text=✔ B 统筹推进基础设施建设 >> span").click()   
    page2.locator("text=✔ A 0.3 >> span").click()   
    page2.locator("text=✔ C 0.092 >> span").click()
    # 16Click text=✔ B 混合分工 >> span
    page2.locator("text=✔ B 混合分工 >> span").click()   
    page2.locator("text=✔ A 35 >> span").click()    
    page2.locator("text=✔ B 行业 >> span").click()   
    page2.locator("text=✔ D 基础公共信息 >> span").click()   
    page2.locator("text=✔ B 实体 >> span").click()
    # Click text=A 京津冀协同发展 >> span
    page2.locator("text=A 京津冀协同发展 >> span").click()   
    page2.locator("text=B 长江经济带发展 >> span").click()   
    page2.locator("text=C 粤港澳大湾区建设 >> span").click()
    page2.locator("text=D 长三角一体化发展 >> span").click()    
    page2.locator("text=E 推动黄河流域生态保护和高质量发展 >> span").click()
    # Click text=A 粮 >> span
    page2.locator("text=A 粮 >> span").click()
    page2.locator("text=B 棉 >> span").click()
    page2.locator("text=C 油 >> span").click()    
    page2.locator("text=D 糖 >> span").click()
    page2.locator("text=E 肉 >> span").click()
    # Click text=A 全面提高对外开放水平 >> span
    page2.locator("text=A 全面提高对外开放水平 >> span").click()    
    page2.locator("text=B 完善外商投资准入前国民待遇加负面清单管理制度，有序扩大服务业对外开放 >> span").click()    
    page2.locator("text=C 完善自由贸易试验区布局 >> span").click()   
    page2.locator("text=D 稳慎推进人民币国际化，坚持市场驱动和企业自主选择 >> span").click()    
    page2.locator("text=E 发挥好中国国际进口博览会等重要展会平台作用 >> span").click()
    # Click text=A 高附加值的制造业 >> span
    page2.locator("text=A 高附加值的制造业 >> span").click()    
    page2.locator("text=B 高附加值的服务业 >> span").click()

    page2.locator("text=A 完善规则、制度、法律 >> span").click()    
    page2.locator("text=B 协调配套国家法律和地方法规 >> span").click()    
    page2.locator("text=C 提升政策、法规的透明度 >> span").click()   
    page2.locator("text=D 切换事中、事后的监管模式 >> span").click()
    # Click text=A 亚洲基础设施投资银行 >> span

    page2.locator("text=A 亚洲基础设施投资银行 >> span").click()  
    page2.locator("text=B 金砖国家新开发银行 >> span").click() 
    page2.locator("text=D 丝路基金 >> span").click()    
    page2.locator("text=E 中非发展基金 >> span").click()
    # Click text=A 继承和创新的关系 >> span

    page2.locator("text=A 继承和创新的关系 >> span").click()
    page2.locator("text=B 政府和市场的关系 >> span").click()
    page2.locator("text=C 开放和自主的关系 >> span").click()
    page2.locator("text=D 发展和安全的关系 >> span").click()
    page2.locator("text=E 战略和战术的关系 >> span").click()

    # Click text=A 国际教育中心、人才中心 >> span
    page2.locator("text=A 国际教育中心、人才中心 >> span").click()
    page2.locator("text=B 国际先进生产力中心、经济中心 >> span").click()
    page2.locator("text=C 国际管理创新中心 >> span").click()
    page2.locator("text=D 全球原始创新策源地 >> span").click()
    page2.locator("text=E 国际文化中心、交流中心 >> span").click()

    page2.locator("text=A 关键核心技术 >> span").click()
    page2.locator("text=D 产业基础高级化和产业链现代化 >> span").click()

    # Click text=A 经济发展取得新成效 >> span
    page2.locator("text=A 经济发展取得新成效 >> span").click()
    page2.locator("text=B 改革开放迈出新步伐 >> span").click()
    page2.locator("text=C 社会文明程度得到新提高 >> span").click()
    page2.locator("text=D 民生福祉达到新水平 >> span").click()
    page2.locator("text=E 国家治理效能得到新提升 >> span").click()

    page2.locator("text=1、根据本讲，深化农村改革，要健全城乡统一的建设用地市场，积极探索实施农村集体经营性建设用地入市制度。（2.5 分） ✔ A 正确 ✔ B 错误 >> span").nth(2).click()
    # Click text=2、推动共建“一带一路”高质量发展，要坚持以政府为主体，以市场为导向，健全多元化投融资体系。（2.5 分） ✔ A 正确 ✔ B 错误 >> span >> nth=3
    page2.locator("text=2、推动共建“一带一路”高质量发展，要坚持以政府为主体，以市场为导向，健全多元化投融资体系。（2.5 分） ✔ A 正确 ✔ B 错误 >> span").nth(3).click()
    # Click text=3、根据本讲，“十四五”期间仍是我国宝贵的战略发展时期。（2.5 分） ✔ A 正确 ✔ B 错误 >> span >> nth=3   
    page2.locator("text=3、根据本讲，“十四五”期间仍是我国宝贵的战略发展时期。（2.5 分） ✔ A 正确 ✔ B 错误 >> span").nth(2).click()
    # Click text=4、根据本讲，只要企业所处行业不在负面清单就可以在自贸区注册登记。（2.5 分） ✔ A 正确 ✔ B 错误 >> span >> nth=3
    page2.locator("text=4、根据本讲，只要企业所处行业不在负面清单就可以在自贸区注册登记。（2.5 分） ✔ A 正确 ✔ B 错误 >> span").nth(2).click()
    # Click text=5、根据本讲，开放引进的外国投资者不利于我国供给侧结构性改革。（2.5 分） ✔ A 正确 ✔ B 错误 >> span >> nth=3
    page2.locator("text=5、根据本讲，开放引进的外国投资者不利于我国供给侧结构性改革。（2.5 分） ✔ A 正确 ✔ B 错误 >> span").nth(3).click()
    # Click text=6、根据本讲，世界贸易组织抵制双边自由贸易协定。（2.5 分） ✔ A 正确 ✔ B 错误 >> span >> nth=3
    page2.locator("text=6、根据本讲，世界贸易组织抵制双边自由贸易协定。（2.5 分） ✔ A 正确 ✔ B 错误 >> span").nth(3).click()
    # Click text=7、根据本讲，我国正在实行降低关税和主动扩大进口。（2.5 分） ✔ A 正确 ✔ B 错误 >> span >> nth=2
    page2.locator("text=7、根据本讲，我国正在实行降低关税和主动扩大进口。（2.5 分） ✔ A 正确 ✔ B 错误 >> span").nth(2).click()
    # Click text=8、十九届五中全会公报指出，我国已转向高质量发展阶段，发展不平衡不充分问题已经得到充分解决。（2.5 分） ✔ A 正确 ✔ B 错误 >> span >> nth=3
    page2.locator("text=8、十九届五中全会公报指出，我国已转向高质量发展阶段，发展不平衡不充分问题已经得到充分解决。（2.5 分） ✔ A 正确 ✔ B 错误 >> span").nth(3).click()
    # Click text=9、经济社会需求和科技供给的内在矛盾是两大驱动力。（2.5 分） ✔ A 正确 ✔ B 错误 >> span >> nth=2
    page2.locator("text=9、经济社会需求和科技供给的内在矛盾是两大驱动力。（2.5 分） ✔ A 正确 ✔ B 错误 >> span").nth(2).click()
    page2.locator("text=10、科学和技术要高度融合，要解决社会和经济发展当中的一些现实问题。（2.5分） ✔ A 正确 ✔ B 错误 >> span").nth(2).click()
     # Click text=提交
    page2.locator("text=提交").click()
    # Click a:has-text("确定")
    page2.locator("a:has-text(\"确定\")").click()
    # Click text=查看结果
    page2.locator("text=查看结果").click()



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
    time.sleep(5)
    global Current_name
    item_sub_count=page.locator('div.cl-catalog-item-sub').count()
    if item_sub_count==0:
        item_sub_count=page.frame_locator("iframe").first.locator("li.section-item").count()
        item_count=item_sub_count -  page.frame_locator("iframe").first.locator("span.finish-tig-item").count() 
        
        for i in range(item_sub_count):
            obj=page.frame_locator("iframe").first.locator("li.section-item").nth(i)
            obj_text=obj.text_content()
            print(Current_name,obj.text_content())
            if '已完成' in obj_text:
                continue
            else:
                obj.click()               
                
                try:
                    do_playing(page)
                except:
                    time_text=obj_text.split()[-1]
                    time_text=time_text.split(':')
                    time_seconds=int(time_text[1])*60+int(time_text[2])
                    print('等待播放时间：',time_seconds)
                    time.sleep(time_seconds)

        return
    else:
        item_count=page.locator("a.scormItem-no.cl-catalog-link.cl-catalog-link-sub.item-no").count()
    print('本节课题数：',item_sub_count)     
    print('本节未完成课题数：',item_count)
    for j in range(item_count):
        print(Current_name,page.locator("a.scormItem-no.cl-catalog-link.cl-catalog-link-sub.item-no").first.text_content(),get_datetime())  #未完成课题
        page.locator("a.scormItem-no.cl-catalog-link.cl-catalog-link-sub.item-no").first.click()
        headertext=page.locator("div >>nth=0").text_content().replace('（','').split()
        if len(headertext)>1:
            times=re.findall('\d+',headertext[1])
            print(Current_name,"观看时长不少于%s分钟,已经观看%s分钟"%(times[0],times[1]))
            sec=(int(times[0])-int(times[1]))*60+30
        else:            
            try:                
                duration_time=page.frame_locator("#iframe_aliplayer").locator("span.duration").text_content()
                current_time=page.frame_locator("#iframe_aliplayer").locator("span.current-time").text_content()
                d1=int(duration_time.split(':')[0])
                d2=int(duration_time.split(':')[1])
                c1=int(current_time.split(':')[0])
                c2=int(current_time.split(':')[1])
                sec=(d1-c1)*60-c2+d2
                print(Current_name,"本节共需要时长%s,已播放%s，还需%s秒"%(duration_time,current_time,sec))                
            except:
                duration_time=60
                current_time=0
                print('没找到时长,默认为60分钟')
                sec=60*60
        print('播放时长%s秒'%sec)            
        delay_play(sec)  


def learn_dialog_inner_list(page):
    global Current_name
    a=get_dialog_inner_list(page)
    print(len(a))
    if len(a)==0:
        time.sleep(2)
        try:
            page.locator("button").first.click()
        except:
            pass
        time.sleep(2)
        print_zs(page)

        return
    a.sort(reverse=True)
    for i in a:  
        print(Current_name,i)      
        #page1=open_popup_text(page,i)
        with page.expect_popup() as popup_info:
            page.frame_locator("iframe").first.locator("text="+i).click()            
        page1 = popup_info.value
        #print(get_datetime(),page1.locator('body').inner_html())
        time.sleep(10)  
        
        if not page1.title()==i:
            page1.click('text='+'进入该课程')
            time.sleep(5)
        try:
            scormItem=get_catalog_playing(page1)
            print(Current_name,scormItem)
        except:
            pass
        #print(get_section_list(page1))
        #current_time=page1.frame_locator("#aliPlayerFrame").locator('span.current-time').text_content()
        #print(current_time)
        headertext=page1.locator("div >>nth=0").text_content().replace('（','').split()
        print(Current_name,headertext[:2])
        if headertext[0]=='关闭':
            print(headertext)
            if headertext[1]=='2021“十四五”大战略与2035远景〔三〕':
                answer_yc(page1)
                continue
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
            print(Current_name,"已经完成",end='\n')           
            #page1.frame_locator("iframe").first.locator("text=关闭").click()
            page1.close()
            continue       
        section=get_section_list(page1)
        section.sort(reverse=True)        
        for sect in section:
            do_play_section(page1,sect)
        page1.close()

def do_play_section(page,sect=None):
    if sect:
        page.frame_locator("iframe").first.locator('div.section >> text='+sect[0]).last.click()
        time.sleep(3)
    do_playing(page)

def delay_play(sec):
    show_delay_time=os.getenv('show_delay_time')
    while sec>0:
        sec-=1
        time.sleep(1)
        if show_delay_time:
            print('倒计时',sec,'秒',end='\r')

def do_playing(page):
        global Current_name
        show_delay_time=os.getenv('show_delay_time')
        plaing=True
        while plaing:
            time.sleep(1)
            if '100%' in page.locator("div >>nth=0").text_content():
                plaing=False
                break
            current_time=page.frame_locator("#aliPlayerFrame").locator('span.current-time').text_content()
            duration_time=page.frame_locator("#aliPlayerFrame").locator('span.duration').text_content()
            if  current_time==duration_time and current_time!='00:00':
                print(Current_name,get_datetime(),page.title(),'——>已经完成')
                plaing=False
                break
            else:
                if show_delay_time=='True':
                    print(current_time,end='\r')
        return 
            
        #time.sleep(waite_time+10)
        
def get_section_list(page):
    

    res=[] 
    time.sleep(2)    
    section_obj=page.frame_locator("iframe").first.locator('li.section-item')
    for i in range(section_obj.count()):
        section_title=section_obj.nth(i).locator('span.section-title').text_content().strip()
        second_line=section_obj.nth(i).locator('div.second-line').text_content().strip()
        res.append([section_title,second_line])       
    print(res)
    r_res=[]    
    return res

def print_zs(page):
    for i in range( page.locator("button").count()):
        page.locator("button").first.click()
        time.sleep(2)

    global Current_name
    print(Current_name,"正在打印")
    with page.expect_popup() as popup_info:
        page.locator('text=证书打印').click()            
    page_print1 = popup_info.value    
    time.sleep(5)
    page_print1.locator('text=已完成').click()
    time.sleep(5)
    #obj=page_print1.locator('div.list-p')
    obj=page_print1.locator('text=打印证书')
    list_count=obj.count()
    if list_count==2:
        print(Current_name,'全部学习完成')
        #f_md_set_complete(sfzh)       
    else:
        print(Current_name,list_count,'完成学习')
        
        #return
    #f_md_set_complete(sfzh)
    obj=page_print1.locator('div.list-p')
    for row in range(list_count):
        title=obj.nth(row).locator('a').first.text_content().strip()
        print(Current_name,title)
        with page_print1.expect_popup() as popup_info:
            page_print1.locator('text=打印证书').nth(row).click()            
        page_print2 = popup_info.value    
        time.sleep(5)
        fn=Current_name+'_'+sfzh+"_"+title+".png"
        #screenshot(page_print2,fn)
        page_print2.screenshot(path=fn)
        #page_print2.locator('text=打印').click()
        #time.sleep(30)
        page_print2.close()
    page_print1.close()
    print(Current_name,"打印完成")
    f_md_set_complete(sfzh)

def f_md_set_complete(sfzh):
    df=pd.read_excel(f_md)
    df.loc[df['身份证号']==sfzh,'标记']='complete'
    df.to_excel(f_md,index=False)


def save_sfzh_to_file(sfzh,name):    
    df=pd.read_excel(f_md)
    if sfzh in df['身份证号'].values:
        pass
    else:
        df.loc[len(df.index)]=[name,sfzh,'是']
        #df.loc[len(df.index)] = [value1, value2, value3, ...]
        df.to_excel(f_md,index=False)



if __name__ == '__main__':
    global Current_name
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
                    df=pd.read_excel(f_md)
                    df=df[df['标记']=='是']
                    sfzh=df['身份证号'].tolist()[randint(0,len(df)-1)]
                    print('随机身份证号为',sfzh,df[df['身份证号']==sfzh]['姓名'],'\n')
                    os.environ.setdefault('sfzh',str(sfzh))
                else:
                    print(sfzh,'身份证号不正确')
                    sys.exit()
   
    login_storage_file=os.environ['sfzh']+'_login_hxpx.json'
    if Path(login_storage_file).exists():
        page2=login_storage(browser,sfzh)
    else:
        page=context.new_page()
        page2=login(page,str(sfzh))
    #问候语 及完成学时数
    time.sleep(1)
    tips_title=page2.locator('div.tips-title.line-over').text_content()
    Current_name=tips_title.split('，')[1]
    print(tips_title,sfzh)
    print(Current_name,page2.locator("a.desc-wrap").last.text_content()) 
    complete_xs=page2.locator("a.desc-wrap>>p").last.text_content().split('.')[0]
    if int(complete_xs)>89:
        print(Current_name,'已完成学时',get_datetime())
        if os.getenv('hxpx_print')=="True":
            print_zs(page2)
        page2.close()
        f_md_set_complete(sfzh)
        sys.exit()
    if page2.locator("img[alt=\"关闭\"]").count()>0:
        page2.locator("img[alt=\"关闭\"]").first.click()
    
    
    save_sfzh_to_file(sfzh,Current_name)    
    
    
    line_over=page2.locator("h4.line-over").count()
    if line_over==0:
        f_md_set_complete(sfzh)    

    for row in range(line_over):
        text=page2.locator("h4.line-over").nth(row).text_content()
        print(Current_name,text)
        if '2022' in text:
            obj=page2.locator("h4.line-over ")
            print(Current_name,obj.count(),obj.nth(row).inner_text())
            obj.nth(row).click()
            time.sleep(2)
            learn_dialog_inner_list(page2)
    f_md_set_complete(sfzh)  
    page2.goto(url['hxpx'])
    print_zs(page2)    
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
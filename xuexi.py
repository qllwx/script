from playwright.sync_api import Playwright, sync_playwright, expect
from PIL import Image
from time import sleep
import sqlite3,json,os,re,random
import pandas as pd
from snownlp import SnowNLP

URL={'专项答题':'https://pc.xuexi.cn/points/exam-paper-list.html',
     '每日答题':'https://pc.xuexi.cn/points/exam-practice.html',
     '我的积分':'https://pc.xuexi.cn/points/my-points.html',
     '积分排行':'https://pc.xuexi.cn/points/points-rank.html',
     '积分规则':'https://pc.xuexi.cn/points/points-rule.html',
     '积分记录':'https://pc.xuexi.cn/points/points-record.html',
     '每周答题':'https://pc.xuexi.cn/points/exam-weekly-list.html',
     }

global played
global my_points
con=sqlite3.connect("xuexi.db")
cur=con.cursor()
sql='create table if not exists dt (id integer primary key,tx text,body text,answers text,ts text,answer text)'
cur.execute(sql)
con.commit()

os.putenv('PLAYWRIGHT_DEBUG', '1')
os.putenv('audio_total', '01:00')

def save_data(dcit):
    #print("save_data:",dcit)
    sql='insert into dt (tx,body,answers,ts,answer) values(?,?,?,?,?)'
    cur.execute(sql,(dcit['tx'],dcit['body'],dcit['answers'],dcit['ts'],dcit['answer']))
    con.commit()



playwright=sync_playwright().start()
browser = playwright.chromium.launch(headless=False,channel='msedge')
context = browser.new_context()
page = context.new_page()
 
def login(page):    
    # Go to https://pc.xuexi.cn/points/my-points.html
    page.goto("https://pc.xuexi.cn/points/my-points.html")
    print(page.title())
    page.screenshot(path="my-points.png")
    page.mouse.wheel(0,1024)    
    while not page.title() == "我的积分":
        sleep(1)
    print(page.title())
    sleep(3)
    put_my_point(page)        
    return page

# Click text=每日答题
def go_exam_practice(page):
    page.goto("https://pc.xuexi.cn/points/exam-practice.html")
    sleep(2)
    expect(page).to_have_url("https://pc.xuexi.cn/points/exam-practice.html")
    print(page.title())
    for count in range(20):
        exam_practice(page)
        print(count)

def get_line_feed(page,get_answer_list=False):
    answer =[]
    if page.locator("text=查看提示").count()==0:
        return None
    page.locator("text=查看提示").click()
    sleep(0.5)
    popover_inner_content=page.locator("div.line-feed").text_content().strip()
    for i in range(page.locator("div.line-feed >> font").count()):
        text=page.locator("div.line-feed >> font").nth(i).inner_text()
        if len(text)>0 and  not(text  in answer):
            answer.append(text) 
    page.locator("text=查看提示").click()
    for a in answer:
        popover_inner_content=popover_inner_content.replace(a,'[%s]'%a,1)
    if get_answer_list:
        return answer
    else:
        popover_inner_content=popover_inner_content.replace('[]','').replace('][','')
        return popover_inner_content

def get_answer_from_page(page):
    answer=get_line_feed(page,get_answer_list=True)
    tx=page.locator("div.q-header").text_content().split()[0]
    body=page.locator("div.q-body").text_content()
    if count_page_kh(page)==len(answer) or tx=='填空题':
        return answer
    else:
        return get_all_answers(page)

def get_all_answers(page):
    answers=[]
    for i in range(page.locator("div.q-answers").count()):
        answers.append(page.locator("div.q-answers").nth(i).inner_text())
    return answers

def is_all_right_answers(page):
    tx=page.locator("div.q-header").text_content().split()[0]
    if tx=='多选题':
        answer=get_line_feed(page,get_answer_list=True)
        if len(answer)<=count_page_kh(page):
            return True
        else:
            return False



def put_answer(page,answer):
    sleep(0.5)
    ans_i=0
    tx=page.locator("div.q-header").text_content().split()[0]
    tx=tx[:3]
    body=page.locator("div.q-body").text_content()
    if tx=='多选题':
        answer_count=count_page_kh(page)
        answers_count=page.locator("div.q-answers >>div ").count()
        print(answer_count,answers_count)
        if answer_count==answers_count:
            print("全选")
            for i in range(page.locator("div.q-answers >> div ").count()):
                page.locator("div.q-answers >> div").nth(i).click()
            for i in range(page.locator("button").count()):
                obj=page.locator("button").nth(i)
                if obj.is_enabled():
                    obj.click()
            sleep(1)
            return

    if tx=='单选题':
        answer_count=1
    else:
        answer_count=len(answer)
    for i in range(answer_count):
        text=answer[i]
        if text=='':           
            continue
        if ans_i<page.locator("div.q-body >> input").count():
            page.locator("div.q-body >> input").nth(ans_i).fill(text)
        else:
            if is_all_right_answers(page):
                page.locator("div.q-answers >> div").nth(i).click()
                continue
            ans_text=page.locator("div.q-answers >> div").nth(ans_i).inner_text()
            ans_zhongwen=re.sub('[^\u4E00-\u9FA5]',"", ans_text)
            text_zhongwen=re.sub('[^a-z|A-Z|\d|\u4E00-\u9FA5|\.]',"", text)
            if  len(re.findall(text,ans_zhongwen))>0:
                page.locator("div.q-answers >> div").nth(ans_i).click()
                continue
            try:
                page.locator("div.q-answers >> div:has-text('%s')"%text_zhongwen).nth(0).click()
            except:
                #没有与提示相同的答案，采用关键词选择 
                keywords=SnowNLP(text).keywords(limit=1) 
                if len(keywords)>0:             
                    keywords=keywords[0]
                else:
                    keywords=text[:2]
                k_count=page.locator("div.q-answers >> div:has-text('%s')"%keywords).count()
                print("keywords:",keywords,k_count)
                if k_count==0:
                    obj=page.locator("div.q-answers >> div").nth(0)
                    obj.click()
                    print("选择第一个:",obj.inner_text())
                    continue

                try:
                    obj=page.locator("div.q-answers >> div:has-text('%s')"%keywords).nth(ans_i)
                    obj.click()
                    print(obj.inner_text())
                except:
                    #没有与提示相同的答案，选择第一个
                    #page.locator("div.q-answers >> div").nth(random.randint(0,page.locator("div.q-answers >> div").count()-1)).click()
                    obj=page.locator("div.q-answers >> div").nth(0)
                    obj.click()
                    print("选择第一个:",obj.inner_text())

                ans_i+=1
                continue
               
                #page.locator("div.q-answer").nth( ans_i).click()
        ans_i+=1
    if page.locator("button").count() == 1:
        print(page.locator("button").first.inner_text())
        page.locator("button").first.click()  
    else:
        page.locator("button:has-text('交 卷')").click()
            
def is_video(page):
    pop_text=get_line_feed(page)
    if pop_text=='请观看视频':
        print('这是-》请观看视频')
        put_answer(page,[pop_text])
        #page.locator("button").click()
        sleep(2)
        
        return True
    else:
        return False

def get_right_answer(page):
    if page.locator("div.answer").count()>0:
        right_answer=page.locator("div.answer").nth(0).inner_text().split('：')[1]
        return right_answer
    else:
        right_answer=db_search_answer(page)
        return right_answer

def db_search_answer(page):
    tx=page.locator("div.q-header").text_content().split()[0]
    body=page.locator("div.q-body").text_content()
    sql='select answer from dt where tx=? and body=? '
    cur.execute(sql,(tx,body))
    answer=cur.fetchone()
    if answer==None:
        return None
    else:
        return answer[0]

def get_exam(page):
    
    sleep(1)
    answer_count=0
    try:
        tx=page.locator("div.q-header").text_content().split()[0]
        tx=tx[:3]
    except:
        if page.locator("button").inner_text() in ['再来一组','下一题','确定']:
            page.locator("button").click()
        return

    body=page.locator("div.q-body").text_content()
    if tx=='填空题':
        answers=''
        answer_count=page.locator("div.q-body >> input").count()          
    else:
        answers=page.locator("div.q-answers").text_content()  
    ts=get_line_feed(page)
    d={'tx':tx,'body':body,'answers':answers,'ts':ts} 
    answer=[]
    if ts:
        if '[' in ts:    
            for item in d['ts'].split('['):
                if item.find(']')>0:
                    answer.append(item.split(']')[0])
    if answer_count>0:
        answer=answer[:answer_count]
    ans='|'.join(answer)
    d['answer']=ans      
    return d
   



def exam_practice(page):
    if page.locator("button").count()>1:
        return
    if page.locator("button").inner_text() in ['再来一组','下一题','确定']:
        page.locator("button").click()
        sleep(1)
    if page.locator("text=查看解析").count()>0:
        d['answer']=page.locator("div.answer").nth(0).inner_text().split('：')[1]
        print("查看解析，正确答案是：",d['answer']) 
        print(d)
        return        
    d=get_exam(page)
    print(list(d.values()))
    if is_video(page):
        answer=get_right_answer(page) 
        print(answer)
        d['answer']=answer
        save_data(d)
        print(d,'已经保存',sep='\n')
        return
    #answer=get_answer_from_page(page)
    #ans='|'.join(answer)
    #d['answer']=ans    
    answer=d['answer'].split('|')
    put_answer(page,answer)
    
    save_data(d)
    print(page.locator("button").inner_text())
    sleep(5)
   

#统计多个答案的个数    
def count_kh(string):
    a=re.findall('（）',string)    
    return len(a)

def count_page_kh(page):
    str=page.locator("div.q-body").text_content()
    return count_kh(str)


def click_first_sapn_text(page):
    global played
    played+=1
    if played>10:
        return
    span_count=page.locator("span.text").count()
    if span_count==0:
        return
    for i in   range(span_count):# random.sample(range(span_count),1):
        obj=page.locator("span.text").nth(i)
        text=obj.inner_text()
        print(text)
        try:
            with page.expect_popup() as popup_info:
                obj.click()
            page_i=popup_info.value
            try_play(page_i)
        except Exception as e:
            print(e)
            pass
        click_first_sapn_text(page_i)
        page_i.close()
        sleep(1)
def try_play(page):
    try:
        page.locator("button.voice-lang-switch").click()
        if os.getenv("audio_total")==None: 
            audio_total=page.locator("span.y-audio-total").inner_text()
        else:
            audio_total=os.getenv("audio_total")      
        audio_current=page.locator("span.y-audio-current").inner_text()         
        while not audio_total==audio_current:
            audio_current=page.locator("span.y-audio-current").inner_text()
            print(audio_current,audio_total,end='\r')    
            sleep(1)
        #page.close()
        #sleep(2)
    except Exception as e:
        print(e,"没有播放音频")
        pass
def get_have_no(page):
    have_no=page.locator("div.no-data").inner_text()
    if have_no=='暂无数据':
        return True
    else:
        return False
def get_card_count(page):
    card_count=page.locator("div.my-points-card").count()
    return card_count
def get_card_text(page):
    card_count=page.locator("div.my-points-card").count()
    card_text=[]
    for i in range(card_count):
        card_text.append(page.locator("p.my-points-card-title").nth(i).inner_text())
    return card_text
def get_card_points(page):
    card_count=page.locator("div.my-points-card").count()
    card_points=[]
    for i in range(card_count):
        card_points.append(page.locator("div.my-points-card-text").nth(i).inner_text())
    return card_points
def get_card_buttonbox(page):
    card_count=page.locator("div.my-points-card").count()
    card_points=[]
    for i in range(card_count):
        card_points.append(page.locator("div.buttonbox").nth(i).inner_text())
    return card_points

         

def xdwz(page):
    global played
    played=0
    # Go to https://pc.xuexi.cn/points/my-points.html
    page.goto("https://pc.xuexi.cn/points/my-points.html")    
    obj=page.locator("text=去看看").nth(0)
    if obj.is_enabled():
        obj.click()
    else:
        print("没有可以点击的按钮")
        return
    print(page.title())
    sleep(2)
    with page.expect_popup() as popup_info:
        page.locator("span:has-text('更多头条')").nth(0).click()
    page1=popup_info.value
    sleep(2)   
    text_count=page1.locator("div.grid-cell >>div.text-link-item-title").count()    
    print('text',text_count)
    for text in range(text_count):
        obj=page1.locator("div.grid-cell >>div.text-link-item-title").nth(text).locator("span.text").first
        text_title=obj.inner_text()
        print(text_title)
        with page1.expect_popup() as popup_info:
            obj.click()
        page2=popup_info.value
        print(page2.title())
        page2.locator("button.voice-lang-switch").nth(0).click()
        play_audio(page2)
        #sleep(60)
        page2.close()
    page1.close()
    sleep(2)
def play_audio(page):
    current_time=page.locator("span.y-audio-current").inner_text()
    total_time=page.locator("span.y-audio-total").inner_text()
    while not current_time==total_time:
        current_time=page.locator("span.y-audio-current").inner_text()
        print(current_time,total_time,end='\r')
        sleep(1)


def xx_tv(page):
    #视频学习
    global played
    played=0
    # Go to https://pc.xuexi.cn/points/my-points.html
    #page.goto("https://pc.xuexi.cn/points/my-points.html")
    page.goto('https://www.xuexi.cn/')
    with page.expect_popup() as popup_info:
        page.locator("text=学习电视台").nth(0).click()
        sleep(2)
    page1=popup_info.value
    print(page1.title(),'学习电视台')
    with page1.expect_popup() as popup_info:
        page1.locator("span:has-text('第一频道')").nth(0).click()
    page2=popup_info.value
    sleep(2)
    print(page2.title(),'第一频道')
    page2.locator("span:has-text('列表')").nth(0).click()
    sleep(3)
    text_count=page2.locator("div.grid-cell >>div.text-link-item-title").count()    
    print('span.text',text_count)
    for text in range(text_count):
        obj=page2.locator("div.grid-cell >>div.text-link-item-title").nth(text).locator("span.text").first
        text_title=obj.inner_text()
        print(text_title)
        with page2.expect_popup() as popup_info:
            obj.click()
        page3=popup_info.value
        print(page3.title())
        sleep(60)
        page3.close()
    page2.close()
    
    #专项答题
#https://pc.xuexi.cn/points/exam-paper-list.html
def zx_dt(page):
    global my_points
    page.goto(URL['专项答题'])  
    sleep(2) 
    item_count=page.locator("div.item").count()
    print(page.title(),item_count,'专项答题')
    for item in range(item_count):
        obj=page.locator("div.item").nth(item)
        zt=obj.locator("div.right").inner_text()
        print(zt)
        #开始答题
        if '已满分' in zt:
            print(obj.locator('div.left').inner_text(),zt)
            #obj.locator('div.right').click()
            continue
        else:
            if not my_points['专项答题']=='去答题':
                continue

                
            print(obj.locator('div.left').inner_text(),zt)
            obj.locator('div.right').click()
            for count in range(10):
                sleep(1)
                d=get_exam(page)
                print(list(d.values()))
                if is_video(page):
                    answer=get_right_answer(page) 
                    print(answer)
                    d['answer']=answer
                    save_data(d)
                    print(d,'已经保存',sep='\n')
                    return
                answer=d['answer'].split('|')
                put_answer(page,answer)
                save_data(d)
                #print(page.locator("button").first.inner_text())
                print(page.locator("button").last.inner_text(),end='\r')
                sleep(5)
                #exam_practice(page)
            page.goto(URL['专项答题']) 
            my_points['专项答题']=='已完成'

def  put_my_point(page):
    global my_points
    my_points={}
    card_button=get_card_buttonbox(page)
    card_title=get_card_text(page)
    card_points=get_card_points(page)
    for i in range(len(card_button)):
        my_points[card_title[i]]=card_button[i]
    print(card_title,card_points,card_button,sep='\n')

def listing_music(page2):
    page2.goto("https://pc.xuexi.cn/points/my-points.html")
    # Click text=去看看 >> nth=1
    page2.locator("text=去看看").nth(1).click()
    # expect(page2).to_have_url("https://www.xuexi.cn/")
    # Click text=听音乐
    with page2.expect_popup() as popup_info:
        page2.locator("text=听音乐").click()
    page3 = popup_info.value
    # Click text=播放整张专辑
    #page3.locator("text=播放整张专辑").click()
    sleep(2)
    play_music(page3)
    page3.close()

def play_music(page):
    obj=page.locator("li.album-list-item")
    item_count=obj.count()
    for item in range(item_count):
        print(obj.nth(item).inner_text())
        obj.nth(item).locator('span.item-play').click()
        sleep(60)

def  mz_dt(page):
    page.goto("https://pc.xuexi.cn/points/my-points.html")
    obj=  page.locator("div.buttonbox").nth(5)
    buttonbox_text=obj.inner_text() 
    if buttonbox_text=='去答题':
        obj.click()
    else:
        print("没有可以点击的按钮")
        return
    sleep(3)
    obj=   page.locator("div.week") 
    button_count=obj.count()
    print(page.title(),button_count)    
    for i in range(button_count):
        print(obj.nth(i).inner_text())
        button_text=obj.nth(i).locator('button').inner_text()
        if not button_text=='重新答题':
            obj.nth(i).locator('button').click()
            sleep(3)
            for count in range(5):
                sleep(1)
                d=get_exam(page)
                print(list(d.values()))
                if is_video(page):
                    answer=get_right_answer(page) 
                    print(answer)
                    d['answer']=answer
                    save_data(d)
                    print(d,'已经保存',sep='\n')
                    return
                answer=d['answer'].split('|')
                put_answer(page,answer)
                save_data(d)
                #print(page.locator("button").first.inner_text())
                print(page.locator("button").last.inner_text(),end='\r')
                sleep(5)
                #exam_practice(page)
            sleep(2)
            page.goto(URL['每周答题'])
            
            


if __name__ == '__main__':
     page=login(page)
     sleep(1)
     #专项答题
     zx_dt(page)
     
     put_my_point(page) 
     #听音乐
     listing_music(page)
     #每日答题
     go_exam_practice(page)
     #视频学习
     xx_tv(page)
    
       
     
     #每周答题
     mz_dt(page)
        
     #选读文章
     xdwz(page) 
     
     
     page.close()
from win32gui import *
import  win32con
from  time import sleep


def reset_windows_pos(targetTitle):
    hwndList=[]
    EnumWindows(lambda hwnd,param: param.append(hwnd),hwndList)
    for hw in hwndList:
        clsname=GetClassName(hw)
        title=GetWindowText(hw)
        if (title.find(targetTitle)==0):  #调整目标窗口到坐标(600,300),大小设置为(600,600)
            SetWindowPos(hwnd, win32con.HWND_TOPMOST, 600,300,600,600, win32con.SWP_SHOWWINDOW)

titles=set()
def foo(hwnd,mouse):
    if IsWindow(hwnd) and IsWindowEnabled(hwnd) and IsWindowVisible(hwnd):
        a=GetWindowText(hwnd)
        if a=="登录":
            print(a,hwnd)
            hwnd_login=hwnd
        if a=="错误":
            print(a,hwnd)
            hwnd_err=hwnd
        titles.add(a)

#
# 输出当前活动窗体句柄
#
def print_GetForegroundWindow():
    hwnd_active = GetForegroundWindow()
    print('hwnd_active hwnd:',hwnd_active)
    print('hwnd_active text:',GetWindowText(hwnd_active))
    print('hwnd_active class:',GetClassName(hwnd_active))

def write_login(string):
    hwnd=FindWindow(None,"登录")
    clsname="ThunderRT6TextBox" 
    tid= FindWindowEx(hwnd, None, clsname, None)
    if tid:
       
       SendMessage(tid,win32con.WM_SETTEXT,None,string)
       PostMessage(tid, win32con.WM_KEYUP, win32con.VK_RETURN, 0)
       PostMessage(tid, win32con.WM_KEYDOWN, win32con.VK_RETURN, 0)
    
    clsname="ThunderRT6CommandButton" 
    title_text="确定"
    bu= FindWindowEx(hwnd, None, clsname,title_text)
    if bu:
       PostMessage(bu, win32con.WM_KEYUP, win32con.VK_RETURN, 0)
       PostMessage(bu, win32con.WM_KEYDOWN, win32con.VK_RETURN, 0)

def check_close_err():
    
    hwnd=FindWindow(None,"错误")   
    if hwnd>0:
        PostMessage(hwnd,win32con.WM_CLOSE,0,0)
        #clsname="Button" 
        #clsname="Button" 
        #title_text="确定"
        #bu= FindWindowEx(hwnd, None, clsname,title_text)
        #PostMessage(bu, win32con.WM_KEYDOWN, win32con.VK_RETURN, 0)
        #PostMessage(bu, win32con.WM_KEYUP, win32con.VK_RETURN, 0)
        return "Err"
    else:
        return "OK"


if __name__=='__main__':
    print_GetForegroundWindow()
    for i in range(102000,100*10000):
        write_login(str(i))
        sleep(0.06)
        print(i)
        if check_close_err()=="OK":
            print(i)
            break
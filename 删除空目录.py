doc='''
删除当前目录下所有空目录
Usage:
python delete_blank.py

Example:
python delete_blank
'''
from pathlib import Path
from tqdm import tqdm


def unlink_blank():
    result=[f for f in Path('.').glob('**/*') if f.is_dir() ]
    del_res=[]
    for d in tqdm(result):        
        try:
            d.rmdir()
            print("删除空目录：%s"%d.resolve())
            del_res.append(d.resolve())
        except:
            #print("%snot null"%d.resolve())
            pass
    print("总记删除%s个空目录"%(len(del_res)))
     

    
    
if __name__=="__main__":
    unlink_blank()
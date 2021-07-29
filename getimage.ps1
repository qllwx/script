echo "从福建省考试院获取2021年普通类本科批常规志愿院校专业组投档最低分公布物理组第1-9页";
for($i=1 ; $i -lt 10;$i++)
{
$filename="wl_0"+$i+".jpg";
echo $filename;
$str="https://www.eeafj.cn/u/cms/default/202107/"+$filename;
wget -o  $filename $str
};
echo "物理组第10-45页";
for($i=10 ; $i -lt 46;$i++)
{
$filename="wl_"+$i+".jpg"
echo $filename
$str="https://www.eeafj.cn/u/cms/default/202107/"+$filename;
wget -o  $filename $str;
};

echo "历史组";
#https://www.eeafj.cn/u/cms/default/202107/ls_01.jpg
echo "第1到9页";
for($i=1 ; $i -lt 10;$i++)
{
$filename="ls_0"+$i+".jpg";
echo $filename;
$str="https://www.eeafj.cn/u/cms/default/202107/"+$filename;
wget -o  $filename $str
};

echo "第10到25页";
for($i=10 ; $i -lt 26;$i++)
{
$filename="ls_"+$i+".jpg";
echo $filename;
$str="https://www.eeafj.cn/u/cms/default/202107/"+$filename;
wget -o  $filename $str;
};
import subprocess
import re
from utils import RED, RESET

def get_user_data(username):
    """
    【作用】通过执行 net user 指令抓取用户信息，并将其解析成 Python 可读的字典格式。
    【返回值】返回两个东西：
      1. data_dict: 存放所有属性和内容的字典。
      2. keys_order: 存放属性名的列表，用于记住原本打印的先后顺序，防止后续输出乱序。
    """
    
    # 【为什么这么做？】
    # subprocess.run 是 Python 官方推荐的调用系统命令的方法。
    # 把它想象成 Python 帮你偷偷打开了一个隐形的 CMD，输入了 'net user xxx /domain'。
    # encoding='gbk': 因为中文版 Windows CMD 吐出的文字编码全是 GBK，不用 GBK 解码就会报乱码错误。
    # errors='ignore': 防止遇到极其特殊的不可见字符导致整个程序崩溃。
    result = subprocess.run(['net', 'user', username, '/domain'], capture_output=True, text=True, encoding='gbk', errors='ignore')
    
    # returncode != 0 表示系统命令执行失败了（比如用户不存在，或者网络断了）
    if result.returncode != 0:
        print(f"{RED}错误：无法查询用户 [{username}]，请检查用户名或网络状况。{RESET}")
        return None, [] # 返回空数据，让主程序知道抓取失败了

    # 把抓回来的那一坨大文本，按“换行符”切成一行一行的列表，方便我们逐行分析
    lines = result.stdout.splitlines()
    data_dict = {}
    keys_order = []
    last_key = "" # 临时变量，用来记住上一行处理的是什么属性名

    for line in lines:
        # 【清洗第一步：过滤杂质】
        # 如果是空行，或者是 '--------------' 这种分割线，或者是最后的 '命令成功完成'，统统跳过不要。
        if not line.strip() or line.startswith('----------------') or "命令成功完成" in line:
            continue
        
        # 【清洗第二步：处理多行延续情况】
        # net user 的特性：如果一个用户加入了十几个组，第一行写不下，第二行它会自动空出几十个空格接着写。
        # 这里判断：如果这行开头有 10 个以上的空格，说明它肯定是上一项属性的延续。
        if line.startswith(' ' * 10):
            if last_key: # 确保上一项有名字
                # 把这个值追加到上一项的列表里
                data_dict[last_key].append(line.strip())
            continue

        # 【清洗第三步：正则匹配正常的键值对】
        # 正则表达式解释：
        # ^(.+?) : 匹配开头任意字符，尽可能少匹配（这部分就是“属性名”）
        # \s{2,} : 匹配至少连续两个以上的空格（这是净网的核心：属性名和内容之间有大段空格分隔）
        # (.*)$  : 匹配剩下的所有字符直到行尾（这部分就是“属性内容”）
        match = re.match(r'^(.+?)\s{2,}(.*)$', line)
        if match:
            last_key = match.group(1).strip() # 拿到属性名，如 "全名"
            value = match.group(2).strip()    # 拿到属性值，如 "张三"
            
            # 如果这是一个全新的属性，先在字典里建个空列表准备装它，并把名字记入顺序表
            if last_key not in data_dict:
                data_dict[last_key] = []
                keys_order.append(last_key)
            # 把值装进去（之所以用列表装，是因为我们要兼容上面“第二步”可能会有多个值的情况）
            data_dict[last_key].append(value)

    # 【清洗第四步：深度加工提取到的数据】
    for k in list(data_dict.keys()):
        # 针对包含“组”或“Group”的属性进行特殊处理
        # 【为什么这么做？】
        # 因为 net user 输出组的格式很奇葩，一行可能挤了好几个组，且都带 '*' 号（比如：'*Domain Users *IT Group'）
        # 我们利用 '*' 这个特征，把它们暴力拆开，变成一个个干干净净的独立群组项，方便后面一行一行去对比。
        if '组' in k or 'Group' in k:
            combined_str = " ".join(data_dict[k]) # 先把可能被折行的组全部捏成一长串
            # 根据 '*' 进行切割，并去除多余空格，去掉空字符串
            groups = [g.strip() for g in combined_str.split('*') if g.strip()]
            data_dict[k] = groups
        else:
            # 如果只是普通属性（比如“上次登录时间”），直接把列表里的文字拼接成字符串即可
            data_dict[k] = " ".join(data_dict[k])

    return data_dict, keys_order

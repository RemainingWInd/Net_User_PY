import csv
import os
from utils import RED, GREEN, YELLOW, CYAN, RESET, get_display_width, pad_string
from fetcher import get_user_data

def process_users(usernames):
    """
    【作用】接收一个包含用户名的列表（1人~N人皆可），抓取他们的数据，比对异同，打印表格并导出。
    """
    user_count = len(usernames)
    is_multi = user_count > 1 # 这是一个布尔值开关，判断当前是单人查询（False）还是多人比对（True）
    
    print(f"\n{CYAN}正在获取并计算对齐宽度: {', '.join(usernames)} ...{RESET}\n")
    
    # 存放所有人数据的超级容器
    all_data = []
    # 存放所有出现过的属性名（去重并保持顺序，取所有人的“并集”）
    all_keys = []
    
    # 【步骤 1：批量抓取所有用户的数据】
    for user in usernames:
        data, keys = get_user_data(user)
        # 只要有一个人抓取失败（可能是名字打错了），立刻终止整个处理流程，防止后面的代码报错
        if data is None:
            return 
        all_data.append(data)
        for k in keys:
            if k not in all_keys:
                all_keys.append(k)

    # 【步骤 2：数据预计算与矩阵构建】
    # 为什么不直接打印？因为在完全分析完所有数据之前，我们不知道到底哪一行最长！
    # 所以要先在内存里把整个表格“画”一遍。
    display_rows = [] # 存放要在屏幕上打印的数据矩阵
    csv_rows = []     # 存放要写入 Excel 的纯净数据矩阵
    
    for key in all_keys:
        # === 分支 A：特殊处理“组”相关的比对 ===
        if '组' in key or 'Group' in key:
            all_unique_groups = set() # 用集合自动去重，收集这几个人到底参与了哪些乱七八糟的组
            for data in all_data:
                groups = data.get(key, []) if isinstance(data.get(key), list) else []
                all_unique_groups.update(groups)
                
            all_unique_groups = sorted(list(all_unique_groups)) or ["-无-"]

            # 将每一个具体的“组”单拎出来作为一行进行横向比对
            for g in all_unique_groups:
                if g == "-无-" and len(all_unique_groups) > 1:
                    continue # 过滤掉无意义的空标记
                
                # 使用列表推导式：如果这个用户在这个组里，就给他填入带*的组名；如果不在，就是个空字符串
                vals = [f"*{g}" if g in (d.get(key, []) if isinstance(d.get(key), list) else []) else "" for d in all_data]
                
                # 【核心比对算法：三色判定】
                # 利用 set(vals) 自动去重。比如有 3 个人，vals 可能是 ['*IT', '*IT', '']
                # 去重后长度是 2（有部分相同）。如果长度是 1 代表全员一样；等于人数代表全员不同。
                unique_vals_count = len(set(vals))
                if not is_multi: # 单人模式：不需要对比状态
                    status_text, color = "", ""
                elif unique_vals_count == 1:
                    status_text, color = "✅ 相同", GREEN
                elif unique_vals_count == user_count:
                    status_text, color = "❌ 不同", RED
                else:
                    status_text, color = "⚠️ 部分相同", YELLOW
                
                # 对于终端打印：如果是空值，用 "[-空-]" 占位，防止屏幕上看起来像个黑洞
                # 对于 CSV 导出：保持真正的空字符串 ""，这样在 Excel 里才是空白单元格，方便筛选
                disp_vals = [v if v else "[-空-]" for v in vals]
                
                row_display = [key] + disp_vals
                row_csv = [key] + vals
                
                if is_multi:
                    row_display.append(status_text)
                    row_csv.append(status_text)
                    
                display_rows.append((row_display, color)) # 连同这行该染什么色一起存入矩阵
                csv_rows.append(row_csv)
                
        # === 分支 B：普通属性的比对 ===
        else:
            # 尝试去每个人的字典里拿这个属性，拿不到说明某人根本没这个属性，返回 "-无此属性-"
            vals = [d.get(key, "-无此属性-") for d in all_data]
            
            # 三色判定算法同上
            unique_vals_count = len(set(vals))
            if not is_multi:
                status_text, color = "", ""
            elif unique_vals_count == 1:
                status_text, color = "✅ 相同", GREEN
            elif unique_vals_count == user_count:
                status_text, color = "❌ 不同", RED
            else:
                status_text, color = "⚠️ 部分相同", YELLOW
            
            row_display = [key] + vals
            row_csv = [key] + vals
            
            if is_multi:
                row_display.append(status_text)
                row_csv.append(status_text)
                
            display_rows.append((row_display, color))
            csv_rows.append(row_csv)

    # 【步骤 3：动态扫描并计算最大宽度】
    # 这部分逻辑极其硬核：它会像扫描仪一样，扫描所有行，找出每一列里最长的那个字符串。
    headers = ["属性名"] + usernames
    if is_multi:
        headers.append("状态")
        
    # 先用表头的宽度作为初始宽度
    col_widths = [get_display_width(h) for h in headers]
    
    # 纵向扫描所有数据行，不断打破并更新最大宽度的记录
    for row_display, _ in display_rows:
        for i, cell in enumerate(row_display):
            col_widths[i] = max(col_widths[i], get_display_width(cell))
            
    # 【细节优化】：强行给算出来的最长宽度再加上 2 个空格。
    # 为什么这么做？就好像排版里的“段间距”，防止左右两列最长的字符紧紧挨在一起，造成视觉上的拥挤和误读。
    col_widths = [w + 2 for w in col_widths]

    # 【步骤 4：正式渲染与打印终端 UI】
    # 第一步：打印表头，利用 pad_string 函数结合刚刚算出来的列宽，精确补齐空格
    header_strs = [pad_string(h, col_widths[i]) for i, h in enumerate(headers)]
    print(" | ".join(header_strs))
    
    # 第二步：打印表头下方的横线。宽度 = 所有列宽之和 + 分隔符 " | " 所占的宽度
    print("-" * (sum(col_widths) + (len(headers) - 1) * 3))

    # 第三步：把存在 display_rows 里的数据，按指定颜色打印出来
    for row_display, color in display_rows:
        row_strs = [pad_string(cell, col_widths[i]) for i, cell in enumerate(row_display)]
        print(f"{color}{' | '.join(row_strs)}{RESET}")

    # 【步骤 5：导出 CSV 数据】
    # 使用 '_'.join() 把人名拼起来作为文件名，比如 Result_UserA_UserB.csv
    filename = f"Result_{'_'.join(usernames)}.csv"
    filepath = os.path.abspath(filename) # 获取文件落在你电脑里的绝对路径，方便打印出来告诉你去哪找
    
    # utf-8-sig 非常关键：它带 BOM 标记，这意味着同事用微软 Excel 打开这个 CSV 时，中文字符绝不会乱码！
    with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        writer.writerow(headers) # 写表头
        writer.writerows(csv_rows) # 批量写入所有行
        
    print(f"\n{CYAN}【任务完成】数据已保存为表格：{filepath}{RESET}")

import sys
from utils import GREEN, YELLOW, RED, RESET
from processor import process_users

# 【为什么用 if __name__ == "__main__":？】
# 这是一个 Python 规范。它意味着：“只有当你直接双击运行、或者用 python main.py 运行这个文件时，以下代码才会执行”。
# 这样不仅规范，还能防止被其他文件当做模块 import 时引发代码错乱自动运行。
if __name__ == "__main__":
    
    # 设置一个全局开关，如果你想支持 10 个人对比，只要把这个 5 改成 10 即可
    MAX_USERS = 5  
    
    print(f"{GREEN}欢迎使用域用户查询工具！{RESET}")
    print(f"{YELLOW}【提示】程序将持续运行，输入字母 'q' 或按下 Ctrl+C 即可随时退出。{RESET}")

    # 外层套用 try...except 结构
    # 【为什么这么做？】
    # 当用户在键盘上强制按下 Ctrl+C 时，Python 默认会崩溃并打印一屏幕极其吓人的红色报错代码。
    # 用 try 包起来捕获这个 KeyboardInterrupt 异常，就能拦截报错，优雅地跟用户说再见。
    try:
        # 开启无限循环模式，这也是为什么工具“查完一次还能接着查”的秘密
        while True:
            print("\n" + "="*65)
            users_to_query = []
            
            # 【第一层输入引导：强制输入阶段】
            u1 = input("请输入第 1 个域用户名 (必填): ").strip()
            
            # 判断用户是否想体面退出
            if u1.lower() == 'q':
                print(f"{YELLOW}已退出程序，感谢使用。{RESET}")
                break # 直接砸碎并跳出 while 循环，程序生命终结
                
            # 防呆设计：如果用户不小心按了回车什么都没输
            if not u1:
                print(f"{RED}用户名不能为空，请重新输入。{RESET}")
                continue # continue 代表终止本轮循环，时间倒流，立刻强制重头开始执行 while 循环
                
            users_to_query.append(u1)

            # 【第二层输入引导：诱导式多选阶段】
            # 用 for 循环优雅地收集第 2 个到第 MAX_USERS 个用户名
            for i in range(2, MAX_USERS + 1):
                u = input(f"请输入第 {i} 个域用户名 (选填，输入 q 退出，直接回车开始查询): ").strip()
                
                # 这里同样支持随时输入 q 跑路，只不过在多层循环深处，用 sys.exit() 是最稳妥直接关掉进程的方法
                if u.lower() == 'q':
                    print(f"{YELLOW}已退出程序，感谢使用。{RESET}")
                    sys.exit() 
                    
                if u: # 如果乖乖输入了第二个名字
                    users_to_query.append(u)
                else:
                    # 如果什么都没输直接敲了回车，意味着收集阶段结束，打破这个 for 循环
                    break 

            # 当收集结束后，把装满了人名的盘子（列表）递给后面的主厨（process_users）去烹饪
            process_users(users_to_query)
            
            # 重点：当主厨烹饪完毕（上面的代码执行完），因为现在身处 while True 的内部，
            # 代码逻辑会自然而然地流回到上面第 24 行的 while True 开头，迎接新一轮查询！
            
    except KeyboardInterrupt:
        print(f"\n{YELLOW}检测到中断指令 (Ctrl+C)，程序已安全退出。{RESET}")

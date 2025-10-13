# github520_app.py
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import urllib.request
import urllib.error
import os
import sys
from datetime import datetime
import json
import shutil
import webbrowser
import time
import logging
import ctypes

class GitHub520App:
    def __init__(self, root):
        self.root = root
        self.root.title("GitHub加速助手 v2.0")
        self.root.geometry("1300x700")  # 增加宽度以容纳侧边栏
        self.root.minsize(1300, 700)
        self.root.resizable(True, True)
        
        # 设置图标（可选）
        try:
            self.root.iconbitmap("icon.ico")  # 如果有图标文件的话
        except:
            pass
        
        # 初始化日志系统
        self.setup_logging()
        
        # 检查管理员权限
        self.is_admin = self.check_admin_privileges()
        if not self.is_admin:
            self.show_admin_warning()
        
        self.config_file = "github520_config.json"
        self.current_hosts = ""
        self.update_history = []
        
        # 备份目录设置
        self.backup_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backup")
        self.original_backup = os.path.join(self.backup_dir, "hosts.original_backup")
        
        # 创建备份目录
        os.makedirs(self.backup_dir, exist_ok=True)
        
        logging.info("程序启动成功")
        
        # DNS服务器列表
        self.dns_servers = [
            "14.114.114.114",
            "8.8.8.8",  
            "172.31.210.1",
            "223.5.5.5",
            "119.29.29.29"
        ]
        # hosts源配置
        self.hosts_sources = {
            "GitHub520": "https://raw.hellogithub.com/hosts",
            "TinsFox": "https://github-hosts.tinsfox.com/hosts"
        }
        self.current_source = "GitHub520"
        
        # GitHub配置项
        self.github_repo = "2489742701/GithubFasterChina"
        self.current_version = "2.0.0"
        self.api_url = f"https://api.github.com/repos/{self.github_repo}/releases/latest"
        self.releases_url = f"https://github.com/{self.github_repo}/releases"
        
        self.load_config()
        self.backup_original_hosts()  # 备份原始hosts
        self.setup_ui()
        self.load_hosts_data()
    
    def backup_original_hosts(self):
        """备份用户原始hosts文件"""
        try:
            if os.name == 'nt':  # Windows
                hosts_path = r'C:\Windows\System32\drivers\etc\hosts'
            else:  # Linux/Mac
                hosts_path = '/etc/hosts'
            
            # 如果原始备份不存在，且系统hosts文件存在，则创建备份
            if not os.path.exists(self.original_backup) and os.path.exists(hosts_path):
                shutil.copy2(hosts_path, self.original_backup)
                print(f"原始hosts已备份到: {self.original_backup}")
        except Exception as e:
            print(f"备份原始hosts失败: {e}")
    
    def check_admin_privileges(self):
        """检查是否有管理员权限"""
        try:
            if os.name == 'nt':  # Windows系统
                # 使用ctypes检查Windows管理员权限
                return ctypes.windll.shell32.IsUserAnAdmin() != 0
            else:  # Linux/Mac系统
                # 检查是否为root用户
                return os.geteuid() == 0
        except:
            logging.error("检查管理员权限时出错")
            return False
    
    def show_admin_warning(self):
        """显示没有管理员权限的警告弹窗"""
        # 记录警告
        logging.warning("程序以普通用户权限启动，某些功能可能无法使用")
        
        # 创建自定义警告弹窗
        warning_window = tk.Toplevel(self.root)
        warning_window.title("权限警告")
        warning_window.geometry("400x250")
        warning_window.resizable(False, False)
        warning_window.transient(self.root)
        warning_window.grab_set()  # 模态窗口
        
        # 设置样式
        style = ttk.Style()
        style.configure("Warning.TLabel", font=("Arial", 11), foreground="#d32f2f")
        style.configure("Info.TLabel", font=("Arial", 10), foreground="#333333")
        style.configure("Warning.TButton", font=("Arial", 10))
        
        # 主框架
        main_frame = ttk.Frame(warning_window, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 警告图标和标题
        warning_label = ttk.Label(main_frame, text="⚠️ 权限警告", style="Warning.TLabel")
        warning_label.pack(pady=(0, 15))
        
        # 警告信息
        message_text = """当前程序没有以管理员权限运行，这可能导致：

• 无法更新系统hosts文件
• 无法备份或恢复hosts文件
• 部分核心功能不可用

请关闭程序，右键点击程序图标，选择"以管理员身份运行"，以获得完整功能。"""
        
        message_label = ttk.Label(main_frame, text=message_text, style="Info.TLabel", justify=tk.LEFT)
        message_label.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
        
        # 确认按钮
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X)
        
        ok_button = ttk.Button(button_frame, text="我知道了", style="Warning.TButton", 
                             command=warning_window.destroy)
        ok_button.pack(side=tk.RIGHT)
    
    def load_config(self):
        """加载配置和历史记录"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    self.update_history = config.get('update_history', [])
            except:
                self.update_history = []
    
    def save_config(self):
        """保存配置和历史记录"""
        config = {
            'update_history': self.update_history[-10:]  # 只保留最近10次记录
        }
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
        except:
            pass
    
    def setup_ui(self):
        """设置用户界面 - 带侧边栏的横向布局"""
        # 清空现有内容
        for widget in self.root.winfo_children():
            widget.destroy()
        
        # 主框架
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 左侧边栏
        sidebar_frame = ttk.Frame(main_frame, width=120, style="Sidebar.TFrame")
        sidebar_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 5))
        sidebar_frame.pack_propagate(False)
        
        # 主内容区域
        content_frame = ttk.Frame(main_frame)
        content_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # ========== 侧边栏内容 ==========
        
        # 标题
        sidebar_title = ttk.Label(sidebar_frame, text="GitHub加速助手", 
                                 font=('Arial', 10, 'bold'), 
                                 style="Sidebar.TLabel")
        sidebar_title.pack(pady=(15, 20))
        
        # 更新窗口标题
        self.root.title(f"GitHub加速助手 v{self.current_version}")
        
        # 导航按钮
        nav_buttons_frame = ttk.Frame(sidebar_frame)
        nav_buttons_frame.pack(fill=tk.X, pady=(0, 20))
        
        self.main_btn = ttk.Button(nav_buttons_frame, text="🏠 主程序", 
                                  command=self.show_main_content,
                                  style="Sidebar.TButton")
        self.main_btn.pack(fill=tk.X, pady=(0, 5))
        
        # 添加Steam按钮
        self.steam_btn = ttk.Button(nav_buttons_frame, text="🎮 Steam加速", 
                                   command=self.show_steam_content,
                                   style="Sidebar.TButton")
        self.steam_btn.pack(fill=tk.X, pady=(5, 0))
        
        self.thanks_btn = ttk.Button(nav_buttons_frame, text="❤️ 致谢", 
                                    command=self.show_thanks_content,
                                    style="Sidebar.TButton")
        self.thanks_btn.pack(fill=tk.X, pady=(5, 0))
        
        # 更新按钮
        self.update_btn = ttk.Button(nav_buttons_frame, text="🔄 检查更新", 
                                   command=self.show_update_content,
                                   style="Sidebar.TButton")
        self.update_btn.pack(fill=tk.X, pady=(5, 0))
        
        # 样式配置
        self.configure_styles()
        
        # ========== 主内容区域 ==========
        self.main_content_frame = ttk.Frame(content_frame)
        self.thanks_content_frame = ttk.Frame(content_frame)
        self.steam_content_frame = ttk.Frame(content_frame)
        self.update_content_frame = ttk.Frame(content_frame)
        
        # 初始化显示主程序内容
        self.setup_main_content()
        self.setup_thanks_content()
        self.setup_steam_content()
        self.setup_update_content()
        
        # 设置初始按钮状态
        self.main_btn.config(style="Pressed.TButton")
        self.thanks_btn.config(style="Sidebar.TButton")
        self.steam_btn.config(style="Sidebar.TButton")
        
        self.show_main_content()
        
    def configure_styles(self):
        """配置样式"""
        style = ttk.Style()
        
        # 侧边栏样式
        style.configure("Sidebar.TFrame", background="#f0f0f0")
        style.configure("Sidebar.TLabel", background="#f0f0f0", foreground="#333333")
        style.configure("Sidebar.TButton", 
                       background="#e0e0e0", 
                       foreground="#333333",
                       borderwidth=1,
                       relief="raised",
                       padding=(5, 8))
        
        style.map("Sidebar.TButton",
                 background=[('active', '#d0d0d0'),
                           ('pressed', '#c0c0c0')])
        
        # 链接样式
        style.configure("Link.TLabel", 
                       foreground="blue", 
                       cursor="hand2",
                       font=('Arial', 9, 'underline'))
        
        # 选中按钮样式
        style.configure("Pressed.TButton", 
                       background="#c0c0c0",
                       relief="sunken")
    
    def show_main_content(self):
        """显示主程序内容"""
        # 隐藏其他内容
        self.thanks_content_frame.pack_forget()
        self.steam_content_frame.pack_forget()
        self.update_content_frame.pack_forget()
        
        # 显示主内容
        self.main_content_frame.pack(fill=tk.BOTH, expand=True)
        
        # 更新按钮状态
        self.main_btn.config(style="Pressed.TButton")
        self.thanks_btn.config(style="Sidebar.TButton")
        self.steam_btn.config(style="Sidebar.TButton")
        self.update_btn.config(style="Sidebar.TButton")
    
    def show_thanks_content(self):
        """显示致谢内容"""
        # 隐藏其他内容
        self.main_content_frame.pack_forget()
        self.steam_content_frame.pack_forget()
        self.update_content_frame.pack_forget()
        
        # 显示致谢内容
        self.thanks_content_frame.pack(fill=tk.BOTH, expand=True)
        
        # 更新按钮状态
        self.main_btn.config(style="Sidebar.TButton")
        self.thanks_btn.config(style="Pressed.TButton")
        self.steam_btn.config(style="Sidebar.TButton")
        self.update_btn.config(style="Sidebar.TButton")
        
    def show_update_content(self):
        """显示更新页面内容"""
        # 隐藏其他内容
        self.main_content_frame.pack_forget()
        self.steam_content_frame.pack_forget()
        self.thanks_content_frame.pack_forget()
        
        # 显示更新内容
        self.update_content_frame.pack(fill=tk.BOTH, expand=True)
        
        # 更新按钮状态
        self.main_btn.config(style="Sidebar.TButton")
        self.thanks_btn.config(style="Sidebar.TButton")
        self.steam_btn.config(style="Sidebar.TButton")
        self.update_btn.config(style="Pressed.TButton")
        
    def setup_update_content(self):
        """设置更新页面内容"""
        # 创建主容器
        main_container = ttk.Frame(self.update_content_frame, padding=20)
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # 创建标题
        title = ttk.Label(main_container, text="程序更新中心", font=("Arial", 16, "bold"))
        title.pack(pady=(0, 20))
        
        # 版本信息区域
        version_frame = ttk.LabelFrame(main_container, text="版本信息", padding=15)
        version_frame.pack(fill=tk.X, pady=(0, 20))
        
        # 当前版本
        current_version_frame = ttk.Frame(version_frame)
        current_version_frame.pack(fill=tk.X, pady=5)
        ttk.Label(current_version_frame, text="当前版本:", width=15).pack(side=tk.LEFT)
        self.current_version_label = ttk.Label(current_version_frame, text=f"v{self.current_version}")
        self.current_version_label.pack(side=tk.LEFT)
        
        # 最新版本
        latest_version_frame = ttk.Frame(version_frame)
        latest_version_frame.pack(fill=tk.X, pady=5)
        ttk.Label(latest_version_frame, text="最新版本:", width=15).pack(side=tk.LEFT)
        self.latest_version_label = ttk.Label(latest_version_frame, text="未检查")
        self.latest_version_label.pack(side=tk.LEFT)
        
        # 状态标签
        self.update_status_label = ttk.Label(version_frame, text="请点击检查更新按钮获取最新版本信息")
        self.update_status_label.pack(fill=tk.X, pady=(10, 5))
        
        # 更新内容区域
        self.update_info_frame = ttk.LabelFrame(main_container, text="更新内容", padding=15)
        self.update_info_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
        
        # 更新内容文本框
        self.update_info_text = tk.Text(self.update_info_frame, wrap=tk.WORD, height=10, state=tk.DISABLED)
        self.update_info_text.pack(fill=tk.BOTH, expand=True)
        
        # 滚动条
        scrollbar = ttk.Scrollbar(self.update_info_text, command=self.update_info_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.update_info_text.config(yscrollcommand=scrollbar.set)
        
        # 按钮区域
        buttons_frame = ttk.Frame(main_container)
        buttons_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        # 检查更新按钮
        self.check_update_btn = ttk.Button(buttons_frame, text="检查新版本", command=self.check_for_updates, width=15)
        self.check_update_btn.pack(side=tk.LEFT, padx=5)
        
        # 下载更新按钮
        self.download_update_btn = ttk.Button(buttons_frame, text="下载更新文件", command=self.start_download_update, state=tk.DISABLED, width=15)
        self.download_update_btn.pack(side=tk.LEFT, padx=5)
        
        # 访问发布页按钮
        self.visit_releases_btn = ttk.Button(buttons_frame, text="访问发布页面", command=self.visit_releases_page, width=15)
        self.visit_releases_btn.pack(side=tk.LEFT, padx=5)
        
        # 重置状态
        self.reset_update_page()
        
    def reset_update_page(self):
        """重置更新页面状态"""
        self.latest_version_label.config(text="未检查")
        self.update_status_label.config(text="请点击检查更新按钮获取最新版本信息")
        self.update_info_text.config(state=tk.NORMAL)
        self.update_info_text.delete(1.0, tk.END)
        self.update_info_text.config(state=tk.DISABLED)
        self.download_update_btn.config(state=tk.DISABLED)
        self.latest_version = None
        self.download_url = None
        
    def check_for_updates(self):
        """检查程序更新"""
        try:
            import requests
            from packaging import version
            
            # 更新界面状态
            self.update_status_label.config(text="正在检查最新版本，请稍候...")
            self.check_update_btn.config(state=tk.DISABLED)
            self.update_content_frame.update_idletasks()
            
            # 发送请求获取最新版本信息
            response = requests.get(self.api_url, timeout=10)
            response.raise_for_status()
            
            # 解析版本信息
            latest_info = response.json()
            latest_version = latest_info['tag_name'].lstrip('v')
            release_notes = latest_info['body']
            download_url = latest_info['assets'][0]['browser_download_url'] if latest_info['assets'] else None
            
            # 更新界面显示
            self.latest_version = latest_version
            self.latest_version_label.config(text=f"v{latest_version}")
            
            # 更新内容
            self.update_info_text.config(state=tk.NORMAL)
            self.update_info_text.delete(1.0, tk.END)
            self.update_info_text.insert(tk.END, release_notes)
            self.update_info_text.config(state=tk.DISABLED)
            
            # 比较版本
            if version.parse(latest_version) > version.parse(self.current_version):
                # 有新版本
                self.update_status_label.config(text="发现新版本！请点击下载更新按钮获取最新版本。")
                self.download_url = download_url
                self.download_update_btn.config(state=tk.NORMAL if download_url else tk.DISABLED)
            else:
                self.update_status_label.config(text="当前已是最新版本！")
                self.download_update_btn.config(state=tk.DISABLED)
                
        except Exception as e:
            logging.error(f"检查更新失败: {str(e)}")
            self.update_status_label.config(text=f"检查更新时出错：{str(e)}")
        finally:
            self.check_update_btn.config(state=tk.NORMAL)
            
    def start_download_update(self):
        """开始下载更新"""
        if hasattr(self, 'download_url') and self.download_url:
            self.download_update(self.download_url)
            
    def visit_releases_page(self):
        """访问GitHub发布页面"""
        import webbrowser
        webbrowser.open(self.releases_url)
            
    def download_update(self, download_url):
        """下载更新文件"""
        try:
            import requests
            from tkinter import ttk
            import tempfile
            import os
            import webbrowser
            
            # 创建进度窗口
            progress_window = tk.Toplevel(self.root)
            progress_window.title("下载更新")
            progress_window.geometry("400x150")
            progress_window.resizable(False, False)
            progress_window.transient(self.root)
            progress_window.grab_set()
            
            # 进度标签
            progress_label = ttk.Label(progress_window, text="正在下载更新文件...")
            progress_label.pack(pady=20)
            
            # 进度条
            progress_var = tk.DoubleVar()
            progress_bar = ttk.Progressbar(progress_window, variable=progress_var, length=350)
            progress_bar.pack(pady=10)
            
            # 百分比标签
            percent_label = ttk.Label(progress_window, text="0%")
            percent_label.pack()
            
            # 下载文件
            temp_dir = tempfile.gettempdir()
            filename = os.path.basename(download_url)
            filepath = os.path.join(temp_dir, filename)
            
            # 定义回调函数更新进度
            def update_progress(count, block_size, total_size):
                if total_size > 0:
                    percent = int(count * block_size * 100 / total_size)
                    progress_var.set(percent)
                    percent_label.config(text=f"{percent}%")
                    progress_window.update_idletasks()
            
            # 下载文件
            with open(filepath, 'wb') as f:
                with requests.get(download_url, stream=True, timeout=30) as r:
                    r.raise_for_status()
                    total_size = int(r.headers.get('content-length', 0))
                    downloaded = 0
                    for chunk in r.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            update_progress(downloaded, 1, total_size)
            
            # 下载完成
            progress_window.destroy()
            
            # 提示用户
            if tk.messagebox.askyesno("下载完成", f"更新文件已下载完成：\n{filepath}\n\n是否打开文件所在文件夹？"):
                # 打开文件所在文件夹
                os.startfile(os.path.dirname(filepath))
                
        except Exception as e:
            logging.error(f"下载更新失败: {str(e)}")
            tk.messagebox.showerror("下载失败", f"下载更新文件时出错：{str(e)}")
            try:
                progress_window.destroy()
            except:
                pass
        
        # 检查是否需要初始化致谢内容UI
        # 我们可以通过检查main_frame是否已经存在来判断
        if len(self.thanks_content_frame.winfo_children()) == 0:
            self.setup_thanks_content()
    
    def setup_thanks_content(self):
        """设置致谢页面内容"""
        # 创建滚动条和Canvas
        canvas = tk.Canvas(self.thanks_content_frame)
        scrollbar = ttk.Scrollbar(self.thanks_content_frame, orient="vertical", command=canvas.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # 创建一个框架放在Canvas内部
        main_frame = ttk.Frame(canvas, padding="30")
        canvas_window = canvas.create_window((0, 0), window=main_frame, anchor="nw")
        
        # 绑定事件，当内容改变时更新滚动区域
        def on_configure(event):
            # 更新Canvas的滚动区域
            canvas.configure(scrollregion=canvas.bbox("all"))
        
        def on_frame_configure(event):
            # 更新Canvas窗口的宽度以匹配Canvas
            canvas.itemconfig(canvas_window, width=event.width)
        
        main_frame.bind("<Configure>", on_configure)
        canvas.bind("<Configure>", on_frame_configure)
        
        # 添加鼠标滚轮支持
        def on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        canvas.bind_all("<MouseWheel>", on_mousewheel)
        
        # 标题
        title_label = ttk.Label(main_frame, text="❤️ 致谢与声明", 
                               font=('Arial', 20, 'bold'),
                               foreground="#e74c3c")
        title_label.pack(pady=(0, 30))
        
        # 开源致谢框架
        opensource_frame = ttk.LabelFrame(main_frame, text="🎉 开源项目致谢", padding="20")
        opensource_frame.pack(fill=tk.X, pady=(0, 20))
        
        opensource_text = """本程序基于以下优秀开源项目构建，特此致谢：

• GitHub520项目 - 提供稳定的GitHub hosts更新服务
  📎 项目地址: https://github.com/521xueweihan/GitHub520

• TinsFox hosts项目 - 提供备用的hosts源
  📎 项目地址: https://github.com/TinsFox/github-hosts

感谢这些项目的开发者和维护者们，他们的辛勤工作让GitHub访问变得更加顺畅！

🎯 互联网分享精神：
本程序秉承开源共享的精神，完全免费使用。技术应当服务于大众，
知识的传播不应受到限制。"""
        
        opensource_label = ttk.Label(opensource_frame, text=opensource_text, 
                                   justify=tk.LEFT, font=('Arial', 10))
        opensource_label.pack(anchor=tk.W)
        
        # 用户支持框架
        support_frame = ttk.LabelFrame(main_frame, text="🌟 用户支持", padding="20")
        support_frame.pack(fill=tk.X, pady=(0, 20))
        
        support_text = """如果您觉得这个程序对您有帮助，欢迎通过以下方式支持：

📊 点赞、收藏、关注 - 您的支持是我持续更新的动力
🔗 分享给更多需要的朋友 - 让知识传播得更远
💡 反馈建议和问题 - 帮助程序不断完善

开发者信息："""
        
        support_label = ttk.Label(support_frame, text=support_text, 
                                justify=tk.LEFT, font=('Arial', 10))
        support_label.pack(anchor=tk.W)
        
        # 链接区域
        links_frame = ttk.Frame(support_frame)
        links_frame.pack(fill=tk.X, pady=(10, 0))
        
        # B站链接
        bili_frame = ttk.Frame(links_frame)
        bili_frame.pack(anchor=tk.W, pady=5)
        
        ttk.Label(bili_frame, text="• B站主页: ", font=('Arial', 10)).pack(side=tk.LEFT)
        bili_link = ttk.Label(bili_frame, text="https://space.bilibili.com/484876657", 
                             style="Link.TLabel")
        bili_link.pack(side=tk.LEFT)
        bili_link.bind("<Button-1>", lambda e: self.open_url("https://space.bilibili.com/484876657"))
        
        # GitHub链接
        github_frame = ttk.Frame(links_frame)
        github_frame.pack(anchor=tk.W, pady=5)
        
        ttk.Label(github_frame, text="• 项目地址: ", font=('Arial', 10)).pack(side=tk.LEFT)
        github_link = ttk.Label(github_frame, text="https://github.com/2489742701/GithubFastInChina", 
                               style="Link.TLabel")
        github_link.pack(side=tk.LEFT)
        github_link.bind("<Button-1>", lambda e: self.open_url("https://github.com/2489742701/GithubFastInChina"))
        
        # 重要声明框架
        warning_frame = ttk.LabelFrame(main_frame, text="⚠️ 重要声明", padding="20")
        warning_frame.pack(fill=tk.X)
        
        warning_text = """🚫 反牟利声明：

本程序完全免费开源，遵循MIT开源协议。
如果您是通过付费方式获得此软件，请立即：
1. 要求退款
2. 举报相关销售行为
3. 从官方GitHub仓库获取正版软件

开发者从未通过此程序牟利，所有功能永久免费。
支持正版，反对软件倒卖行为！"""
        
        warning_label = ttk.Label(warning_frame, text=warning_text, 
                                justify=tk.LEFT, font=('Arial', 10, 'bold'),
                                foreground="#c0392b")
        warning_label.pack(anchor=tk.W)
        
    def open_url(self, url):
        """打开指定URL"""
        webbrowser.open(url)
    
    def setup_steam_content(self):
        """设置Steam加速内容"""
        main_frame = ttk.Frame(self.steam_content_frame, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 标题
        title_label = ttk.Label(main_frame, text="Steam加速助手", 
                               font=('Arial', 16, 'bold'))
        title_label.pack(pady=(0, 10), anchor=tk.W)
        
        desc_label = ttk.Label(main_frame, text="一键更新hosts，解决Steam访问缓慢和连接问题",
                              font=('Arial', 9))
        desc_label.pack(pady=(0, 20), anchor=tk.W)
        
        # 状态卡片
        status_frame = ttk.LabelFrame(main_frame, text="当前状态", padding="10")
        status_frame.pack(fill=tk.X, pady=(0, 15))
        
        self.steam_status_icon = ttk.Label(status_frame, text="●", font=('Arial', 16),
                                          foreground="red")
        self.steam_status_icon.pack(anchor=tk.W, pady=(0, 5))
        
        self.steam_status_label = ttk.Label(status_frame, text="正在检查状态...",
                                           font=('Arial', 10))
        self.steam_status_label.pack(anchor=tk.W)
        
        self.steam_last_update_label = ttk.Label(status_frame, text="上次更新: 从未更新",
                                                font=('Arial', 9), foreground="gray")
        self.steam_last_update_label.pack(anchor=tk.W)
        
        # 更新按钮和工具按钮区域 - 所有按钮在一行
        buttons_frame = ttk.Frame(status_frame)
        buttons_frame.pack(fill=tk.X, pady=(10, 0))
        
        # 主要更新按钮（缩短）
        self.steam_update_btn = ttk.Button(buttons_frame, text="更新Steam Hosts", 
                                          command=self.update_steam_hosts, state="normal", width=15)
        self.steam_update_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        # 刷新DNS按钮
        ttk.Button(buttons_frame, text="刷新DNS", width=8, 
                  command=self.flush_dns).pack(side=tk.LEFT, padx=2)
        
        # 网络诊断按钮
        ttk.Button(buttons_frame, text="网络诊断", width=8, 
                  command=self.network_diagnosis).pack(side=tk.LEFT, padx=2)
        
        # Steam Hosts内容区域
        hosts_frame = ttk.LabelFrame(main_frame, text="Steam Hosts配置", padding="10")
        hosts_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # 控制栏
        control_frame = ttk.Frame(hosts_frame)
        control_frame.pack(fill=tk.X, pady=(0, 5))
        
        # 左侧标签
        ttk.Label(control_frame, text="最新Steam hosts配置预览:").pack(side=tk.LEFT)
        
        # 右侧URL选择和获取按钮
        right_frame = ttk.Frame(control_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.X)
        
        # URL选择下拉框
        self.steam_url_var = tk.StringVar()
        self.steam_url_var.set("GitMirror国内镜像")  # 默认选择GitMirror国内镜像
        
        url_frame = ttk.Frame(right_frame)
        url_frame.pack(side=tk.RIGHT, padx=(10, 0))
        
        ttk.Label(url_frame, text="URL源:").pack(side=tk.LEFT, padx=(0, 5))
        url_combobox = ttk.Combobox(url_frame, textvariable=self.steam_url_var, 
                                  values=["GitHub", "GitMirror国内镜像", "GitHubUser源"], width=15, state="readonly")
        url_combobox.pack(side=tk.RIGHT)
        
        # 获取按钮
        ttk.Button(right_frame, text="获取配置", 
                  command=self.load_steam_hosts_data).pack(side=tk.RIGHT)
        
        # 文本框
        self.steam_hosts_text = scrolledtext.ScrolledText(hosts_frame, wrap=tk.WORD, 
                                                         font=('Consolas', 9))
        self.steam_hosts_text.pack(fill=tk.BOTH, expand=True)
        
        # 说明信息
        info_frame = ttk.LabelFrame(main_frame, text="使用说明", padding="10")
        info_frame.pack(fill=tk.X)
        
        # 创建可点击的链接标签
        info_text = """• 此功能使用 Clov614/SteamHostSync 项目的Steam专用hosts配置
• 更新后可以改善Steam商店、社区、创意工坊的访问速度
• 建议同时使用GitHub加速功能以获得最佳效果
• 如果遇到问题，可以使用紧急恢复功能"""
        
        # 说明文本
        info_label = ttk.Label(info_frame, text=info_text, justify=tk.LEFT)
        info_label.pack(anchor=tk.W, pady=(0, 5))
        
        # 项目链接
        project_frame = ttk.Frame(info_frame)
        project_frame.pack(anchor=tk.W)
        
        ttk.Label(project_frame, text="项目地址: ", justify=tk.LEFT).pack(side=tk.LEFT)
        project_link = ttk.Label(project_frame, text="https://github.com/Clov614/SteamHostSync", 
                               style="Link.TLabel")
        project_link.pack(side=tk.LEFT)
        project_link.bind("<Button-1>", lambda e: self.open_url("https://github.com/Clov614/SteamHostSync"))
    
    def show_steam_content(self):
        """显示Steam加速内容"""
        # 隐藏其他内容
        self.main_content_frame.pack_forget()
        self.thanks_content_frame.pack_forget()
        self.update_content_frame.pack_forget()
        
        # 显示Steam内容
        self.steam_content_frame.pack(fill=tk.BOTH, expand=True)
        
        # 更新按钮状态
        self.main_btn.config(style="Sidebar.TButton")
        self.thanks_btn.config(style="Sidebar.TButton")
        self.steam_btn.config(style="Pressed.TButton")
        self.update_btn.config(style="Sidebar.TButton")
        
        # 检查是否需要初始化Steam内容UI
        if not hasattr(self, 'steam_status_label'):
            self.setup_steam_content()
        
        # 不自动加载，用户需要点击按钮手动更新
        self.steam_status_label.config(text="请点击'获取配置'按钮来更新Steam专用hosts")
        self.steam_update_btn.config(state="normal")
    
    def load_steam_hosts_data(self):
        """加载Steam hosts数据 - 使用重试机制"""
        try:
            self.steam_status_label.config(text="正在获取Steam专用hosts配置...")
            self.steam_update_btn.config(state="disabled")
            
            # 根据用户选择获取相应的URL
            selected_url = self.steam_url_var.get()
            if "GitMirror" in selected_url:
                url = "https://hub.gitmirror.com/raw.githubusercontent.com/Clov614/SteamHostSync/main/Hosts_steam"
                logging.info("使用GitMirror国内镜像获取Steam hosts")

            elif "GitHubUser" in selected_url:
                url = "https://raw.githubusercontent.com/Clov614/SteamHostSync/main/Hosts_steam"
                logging.info("使用GitHubUser源获取Steam hosts")
            else:
                url = "https://raw.githubusercontent.com/Clov614/SteamHostSync/main/Hosts_steam"
                logging.info("使用GitHub获取Steam hosts")
            
            # 使用带重试机制的网络请求
            try:
                with self.fetch_with_retry(url) as response:
                    content = response.read().decode('utf-8')
                    
                    # 添加调试信息
                    logging.info(f"获取到的原始内容长度: {len(content)} 字符")
                    # 记录前200个字符作为样本
                    logging.debug(f"原始内容前200字符:\n{content[:200]}...")
                    
                    # 提取Steam相关hosts
                    steam_hosts = self.extract_steam_hosts(content)
                    self.steam_current_hosts = steam_hosts
                    
                    # 更新UI
                    self.steam_hosts_text.delete(1.0, tk.END)
                    self.steam_hosts_text.insert(tk.END, steam_hosts)
                    self.steam_status_label.config(text="已获取最新Steam专用hosts配置")
                    self.steam_update_btn.config(state="normal")
                    self.check_steam_hosts_status()
                    
            except Exception as e:
                logging.warning(f"获取Steam hosts失败: {str(e)}")
                # 尝试自动切换到另一个源
                try:
                    logging.info("尝试切换到另一个URL源...")
                    # 切换到另一个源
                    if "GitMirror" in selected_url:
                        fallback_url = "https://raw.githubusercontent.com/Clov614/SteamHostSync/main/Hosts_steam"
                        logging.info("切换到GitHub直接源")
                    elif "GitHubUser" in selected_url:
                        fallback_url = "https://hub.gitmirror.com/raw.githubusercontent.com/Clov614/SteamHostSync/main/Hosts_steam"
                        logging.info("切换到GitMirror国内镜像源")
                    else:
                        fallback_url = "https://hub.gitmirror.com/raw.githubusercontent.com/Clov614/SteamHostSync/main/Hosts_steam"
                        logging.info("切换到GitMirror国内镜像源")
                    
                    with self.fetch_with_retry(fallback_url) as response:
                        content = response.read().decode('utf-8')
                        
                        # 提取Steam相关hosts
                        steam_hosts = self.extract_steam_hosts(content)
                        self.steam_current_hosts = steam_hosts
                        
                        # 更新UI
                        self.steam_hosts_text.delete(1.0, tk.END)
                        self.steam_hosts_text.insert(tk.END, steam_hosts)
                        self.steam_status_label.config(text="已通过备用源获取Steam hosts配置")
                        self.steam_update_btn.config(state="normal")
                        self.check_steam_hosts_status()
                except:
                    # 两个源都失败时使用示例数据
                    self.fallback_to_sample_steam_hosts()
                    self.steam_status_label.config(text="使用示例配置，可手动更新")
                    self.steam_update_btn.config(state="normal")
                    self.check_steam_hosts_status()
                
        except Exception as e:
            logging.error(f"加载Steam hosts数据完全失败: {str(e)}")
            # 完全失败时确保有默认数据
            self.fallback_to_sample_steam_hosts()
            self.steam_status_label.config(text="获取失败，使用示例配置")
            self.steam_update_btn.config(state="normal")
            self.check_steam_hosts_status()
    
    def fallback_to_sample_steam_hosts(self):
        """使用示例Steam hosts数据作为后备"""
        sample_hosts = """# Steam Hosts 配置 (示例数据)
# 来源: 本地示例 (因网络问题无法获取在线配置)
# 建议手动从 https://github.com/Clov614/SteamHostSync 获取最新配置

# 请点击"立即更新Steam Hosts"按钮手动应用配置
# 或访问上述链接手动复制hosts内容到此文本框
"""
        self.steam_current_hosts = sample_hosts
        self.steam_hosts_text.delete(1.0, tk.END)
        self.steam_hosts_text.insert(tk.END, sample_hosts)
    
    def extract_steam_hosts(self, content):
        """从原始hosts中提取Steam相关条目"""
        # 检查是否包含 #steam Start 标记
        if '#steam Start' in content and '#steam End' in content:
            # 提取 #steam Start 和 #steam End 之间的内容
            start_idx = content.find('#steam Start') + len('#steam Start')
            end_idx = content.find('#steam End')
            steam_section = content[start_idx:end_idx]
            lines = steam_section.split('\n')
        else:
            # 按行处理
            lines = content.split('\n')
        
        steam_domains = [
            'steamcommunity.com',
            'store.steampowered.com',
            'api.steampowered.com',
            'media.steampowered.com',
            'cloud-ops.steamstatic.com',
            'client-download.steamstatic.com',
            'cm.steampowered.com',
            'content.steampowered.com',
            'content1.steampowered.com',
            'content2.steampowered.com',
            'content3.steampowered.com',
            'content4.steampowered.com',
            'content5.steampowered.com',
            'content6.steampowered.com',
            'content7.steampowered.com',
            'content8.steampowered.com',
            'edge.steam-dns.top.comcast.net'
        ]
        
        steam_lines = []
        
        # 遍历所有行，提取Steam相关hosts
        for line in lines:
            line = line.strip()
            if line and not line.startswith('#'):
                # 检查是否包含Steam相关域名
                if any(domain in line for domain in steam_domains):
                    steam_lines.append(line)
        
        # 添加文件头注释
        header = """# Steam Hosts 配置
# 来源: https://github.com/Clov614/SteamHostSync
# 更新时间: {}\n\n""".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        
        # 如果没有找到任何Steam相关hosts条目，添加提示信息
        if not steam_lines:
            logging.warning("未提取到Steam相关hosts条目，可能源文件格式发生变化")
            # 添加示例hosts条目作为参考
            sample_entries = """
# 示例Steam hosts条目（当前未提取到实际内容）
# 您可以手动从GitHub仓库复制最新配置
# 或尝试刷新获取最新数据
"""
            return header + sample_entries
        
        return header + '\n'.join(steam_lines)
    
    def update_steam_hosts(self):
        """更新Steam hosts文件 - 修复版本"""
        # 检查是否有有效数据
        if not hasattr(self, 'steam_current_hosts') or not self.steam_current_hosts:
            messagebox.showwarning("警告", "请先获取Steam hosts配置数据")
            return
        
        # 如果是示例数据，提示用户
        if "示例数据" in self.steam_current_hosts:
            result = messagebox.askyesno("提示", 
                "当前使用的是示例配置，可能不是最新版本。\n\n"
                "建议从 https://github.com/Clov614/SteamHostSync 获取最新配置\n"
                "确定要继续应用示例配置吗？")
            
            if not result:
                return
        
        # 确认对话框
        confirm_result = messagebox.askyesno("确认更新", 
            "即将更新系统hosts文件中的Steam相关配置。\n\n"
            "更新前会自动备份原hosts文件到backup目录。\n"
            "确定要继续吗？")
        
        if not confirm_result:
            return
        
        try:
            self.steam_update_btn.config(state="disabled", text="更新中...")
            
            # 确定hosts文件路径
            if os.name == 'nt':  # Windows
                hosts_path = r'C:\Windows\System32\drivers\etc\hosts'
            else:  # Linux/Mac
                hosts_path = '/etc/hosts'
            
            # 读取当前hosts文件
            current_content = ""
            if os.path.exists(hosts_path):
                with open(hosts_path, 'r', encoding='utf-8') as f:
                    current_content = f.read()
            
            # 备份原文件
            backup_filename = f"hosts.steam_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            backup_path = os.path.join(self.backup_dir, backup_filename)
            if os.path.exists(hosts_path):
                shutil.copy2(hosts_path, backup_path)
            
            # 移除旧的Steam相关配置
            cleaned_content = self.remove_old_steam_hosts(current_content)
            
            # 添加新的Steam配置
            new_content = cleaned_content.strip() + "\n\n" + self.steam_current_hosts
            
            # 写入新内容
            with open(hosts_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            # 记录更新历史
            update_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            hosts_count = len([line for line in self.steam_current_hosts.split('\n') 
                             if line.strip() and not line.startswith('#')])
            
            self.update_history.append({
                'time': update_time,
                'count': f"Steam {hosts_count}条",
                'type': 'steam_update'
            })
            self.save_config()
            
            # 更新UI
            self.check_steam_hosts_status()
            
            messagebox.showinfo("成功", f"Steam hosts配置更新成功！\n更新了 {hosts_count} 条记录")
            
        except PermissionError:
            messagebox.showerror("权限错误", 
                "需要管理员权限来修改hosts文件。\n\n"
                "请以管理员身份运行此程序。")
        except Exception as e:
            messagebox.showerror("错误", f"更新失败: {str(e)}")
        finally:
            self.steam_update_btn.config(state="normal", text="立即更新Steam Hosts")
    
    def remove_old_steam_hosts(self, content):
        """移除旧的Steam相关hosts配置"""
        steam_keywords = [
            'steamcommunity.com',
            'store.steampowered.com',
            'Steam Hosts',
            'SteamHostSync'
        ]
        
        lines = content.split('\n')
        cleaned_lines = []
        in_steam_section = False
        
        for line in lines:
            line_stripped = line.strip()
            
            # 检查是否进入Steam配置区域
            if any(keyword in line for keyword in ['Steam Hosts', 'SteamHostSync']):
                in_steam_section = True
                continue
            
            # 如果在Steam区域，跳过所有行直到空行
            if in_steam_section:
                if not line_stripped:  # 遇到空行，结束Steam区域
                    in_steam_section = False
                continue
            
            # 移除单独的Steam域名行
            if line_stripped and not line_stripped.startswith('#'):
                if any(domain in line for domain in ['steamcommunity.com', 'store.steampowered.com']):
                    continue
            
            cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines)
    
    def check_steam_hosts_status(self):
        """检查Steam hosts文件状态"""
        try:
            if os.name == 'nt':  # Windows
                hosts_path = r'C:\Windows\System32\drivers\etc\hosts'
            else:  # Linux/Mac
                hosts_path = '/etc/hosts'
            
            if os.path.exists(hosts_path):
                with open(hosts_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 检查是否包含Steam相关域名
                if 'steamcommunity.com' in content and 'store.steampowered.com' in content:
                    self.steam_status_icon.config(foreground="green")
                    self.steam_status_label.config(text="hosts文件已包含Steam加速配置")
                else:
                    self.steam_status_icon.config(foreground="orange")
                    self.steam_status_label.config(text="hosts文件需要更新Steam配置")
            else:
                self.steam_status_icon.config(foreground="red")
                self.steam_status_label.config(text="未找到hosts文件")
                
            # 显示最后更新时间
            steam_updates = [h for h in self.update_history if h.get('type') == 'steam_update']
            if steam_updates:
                last_time = steam_updates[-1]['time']
                self.steam_last_update_label.config(text=f"上次更新: {last_time}")
                
        except PermissionError:
            self.steam_status_icon.config(foreground="red")
            self.steam_status_label.config(text="无权限读取hosts文件")
        except Exception as e:
            self.steam_status_icon.config(foreground="red")
            self.steam_status_label.config(text=f"检查状态失败: {str(e)}")
        
    def setup_main_content(self):
        """设置主程序内容"""
        # 主框架 - 使用横向布局
        main_frame = ttk.Frame(self.main_content_frame, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # ========== 左侧面板内容 ==========
        left_frame = ttk.Frame(main_frame, width=300)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        left_frame.pack_propagate(False)
        
        # ========== 右侧面板内容 ==========
        right_frame = ttk.Frame(main_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # 标题
        title_label = ttk.Label(left_frame, text="GitHub加速助手", 
                               font=('Arial', 16, 'bold'))
        title_label.pack(pady=(0, 10), anchor=tk.W)
        
        desc_label = ttk.Label(left_frame, text="一键更新hosts，解决GitHub访问缓慢问题",
                              font=('Arial', 9))
        desc_label.pack(pady=(0, 20), anchor=tk.W)
        
        # 状态卡片
        status_frame = ttk.LabelFrame(left_frame, text="当前状态", padding="10")
        status_frame.pack(fill=tk.X, pady=(0, 15))
        
        self.status_icon = ttk.Label(status_frame, text="●", font=('Arial', 16),
                                   foreground="red")
        self.status_icon.pack(anchor=tk.W, pady=(0, 5))
        
        self.status_label = ttk.Label(status_frame, text="正在检查状态...",
                                     font=('Arial', 10))
        self.status_label.pack(anchor=tk.W)
        
        self.last_update_label = ttk.Label(status_frame, text="上次更新: 从未更新",
                                          font=('Arial', 9), foreground="gray")
        self.last_update_label.pack(anchor=tk.W)
        
        self.update_btn = ttk.Button(status_frame, text="立即更新", 
                                    command=self.update_hosts, state="normal")
        self.update_btn.pack(fill=tk.X, pady=(10, 0))
        
        # 紧急恢复区域
        emergency_frame = ttk.LabelFrame(left_frame, text="紧急恢复", padding="10")
        emergency_frame.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Label(emergency_frame, text="如果更新后出现问题，可恢复原始hosts", 
                 font=('Arial', 9), foreground="red").pack(anchor=tk.W)
        
        ttk.Button(emergency_frame, text="恢复原始备份", 
                  command=self.restore_original_backup, style="Emergency.TButton").pack(fill=tk.X, pady=(5, 0))
        
        # 配置样式
        style = ttk.Style()
        style.configure("Emergency.TButton", foreground="red")
        
        # 源选择
        source_frame = ttk.LabelFrame(left_frame, text="Hosts源选择", padding="10")
        source_frame.pack(fill=tk.X, pady=(0, 15))
        
        self.source_var = tk.StringVar(value=self.current_source)
        
        for source in self.hosts_sources.keys():
            ttk.Radiobutton(source_frame, text=source, variable=self.source_var, 
                           value=source, command=self.on_source_change).pack(anchor=tk.W, pady=2)
        
        # 网络工具
        tools_frame = ttk.LabelFrame(left_frame, text="网络工具", padding="10")
        tools_frame.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Button(tools_frame, text="DNS配置助手", 
                  command=self.show_dns_helper).pack(fill=tk.X, pady=2)
        
        ttk.Button(tools_frame, text="刷新DNS缓存", 
                  command=self.flush_dns).pack(fill=tk.X, pady=2)
        
        ttk.Button(tools_frame, text="网络诊断", 
                  command=self.network_diagnosis).pack(fill=tk.X, pady=2)
        
        ttk.Button(tools_frame, text="备份管理", 
                  command=self.show_backup_manager).pack(fill=tk.X, pady=2)
        
        # 字体控制
        font_frame = ttk.LabelFrame(left_frame, text="显示设置", padding="10")
        font_frame.pack(fill=tk.X)
        
        font_control = ttk.Frame(font_frame)
        font_control.pack(fill=tk.X)
        
        ttk.Label(font_control, text="字体大小:").pack(side=tk.LEFT)
        self.font_size = tk.IntVar(value=9)
        
        ttk.Button(font_control, text="A-", width=3, 
                   command=lambda: self.change_font_size(-1)).pack(side=tk.LEFT, padx=(5, 2))
        
        ttk.Button(font_control, text="A+", width=3, 
                   command=lambda: self.change_font_size(1)).pack(side=tk.LEFT, padx=(2, 0))
        
        # ========== 右侧面板内容 ==========
        
        # Hosts内容区域
        hosts_frame = ttk.LabelFrame(right_frame, text="GitHub Hosts配置", padding="10")
        hosts_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # 控制栏
        control_frame = ttk.Frame(hosts_frame)
        control_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(control_frame, text="最新hosts配置预览:").pack(side=tk.LEFT)
        
        # 文本框
        self.hosts_text = scrolledtext.ScrolledText(hosts_frame, wrap=tk.WORD, 
                                                   font=('Consolas', self.font_size.get()))
        self.hosts_text.pack(fill=tk.BOTH, expand=True)
        
        # 历史记录区域
        history_frame = ttk.LabelFrame(right_frame, text="更新历史", padding="10")
        history_frame.pack(fill=tk.X)
        
        # 历史记录控制栏
        history_control = ttk.Frame(history_frame)
        history_control.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(history_control, text="最近操作记录:").pack(side=tk.LEFT)
        
        ttk.Button(history_control, text="清空历史", 
                   command=self.clear_history).pack(side=tk.RIGHT)
        
        self.history_text = scrolledtext.ScrolledText(history_frame, height=6,
                                                     font=('Arial', 8))
        self.history_text.pack(fill=tk.X)
        self.update_history_display()
        
        # 底部信息
        footer_frame = ttk.Frame(right_frame)
        footer_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Label(footer_frame, text="数据来源: GitHub520/TinsFox项目 | 备份目录: backup/", 
                 font=('Arial', 8), foreground="gray").pack(side=tk.LEFT)
        
        ttk.Label(footer_frame, text="需要管理员权限", 
                 font=('Arial', 8), foreground="orange").pack(side=tk.RIGHT)
    
    def on_source_change(self):
        """切换hosts源"""
        self.current_source = self.source_var.get()
        self.update_btn.config(state="disabled", text="加载中...")
        self.load_hosts_data()
    
    def load_hosts_data(self):
        """从选择的源加载hosts数据 - 使用重试机制"""
        def do_load():
            try:
                self.status_label.config(text=f"正在从{self.current_source}获取hosts配置...")
                self.update_btn.config(state="disabled")
                
                url = self.hosts_sources[self.current_source]
                # 使用带重试机制的网络请求
                with self.fetch_with_retry(url) as response:
                    self.current_hosts = response.read().decode('utf-8')
                    
                    # 在主线程中更新UI
                    self.root.after(0, self.update_ui_after_load)
                    
            except urllib.error.URLError as e:
                error_msg = f"网络错误: {e.reason}"
                self.root.after(0, lambda msg=error_msg: self.show_error(msg))
            except Exception as e:
                error_msg = f"从{self.current_source}获取配置失败: {str(e)}"
                self.root.after(0, lambda msg=error_msg: self.show_error(msg))
        
        # 在后台线程中加载
        import threading
        thread = threading.Thread(target=do_load)
        thread.daemon = True
        thread.start()
    
    def update_ui_after_load(self):
        """加载完成后更新UI"""
        self.hosts_text.delete(1.0, tk.END)
        self.hosts_text.insert(tk.END, self.current_hosts)
        self.status_label.config(text="已获取最新hosts配置")
        self.update_btn.config(state="normal")
        self.check_hosts_status()
    
    def show_error(self, message):
        """显示错误信息"""
        messagebox.showerror("错误", message)
        self.status_label.config(text="获取配置失败")
        self.update_btn.config(state="normal")
    
    def check_hosts_status(self):
        """检查hosts文件状态"""
        try:
            if os.name == 'nt':  # Windows
                hosts_path = r'C:\Windows\System32\drivers\etc\hosts'
            else:  # Linux/Mac
                hosts_path = '/etc/hosts'
            
            if os.path.exists(hosts_path):
                with open(hosts_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 简单检查是否包含GitHub相关域名
                if 'github.com' in content and 'raw.githubusercontent.com' in content:
                    self.status_icon.config(foreground="green")
                    self.status_label.config(text="hosts文件已包含GitHub加速配置")
                else:
                    self.status_icon.config(foreground="orange")
                    self.status_label.config(text="hosts文件需要更新GitHub配置")
            else:
                self.status_icon.config(foreground="red")
                self.status_label.config(text="未找到hosts文件")
                
            # 显示最后更新时间
            if self.update_history:
                last_time = self.update_history[-1]['time']
                self.last_update_label.config(text=f"上次更新: {last_time}")
                
        except PermissionError:
            self.status_icon.config(foreground="red")
            self.status_label.config(text="无权限读取hosts文件")
        except Exception as e:
            self.status_icon.config(foreground="red")
            self.status_label.config(text=f"检查状态失败: {str(e)}")
    
    def setup_logging(self):
        """设置日志系统"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'github520.log')),
                logging.StreamHandler()
            ]
        )
    
    def validate_hosts_content(self, content):
        """验证hosts内容格式"""
        required_domains = ['github.com', 'raw.githubusercontent.com']
        is_valid = all(domain in content for domain in required_domains)
        logging.info(f"Hosts内容验证结果: {is_valid}")
        return is_valid
    
    def fetch_with_retry(self, url, retries=3):
        """带重试机制的网络请求"""
        for i in range(retries):
            try:
                logging.info(f"第{i+1}/{retries}次尝试获取: {url}")
                response = urllib.request.urlopen(url, timeout=10)
                logging.info(f"成功获取数据: {url}")
                return response
            except Exception as e:
                logging.warning(f"第{i+1}次获取失败: {str(e)}")
                if i == retries - 1:
                    logging.error(f"所有重试失败: {url}")
                    raise
                time.sleep(2)
    
    def confirm_update(self):
        """确认更新操作"""
        if not self.current_hosts:
            messagebox.showwarning("警告", "请先获取hosts配置数据")
            logging.warning("尝试更新但无hosts数据")
            return False
        
        # 验证hosts内容
        if not self.validate_hosts_content(self.current_hosts):
            messagebox.showwarning("警告", "获取的hosts内容不完整，可能无法正常工作")
            logging.warning("Hosts内容验证失败")
        
        # 确认对话框
        result = messagebox.askyesno("确认更新", 
            "即将更新系统hosts文件，这会修改网络配置。\n\n"
            "更新前会自动备份原hosts文件到backup目录。\n"
            "确定要继续吗？")
        
        logging.info(f"用户确认更新: {result}")
        return result
    
    def create_backup(self):
        """创建hosts文件备份"""
        try:
            # 确定hosts文件路径
            if os.name == 'nt':  # Windows
                hosts_path = r'C:\Windows\System32\drivers\etc\hosts'
            else:  # Linux/Mac
                hosts_path = '/etc/hosts'
            
            # 备份原文件到backup目录
            backup_filename = f"hosts.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            backup_path = os.path.join(self.backup_dir, backup_filename)
            
            if os.path.exists(hosts_path):
                shutil.copy2(hosts_path, backup_path)
                logging.info(f"成功创建备份: {backup_path}")
            else:
                logging.warning(f"hosts文件不存在: {hosts_path}")
                
            return True, backup_path
        except Exception as e:
            logging.error(f"创建备份失败: {str(e)}")
            return False, str(e)
    
    def apply_new_hosts(self, hosts_content, hosts_path):
        """应用新的hosts内容"""
        try:
            with open(hosts_path, 'w', encoding='utf-8') as f:
                f.write(hosts_content)
            logging.info(f"成功应用新的hosts内容: {hosts_path}")
            return True
        except PermissionError:
            logging.error(f"权限错误: 无法写入hosts文件 {hosts_path}")
            messagebox.showerror("权限错误", 
                "需要管理员权限来修改hosts文件。\n\n"
                "请以管理员身份运行此程序。")
            return False
        except Exception as e:
            logging.error(f"应用hosts失败: {str(e)}")
            return False
    
    def record_success(self, backup_path):
        """记录更新成功并更新UI"""
        # 记录更新历史
        update_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        hosts_count = len([line for line in self.current_hosts.split('\n') 
                         if line.strip() and not line.startswith('#')])
        
        self.update_history.append({
            'time': update_time,
            'count': hosts_count
        })
        self.save_config()
        
        # 更新UI
        self.check_hosts_status()
        self.update_history_display()
        
        # 显示成功对话框
        self.show_backup_success_dialog(hosts_count, backup_path)
        
        logging.info(f"更新记录已保存，更新了 {hosts_count} 条记录")
    
    def update_hosts(self):
        """更新hosts文件 - 重构版本"""
        if self.confirm_update():
            self.update_btn.config(state="disabled", text="更新中...")
            
            success, backup_path = self.create_backup()
            if success:
                # 确定hosts文件路径
                hosts_path = r'C:\Windows\System32\drivers\etc\hosts' if os.name == 'nt' else '/etc/hosts'
                
                if self.apply_new_hosts(self.current_hosts, hosts_path):
                    self.record_success(backup_path)
                    return
                else:
                    messagebox.showerror("错误", "应用hosts内容失败")
            else:
                messagebox.showerror("错误", f"创建备份失败: {backup_path}")
        
        self.update_btn.config(state="normal", text="立即更新")
    
    def show_backup_success_dialog(self, hosts_count, backup_path):
        """显示更新成功对话框并允许访问备份目录"""
        # 创建自定义对话框
        dialog = tk.Toplevel(self.root)
        dialog.title("更新成功")
        dialog.geometry("500x200")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()
        
        # 居中显示
        dialog.update_idletasks()
        x = (self.root.winfo_screenwidth() - dialog.winfo_width()) // 2
        y = (self.root.winfo_screenheight() - dialog.winfo_height()) // 2
        dialog.geometry(f"+{x}+{y}")
        
        # 内容框架
        content_frame = ttk.Frame(dialog, padding="20")
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # 成功图标和文字
        success_frame = ttk.Frame(content_frame)
        success_frame.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Label(success_frame, text="✓", font=('Arial', 24), 
                 foreground="green").pack(side=tk.LEFT, padx=(0, 10))
        
        text_frame = ttk.Frame(success_frame)
        text_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        ttk.Label(text_frame, text="Hosts文件更新成功！", 
                 font=('Arial', 12, 'bold')).pack(anchor=tk.W)
        ttk.Label(text_frame, text=f"更新了 {hosts_count} 条记录", 
                 font=('Arial', 10)).pack(anchor=tk.W)
        
        # 备份信息
        backup_info = f"原文件已备份为: {os.path.basename(backup_path)}"
        backup_dir = os.path.dirname(backup_path)
        
        backup_frame = ttk.Frame(content_frame)
        backup_frame.pack(fill=tk.X, pady=(0, 20))
        
        ttk.Label(backup_frame, text=backup_info, font=('Arial', 9)).pack(anchor=tk.W)
        ttk.Label(backup_frame, text=f"备份位置: {backup_dir}", 
                 font=('Arial', 9), foreground="blue").pack(anchor=tk.W)
        
        # 按钮框架
        button_frame = ttk.Frame(content_frame)
        button_frame.pack(fill=tk.X)
        
        ttk.Button(button_frame, text="打开备份目录", 
                  command=lambda: self.open_backup_directory(backup_dir, dialog)).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(button_frame, text="查看备份文件", 
                  command=lambda: self.view_backup_file(backup_path, dialog)).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(button_frame, text="恢复此备份", 
                  command=lambda: self.restore_backup(backup_path, dialog)).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(button_frame, text="确定", 
                  command=dialog.destroy).pack(side=tk.RIGHT)
    
    def restore_original_backup(self):
        """恢复原始备份"""
        try:
            if not os.path.exists(self.original_backup):
                messagebox.showerror("错误", "原始备份文件不存在")
                return
            
            result = messagebox.askyesno("确认恢复", 
                "确定要恢复原始hosts备份吗？\n\n"
                "这将撤销所有GitHub加速设置，恢复系统原始状态。")
            
            if not result:
                return
            
            # 确定hosts文件路径
            if os.name == 'nt':  # Windows
                hosts_path = r'C:\Windows\System32\drivers\etc\hosts'
            else:  # Linux/Mac
                hosts_path = '/etc/hosts'
            
            # 创建恢复前的备份
            restore_backup_path = os.path.join(self.backup_dir, f"hosts.before_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
            if os.path.exists(hosts_path):
                shutil.copy2(hosts_path, restore_backup_path)
            
            # 恢复原始备份
            shutil.copy2(self.original_backup, hosts_path)
            
            # 记录恢复历史
            restore_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.update_history.append({
                'time': restore_time,
                'count': '恢复原始备份',
                'type': 'restore_original'
            })
            self.save_config()
            
            # 更新UI
            self.check_hosts_status()
            self.update_history_display()
            
            messagebox.showinfo("恢复成功", 
                "已成功恢复原始hosts文件！\n\n"
                "所有GitHub加速设置已被清除。")
            
        except PermissionError:
            messagebox.showerror("权限错误", "需要管理员权限来恢复hosts文件")
        except Exception as e:
            messagebox.showerror("错误", f"恢复原始备份失败: {str(e)}")
    
    def open_backup_directory(self, directory, dialog=None):
        """打开备份文件所在目录"""
        try:
            if os.name == 'nt':  # Windows
                os.startfile(directory)
            else:  # Linux/Mac
                import subprocess
                subprocess.run(['open', directory] if sys.platform == 'darwin' else ['xdg-open', directory])
            
            if dialog:
                dialog.destroy()
                
        except Exception as e:
            messagebox.showerror("错误", f"无法打开目录: {str(e)}")
    
    def view_backup_file(self, backup_path, dialog=None):
        """查看备份文件内容"""
        try:
            if os.path.exists(backup_path):
                # 创建查看窗口
                view_window = tk.Toplevel(self.root)
                view_window.title("查看备份文件")
                view_window.geometry("800x500")
                view_window.transient(self.root)
                
                # 标题
                title_frame = ttk.Frame(view_window, padding="10")
                title_frame.pack(fill=tk.X)
                
                ttk.Label(title_frame, text=f"备份文件: {os.path.basename(backup_path)}", 
                         font=('Arial', 11, 'bold')).pack(anchor=tk.W)
                ttk.Label(title_frame, text=f"路径: {backup_path}", 
                         font=('Arial', 9), foreground="gray").pack(anchor=tk.W)
                
                # 内容区域
                content_frame = ttk.Frame(view_window, padding="10")
                content_frame.pack(fill=tk.BOTH, expand=True)
                
                # 添加滚动文本框
                text_frame = ttk.Frame(content_frame)
                text_frame.pack(fill=tk.BOTH, expand=True)
                
                backup_text = scrolledtext.ScrolledText(text_frame, wrap=tk.WORD, 
                                                       font=('Consolas', 9))
                backup_text.pack(fill=tk.BOTH, expand=True)
                
                # 读取并显示备份文件内容
                with open(backup_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    backup_text.insert(tk.END, content)
                    backup_text.config(state=tk.DISABLED)  # 设为只读
                
                # 按钮区域
                button_frame = ttk.Frame(content_frame)
                button_frame.pack(fill=tk.X, pady=(10, 0))
                
                ttk.Button(button_frame, text="打开文件位置", 
                          command=lambda: self.open_backup_directory(os.path.dirname(backup_path))).pack(side=tk.LEFT)
                
                ttk.Button(button_frame, text="关闭", 
                          command=view_window.destroy).pack(side=tk.RIGHT)
                
                if dialog:
                    dialog.destroy()
            else:
                messagebox.showerror("错误", "备份文件不存在")
                
        except Exception as e:
            messagebox.showerror("错误", f"无法查看备份文件: {str(e)}")
    
    def change_font_size(self, delta):
        """改变字体大小"""
        new_size = self.font_size.get() + delta
        if 8 <= new_size <= 20:  # 限制字体大小范围
            self.font_size.set(new_size)
            self.hosts_text.config(font=('Consolas', new_size))
            
            # 同时更新历史记录框的字体大小
            history_size = max(8, new_size - 1)  # 历史记录字体稍小
            self.history_text.config(font=('Arial', history_size))
    
    def clear_history(self):
        """清空更新历史"""
        if self.update_history:
            result = messagebox.askyesno("确认清空", "确定要清空所有更新历史记录吗？")
            if result:
                self.update_history = []
                self.save_config()
                self.update_history_display()
    
    def update_history_display(self):
        """更新历史记录显示"""
        self.history_text.delete(1.0, tk.END)
        if not self.update_history:
            self.history_text.insert(tk.END, "暂无更新记录")
        else:
            # 过滤并只保留字典类型的记录
            valid_history = []
            for history in self.update_history[-5:]:  # 显示最近5次
                if isinstance(history, dict):
                    valid_history.append(history)
                else:
                    logging.warning(f"发现无效的历史记录类型: {type(history).__name__}")
            
            if not valid_history:
                self.history_text.insert(tk.END, "历史记录格式错误")
            else:
                for history in valid_history:
                    if history.get('type') == 'restore':
                        self.history_text.insert(tk.END, 
                            f"{history['time']} - {history['count']} ({history['backup_file']})\n")
                    elif history.get('type') == 'restore_original':
                        self.history_text.insert(tk.END, 
                            f"{history['time']} - {history['count']}\n")
                    else:
                        self.history_text.insert(tk.END, 
                            f"{history['time']} - 更新了 {history['count']} 条记录\n")
            
            # 如果有无效记录，清理更新历史
            if len(valid_history) != len(self.update_history[-5:]):
                self.update_history = valid_history + [h for h in self.update_history[:-5] if isinstance(h, dict)]
                self.save_config()
    
    # DNS和网络相关方法
    def show_dns_helper(self):
        """显示DNS配置助手窗口"""
        dns_window = tk.Toplevel(self.root)
        dns_window.title("DNS配置助手")
        dns_window.geometry("600x700")  # 设置合适的窗口高度以完全显示所有内容
        dns_window.resizable(True, True)
        dns_window.transient(self.root)
        dns_window.grab_set()
        
        # 主框架
        main_frame = ttk.Frame(dns_window, padding="15")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # DNS说明
        desc_frame = ttk.LabelFrame(main_frame, text="DNS配置说明", padding="10")
        desc_frame.pack(fill=tk.X, pady=(0, 15))
        
        desc_text = """如果遇到GitHub访问问题，可能是DNS服务器配置问题。

推荐DNS服务器：
• 114.114.114.114 (国内)
• 8.8.8.8 (Google)
• 223.5.5.5 (阿里云)
• 119.29.29.29 (腾讯云)

操作步骤：
1. 选择推荐的DNS服务器
2. 点击'应用DNS设置'按钮
3. 勾选需要执行的清理操作
4. 点击'执行选中操作'"""
        
        desc_label = ttk.Label(desc_frame, text=desc_text, justify=tk.LEFT)
        desc_label.pack(anchor=tk.W)
        
        # DNS服务器选择
        dns_frame = ttk.LabelFrame(main_frame, text="选择DNS服务器", padding="10")
        dns_frame.pack(fill=tk.X, pady=(0, 15))
        
        self.selected_dns = tk.StringVar(value=self.dns_servers[0])
        
        for i, dns in enumerate(self.dns_servers):
            ttk.Radiobutton(dns_frame, text=dns, variable=self.selected_dns, 
                           value=dns).pack(anchor=tk.W, pady=2)
        
        # 自定义DNS
        custom_frame = ttk.Frame(dns_frame)
        custom_frame.pack(fill=tk.X, pady=(5, 0))
        
        ttk.Radiobutton(custom_frame, text="自定义:", variable=self.selected_dns, 
                       value="custom").pack(side=tk.LEFT)
        self.custom_dns = ttk.Entry(custom_frame, width=15)
        self.custom_dns.pack(side=tk.LEFT, padx=(5, 0))
        
        # 操作选项
        action_frame = ttk.LabelFrame(main_frame, text="网络修复操作", padding="10")
        action_frame.pack(fill=tk.X, pady=(0, 15))
        
        self.flush_dns_var = tk.BooleanVar(value=True)
        self.reset_winsock_var = tk.BooleanVar(value=False)
        
        ttk.Checkbutton(action_frame, text="刷新DNS缓存", 
                       variable=self.flush_dns_var).pack(anchor=tk.W, pady=2)
        ttk.Checkbutton(action_frame, text="重置Winsock", 
                       variable=self.reset_winsock_var).pack(anchor=tk.W, pady=2)
        
        # 按钮区域
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X)
        
        ttk.Button(button_frame, text="应用DNS设置", 
                  command=lambda: self.apply_dns_settings(dns_window)).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(button_frame, text="执行选中操作", 
                  command=lambda: self.execute_network_ops(dns_window)).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(button_frame, text="关闭", 
                  command=dns_window.destroy).pack(side=tk.RIGHT)
    
    def apply_dns_settings(self, window):
        """应用DNS设置"""
        try:
            dns_server = self.selected_dns.get()
            if dns_server == "custom":
                dns_server = self.custom_dns.get().strip()
                if not dns_server:
                    messagebox.showwarning("警告", "请输入自定义DNS服务器地址")
                    return
            
            # 确认对话框
            result = messagebox.askyesno("确认更改DNS", 
                f"即将将DNS服务器设置为: {dns_server}\n\n"
                "此操作需要管理员权限，可能会影响您的网络连接。\n"
                "确定要继续吗？")
            
            if not result:
                return
            
            # 这里需要根据操作系统执行DNS设置命令
            # Windows示例
            if os.name == 'nt':
                # 设置DNS（需要管理员权限）
                import subprocess
                # 这里只是示例，实际DNS设置更复杂
                result = subprocess.run(['netsh', 'interface', 'ip', 'set', 'dns', 
                                       '本地连接', 'static', dns_server], 
                                      capture_output=True, text=True)
                
                if result.returncode == 0:
                    messagebox.showinfo("成功", f"DNS已设置为: {dns_server}")
                else:
                    messagebox.showerror("错误", "DNS设置失败，请以管理员权限运行")
            else:
                messagebox.showinfo("提示", f"请在系统网络设置中手动设置DNS: {dns_server}")
                
        except Exception as e:
            messagebox.showerror("错误", f"DNS设置失败: {str(e)}")
    
    def execute_network_ops(self, window):
        """执行选中的网络操作"""
        try:
            results = []
            
            if self.flush_dns_var.get():
                success = self.flush_dns(silent=True)
                results.append(f"刷新DNS缓存: {'成功' if success else '失败'}")
            
            if self.reset_winsock_var.get():
                success = self.reset_winsock()
                results.append(f"重置Winsock: {'成功' if success else '失败'}")
            
            if results:
                messagebox.showinfo("操作完成", "\n".join(results))
            else:
                messagebox.showwarning("警告", "请至少选择一个操作")
                
        except Exception as e:
            messagebox.showerror("错误", f"操作执行失败: {str(e)}")
    
    def flush_dns(self, silent=False):
        """刷新DNS缓存"""
        try:
            import subprocess
            
            if os.name == 'nt':  # Windows
                result = subprocess.run(['ipconfig', '/flushdns'], 
                                      capture_output=True, text=True)
                success = result.returncode == 0
            else:  # Linux/Mac
                result = subprocess.run(['sudo', 'systemd-resolve', '--flush-caches'], 
                                      capture_output=True, text=True)
                success = result.returncode == 0
            
            if not silent:
                if success:
                    messagebox.showinfo("成功", "DNS缓存已刷新")
                else:
                    messagebox.showerror("错误", "DNS缓存刷新失败")
            
            return success
            
        except Exception as e:
            if not silent:
                messagebox.showerror("错误", f"刷新DNS缓存失败: {str(e)}")
            return False
    
    def reset_winsock(self):
        """重置Winsock"""
        try:
            if os.name == 'nt':  # Windows
                import subprocess
                result = subprocess.run(['netsh', 'winsock', 'reset'], 
                                      capture_output=True, text=True)
                success = result.returncode == 0
                
                if success:
                    messagebox.showinfo("成功", "Winsock已重置，请重启电脑生效")
                else:
                    messagebox.showerror("错误", "Winsock重置失败")
                
                return success
            else:
                messagebox.showinfo("提示", "此功能仅适用于Windows系统")
                return False
                
        except Exception as e:
            messagebox.showerror("错误", f"重置Winsock失败: {str(e)}")
            return False
    
    def network_diagnosis(self):
        """网络诊断"""
        try:
            import subprocess
            
            # 测试网络连通性
            targets = ['github.com', 'raw.githubusercontent.com', '8.8.8.8']
            diagnosis_results = []
            
            for target in targets:
                param = '-n' if os.name == 'nt' else '-c'
                result = subprocess.run(['ping', param, '3', target], 
                                      capture_output=True, text=True)
                is_reachable = result.returncode == 0
                status_text = "可访问" if is_reachable else "不可访问"
                diagnosis_results.append((target, status_text, is_reachable))
            
            # 创建自定义对话框显示结果
            diag_window = tk.Toplevel(self.root)
            diag_window.title("网络诊断结果")
            diag_window.geometry("400x200")
            diag_window.transient(self.root)
            
            # 主框架
            main_frame = ttk.Frame(diag_window, padding="20")
            main_frame.pack(fill=tk.BOTH, expand=True)
            
            # 显示每个目标的诊断结果
            for target, status, is_reachable in diagnosis_results:
                result_frame = ttk.Frame(main_frame)
                result_frame.pack(fill=tk.X, pady=5)
                
                # 目标名称标签
                ttk.Label(result_frame, text=f"{target}: ", width=25).pack(side=tk.LEFT)
                
                # 状态标签，根据连通性设置不同颜色
                status_label = ttk.Label(result_frame, text=status, 
                                       foreground="green" if is_reachable else "red",
                                       font=('Arial', 10, 'bold'))
                status_label.pack(side=tk.LEFT)
            
            # 关闭按钮
            button_frame = ttk.Frame(main_frame)
            button_frame.pack(fill=tk.X, pady=(20, 0))
            
            close_button = ttk.Button(button_frame, text="关闭", command=diag_window.destroy)
            close_button.pack(side=tk.RIGHT)
            
        except Exception as e:
            messagebox.showerror("错误", f"网络诊断失败: {str(e)}")
    
    def show_backup_manager(self):
        """显示备份管理器窗口"""
        backup_window = tk.Toplevel(self.root)
        backup_window.title("备份管理器")
        backup_window.geometry("800x500")
        backup_window.resizable(True, True)
        backup_window.transient(self.root)
        backup_window.grab_set()
        
        # 主框架
        main_frame = ttk.Frame(backup_window, padding="15")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 标题
        title_frame = ttk.Frame(main_frame)
        title_frame.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Label(title_frame, text="备份管理器", 
                 font=('Arial', 14, 'bold')).pack(anchor=tk.W)
        
        ttk.Label(title_frame, text=f"备份目录: {self.backup_dir}", 
                 font=('Arial', 10), foreground="gray").pack(anchor=tk.W)
        
        # 备份文件列表
        list_frame = ttk.LabelFrame(main_frame, text="备份文件列表", padding="10")
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        # 列表控件框架
        list_control_frame = ttk.Frame(list_frame)
        list_control_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(list_control_frame, text="刷新列表", 
                  command=lambda: self.refresh_backup_list(backup_list)).pack(side=tk.LEFT)
        
        ttk.Button(list_control_frame, text="打开备份目录", 
                  command=lambda: self.open_backup_directory(self.backup_dir)).pack(side=tk.LEFT, padx=(10, 0))
        
        # 备份文件列表
        backup_list_frame = ttk.Frame(list_frame)
        backup_list_frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建列表和滚动条
        columns = ("文件名", "大小", "修改时间")
        backup_list = ttk.Treeview(backup_list_frame, columns=columns, show="headings", height=12)
        
        # 设置列
        backup_list.heading("文件名", text="文件名")
        backup_list.heading("大小", text="大小")
        backup_list.heading("修改时间", text="修改时间")
        
        backup_list.column("文件名", width=300)
        backup_list.column("大小", width=100)
        backup_list.column("修改时间", width=150)
        
        # 滚动条
        scrollbar = ttk.Scrollbar(backup_list_frame, orient=tk.VERTICAL, command=backup_list.yview)
        backup_list.configure(yscrollcommand=scrollbar.set)
        
        backup_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 操作按钮框架
        action_frame = ttk.Frame(main_frame)
        action_frame.pack(fill=tk.X)
        
        ttk.Button(action_frame, text="查看选中备份", 
                  command=lambda: self.view_selected_backup(backup_list)).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(action_frame, text="恢复选中备份", 
                  command=lambda: self.restore_selected_backup(backup_list, backup_window)).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(action_frame, text="删除选中备份", 
                  command=lambda: self.delete_selected_backup(backup_list)).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(action_frame, text="关闭", 
                  command=backup_window.destroy).pack(side=tk.RIGHT)
        
        # 填充列表
        self.refresh_backup_list(backup_list)
        
        # 绑定双击事件
        backup_list.bind('<Double-1>', lambda e: self.view_selected_backup(backup_list))
    
    def refresh_backup_list(self, backup_list):
        """刷新备份文件列表"""
        # 清空列表
        for item in backup_list.get_children():
            backup_list.delete(item)
        
        try:
            if os.path.exists(self.backup_dir):
                # 查找所有备份文件
                backup_files = []
                for filename in os.listdir(self.backup_dir):
                    if filename.startswith('hosts.'):
                        filepath = os.path.join(self.backup_dir, filename)
                        if os.path.isfile(filepath):
                            # 获取文件信息
                            stat = os.stat(filepath)
                            size = self.format_file_size(stat.st_size)
                            mtime = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
                            
                            backup_files.append((filename, size, mtime, filepath))
                
                # 按修改时间排序（最新的在前面）
                backup_files.sort(key=lambda x: x[2], reverse=True)
                
                # 添加到列表
                for filename, size, mtime, filepath in backup_files:
                    backup_list.insert("", tk.END, values=(filename, size, mtime), tags=(filepath,))
            
        except Exception as e:
            messagebox.showerror("错误", f"无法读取备份目录: {str(e)}")
    
    def format_file_size(self, size_bytes):
        """格式化文件大小"""
        if size_bytes == 0:
            return "0 B"
        
        size_names = ["B", "KB", "MB", "GB"]
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024.0
            i += 1
        
        return f"{size_bytes:.1f} {size_names[i]}"
    
    def view_selected_backup(self, backup_list):
        """查看选中的备份文件"""
        selection = backup_list.selection()
        if not selection:
            messagebox.showwarning("警告", "请先选择一个备份文件")
            return
        
        item = selection[0]
        filename = backup_list.item(item)['values'][0]
        filepath = os.path.join(self.backup_dir, filename)
        
        self.view_backup_file(filepath)
    
    def restore_selected_backup(self, backup_list, window):
        """恢复选中的备份文件"""
        selection = backup_list.selection()
        if not selection:
            messagebox.showwarning("警告", "请先选择一个备份文件")
            return
        
        item = selection[0]
        filename = backup_list.item(item)['values'][0]
        filepath = os.path.join(self.backup_dir, filename)
        
        self.restore_backup(filepath)
        window.destroy()
    
    def delete_selected_backup(self, backup_list):
        """删除选中的备份文件"""
        selection = backup_list.selection()
        if not selection:
            messagebox.showwarning("警告", "请先选择一个备份文件")
            return
        
        item = selection[0]
        filename = backup_list.item(item)['values'][0]
        filepath = os.path.join(self.backup_dir, filename)
        
        # 不允许删除原始备份
        if filename == "hosts.original_backup":
            messagebox.showwarning("警告", "不能删除原始备份文件")
            return
        
        result = messagebox.askyesno("确认删除", f"确定要删除备份文件吗？\n\n{filename}")
        if result:
            try:
                os.remove(filepath)
                self.refresh_backup_list(backup_list)
                messagebox.showinfo("成功", "备份文件已删除")
            except Exception as e:
                messagebox.showerror("错误", f"删除文件失败: {str(e)}")
    
    def restore_backup(self, backup_path):
        """从备份恢复hosts文件"""
        try:
            if not os.path.exists(backup_path):
                messagebox.showerror("错误", "备份文件不存在")
                return
            
            # 确认对话框
            result = messagebox.askyesno("确认恢复", 
                f"确定要从备份恢复hosts文件吗？\n\n"
                f"备份文件: {os.path.basename(backup_path)}\n"
                f"这将覆盖当前的hosts文件。")
            
            if not result:
                return
            
            # 读取备份文件内容
            with open(backup_path, 'r', encoding='utf-8') as f:
                backup_content = f.read()
            
            # 确定hosts文件路径
            if os.name == 'nt':  # Windows
                hosts_path = r'C:\Windows\System32\drivers\etc\hosts'
            else:  # Linux/Mac
                hosts_path = '/etc/hosts'
            
            # 创建当前状态的备份（在恢复前备份当前状态）
            current_backup_path = os.path.join(self.backup_dir, f"hosts.before_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
            if os.path.exists(hosts_path):
                shutil.copy2(hosts_path, current_backup_path)
            
            # 写入备份内容
            with open(hosts_path, 'w', encoding='utf-8') as f:
                f.write(backup_content)
            
            # 记录恢复历史
            restore_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.update_history.append({
                'time': restore_time,
                'count': '恢复备份',
                'type': 'restore',
                'backup_file': os.path.basename(backup_path)
            })
            self.save_config()
            
            # 更新UI
            self.check_hosts_status()
            self.update_history_display()
            
            # 显示成功消息
            success_msg = (f"hosts文件已从备份恢复！\n\n"
                          f"恢复的备份: {os.path.basename(backup_path)}\n"
                          f"恢复时间: {restore_time}\n"
                          f"当前状态已备份为: {os.path.basename(current_backup_path)}")
            
            messagebox.showinfo("恢复成功", success_msg)
            
        except PermissionError:
            messagebox.showerror("权限错误", 
                "需要管理员权限来恢复hosts文件。\n\n"
                "请以管理员身份运行此程序。")
        except Exception as e:
            messagebox.showerror("错误", f"恢复备份失败: {str(e)}")

def main():
    # 添加完整的异常处理
    try:
        # 检查是否以管理员权限运行（Windows）
        if os.name == 'nt':
            try:
                # 尝试在系统目录创建文件来检查权限
                test_path = r'C:\Windows\System32\drivers\etc\test_permission'
                with open(test_path, 'w') as f:
                    pass
                os.remove(test_path)
            except PermissionError:
                # 如果没有权限，请求管理员权限
                try:
                    import ctypes
                    if ctypes.windll.shell32.IsUserAnAdmin():
                        pass
                    else:
                        # 重新以管理员权限启动
                        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
                        sys.exit()
                except Exception as e:
                    print(f"权限检查失败: {e}")
        
        # 启动应用程序
        root = tk.Tk()
        app = GitHub520App(root)
        root.mainloop()
    except Exception as e:
        print(f"程序启动失败: {e}")
        import traceback
        traceback.print_exc()
        # 如果不在GUI环境中，可以使用input等待用户查看错误
        if os.name == 'nt':
            input("按Enter键退出...")

if __name__ == "__main__":
    main()
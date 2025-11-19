#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库配置GUI工具
用于配置target_databases的Windows图形界面
"""

import json
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import Dict, Any, Optional, List
import os


class DatabaseConfigGUI:
    """数据库配置GUI"""
    
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("数据库配置工具")
        self.root.geometry("900x700")
        
        self.config_file = "config.json"
        self.config_data: Dict[str, Any] = {}
        self.current_db_name: Optional[str] = None
        
        # 创建主界面
        self.create_widgets()
        
        # 加载配置
        self.load_config()
    
    def create_widgets(self):
        """创建界面组件"""
        # 存储输入字段的引用（必须先初始化）
        self.input_fields: Dict[str, Any] = {}
        self.input_widgets: Dict[str, Any] = {}  # 存储实际的widget
        
        # 顶部工具栏
        toolbar = ttk.Frame(self.root, padding="10")
        toolbar.pack(fill=tk.X)
        
        ttk.Button(toolbar, text="加载配置", command=self.load_config_file).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="保存配置", command=self.save_config).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="测试连接", command=self.test_connection).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="执行结构对比", command=self.run_comparison).pack(side=tk.LEFT, padx=5)
        
        # 主容器
        main_container = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 左侧：数据库列表
        left_frame = ttk.Frame(main_container, width=200)
        main_container.add(left_frame, weight=1)
        
        ttk.Label(left_frame, text="目标数据库列表", font=("Arial", 12, "bold")).pack(pady=5)
        
        # 数据库列表（带复选框）
        list_frame = ttk.Frame(left_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 创建带滚动条的框架
        canvas_list = tk.Canvas(list_frame)
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=canvas_list.yview)
        scrollable_list_frame = ttk.Frame(canvas_list)
        
        scrollable_list_frame.bind(
            "<Configure>",
            lambda e: canvas_list.configure(scrollregion=canvas_list.bbox("all"))
        )
        
        canvas_list.create_window((0, 0), window=scrollable_list_frame, anchor="nw")
        canvas_list.configure(yscrollcommand=scrollbar.set)
        
        canvas_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 存储复选框变量
        self.db_checkboxes: Dict[str, tk.BooleanVar] = {}
        self.db_checkbox_widgets: Dict[str, ttk.Checkbutton] = {}
        
        # 用于编辑的列表（隐藏，仅用于选择编辑）
        # 创建一个不可见的listbox用于内部选择逻辑
        self.db_listbox = tk.Listbox(list_frame)
        self.db_listbox.pack_forget()  # 隐藏listbox
        
        # 数据库操作按钮
        btn_frame = ttk.Frame(left_frame)
        btn_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(btn_frame, text="添加", command=self.add_database).pack(side=tk.LEFT, padx=2, fill=tk.X, expand=True)
        ttk.Button(btn_frame, text="删除", command=self.delete_database).pack(side=tk.LEFT, padx=2, fill=tk.X, expand=True)
        
        # 对比操作区域
        compare_frame = ttk.LabelFrame(left_frame, text="结构对比", padding="10")
        compare_frame.pack(fill=tk.X, padx=5, pady=10)
        
        ttk.Button(compare_frame, text="执行结构对比", command=self.run_comparison, 
                  style="Accent.TButton").pack(fill=tk.X, pady=5)
        
        ttk.Button(compare_frame, text="全选", command=self.select_all_databases).pack(fill=tk.X, pady=2)
        ttk.Button(compare_frame, text="全不选", command=self.deselect_all_databases).pack(fill=tk.X, pady=2)
        
        # 保存scrollable_list_frame的引用
        self.scrollable_list_frame = scrollable_list_frame
        
        # 右侧：配置表单
        right_frame = ttk.Frame(main_container)
        main_container.add(right_frame, weight=3)
        
        # 创建滚动框架
        canvas = tk.Canvas(right_frame)
        scrollbar2 = ttk.Scrollbar(right_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar2.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar2.pack(side="right", fill="y")
        
        # 配置表单
        form_frame = scrollable_frame
        ttk.Label(form_frame, text="数据库配置", font=("Arial", 14, "bold")).pack(pady=10)
        
        # 基本信息
        basic_frame = ttk.LabelFrame(form_frame, text="基本信息", padding="10")
        basic_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.create_input_field(basic_frame, "数据库名称:", "db_name", 0)
        self.create_input_field(basic_frame, "数据库类型:", "db_type", 1, values=["mysql", "postgresql", "sqlite"])
        self.create_input_field(basic_frame, "主机地址:", "host", 2)
        self.create_input_field(basic_frame, "端口:", "port", 3)
        self.create_input_field(basic_frame, "用户名:", "user", 4)
        self.create_input_field(basic_frame, "密码:", "password", 5, show="*")
        self.create_input_field(basic_frame, "数据库名:", "database", 6)
        
        # SSH隧道配置
        ssh_frame = ttk.LabelFrame(form_frame, text="SSH隧道配置（可选）", padding="10")
        ssh_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.ssh_enabled_var = tk.BooleanVar()
        ttk.Checkbutton(ssh_frame, text="启用SSH隧道", variable=self.ssh_enabled_var,
                       command=self.toggle_ssh_fields).grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=5)
        
        self.create_input_field(ssh_frame, "SSH主机:", "ssh_host", 1)
        self.create_input_field(ssh_frame, "SSH端口:", "ssh_port", 2)
        self.create_input_field(ssh_frame, "SSH用户名:", "ssh_user", 3)
        self.create_input_field(ssh_frame, "SSH密码:", "ssh_password", 4, show="*")
        
        # SSH私钥路径（带文件选择按钮）
        ttk.Label(ssh_frame, text="SSH私钥路径:", width=15).grid(row=5, column=0, sticky=tk.W, padx=5, pady=5)
        key_frame = ttk.Frame(ssh_frame)
        key_frame.grid(row=5, column=1, sticky=tk.EW, padx=5, pady=5)
        var = tk.StringVar()
        entry = ttk.Entry(key_frame, textvariable=var, width=35)
        entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(key_frame, text="浏览...", command=lambda: self.select_private_key(var)).pack(side=tk.LEFT, padx=5)
        self.input_fields['ssh_private_key'] = var
        self.input_widgets['ssh_private_key'] = entry
        ssh_frame.columnconfigure(1, weight=1)
        
        # 初始化字段状态
        self.toggle_ssh_fields()
    
    def create_input_field(self, parent, label_text, field_name, row, values=None, show=None):
        """创建输入字段"""
        ttk.Label(parent, text=label_text, width=15).grid(row=row, column=0, sticky=tk.W, padx=5, pady=5)
        
        if values:
            var = tk.StringVar()
            combo = ttk.Combobox(parent, textvariable=var, values=values, width=40, state="readonly")
            combo.grid(row=row, column=1, sticky=tk.EW, padx=5, pady=5)
            self.input_fields[field_name] = var
            self.input_widgets[field_name] = combo
        else:
            var = tk.StringVar()
            entry = ttk.Entry(parent, textvariable=var, width=40, show=show)
            entry.grid(row=row, column=1, sticky=tk.EW, padx=5, pady=5)
            self.input_fields[field_name] = var
            self.input_widgets[field_name] = entry
        
        parent.columnconfigure(1, weight=1)
    
    def select_private_key(self, var):
        """选择SSH私钥文件"""
        file_path = filedialog.askopenfilename(
            title="选择SSH私钥文件",
            filetypes=[("All files", "*.*"), ("PEM files", "*.pem"), ("Key files", "*.key")]
        )
        if file_path:
            var.set(file_path)
    
    def toggle_ssh_fields(self):
        """切换SSH字段的启用状态"""
        enabled = self.ssh_enabled_var.get()
        state = 'normal' if enabled else 'disabled'
        
        for field_name in ['ssh_host', 'ssh_port', 'ssh_user', 'ssh_password', 'ssh_private_key']:
            if field_name in self.input_widgets:
                widget = self.input_widgets[field_name]
                if isinstance(widget, ttk.Combobox):
                    widget.config(state=state)
                elif isinstance(widget, ttk.Entry):
                    widget.config(state=state)
    
    def load_config(self):
        """加载配置文件"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self.config_data = json.load(f)
                self.refresh_db_list()
                messagebox.showinfo("成功", f"已加载配置文件: {self.config_file}")
            except Exception as e:
                messagebox.showerror("错误", f"加载配置文件失败: {e}")
        else:
            # 创建默认配置
            self.config_data = {
                "template_database": {
                    "name": "template_db",
                    "type": "mysql",
                    "host": "localhost",
                    "port": 3306,
                    "user": "username",
                    "password": "password",
                    "database": "template_database_name"
                },
                "target_databases": {},
                "tables_to_compare": "*"
            }
            self.refresh_db_list()
    
    def load_config_file(self):
        """从文件加载配置"""
        file_path = filedialog.askopenfilename(
            title="选择配置文件",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if file_path:
            self.config_file = file_path
            self.load_config()
    
    def refresh_db_list(self):
        """刷新数据库列表"""
        # 保存当前选中的数据库
        selected_dbs = set()
        for db_name, var in self.db_checkboxes.items():
            if var.get():
                selected_dbs.add(db_name)
        
        # 清空现有的复选框
        for widget in self.db_checkbox_widgets.values():
            widget.destroy()
        self.db_checkboxes.clear()
        self.db_checkbox_widgets.clear()
        
        # 清空隐藏的listbox
        self.db_listbox.delete(0, tk.END)
        
        # 创建新的复选框
        target_dbs = self.config_data.get('target_databases', {})
        for idx, db_name in enumerate(target_dbs.keys()):
            # 添加到隐藏的listbox（用于编辑选择）
            self.db_listbox.insert(tk.END, db_name)
            
            # 创建复选框
            var = tk.BooleanVar()
            # 恢复之前的选中状态
            if db_name in selected_dbs:
                var.set(True)
                
            checkbox = ttk.Checkbutton(
                self.scrollable_list_frame,
                text=db_name,
                variable=var,
                command=lambda name=db_name: self.on_checkbox_select(name)
            )
            # 绑定双击事件来编辑数据库
            checkbox.bind('<Double-Button-1>', lambda e, name=db_name: self.load_db_config(name))
            checkbox.pack(anchor=tk.W, padx=5, pady=2)
            
            self.db_checkboxes[db_name] = var
            self.db_checkbox_widgets[db_name] = checkbox
    
    def on_db_select(self, event):
        """选择数据库时的回调（用于编辑）"""
        selection = self.db_listbox.curselection()
        if selection:
            db_name = self.db_listbox.get(selection[0])
            self.current_db_name = db_name
            self.load_db_config(db_name)
    
    def on_checkbox_select(self, db_name: str):
        """复选框选择时的回调"""
        # 选中复选框时，同时选中对应的listbox项（用于编辑时的选择）
        items = self.db_listbox.get(0, tk.END)
        if db_name in items:
            index = list(items).index(db_name)
            self.db_listbox.selection_clear(0, tk.END)
            self.db_listbox.selection_set(index)
            self.current_db_name = db_name
            # 自动加载配置到表单
            self.load_db_config(db_name)
    
    def select_all_databases(self):
        """全选所有数据库"""
        for var in self.db_checkboxes.values():
            var.set(True)
    
    def deselect_all_databases(self):
        """全不选所有数据库"""
        for var in self.db_checkboxes.values():
            var.set(False)
    
    def get_selected_databases(self) -> List[str]:
        """获取选中的数据库列表"""
        selected = []
        for db_name, var in self.db_checkboxes.items():
            if var.get():
                selected.append(db_name)
        return selected
    
    def run_comparison(self):
        """执行结构对比"""
        # 先保存当前配置
        if self.current_db_name or self.input_fields['db_name'].get().strip():
            if not self.save_db_config():
                return  # 如果保存失败，不继续
        
        # 获取选中的数据库
        selected_dbs = self.get_selected_databases()
        if not selected_dbs:
            messagebox.showwarning("警告", "请至少选择一个目标数据库进行对比")
            return
        
        # 检查配置文件是否存在
        if not os.path.exists(self.config_file):
            messagebox.showerror("错误", f"配置文件不存在: {self.config_file}\n请先保存配置")
            return
        
        # 确认执行
        db_list = ", ".join(selected_dbs)
        if not messagebox.askyesno("确认", f"将对以下数据库执行结构对比：\n{db_list}\n\n是否继续？"):
            return
        
        try:
            # 导入比较器
            from database_schema_comparator import DatabaseSchemaComparator
            
            # 创建临时配置文件，只包含选中的数据库
            import tempfile
            temp_config = self.config_data.copy()
            temp_config['target_databases'] = {
                db_name: self.config_data['target_databases'][db_name]
                for db_name in selected_dbs
            }
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
                json.dump(temp_config, f, ensure_ascii=False, indent=2)
                temp_file = f.name
            
            try:
                # 创建比较器并执行对比
                comparator = DatabaseSchemaComparator(temp_file)
                
                # 显示进度窗口
                progress_window = tk.Toplevel(self.root)
                progress_window.title("执行对比中...")
                progress_window.geometry("400x150")
                progress_window.transient(self.root)
                progress_window.grab_set()
                
                progress_label = ttk.Label(progress_window, text="正在执行数据库结构对比，请稍候...", font=("Arial", 10))
                progress_label.pack(pady=20)
                
                progress_bar = ttk.Progressbar(progress_window, mode='indeterminate')
                progress_bar.pack(pady=10, padx=20, fill=tk.X)
                progress_bar.start()
                
                # 更新窗口
                progress_window.update()
                
                # 执行对比
                results = comparator.compare_and_generate_sql()
                
                # 保存结果
                output_dir = "output"
                comparator.save_results(results, output_dir)
                
                # 停止进度条
                progress_bar.stop()
                progress_window.destroy()
                
                # 显示结果摘要
                summary = "=== 对比结果摘要 ===\n\n"
                for db_name, db_results in results.items():
                    summary += f"数据库: {db_name}\n"
                    
                    create_count = sum(1 for r in db_results.values() if r.get('action') == 'create_table')
                    alter_count = sum(1 for r in db_results.values() if r.get('action') == 'alter_table' and r.get('has_differences', False))
                    rename_count = sum(1 for r in db_results.values() if r.get('action') == 'rename_table')
                    consistent_count = sum(1 for r in db_results.values() if r.get('action') == 'alter_table' and not r.get('has_differences', False))
                    error_count = sum(1 for r in db_results.values() if r.get('action') == 'error')
                    
                    summary += f"  需要创建的表: {create_count}\n"
                    summary += f"  需要修改的表: {alter_count}\n"
                    summary += f"  需要重命名的表: {rename_count}\n"
                    summary += f"  结构一致的表: {consistent_count}\n"
                    if error_count > 0:
                        summary += f"  处理失败的表: {error_count}\n"
                    summary += "\n"
                
                summary += f"详细结果已保存到: {output_dir} 目录"
                
                # 创建结果窗口
                result_window = tk.Toplevel(self.root)
                result_window.title("对比结果")
                result_window.geometry("600x400")
                
                text_widget = tk.Text(result_window, wrap=tk.WORD, font=("Consolas", 9))
                text_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
                text_widget.insert(tk.END, summary)
                text_widget.config(state=tk.DISABLED)
                
                button_frame = ttk.Frame(result_window)
                button_frame.pack(pady=10)
                ttk.Button(button_frame, text="关闭", command=result_window.destroy).pack()
                
                messagebox.showinfo("成功", f"结构对比完成！\n结果已保存到: {output_dir} 目录")
                
            finally:
                # 清理临时文件
                if os.path.exists(temp_file):
                    os.unlink(temp_file)
                    
        except Exception as e:
            messagebox.showerror("错误", f"执行结构对比失败:\n{str(e)}")
            import traceback
            traceback.print_exc()
    
    def load_db_config(self, db_name: str):
        """加载数据库配置到表单"""
        target_dbs = self.config_data.get('target_databases', {})
        if db_name not in target_dbs:
            return
        
        db_config = target_dbs[db_name]
        
        # 填充基本信息
        self.input_fields['db_name'].set(db_config.get('name', db_name))
        self.input_fields['db_type'].set(db_config.get('type', 'mysql'))
        self.input_fields['host'].set(db_config.get('host', ''))
        self.input_fields['port'].set(str(db_config.get('port', 3306)))
        self.input_fields['user'].set(db_config.get('user', ''))
        self.input_fields['password'].set(db_config.get('password', ''))
        self.input_fields['database'].set(db_config.get('database', ''))
        
        # 填充SSH配置
        ssh_config = db_config.get('ssh_tunnel', {})
        self.ssh_enabled_var.set(ssh_config.get('enabled', False))
        self.input_fields['ssh_host'].set(ssh_config.get('ssh_host', ''))
        self.input_fields['ssh_port'].set(str(ssh_config.get('ssh_port', 22)))
        self.input_fields['ssh_user'].set(ssh_config.get('ssh_user', ''))
        self.input_fields['ssh_password'].set(ssh_config.get('ssh_password', ''))
        self.input_fields['ssh_private_key'].set(ssh_config.get('ssh_private_key_path', ''))
        
        self.toggle_ssh_fields()
    
    def save_db_config(self):
        """保存当前数据库配置"""
        # 获取表单数据
        db_name = self.input_fields['db_name'].get().strip()
        if not db_name:
            messagebox.showerror("错误", "数据库名称不能为空")
            return False
        
        try:
            port = int(self.input_fields['port'].get() or 3306)
        except ValueError:
            messagebox.showerror("错误", "端口必须是数字")
            return False
        
        db_config = {
            'name': db_name,
            'type': self.input_fields['db_type'].get(),
            'host': self.input_fields['host'].get().strip(),
            'port': port,
            'user': self.input_fields['user'].get().strip(),
            'password': self.input_fields['password'].get(),
            'database': self.input_fields['database'].get().strip()
        }
        
        # SSH配置
        if self.ssh_enabled_var.get():
            try:
                ssh_port = int(self.input_fields['ssh_port'].get() or 22)
            except ValueError:
                messagebox.showerror("错误", "SSH端口必须是数字")
                return False
            
            db_config['ssh_tunnel'] = {
                'enabled': True,
                'ssh_host': self.input_fields['ssh_host'].get().strip(),
                'ssh_port': ssh_port,
                'ssh_user': self.input_fields['ssh_user'].get().strip(),
                'ssh_password': self.input_fields['ssh_password'].get(),
                'ssh_private_key_path': self.input_fields['ssh_private_key'].get().strip()
            }
        
        # 更新配置
        if 'target_databases' not in self.config_data:
            self.config_data['target_databases'] = {}
        
        # 如果名称改变了，删除旧的
        if self.current_db_name and self.current_db_name != db_name and self.current_db_name in self.config_data['target_databases']:
            del self.config_data['target_databases'][self.current_db_name]
        
        self.config_data['target_databases'][db_name] = db_config
        self.current_db_name = db_name
        self.refresh_db_list()
        
        # 选中新保存的数据库（在隐藏的listbox中）
        items = self.db_listbox.get(0, tk.END)
        if db_name in items:
            index = list(items).index(db_name)
            self.db_listbox.selection_clear(0, tk.END)
            self.db_listbox.selection_set(index)
            self.db_listbox.see(index)
        
        # 更新复选框状态
        if db_name in self.db_checkboxes:
            # 保持原有的选中状态
            pass
        
        return True
    
    def add_database(self):
        """添加新数据库"""
        # 清空表单
        self.current_db_name = None
        for field_name in self.input_fields:
            if field_name != 'db_type':
                self.input_fields[field_name].set('')
            else:
                self.input_fields[field_name].set('mysql')
        self.ssh_enabled_var.set(False)
        self.toggle_ssh_fields()
        
        # 生成默认名称
        target_dbs = self.config_data.get('target_databases', {})
        counter = 1
        default_name = f"database_{counter}"
        while default_name in target_dbs:
            counter += 1
            default_name = f"database_{counter}"
        
        self.input_fields['db_name'].set(default_name)
        self.current_db_name = default_name
    
    def delete_database(self):
        """删除数据库"""
        # 尝试从选中的复选框获取
        selected_dbs = self.get_selected_databases()
        if selected_dbs:
            db_name = selected_dbs[0]  # 如果有多个选中，删除第一个
        else:
            # 如果没有选中的复选框，尝试从listbox获取
            selection = self.db_listbox.curselection()
            if not selection:
                messagebox.showwarning("警告", "请先选择一个数据库")
                return
            db_name = self.db_listbox.get(selection[0])
        
        if messagebox.askyesno("确认", f"确定要删除数据库 '{db_name}' 吗？"):
            if 'target_databases' in self.config_data:
                if db_name in self.config_data['target_databases']:
                    del self.config_data['target_databases'][db_name]
            self.refresh_db_list()
            self.current_db_name = None
            # 清空表单
            for field_name in self.input_fields:
                if field_name != 'db_type':
                    self.input_fields[field_name].set('')
                else:
                    self.input_fields[field_name].set('mysql')
            self.ssh_enabled_var.set(False)
    
    def save_config(self):
        """保存配置到文件"""
        # 先保存当前编辑的数据库
        if self.current_db_name or self.input_fields['db_name'].get().strip():
            if not self.save_db_config():
                return  # 如果保存失败，不继续
        
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config_data, f, ensure_ascii=False, indent=2)
            messagebox.showinfo("成功", f"配置已保存到: {self.config_file}")
        except Exception as e:
            messagebox.showerror("错误", f"保存配置文件失败: {e}")
    
    def test_connection(self):
        """测试数据库连接"""
        # 先保存当前配置
        if not self.save_db_config():
            return  # 如果保存失败，不继续
        
        # 获取配置
        db_name = self.input_fields['db_name'].get().strip()
        if not db_name:
            messagebox.showwarning("警告", "请先填写数据库配置")
            return
        
        target_dbs = self.config_data.get('target_databases', {})
        if db_name not in target_dbs:
            messagebox.showerror("错误", "数据库配置不存在，请先保存配置")
            return
        
        db_config = target_dbs[db_name]
        
        # 测试连接
        try:
            from database_schema_comparator import DatabaseSchemaComparator
            # 创建临时配置文件用于测试
            import tempfile
            import os
            temp_config = {
                "template_database": self.config_data.get('template_database', {}),
                "target_databases": {db_name: db_config},
                "tables_to_compare": "*"
            }
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
                json.dump(temp_config, f, ensure_ascii=False, indent=2)
                temp_file = f.name
            
            try:
                comparator = DatabaseSchemaComparator(temp_file)
                connector = comparator.create_connector(db_config)
                connector.connect()
                connector.disconnect()
                messagebox.showinfo("成功", f"数据库 '{db_name}' 连接成功！")
            finally:
                if os.path.exists(temp_file):
                    os.unlink(temp_file)
        except Exception as e:
            messagebox.showerror("连接失败", f"无法连接到数据库 '{db_name}':\n{str(e)}")


def main():
    """主函数"""
    root = tk.Tk()
    app = DatabaseConfigGUI(root)
    
    # 绑定保存快捷键
    def on_closing():
        if messagebox.askyesno("退出", "是否保存配置后退出？"):
            app.save_config()
        root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()


if __name__ == "__main__":
    main()


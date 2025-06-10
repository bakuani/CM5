import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from solver import *

MAX_POINTS = 20
FUNCTIONS = ["sin(x)", "cos(x)", "exp(x)"]


class InterpolatorApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Интерполятор")
        self.root.geometry("1200x700")

        self.point_entries = []  
        self._build_ui()

        
        self.var_newton_divided.set(True)

        self.root.mainloop()

    def _build_ui(self):
        
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True)

        
        left_panel = ttk.Frame(main_frame)
        left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)

        
        right_panel = ttk.Frame(main_frame)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        src_box = ttk.Labelframe(left_panel, text="Ввод данных")
        src_box.pack(fill=tk.X, pady=5)

        self.var_input_mode = tk.StringVar(value='table')
        rb_table = ttk.Radiobutton(
            src_box, text="Таблица", variable=self.var_input_mode, value='table', command=self._switch_page
        )
        rb_file = ttk.Radiobutton(
            src_box, text="Файл", variable=self.var_input_mode, value='file', command=self._switch_page
        )
        rb_func = ttk.Radiobutton(
            src_box, text="Функция", variable=self.var_input_mode, value='func', command=self._switch_page
        )
        rb_table.pack(anchor=tk.W, pady=2)
        rb_file.pack(anchor=tk.W, pady=2)
        rb_func.pack(anchor=tk.W, pady=2)

        self.pages_container = ttk.Frame(left_panel)
        self.pages_container.pack(fill=tk.X, pady=5)
        self._page_table()
        self._page_file()
        self._page_func()
        self._switch_page()

        
        meth_box = ttk.Labelframe(left_panel, text="Методы интерполяции")
        meth_box.pack(fill=tk.X, pady=5)
        self.var_lagr = tk.BooleanVar()
        self.var_newton_divided = tk.BooleanVar()
        self.var_gauss = tk.BooleanVar()
        self.var_stirling = tk.BooleanVar()
        self.var_bessel = tk.BooleanVar()
        self.var_newton_finite = tk.BooleanVar()
        cb_lagr = ttk.Checkbutton(meth_box, text="Лагранж", variable=self.var_lagr)
        cb_newton = ttk.Checkbutton(meth_box, text="Ньютон (раздел.)", variable=self.var_newton_divided)
        cb_newton_finite = ttk.Checkbutton(
            meth_box, text="Ньютон (конеч.)", variable=self.var_newton_finite
        )
        cb_stirling = ttk.Checkbutton(meth_box, text="Стирлинг", variable=self.var_stirling)
        cb_bessel = ttk.Checkbutton(meth_box, text="Бессель", variable=self.var_bessel)
        cb_lagr.pack(anchor=tk.W, pady=2)
        cb_newton.pack(anchor=tk.W, pady=2)
        cb_stirling.pack(anchor=tk.W, pady=2)
        cb_bessel.pack(anchor=tk.W, pady=2)
        cb_newton_finite.pack(anchor=tk.W, pady=2)
        btn_all = ttk.Button(meth_box, text="Выбрать всё", command=self._select_all)
        btn_all.pack(pady=5)

        
        xstar_frame = ttk.Frame(left_panel)
        xstar_frame.pack(fill=tk.X, pady=5)
        ttk.Label(xstar_frame, text="x* =").pack(side=tk.LEFT, padx=(0, 5))
        self.sb_xstar = ttk.Spinbox(
            xstar_frame, from_=-1e6, to=1e6, increment=0.000001, format="%.6f"
        )
        self.sb_xstar.set("0.0")
        self.sb_xstar.pack(side=tk.LEFT, fill=tk.X, expand=True)

        
        self.btn_solve = ttk.Button(left_panel, text="Решить", command=self._solve)
        self.btn_solve.pack(fill=tk.X, pady=(20, 5))

        
        self.status_var = tk.StringVar()
        self.status_label = ttk.Label(
            self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W
        )
        self.status_label.pack(side=tk.BOTTOM, fill=tk.X)

        self.fig = Figure(figsize=(5, 4))
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.fig, master=right_panel)
        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.grid(row=0, column=0, columnspan=2, sticky="nsew")

        
        diff_box = ttk.Labelframe(right_panel, text="Таблица конечных разностей")
        diff_box.grid(row=1, column=0, sticky="nsew", padx=(0, 5), pady=(10, 0))

        results_box = ttk.Labelframe(right_panel, text="Результаты")
        results_box.grid(row=1, column=1, sticky="nsew", padx=(5, 0), pady=(10, 0))

        
        right_panel.rowconfigure(0, weight=3)  
        right_panel.rowconfigure(1, weight=1)  
        right_panel.columnconfigure(0, weight=3)  
        right_panel.columnconfigure(1, weight=1)  

        
        frame_diff = ttk.Frame(diff_box)
        frame_diff.pack(fill=tk.BOTH, expand=True)

        self.diff_tree = ttk.Treeview(frame_diff, show='headings')
        v_scroll = ttk.Scrollbar(frame_diff, orient=tk.VERTICAL, command=self.diff_tree.yview)
        h_scroll = ttk.Scrollbar(frame_diff, orient=tk.HORIZONTAL, command=self.diff_tree.xview)
        self.diff_tree.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)

        
        self.diff_tree.grid(row=0, column=0, sticky="nsew")
        v_scroll.grid(row=0, column=1, sticky="ns")
        h_scroll.grid(row=1, column=0, columnspan=2, sticky="ew")

        frame_diff.rowconfigure(0, weight=1)
        frame_diff.columnconfigure(0, weight=1)

        
        frame_res = ttk.Frame(results_box)
        frame_res.pack(fill=tk.BOTH, expand=True)

        self.res_tree = ttk.Treeview(frame_res, columns=("method", "value"), show='headings')
        self.res_tree.heading("method", text="Метод")
        self.res_tree.heading("value", text="Значение")
        self.res_tree.column("method", anchor=tk.W)
        self.res_tree.column("value", anchor=tk.E)
        v_scroll_res = ttk.Scrollbar(frame_res, orient=tk.VERTICAL, command=self.res_tree.yview)
        self.res_tree.configure(yscrollcommand=v_scroll_res.set)

        self.res_tree.grid(row=0, column=0, sticky="nsew")
        v_scroll_res.grid(row=0, column=1, sticky="ns")

        frame_res.rowconfigure(0, weight=1)
        frame_res.columnconfigure(0, weight=1)

    
    
    def _page_table(self):
        self.page_table = ttk.Frame(self.pages_container)
        self.page_table.pack(fill=tk.X)

        self.table_frame = ttk.Frame(self.page_table)
        self.table_frame.pack(fill=tk.X)

        
        for _ in range(3):
            self._add_table_row()

        btns_frame = ttk.Frame(self.page_table)
        btns_frame.pack(fill=tk.X, pady=5)
        btn_plus = ttk.Button(btns_frame, text="+ строка", command=self._add_table_row)
        btn_minus = ttk.Button(btns_frame, text="– строка", command=self._del_table_row)
        btn_plus.pack(side=tk.LEFT, padx=5)
        btn_minus.pack(side=tk.LEFT, padx=5)

    def _page_file(self):
        self.page_file = ttk.Frame(self.pages_container)
        file_frame = ttk.Frame(self.page_file)
        file_frame.pack(fill=tk.X)
        self.le_path = ttk.Entry(file_frame, state='readonly')
        self.le_path.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        btn_browse = ttk.Button(file_frame, text="Обзор…", command=self._browse_file)
        btn_browse.pack(side=tk.LEFT)

    def _page_func(self):
        self.page_func = ttk.Frame(self.pages_container)

        row1 = ttk.Frame(self.page_func)
        row1.pack(fill=tk.X, pady=2)
        ttk.Label(row1, text="f(x) =").pack(side=tk.LEFT, padx=(0, 5))
        self.cmb_func = ttk.Combobox(row1, values=FUNCTIONS, state="readonly")
        self.cmb_func.current(0)
        self.cmb_func.pack(side=tk.LEFT, fill=tk.X, expand=True)

        row2 = ttk.Frame(self.page_func)
        row2.pack(fill=tk.X, pady=2)
        val_left = tk.StringVar(value="-3.14")
        val_right = tk.StringVar(value="3.14")
        self.le_left = ttk.Entry(row2, textvariable=val_left)
        self.le_right = ttk.Entry(row2, textvariable=val_right)
        ttk.Label(row2, text="От").pack(side=tk.LEFT, padx=(0, 5))
        self.le_left.pack(side=tk.LEFT, padx=(0, 5))
        ttk.Label(row2, text="До").pack(side=tk.LEFT, padx=(5, 5))
        self.le_right.pack(side=tk.LEFT)

        row3 = ttk.Frame(self.page_func)
        row3.pack(fill=tk.X, pady=2)
        ttk.Label(row3, text="N точек").pack(side=tk.LEFT, padx=(0, 5))
        self.sb_n = ttk.Spinbox(row3, from_=2, to=MAX_POINTS, increment=1)
        self.sb_n.set("5")
        self.sb_n.pack(side=tk.LEFT)

    def _switch_page(self):
        mode = self.var_input_mode.get()
        for child in self.pages_container.winfo_children():
            child.pack_forget()
        if mode == 'table':
            self.page_table.pack(fill=tk.X)
        elif mode == 'file':
            self.page_file.pack(fill=tk.X)
        else:
            self.page_func.pack(fill=tk.X)

    
    
    def _add_table_row(self):
        if len(self.point_entries) >= MAX_POINTS:
            self.show_error(f"Максимум {MAX_POINTS} точек")
            return
        row_frame = ttk.Frame(self.table_frame)
        row_frame.pack(fill=tk.X, pady=1)
        var_x = tk.StringVar()
        var_y = tk.StringVar()
        ent_x = ttk.Entry(row_frame, textvariable=var_x, width=15)
        ent_y = ttk.Entry(row_frame, textvariable=var_y, width=15)
        ent_x.pack(side=tk.LEFT, padx=5)
        ent_y.pack(side=tk.LEFT, padx=5)
        self.point_entries.append((row_frame, var_x, var_y))

    def _del_table_row(self):
        if not self.point_entries:
            return
        row_frame, var_x, var_y = self.point_entries.pop()
        row_frame.destroy()

    def _select_all(self):
        self.var_lagr.set(True)
        self.var_newton_divided.set(True)
        self.var_newton_finite.set(True)
        self.var_gauss.set(True)
        self.var_stirling.set(True)
        self.var_bessel.set(True)

    def _browse_file(self):
        path = filedialog.askopenfilename(filetypes=[("Text files", "*.txt *.csv"), ("All files", "*.*")])
        if path:
            self.le_path.config(state='normal')
            self.le_path.delete(0, tk.END)
            self.le_path.insert(0, path)
            self.le_path.config(state='readonly')

    
    
    def clear_diff_table(self):
        for item in self.diff_tree.get_children():
            self.diff_tree.delete(item)
        self.diff_tree["columns"] = ()
        self.diff_tree["show"] = "headings"

    def update_diff_table(self, diffs):
        self.clear_diff_table()
        if not diffs:
            return

        cols = len(diffs)
        rows = max(len(col) for col in diffs)

        headers = ["y"] + [f"Δ^{i}" for i in range(1, cols)]
        self.diff_tree["columns"] = headers

        for h in headers:
            self.diff_tree.heading(h, text=h)
            self.diff_tree.column(h, anchor=tk.E, width=80, stretch=False)

        for r in range(rows):
            row_vals = []
            for c in range(cols):
                if r < len(diffs[c]):
                    row_vals.append(f"{diffs[c][r]:.6g}")
                else:
                    row_vals.append("")
            self.diff_tree.insert("", tk.END, values=row_vals)

    
    
    def clear_results(self):
        for item in self.res_tree.get_children():
            self.res_tree.delete(item)

    def add_result(self, method, value):
        self.res_tree.insert("", tk.END, values=(method, value))

    
    
    def show_error(self, msg):
        self.status_label.config(foreground="red")
        self.status_var.set(f"Ошибка: {msg}")
        self.root.after(5000, lambda: self.status_var.set(""))

    def show_ok(self, msg):
        self.status_label.config(foreground="black")
        self.status_var.set(msg)
        self.root.after(5000, lambda: self.status_var.set(""))



    def plot(self, points, x0):
        if not points:
            self.ax.clear()
            self.canvas.draw()
            return

        self.ax.clear()
        xs, ys = zip(*points)
        self.ax.scatter(xs, ys, label="Узлы")

        x_min, x_max = xs[0], xs[-1]
        xx = [x_min + i * (x_max - x_min) / 300 for i in range(301)]


        if self.var_newton_divided.get():
            yy_g = [newton_divided(points, x) for x in xx]
            self.ax.plot(xx, yy_g, linestyle="-.", label="Ньютон (раздел.)")
        if self.var_stirling.get():
            yy_s = [stirling_interpolation(points, x) for x in xx]
            self.ax.plot(xx, yy_s, linestyle=":", label="Стирлинг")
        if self.var_bessel.get():
            yy_b = [bessel_interpolation(points, x) for x in xx]
            self.ax.plot(xx, yy_b, linestyle="--", label="Бессель")
        if self.var_lagr.get():
            yy_l = [lagrange_interpolation(points, x) for x in xx]
            self.ax.plot(xx, yy_l, linestyle="-", label="Лагранж")
        if self.var_newton_finite.get():
            yy_n = [newton_finite(points, x) for x in xx]
            self.ax.plot(xx, yy_n, linestyle="--", label="Ньютон (конеч.)")

        try:
            y0 = newton_divided(points, x0)
            self.ax.scatter([x0], [y0], marker="x", s=100, label=f"x*={x0:.4g}")
        except Exception:
            y0 = newton_finite(points, x0)
            self.ax.scatter([x0], [y0], marker="x", s=100, label=f"x*={x0:.4g}")

        self.ax.set_xlabel("x")
        self.ax.set_ylabel("y")
        self.ax.set_title("Интерполяция")
        self.ax.legend()
        self.ax.grid(True)
        self.canvas.draw()

    
    
    def _solve(self):
        self.clear_diff_table()
        self.clear_results()
        self.show_ok("")  

        
        try:
            mode = self.var_input_mode.get()
            if mode == 'table':
                pts = []
                for _, var_x, var_y in self.point_entries:
                    x_text = var_x.get().strip()
                    y_text = var_y.get().strip()
                    if x_text == "" or y_text == "":
                        raise ValueError("Заполните все ячейки таблицы")
                    pts.append((float(x_text), float(y_text)))
                if len(pts) < 2:
                    raise ValueError("Необходимо минимум 2 точки")
                data_kind = 'table'
                data = pts

            elif mode == 'file':
                path = self.le_path.get().strip()
                if not path:
                    raise ValueError("Файл не выбран")
                data_kind = 'file'
                data = path

            else:  
                left = float(self.le_left.get())
                right = float(self.le_right.get())
                count = int(self.sb_n.get())
                if right <= left:
                    raise ValueError("Правая граница ≤ левой")
                if count < 2:
                    raise ValueError("Для режима «Функция» нужно N ≥ 2")
                data_kind = 'func'
                data = {
                    'name': self.cmb_func.get(),
                    'left': left,
                    'right': right,
                    'n': count
                }
        except Exception as e:
            self.show_error(str(e))
            return

        methods = {
            'lagrange': self.var_lagr.get(),
            'newton_divided': self.var_newton_divided.get(),
            'gauss': self.var_gauss.get(),
            'stirling': self.var_stirling.get(),
            'newton_finite': self.var_newton_finite.get(),
            'bessel': self.var_bessel.get()
        }

        try:
            xstar = float(self.sb_xstar.get())
        except Exception:
            self.show_error("Некорректное значение x*")
            return

        try:
            execute_interpolation(data_kind, data, methods, xstar, self)
        except Exception as e:
            self.show_error(str(e))



if __name__ == "__main__":
    InterpolatorApp()
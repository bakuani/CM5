import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

import solver  # Предполагается, что модуль solver остаётся без изменений

MAX_POINTS = 20
FUNCTIONS = ["sin(x)", "cos(x)", "exp(x)"]


class InterpolatorApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Интерполятор")
        self.root.geometry("1200x700")

        self.point_entries = []  # список кортежей (frame, var_x, var_y) для ручного ввода
        self._build_ui()
        self.root.mainloop()

    def _build_ui(self):
        # Главная рамка
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Разбивка на верхний и нижний фрейм
        top_frame = ttk.Frame(main_frame)
        top_frame.pack(fill=tk.BOTH, expand=True)
        bottom_frame = ttk.Frame(main_frame)
        bottom_frame.pack(fill=tk.X)

        # Левая панель (контролы) и правая панель (график + таблицы)
        left_panel = ttk.Frame(top_frame)
        left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)
        right_panel = ttk.Frame(top_frame)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        # -----------------
        # Блок выбора ввода данных
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

        # Стек страниц для ввода (таблица, файл, функция)
        self.pages_container = ttk.Frame(left_panel)
        self.pages_container.pack(fill=tk.X, pady=5)
        self._page_table()
        self._page_file()
        self._page_func()
        self._switch_page()

        # -----------------
        # Блок выбора методов интерполяции
        meth_box = ttk.Labelframe(left_panel, text="Методы интерполяции")
        meth_box.pack(fill=tk.X, pady=5)
        self.var_lagr = tk.BooleanVar()
        self.var_newton = tk.BooleanVar()
        self.var_gauss = tk.BooleanVar()
        self.var_stirling = tk.BooleanVar()
        self.var_bessel = tk.BooleanVar()
        cb_lagr = ttk.Checkbutton(meth_box, text="Лагранж", variable=self.var_lagr)
        cb_newton = ttk.Checkbutton(meth_box, text="Ньютон", variable=self.var_newton)
        cb_gauss = ttk.Checkbutton(meth_box, text="Гаусс", variable=self.var_gauss)
        cb_stirling = ttk.Checkbutton(meth_box, text="Стирлинг", variable=self.var_stirling)
        cb_bessel = ttk.Checkbutton(meth_box, text="Бессель", variable=self.var_bessel)
        cb_lagr.pack(anchor=tk.W, pady=2)
        cb_newton.pack(anchor=tk.W, pady=2)
        cb_gauss.pack(anchor=tk.W, pady=2)
        cb_stirling.pack(anchor=tk.W, pady=2)
        cb_bessel.pack(anchor=tk.W, pady=2)
        btn_all = ttk.Button(meth_box, text="Выбрать всё", command=self._select_all)
        btn_all.pack(pady=5)

        # -----------------
        # Блок ввода x*
        xstar_frame = ttk.Frame(left_panel)
        xstar_frame.pack(fill=tk.X, pady=5)
        ttk.Label(xstar_frame, text="x* =").pack(side=tk.LEFT, padx=(0, 5))
        self.sb_xstar = ttk.Spinbox(xstar_frame, from_=-1e6, to=1e6, increment=0.000001, format="%.6f")
        self.sb_xstar.set("0.0")
        self.sb_xstar.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # -----------------
        # Кнопка "Решить"
        self.btn_solve = ttk.Button(left_panel, text="Решить", command=self._solve)
        self.btn_solve.pack(fill=tk.X, pady=(20, 5))

        # -----------------
        # Полоса статуса
        self.status_var = tk.StringVar()
        self.status_label = ttk.Label(
            bottom_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W
        )
        self.status_label.pack(fill=tk.X)

        # -----------------
        # Правая часть: график + таблицы
        # График
        self.fig = Figure(figsize=(5, 4))
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.fig, master=right_panel)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Таблицы: разместим их под графиком в отдельном фрейме
        tables_frame = ttk.Frame(right_panel)
        tables_frame.pack(fill=tk.BOTH, expand=False, pady=(10, 0))

        # Таблица конечных разностей
        diff_box = ttk.Labelframe(tables_frame, text="Таблица конечных разностей")
        diff_box.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        self.diff_tree = None
        self._init_diff_table(diff_box)

        # Таблица результатов
        res_box = ttk.Labelframe(tables_frame, text="Результаты")
        res_box.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        self.res_tree = None
        self._init_results_table(res_box)

    # ----------------------------------------
    # Страницы ввода данных
    def _page_table(self):
        """Страница ввода точек вручную (таблица)"""
        self.page_table = ttk.Frame(self.pages_container)
        self.page_table.pack(fill=tk.X)

        # Фрейм для строк точек
        self.table_frame = ttk.Frame(self.page_table)
        self.table_frame.pack(fill=tk.X)

        # Начально создадим 3 строки
        for _ in range(3):
            self._add_table_row()

        # Кнопки добавления/удаления строки
        btns_frame = ttk.Frame(self.page_table)
        btns_frame.pack(fill=tk.X, pady=5)
        btn_plus = ttk.Button(btns_frame, text="+ строка", command=self._add_table_row)
        btn_minus = ttk.Button(btns_frame, text="– строка", command=self._del_table_row)
        btn_plus.pack(side=tk.LEFT, padx=5)
        btn_minus.pack(side=tk.LEFT, padx=5)

    def _page_file(self):
        """Страница выбора файла"""
        self.page_file = ttk.Frame(self.pages_container)

        file_frame = ttk.Frame(self.page_file)
        file_frame.pack(fill=tk.X)
        self.le_path = ttk.Entry(file_frame, state='readonly')
        self.le_path.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        btn_browse = ttk.Button(file_frame, text="Обзор…", command=self._browse_file)
        btn_browse.pack(side=tk.LEFT)

    def _page_func(self):
        """Страница выбора функции"""
        self.page_func = ttk.Frame(self.pages_container)

        # Выбор функции
        row1 = ttk.Frame(self.page_func)
        row1.pack(fill=tk.X, pady=2)
        ttk.Label(row1, text="f(x) =").pack(side=tk.LEFT, padx=(0, 5))
        self.cmb_func = ttk.Combobox(row1, values=FUNCTIONS, state="readonly")
        self.cmb_func.current(0)
        self.cmb_func.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Границы от-до
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

        # Количество точек N
        row3 = ttk.Frame(self.page_func)
        row3.pack(fill=tk.X, pady=2)
        ttk.Label(row3, text="N точек").pack(side=tk.LEFT, padx=(0, 5))
        self.sb_n = ttk.Spinbox(row3, from_=2, to=MAX_POINTS, increment=1)
        self.sb_n.set("5")
        self.sb_n.pack(side=tk.LEFT)

    def _switch_page(self):
        mode = self.var_input_mode.get()
        # Скрываем все страницы
        for child in self.pages_container.winfo_children():
            child.pack_forget()
        # Показываем нужную
        if mode == 'table':
            self.page_table.pack(fill=tk.X)
        elif mode == 'file':
            self.page_file.pack(fill=tk.X)
        else:
            self.page_func.pack(fill=tk.X)

    # ----------------------------------------
    # Работа с таблицей ввода точек
    def _add_table_row(self):
        if len(self.point_entries) >= MAX_POINTS:
            self._show_status(f"Максимум {MAX_POINTS} точек", error=True)
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

    # ----------------------------------------
    # Блок выбора всех методов
    def _select_all(self):
        self.var_lagr.set(True)
        self.var_newton.set(True)
        self.var_gauss.set(True)
        self.var_stirling.set(True)
        self.var_bessel.set(True)

    # ----------------------------------------
    # Диалог выбора файла
    def _browse_file(self):
        path = filedialog.askopenfilename(filetypes=[("Text files", "*.txt *.csv"), ("All files", "*.*")])
        if path:
            self.le_path.config(state='normal')
            self.le_path.delete(0, tk.END)
            self.le_path.insert(0, path)
            self.le_path.config(state='readonly')

    # ----------------------------------------
    # Инициализация таблиц справа
    def _init_diff_table(self, parent):
        self.diff_tree = ttk.Treeview(parent, show='headings')
        self.diff_tree.pack(fill=tk.BOTH, expand=True)
        # Колонки задаются динамически в update_diff_table

    def _init_results_table(self, parent):
        self.res_tree = ttk.Treeview(parent, columns=("method", "value"), show='headings')
        self.res_tree.heading("method", text="Метод")
        self.res_tree.heading("value", text="Значение")
        self.res_tree.column("method", anchor=tk.W, width=100)
        self.res_tree.column("value", anchor=tk.E, width=100)
        self.res_tree.pack(fill=tk.BOTH, expand=True)

    # ----------------------------------------
    # Методы для обновления таблиц и статуса (используются solver.process_data)
    def clear_diff_table(self):
        for col in self.diff_tree.get_children():
            self.diff_tree.delete(col)
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
            self.diff_tree.column(h, anchor=tk.E, width=60)

        for r in range(rows):
            row_vals = []
            for c in range(cols):
                if r < len(diffs[c]):
                    row_vals.append(f"{diffs[c][r]:.6g}")
                else:
                    row_vals.append("")  # пустая ячейка
            self.diff_tree.insert("", tk.END, values=row_vals)

    def clear_results(self):
        for item in self.res_tree.get_children():
            self.res_tree.delete(item)

    def add_result(self, method, value):
        self.res_tree.insert("", tk.END, values=(method, value))

    def show_error(self, msg):
        self._show_status(f"Ошибка: {msg}", error=True)

    def show_ok(self, msg):
        self._show_status(msg, error=False)

    def _show_status(self, text, error=False):
        self.status_var.set(text)
        if error:
            self.status_label.config(foreground="red")
        else:
            self.status_label.config(foreground="black")
        # Очистим сообщение через 5 секунд
        self.root.after(5000, lambda: self.status_var.set(""))

    def plot(self, points, x0):
        # Защита от пустого списка точек
        if not points:
            self.ax.clear()
            self.canvas.draw()
            return

        self.ax.clear()
        xs, ys = zip(*points)
        self.ax.scatter(xs, ys, label="Узлы")

        # Сетка точек для графиков
        x_min, x_max = xs[0], xs[-1]
        xx = [x_min + i * (x_max - x_min) / 300 for i in range(301)]

        # Линии каждого метода (если выбраны)
        if self.var_newton.get():
            yy_n = [solver.interp_newton(points, x) for x in xx]
            self.ax.plot(xx, yy_n, linestyle="--", label="Ньютон")
        if self.var_gauss.get():
            yy_g = [solver.interp_gauss(points, x) for x in xx]
            self.ax.plot(xx, yy_g, linestyle="-.", label="Гаусс")
        if self.var_stirling.get():
            yy_s = [solver.interp_stirling(points, x) for x in xx]
            self.ax.plot(xx, yy_s, linestyle=":", label="Стирлинг")
        if self.var_bessel.get():
            yy_b = [solver.interp_bessel(points, x) for x in xx]
            self.ax.plot(xx, yy_b, linestyle="--", label="Бессель")
        if self.var_lagr.get():
            yy_l = [solver.interp_lagrange(points, x) for x in xx]
            self.ax.plot(xx, yy_l, linestyle="-", label="Лагранж")

        # Отметка точки x*
        try:
            y0 = solver.interp_newton(points, x0)
            self.ax.scatter([x0], [y0], marker="x", s=100, label=f"x*={x0:.4g}")
        except Exception:
            # Если не получилось вычислить y* (например, вне диапазона узлов), просто не ставим крестик
            pass

        self.ax.set_xlabel("x")
        self.ax.set_ylabel("y")
        self.ax.set_title("Интерполяция")
        self.ax.legend()
        self.ax.grid(True)
        self.canvas.draw()

    # ----------------------------------------
    # Основной метод "Решить"
    def _solve(self):
        self.clear_diff_table()
        self.clear_results()
        self._show_status("", error=False)

        # Читаем данные в зависимости от режима
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

                # Проверка, что минимум 2 точки
                if len(pts) < 2:
                    raise ValueError("Необходимо минимум 2 точки для интерполяции")

                data_kind = 'table'
                data = pts

            elif mode == 'file':
                path = self.le_path.get().strip()
                if not path:
                    raise ValueError("Файл не выбран")
                data_kind = 'file'
                data = path

            else:  # func
                left = float(self.le_left.get())
                right = float(self.le_right.get())
                if right <= left:
                    raise ValueError("Правая граница ≤ левой")
                n_points = int(self.sb_n.get())
                if n_points < 2:
                    raise ValueError("N точек ≥ 2")
                data_kind = 'func'
                data = {
                    'name': self.cmb_func.get(),
                    'left': left,
                    'right': right,
                    'n': n_points
                }
        except Exception as e:
            self.show_error(str(e))
            return

        methods = {
            'lagrange': self.var_lagr.get(),
            'newton': self.var_newton.get(),
            'gauss': self.var_gauss.get(),
            'stirling': self.var_stirling.get(),
            'bessel': self.var_bessel.get()
        }

        try:
            xstar = float(self.sb_xstar.get())
        except Exception:
            self.show_error("Некорректное значение x*")
            return

        # Вызов solver.process_data:
        # предполагается, что внутри этого метода:
        #  - вычисляется и передаётся в GUI таблица разностей через update_diff_table
        #  - вычисляются результаты методов через add_result
        #  - в конце вызывается gui.plot(points, xstar)
        try:
            solver.process_data(data_kind, data, methods, xstar, self)
        except Exception as e:
            self.show_error(str(e))


def main():
    InterpolatorApp()


if __name__ == "__main__":
    main()

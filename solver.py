import csv
import math


MATH_FUNCTIONS = {
    "sin(x)": math.sin,
    "cos(x)": math.cos,
    "exp(x)": math.exp,
}


def build_diff_table(data):
    table = [[y for _, y in data]]
    for lvl in range(1, len(data)):
        prev = table[-1]
        curr = [prev[i + 1] - prev[i] for i in range(len(prev) - 1)]
        table.append(curr)
    return table


def build_divided_diff(data):
    n = len(data)
    x_vals = [pt[0] for pt in data]
    dd = [[pt[1]] for pt in data]
    for level in range(1, n):
        for i in range(n - level):
            numerator = dd[i + 1][level - 1] - dd[i][level - 1]
            denominator = x_vals[i + level] - x_vals[i]
            dd[i].append(numerator / denominator)
    return dd


def lagrange_interpolation(data, x):
    total = 0.0
    n = len(data)
    for i in range(n):
        xi = data[i][0]
        yi = data[i][1]
        basis = yi
        for j in range(n):
            if i != j:
                xj = data[j][0]
                basis = basis * (x - xj) / (xi - xj)
        total = total + basis
    return total


def newton_divided(data, x):
    n = len(data)
    x_vals = []
    for i in range(n):
        x_vals.append(data[i][0])
    dd = build_divided_diff(data)
    result = dd[0][0]
    product = 1.0
    for level in range(1, n):
        product = product * (x - x_vals[level - 1])
        term = dd[0][level]
        result = result + term * product
    return result



def newton_finite(data, x):
    pts = sorted(data, key=lambda pt: pt[0])
    n = len(pts)

    x_vals = []
    for i in range(n):
        x_vals.append(pts[i][0])

    y_vals = []
    for i in range(n):
        y_vals.append(pts[i][1])

    h = x_vals[1] - x_vals[0]
    for i in range(1, n - 1):
        if abs((x_vals[i + 1] - x_vals[i]) - h) > 1e-8:
            raise ValueError("Узлы неравномерны: метод конечных разностей недоступен")

    diff_table = build_diff_table(pts)

    if x <= x_vals[n // 2]:
        t = (x - x_vals[0]) / h
        result = y_vals[0]
        factorial = 1.0
        term_prod = 1.0
        for k in range(1, n):
            term_prod = term_prod * (t - (k - 1))
            factorial = factorial * k
            delta = diff_table[k][0]
            result = result + term_prod * delta / factorial
        return result
    else:
        t = (x - x_vals[n - 1]) / h
        result = y_vals[n - 1]
        factorial = 1.0
        term_prod = 1.0
        for k in range(1, n):
            term_prod = term_prod * (t + (k - 1))
            factorial = factorial * k
            delta = diff_table[k][n - k - 1]
            result = result + term_prod * delta / factorial
        return result

def stirling_interpolation(data, x):
    pts = sorted(data, key=lambda pt: pt[0])
    n = len(pts) - 1
    x_vals = []
    y_vals = []
    for pt in pts:
        x_vals.append(pt[0])
        y_vals.append(pt[1])

    h = x_vals[1] - x_vals[0]
    center = n // 2
    t = (x - x_vals[center]) / h

    diff_table = build_diff_table(pts)

    shifts = [0]
    for i in range(1, n + 1):
        shifts.append(-i)
        shifts.append(i)
    new_shifts = []
    for i in range(0, n):
        new_shifts.append(shifts[i])
    shifts = new_shifts

    s_forward = y_vals[center]
    s_backward = y_vals[center]
    factorial = 1.0
    term_f = 1.0
    term_b = 1.0

    for k in range(1, n + 1):
        factorial = factorial * k
        shift_val = shifts[k - 1]

        term_f = term_f * (t + shift_val)
        term_b = term_b * (t - shift_val)

        col = diff_table[k]
        idx_mid = len(col) // 2
        delta_mid = col[idx_mid]

        if len(col) % 2 == 0:
            offset = 1
        else:
            offset = 0
        delta_side = col[idx_mid - offset]

        s_forward = s_forward + term_f * delta_mid / factorial
        s_backward = s_backward + term_b * delta_side / factorial

    return 0.5 * (s_forward + s_backward)



def bessel_interpolation(data, x):
    pts = sorted(data, key=lambda pt: pt[0])
    n = len(pts)
    x_vals = []
    y_vals = []
    for pt in pts:
        x_vals.append(pt[0])
        y_vals.append(pt[1])

    h = x_vals[1] - x_vals[0]
    diff_table = build_diff_table(pts)

    m = n // 2 - 1
    t = (x - x_vals[m]) / h

    result = 0.5 * (y_vals[m] + y_vals[m + 1])
    result += (t - 0.5) * diff_table[1][m]

    term_even = t * (t - 1) / 2
    term_odd = (t - 0.5) * t * (t - 1) / 6

    r = 1
    while True:
        k_even = 2 * r
        k_odd = k_even + 1

        if k_even < len(diff_table):
            left = m - r
            right = left + 1
            if 0 <= left and right < len(diff_table[k_even]):
                avg_val = 0.5 * (diff_table[k_even][left] + diff_table[k_even][right])
                result += term_even * avg_val

        if k_odd < len(diff_table):
            idx = m - r
            if 0 <= idx < len(diff_table[k_odd]):
                result += term_odd * diff_table[k_odd][idx]

        if k_even >= len(diff_table) and k_odd >= len(diff_table):
            break
        if m - r - 1 < 0:
            break

        term_even *= (t + r) * (t - r - 1) / ((2 * r + 2) * (2 * r + 1))
        term_odd *= (t + r) * (t - r - 1) / ((2 * r + 3) * (2 * r + 2))
        r += 1

    return result


def execute_interpolation(source, source_data, methods, x_point, gui):
    try:
        if source == 'file':
            pts = []
            with open(source_data, newline='') as f:
                reader = csv.reader(f)
                for row in reader:
                    if len(row) >= 2:
                        pts.append((float(row[0]), float(row[1])))
        elif source == 'func':
            fname = source_data['name']
            left = source_data['left']
            right = source_data['right']
            count = source_data['n']
            step = (right - left) / (count - 1)
            func = MATH_FUNCTIONS[fname]
            pts = [(left + i * step, func(left + i * step)) for i in range(count)]
        else:  
            pts = list(source_data)

        pts.sort(key=lambda p: p[0])
    except Exception as e:
        gui.show_error(f"Ошибка подготовки данных: {e}")
        return

    gui.clear_diff_table()
    gui.clear_results()

    diffs = build_diff_table(pts)
    gui.update_diff_table(diffs)

    if methods.get('lagrange'):
        try:
            y_val = lagrange_interpolation(pts, x_point)
            gui.add_result('Лагранж', f"{y_val:.6f}")
        except Exception as e:
            gui.show_error(f"Лагранж: {e}")

    if methods.get('newton_divided'):
        try:
            y_val = newton_divided(pts, x_point)
            gui.add_result('Ньютон (раздел.)', f"{y_val:.6f}")
        except Exception as e:
            gui.show_error(f"Ньютон (раздел.): {e}")

    if methods.get('newton_finite'):
        try:
            y_val = newton_finite(pts, x_point)
            gui.add_result('Ньютон (конеч.)', f"{y_val:.6f}")
        except Exception as e:
            gui.show_error(f"Ньютон (конеч.): {e}")

    if methods.get('stirling'):
        if len(pts) % 2 == 0:
            gui.show_error("Для Стирлинга нужно нечётное число узлов")
        else:
            try:
                y_val = stirling_interpolation(pts, x_point)
                gui.add_result('Стирлинг', f"{y_val:.6f}")
            except Exception as e:
                gui.show_error(f"Стирлинг: {e}")

    if methods.get('bessel'):
        if len(pts) % 2 == 1:
            gui.show_error("Для Бесселя нужно чётное число узлов")
        else:
            try:
                y_val = bessel_interpolation(pts, x_point)
                gui.add_result('Бессель', f"{y_val:.6f}")
            except Exception as e:
                gui.show_error(f"Бессель: {e}")

    try:
        gui.plot(pts, x_point)
    except AttributeError:
        pass

    gui.show_ok("Вычислено успешно")

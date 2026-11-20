from streamlit import error
from sympy import Derivative, E, Function, Integral, Limit, Product, Sum, Symbol, cos, exp, latex, log, oo, pi, sin, sqrt, symbols, tan

class MathRenderer:
    def __init__(self):
        self.setup_symbols()
    
    def setup_symbols(self):
        """初始化數學符號"""
        self.x, self.y, self.z, self.t = symbols('x y z t')
        self.v, self.a, self.F, self.m = symbols('v a F m')
        self.g, self.theta, self.omega = symbols('g theta omega')
    
    def parse_expression(self, text):
        """解析文字為 SymPy 表達式"""
        try:
            # 安全字典
            safe_dict = {
                'x': self.x, 'y': self.y, 'z': self.z, 't': self.t,
                'v': self.v, 'a': self.a, 'F': self.F, 'm': self.m,
                'g': self.g, 'theta': self.theta, 'omega': self.omega,
                'sin': sin, 'cos': cos, 'tan': tan,
                'exp': exp, 'log': log, 'sqrt': sqrt,
                'pi': pi, 'E': E, 'oo': oo,
                'Symbol': Symbol, 'Function': Function,
                'Integral': Integral, 'Derivative': Derivative,
                'Sum': Sum, 'Product': Product, 'Limit': Limit
            }
            
            expr = eval(text, {"__builtins__": {}}, safe_dict)
            return expr
        except Exception as e:
            error(f"解析錯誤: {e}")
            return None
    
    def render_latex(self, expr):
        """渲染為 LaTeX"""
        try:
            return latex(expr)
        except:
            return None



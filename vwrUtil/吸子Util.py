from numpy import array, linspace
from scipy.integrate import solve_ivp

class ChaosAttractor:
    """混沌吸子基底類別"""

    def __init__(self, params, initial_condition, t_span=(0, 100), n_steps=20000):
        self.params = params
        self.y0 = array(initial_condition, dtype=float)
        self.t_span = t_span
        self.n_steps = n_steps
        self.solution = None
        self.trajectory = None
        self.time = None

    def ode(self, t, y):
        raise NotImplementedError

    def integrate(self, method='DOP853', rtol=1e-10, atol=1e-12):
        """數值積分"""
        t_eval = linspace(self.t_span[0], self.t_span[1], self.n_steps)
        self.solution = solve_ivp(
            self.ode, self.t_span, self.y0,
            method=method, t_eval=t_eval,
            rtol=rtol, atol=atol, dense_output=True
        )
        self.time = self.solution.t
        self.trajectory = self.solution.y.T
        return self

    def get_trajectory(self):
        return self.trajectory

    def get_time(self):
        return self.time

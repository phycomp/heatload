# ~/.config/nvim/rplugin/python3/strip_alias.py
import pynvim
import re

@pynvim.plugin
class StripAlias:
    def __init__(self, nvim: pynvim.Nvim):
        self.nvim = nvim
        # 要剝離的別名清單
        self.aliases = ['np', 'plt', 'st']

    @pynvim.command("StripAlias", nargs=0, range=True, sync=True)
    def strip_alias(self, rng):
        """
        去掉指定別名前綴
        可視選取或整檔案
        """
        buf = self.nvim.current.buffer
        if rng:
            # 可視模式
            start, end = rng
            lines = buf[start-1:end]
            idx0 = start-1
        else:
            # 整檔案
            lines = buf[:]
            idx0 = 0

        pat = r'\b(' + '|'.join(map(re.escape, self.aliases)) + r')\.([A-Za-z_]\w*\b)'
        new_lines = []
        changed = 0
        for ln in lines:
            new_ln, n = re.subn(pat, r'\2', ln)
            new_lines.append(new_ln)
            changed += n

        if not changed:
            self.nvim.echo('沒有找到可剝離的別名')
            return

        # 一次取代（可 undo）
        buf[idx0:idx0+len(lines)] = new_lines
        self.nvim.echo(f'已剝離 {changed} 處別名前綴')

    @pynvim.autocmd("VimEnter", sync=True)
    def setup(self):
        self.nvim.command('nnoremap <leader>sa :StripAlias<CR>')
        self.nvim.command('vnoremap <leader>sa :StripAlias<CR>')

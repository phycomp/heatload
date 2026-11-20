vim.keymap.set('n', '<leader>ru', function()
  -- 1. 讓 Neovim 更新 rplugin.vim 資訊清單（記住新命令名稱）
  vim.cmd('UpdateRemotePlugins')
  
  -- 2. 尋找並強制結束現有的 Python3 Host 進程頻道 (Channel)
  local found_host = false
  for _, chan in ipairs(vim.api.nvim_list_chans()) do
    -- 尋找名字包含 "python3" 的遠端主機
    if chan.client and chan.client.name == "python3" then
      -- 使用 jobstop 強制關閉該進程
      vim.fn.jobstop(chan.id)
      found_host = true
      break
    end
  end
  
  -- 3. 重新載入資訊清單，確保系統映射刷新
  vim.cmd('runtime! rplugin.vim')
  
  if found_host then
    print("Python 遠端進程已重載，外掛熱更新成功！")
  else
    print("外掛資訊已更新（未偵測到執行中的 Python 進程，下次呼叫命令時將自動啟用新程式碼）")
  end
end, { desc = "免重啟熱更新 Python 遠端外掛" })

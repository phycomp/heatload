shlex —— 簡單的詞法分析
源代碼： Lib/shlex.py

shlex 類可用于編寫類似 Unix shell 的簡單詞法分析程序。通常可用于編寫“迷你語言”（如 Python 應用程序的運行控制文件）或解析帶引號的字符串。

shlex 模塊中定義了以下函數：

shlex.split(s, comments=False, posix=True)
用類似 shell 的語法拆分字符串 s。如果 comments 爲 False (默認值)，則不會解析給定字符串中的注釋 (commenters 屬性的 shlex 實例設爲空字符串)。 本函數默認工作于 POSIX 模式下，但若 posix 參數爲 False，則采用非 POSIX 模式。

備註 Since the split() function instantiates a shlex instance, passing None for s will read the string to split from standard input.
3.9 版後已棄用: 在以後的 Python 版本中，給 s 傳入 None 將觸發異常。

shlex.join(split_command)
將列表 split_command 中的詞法單元（token）串聯起來，返回一個字符串。本函數是 split() 的逆運算。

>>>
from shlex import join
print(join(['echo', '-n', 'Multiple words']))
echo -n 'Multiple words'
爲防止注入漏洞，返回值是經過 shell 轉義的（參見 quote() ）。

3.8 版新加入.

shlex.quote(s)
返回經過 shell 轉義的字符串 s 。返回值爲字符串，可以安全地用作 shell 命令行中的詞法單元，可用于不能使用列表的場合。

以下用法是不安全的：

>>>
filename = 'somefile; rm -rf ~'
command = 'ls -l {}'.format(filename)
print(command)  # executed by a shell: boom!
ls -l somefile; rm -rf ~
用 quote() 可以堵住這種安全漏洞：

>>>
from shlex import quote
command = 'ls -l {}'.format(quote(filename))
print(command)
ls -l 'somefile; rm -rf ~'
remote_command = 'ssh home {}'.format(quote(command))
print(remote_command)
ssh home 'ls -l '"'"'somefile; rm -rf ~'"'"''
這種包裝方式兼容于 UNIX shell 和 split() 。

>>>
from shlex import split
remote_command = split(remote_command)
remote_command
['ssh', 'home', "ls -l 'somefile; rm -rf ~'"]
command = split(remote_command[-1])
command
['ls', '-l', 'somefile; rm -rf ~']
3.3 版新加入.

shlex 模塊中定義了以下類：

class shlex.shlex(instream=None, infile=None, posix=False, punctuation_chars=False)
shlex 及其子類的實例是一種詞義分析器對象。 利用初始化參數可指定從哪裏讀取字符。 初始化參數必須是具備 read() 和 readline() 方法的文件/流對象，或者是一個字符串。 如果沒有給出初始化參數，則會從 sys.stdin 獲取輸入。 第二個可選參數是個文件名字符串，用于設置 infile 屬性的初始值。 如果 instream 參數被省略或等于 sys.stdin，則第二個參數默認爲 "stdin"。 posix 參數定義了操作的模式：若 posix 不爲真值（默認），則 shlex 實例將工作于兼容模式。 若運行于 POSIX 模式下，則 shlex 會盡可能地應用 POSIX shell 解析規則。 punctuation_chars 參數提供了一種使行爲更接近于真正的 shell 解析的方式。 該參數可接受多種值：默認值、False、保持 Python 3.5 及更早版本的行爲。 如果設爲 True，則會改變對字符 ();<>|& 的解析方式：這些字符將作爲獨立的詞法單元被返回（視作標點符號）。 如果設爲非空字符串，則這些字符將被用作標點符號。 出現在 punctuation_chars 中的 wordchars 屬性中的任何字符都會從 wordchars 中被刪除。 請參閱 改進的 shell 兼容性 了解詳情。 punctuation_chars 只能在創建 shlex 實例時設置，以後不能再作修改。

3.6 版更變: 加入 punctuation_chars 參數。

也參考
configparser 模塊
配置文件解析器，類似于 Windows 的 .ini 文件。

shlex 對象
shlex 實例具備以下方法：

shlex.get_token()
返回一個詞法單元。如果所有單詞已用 push_token() 堆叠在一起了，則從堆棧中彈出一個詞法單元。否則就從輸入流中讀取一個。如果讀取時遇到文件結束符，則會返回 eof`（在非 POSIX 模式下爲空字符串 `''，在 POSIX 模式下爲 ``None）。

shlex.push_token(str)
將參數值壓入詞法單元堆棧。

shlex.read_token()
讀取一個原始詞法單元。忽略堆棧，且不解釋源請求。（通常沒什麼用，只是爲了完整起見。）

shlex.sourcehook(filename)
當 shlex 檢測到源請求（見下面的 source），以下詞法單元可作爲參數，并應返回一個由文件名和打開的文件對象組成的元組。

通常本方法會先移除參數中的引號。如果結果爲絕對路徑名，或者之前沒有有效的源請求，或者之前的源請求是一個流對象（比如 sys.stdin），那麼結果將不做處理。否則，如果結果是相對路徑名，那麼前面將會加上目錄部分，目錄名來自于源堆棧中前一個文件名（類似于 C 預處理器對 #include "file.h" 的處理方式）。

結果被視爲一個文件名，并作爲元組的第一部分返回，元組的第二部分以此爲基礎調用 open() 獲得。（注意：這與實例初始化過程中的參數順序相反！)

此鉤子函數是公開的，可用于實現路徑搜索、添加文件擴展名或黑入其他命名空間。沒有對應的“關閉”鉤子函數，但 shlex 實例在返回 EOF 時會調用源輸入流的 close() 方法。

若要更明確地控制源堆棧，請采用 push_source() 和 pop_source() 方法。

shlex.push_source(newstream, newfile=None)
將輸入源流壓入輸入堆棧。如果指定了文件名參數，以後錯誤信息中將會用到。sourcehook() 內部同樣使用了本方法。

shlex.pop_source()
從輸入堆棧中彈出最後一條輸入源。當遇到輸入流的 EOF 時，內部也使用同一方法。

shlex.error_leader(infile=None, lineno=None)
本方法生成一條錯誤信息的首部，以 Unix C 編譯器錯誤標簽的形式；格式爲 '"%s", line %d: '，其中 %s 被替換爲當前源文件的名稱，%d 被替換爲當前輸入行號（可用可選參數覆蓋）。

這是個快捷函數，旨在鼓勵 shlex 用戶以標準的、可解析的格式生成錯誤信息，以便 Emacs 和其他 Unix 工具理解。

shlex 子類的實例有一些公共實例變量，這些變量可以控制詞義分析，也可用于調試。

shlex.commenters
將被視爲注釋起始字符串。從注釋起始字符串到行尾的所有字符都將被忽略。默認情況下只包括 '#'。

shlex.wordchars
可連成多字符詞法單元的字符串。默認包含所有 ASCII 字母數字和下划線。在 POSIX 模式下，Latin-1 字符集的重音字符也被包括在內。如果 punctuation_chars 不爲空，則可出現在文件名規範和命令行參數中的 ~-./*?= 字符也將包含在內，任何 punctuation_chars 中的字符將從 wordchars 中移除。如果 whitespace_split 設爲 True，則本規則無效。

shlex.whitespace
將被視爲空白符并跳過的字符。空白符是詞法單元的邊界。默認包含空格、制表符、換行符和回車符。

shlex.escape
將視爲轉義字符。僅適用于 POSIX 模式，默認只包含 '\'。

shlex.quotes
將視爲引號的字符。詞法單元中的字符將會累至再次遇到同樣的引號（因此，不同的引號會像在 shell 中一樣相互包含。）默認包含 ASCII 單引號和雙引號。

shlex.escapedquotes
quotes 中的字符將會解析 escape 定義的轉義字符。這只在 POSIX 模式下使用，默認只包含 '"'。

shlex.whitespace_split
若爲 True，則只根據空白符拆分詞法單元。這很有用，比如用 shlex 解析命令行，用類似 shell 參數的方式讀取各個詞法單元。當與 punctuation_chars 一起使用時，將根據空白符和這些字符拆分詞法單元。

3.8 版更變: punctuation_chars 屬性已與 whitespace_split 屬性兼容。

shlex.infile
當前輸入的文件名，可能是在類實例化時設置的，或者是由後來的源請求堆棧生成的。在構建錯誤信息時可能會用到本屬性。

shlex.instream
shlex 實例正從中讀取字符的輸入流。

shlex.source
本屬性默認值爲 None。 如果給定一個字符串，則會識別爲包含請求，類似于各種 shell 中的 source 關鍵字。 也就是說，緊隨其後的詞法單元將作爲文件名打開，作爲輸入流，直至遇到 EOF 後調用流的 close() 方法，然後原輸入流仍變回輸入源。Source 請求可以在詞義堆棧中嵌套任意深度。

shlex.debug
如果本屬性爲大于 1 的數字，則 shlex 實例會把動作進度詳細地輸出出來。若需用到本屬性，可閱讀源代碼來了解細節。

shlex.lineno
源的行數（到目前爲止讀到的換行符數量加 1）。

shlex.token
詞法單元的緩衝區。在捕獲異常時可能會用到。

shlex.eof
用于確定文件結束的詞法單元。在非 POSIX 模式下，將設爲空字符串 ''，在 POSIX 模式下被設爲 None。

shlex.punctuation_chars
只讀屬性。表示應視作標點符號的字符。標點符號將作爲單個詞法單元返回。然而，請注意不會進行語義有效性檢查：比如 “>>>” 可能會作爲一個詞法單元返回，雖然 shell 可能無法識別。

3.6 版新加入.

解析規則
在非 POSIX 模式下時，shlex 會試圖遵守以下規則：

不識別單詞中的引號（Do"Not"Separate 解析爲一個單詞 Do"Not"Separate）；

不識別轉義字符；

引號包裹的字符保留字面意思；

成對的引號會將單詞分離（"Do"Separate 解析爲 "Do" 和 Separate）；

如果 whitespace_split 爲 False，則未聲明爲單詞字符、空白或引號的字符將作爲單字符的詞法單元返回。若爲 True， 則 shlex 只根據空白符拆分單詞。

EOF 用空字符串（''）表示；

空字符串無法解析，即便是加了引號。

在 POSIX 模式時，shlex 將嘗試遵守以下解析規則：

引號會被剔除，且不會拆分單詞（ "Do"Not"Separate" 將解析爲單個單詞 DoNotSeparate）；

未加引號包裹的轉義字符（如 '\' ）保留後一個字符的字面意思；

引號中的字符不屬于 escapedquotes （例如，"'"），則保留引號中所有字符的字面值；

若引號包裹的字符屬于 escapedquotes （例如 '"'），則保留引號中所有字符的字面意思，屬于 escape 中的字符除外。僅當後跟後半個引號或轉義字符本身時，轉義字符才保留其特殊含義。否則，轉義字符將視作普通字符；

EOF 用 None 表示；

允許出現引號包裹的空字符串（''）。

改進的 shell 兼容性
3.6 版新加入.

shlex 類提供了與常見 Unix shell（如 bash、 dash 和 sh）的解析兼容性。爲了充分利用這種兼容性，請在構造函數中設定 punctuation_chars 參數。該參數默認爲 False，維持 3.6 以下版本的行爲。如果設爲 True，則會改變對 ();<>|& 字符的解析方式：這些字符都將視爲單個的詞法單元返回。雖然不算是完整的 shell 解析程序（考慮到 shell 的多樣性，超出了標準庫的範圍），但確實能比其他方式更容易進行命令行的處理。以下代碼段演示了兩者的差異：

 >>> import shlex
 >>> text = "a && b; c && d || e; f >'abc'; (def \"ghi\")"
 >>> s = shlex.shlex(text, posix=True)
 >>> s.whitespace_split = True
 >>> list(s)
 ['a', '&&', 'b;', 'c', '&&', 'd', '||', 'e;', 'f', '>abc;', '(def', 'ghi)']
 >>> s = shlex.shlex(text, posix=True, punctuation_chars=True)
 >>> s.whitespace_split = True
 >>> list(s)
 ['a', '&&', 'b', ';', 'c', '&&', 'd', '||', 'e', ';', 'f', '>', 'abc', ';',
 '(', 'def', 'ghi', ')']
當然，返回的詞法單元對 shell 無效，需要對返回的詞法單元自行進行錯誤檢查。

punctuation_chars 參數可以不傳入 True ，而是傳入包含特定字符的字符串，用于確定由哪些字符構成標點符號。例如：

>>>
>>> import shlex
>>> s = shlex.shlex("a && b || c", punctuation_chars="|")
>>> list(s)
['a', '&', '&', 'b', '||', 'c']
備註 如果指定了 punctuation_chars，則 wordchars 屬性的參數會是 ~-./*?=。因爲這些字符可以出現在文件名（包括通配符）和命令行參數中（如 --color=auto）。因此：
>>>
>>> import shlex
>>> s = shlex.shlex('~/a && b-c --color=auto || d *.py?',
...                 punctuation_chars=True)
>>> list(s)
['~/a', '&&', 'b-c', '--color=auto', '||', 'd', '*.py?']
不過爲了盡可能接近于 shell ，建議在使用 punctuation_chars 時始終使用 posix 和 whitespace_split ，這將完全否定 wordchars 。

為了達到最佳效果，punctuation_chars 應與 posix=True 一起設置。（注意 posix=False 是 shlex 的默認設置)。

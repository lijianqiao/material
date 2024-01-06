"""
-*- coding: utf-8 -*-
 @Author: lee
 @ProjectName: material
 @Email: lijianqiao2906@live.com
 @FileName: simpleui_conf.py.py
 @DateTime: 2024/1/2 10:36
 @Docs:  simpleui配置文件
"""
# 隐藏首页服务器信息
SIMPLEUI_HOME_INFO = False
# 使用分析，默认开启，统计分析信息只是为了更好的帮助simpleui改进，并不会读取敏感信息。并且分析数据不会分享至任何第三方。
SIMPLEUI_ANALYSIS = False
# 离线模式
SIMPLEUI_STATIC_OFFLINE = True
# 关闭Loading遮罩层，默认开启
# SIMPLEUI_LOADING = False
# 默认主题
SIMPLEUI_DEFAULT_THEME = 'orange.css'
SIMPLEUI_CONFIG = {
    'system_keep': True,
    'dynamic': False,
}

# Local Deployment Version

在 [python_github_calendar_api](https://github.com/Zfour/python_github_calendar_api) 的基础上，增加了本地部署版本，方便大家使用。

## 新增功能

1. 转换为 Web 服务, 提供 `/api` 接口;
2. 增加缓存, 默认为 3 天;
3. 更新依赖;

## 使用方法

1. 创建虚拟环境

```bash
python -m venv venv
```

2. 激活虚拟环境

```bash
source venv/bin/activate
```

3. 安装依赖

```bash
pip install -r requirements.txt
```

4. 启动服务

```bash
# 默认端口为 8080
python api/app.py

## 使用 --port 修改端口
python api/app.py --port 8888

## 使用 --cache 修改缓存时间(默认为 3 天)
python api/app.py --port 8888 --cache 5
```

## 添加自启动

```bash
sudo vim /etc/systemd/system/github_calendar.service
```

```bash
[Service]
User={your_username}
WorkingDirectory=/path/to/python_github_calendar_api
ExecStart=/path/to/python_github_calendar_api/venv/bin/python3 /path/to/python_github_calendar_api/api/app.py
Restart=always
StandardOutput=append:/path/to/python_github_calendar_api/server.log
StandardError=append:/path/to/python_github_calendar_api/server.log

[Install]
WantedBy=multi-user.target
```

## 启动服务

```bash
sudo systemctl daemon-reload
sudo systemctl start github_calendar
sudo systemctl enable github_calendar
```

## 添加代理

因为众所周知的原因, GitHub 可能访问较慢会导致 api 超时, 所以可以在自启动中添加代理

```bash
[Service]
User={your_username}
WorkingDirectory=/path/to/python_github_calendar_api
Environment="https_proxy=http://ip:port"
Environment="https_proxy=http://ip:port"
Environment="no_proxy=localhost,127.0.0.1"
ExecStart=/path/to/python_github_calendar_api/venv/bin/python3 /path/to/python_github_calendar_api/api/app.py
Restart=always
StandardOutput=append:/path/to/python_github_calendar_api/server.log
StandardError=append:/path/to/python_github_calendar_api/server.log

[Install]
WantedBy=multi-user.target
```

## 我的使用方式

为了实时性, 会缓存一天的数据, 所以使用使用 `python api/app.py --port 8888 --cache 1` 启动服务, 并在服务器上使用定时任务定时刷新数据:

```bash
0 1 * * * /usr/bin/curl http://127.0.0.1:8888/api?user=dong4j
```

## 调用服务

`GET http://ip:port/api?user={github username}`

比如我本地部署在 `192.168.31.7:7779`，那么调用方式为 `http://192.168.31.7:7779/api?user=dong4j`

![alt text](CleanShot_20241224cCLWeAHv.png)

## 配合 Hexo 使用

[前端 Hexo 插件](https://github.com/Barry-Flynn/hexo-github-calendar)

### 即将本地服务发布到公网

这个需要你有公网 IP, 如果没有就使用原版仓库部署到 Vercel 吧.

假设我部署到公网并映射的域名为: `https://github-calendar.dong4j.top:8888`

### 解决跨域问题

我的上述服务和 Hexo 部署的公网域名不一样, 会存在跨域问题, 所以需要在本地的 Nginx 转发中配置允许跨域:

```bash
# 添加 CORS 相关的头部
add_header 'Access-Control-Allow-Origin' '*' always;
add_header 'Access-Control-Allow-Methods' 'GET, POST, OPTIONS' always;
add_header 'Access-Control-Allow-Headers' 'DNT,X-CustomHeader,Keep-Alive,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Authorization' always;

# 如果需要处理预检请求（preflight request）
if ($request_method = 'OPTIONS') {
   add_header 'Access-Control-Allow-Origin' '*';
   add_header 'Access-Control-Allow-Methods' 'GET, POST, OPTIONS';
   add_header 'Access-Control-Allow-Headers' 'DNT,X-CustomHeader,Keep-Alive,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Authorization';
   # 返回 204 状态码，表示不需要发送请求体
   return 204;
}
```

### 安装依赖

```bash
npm i @barry-flynn/hexo-github-calendar --save
```

### 添加配置

在 Hexo 项目根目录的 `_config.yml` 文件最后面添加如下配置:

```yaml
# hexo-github-canlendar
githubcalendar:
  enable: true # 是否启用本插件
  enable_page: / # 要生效的页面，如 / 首页，/about/ 介绍页等
  user: shiguang-coding # GitHub 用户名
  layout:
    type: id
    name: recent-posts
    index: 0
  githubcalendar_html: '<div class="recent-post-item" style="width:100%;height:auto;padding:10px;"><div id="github_loading" style="width:10%;height:100%;margin:0 auto;display: block"><svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink"  viewBox="0 0 50 50" style="enable-background:new 0 0 50 50" xml:space="preserve"><path fill="#d0d0d0" d="M25.251,6.461c-10.318,0-18.683,8.365-18.683,18.683h4.068c0-8.071,6.543-14.615,14.615-14.615V6.461z" transform="rotate(275.098 25 25)"><animateTransform attributeType="xml" attributeName="transform" type="rotate" from="0 25 25" to="360 25 25" dur="0.6s" repeatCount="indefinite"></animateTransform></path></svg></div><div id="github_container"></div></div>'
  pc_minheight: 280px
  mobile_minheight: 0px
  # 贡献统计的梯度色卡值，可自行调整
  color: "['#ebedf0', '#a2f7af', '#6ce480', '#54ad63', '#469252', '#31753c', '#1f5f2a', '#13531f', '#084111', '#032b09', '#000000']"
  # 推荐填写你自建的API接口
  api: https://github-calendar.dong4j.top:8888/api
  # 推荐下载后使用本地文件
  # calendar_js: https://cdn.jsdelivr.net/gh/barry-flynn/hexo-github-calendar/hexo_githubcalendar.js # 在线文件，容易加载失败
  calendar_js: /js/hexo_githubcalendar.js # 本地文件，请下载到主题文件夹的source目录下
  plus_style: ""
```

---

# What's this?

此项目改造自 [python_github_calendar_api](https://github.com/Zfour/python_github_calendar_api) 仓库，原理通过 Python 获取 GitHub 的用户贡献信息，你可以部署到 Vercel 上作为 API 使用。调用方式为标准的 key-value 格式：`/api?user=Barry-Flynn`，推荐结合本文档自行部署，如果帮到你了，请给个免费的 star 鼓励支持一下我吧！

如果你有 Hexo 博客，可以搭配使用 [Barry-Flynn/hexo-github-calendar](https://github.com/Barry-Flynn/hexo-github-calendar) 插件在前端渲染贡献热力图。

## 如何部署自用的 Vercel API

### 1. 注册 Vercel

首先前往 [Vercel 官网](https://vercel.com/)，点击右上角的 sign up 进行注册。

![image.png](https://cdn.nlark.com/yuque/0/2021/png/8391485/1612880174758-059d6e22-d5ec-4478-9b8c-4a9d7c041f44.png)

极有可能遇到的 bug

若注册时提示 `Error:This user account is blocked.Contact support@vercel.com for more information.`

这是由于 `Vercel` 不支持大部分国内邮箱。可以将 `github` 账号主邮箱改为 `Gmail` 邮箱。

但是根据群友反应，将 `github` 账号主邮箱切换为 `Gmail` 以后，`Vercel` 又会提示需要使用手机号码验证。然而 `github` 并没有提供手机号码绑定的内容。

综上，建议一开始注册 `github` 账号时就使用 `Gmail` 等国外邮箱进行注册。

1. 国内访问`Gmail`的方案：

   - 直接使用 QQ 邮箱手机版，它提供 `Gmail` 的访问路线，可以直接注册并使用。

   - 使用 `Ghelper` 等浏览器插件访问。详情可以参考这篇文章：[玩转 Microsoft-Edge](https://github.com/Zfour/python_github_calendar_api/blob/master/posts/8c8df126)

2. 若是执着于当前`Github`账号，可以参考以下方案进行尝试:

   - 完成了 `Gmail` 等国外邮箱的注册，打开 [github-> 头像 ->settings->Emails](https://github.com/settings/emails)->Add email address, 并完成邮箱验证。
   - 在 Add email address 下方的 Primary email address 选项中将 `Gmail` 设置为主邮箱。

### 2. 新建项目，fork 我的项目

打开 [dashboard](https://vercel.com/dashboard) 点击新建项目的 `New Project` 按钮。点击导入第三方库。

![image.png](https://cdn.nlark.com/yuque/0/2021/png/8391485/1612949541795-cfe67df4-a443-4604-86fd-a34ea9c34bed.png)

填入俺提供的自建 API 项目地址:

```
https://github.com/Barry-Flynn/python_github_calendar_api
```

![image.png](https://cdn.nlark.com/yuque/0/2021/png/8391485/1612949577842-18cc23f8-5cf6-4f72-b892-d244d22a3089.png)

选择私有账户。点击`select`。

![image.png](https://cdn.nlark.com/yuque/0/2021/png/8391485/1612949622863-54b72f81-9add-479d-94ed-aeb125099afe.png)

选择 github 按钮然后会帮你将仓库克隆到你的 github 中，填入自定义仓库名称，如 `python_github_calendar_api`。

![image.png](https://cdn.nlark.com/yuque/0/2021/png/8391485/1612949755226-a97f3c75-8328-4630-91f2-2dd9dddf3665.png)

之后会识别出项目文件，单击 `Continue`。

![image.png](https://cdn.nlark.com/yuque/0/2021/png/8391485/1612949831064-f4b2cef1-eb64-4bac-8841-b991768ffee8.png)

`Vercel` 的 `PROJECT NAME` 可以自定义，不用太过在意，但是之后不支持修改，若要改名，只能删除 `PROJECT` 以后重建一个了。下方三个选项保持默认就好。

![image.png](https://cdn.nlark.com/yuque/0/2021/png/8391485/1612949883724-064103a2-658f-49cb-b1e6-f3a7f0a511d1.png)

此时点击 Deploy，`Vercel` 的 api 部署已经完成。

### 3. 检查 API 是否配置成功

访问**API 链接**（图中链接+'/api'+查询参数）,如我的为

https://python-github-calendar-api.vercel.app/api/?user=Barry-Flynn

如果显示数据则说明 API 配置成功。

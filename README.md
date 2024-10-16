# TimeTrackMap
利用高德地图api进行轨迹打点
## 依赖
Pandas 2.2.1

Jinja2 3.1.4
## 须知
需要用到高德地图的API，因此需要在[高德开放平台](https://lbs.amap.com/)上注册一个账号，并且在我的应用里创建一个新的应用，获得一个随机生成的key，把这个key填到Python文件中的145行中即可
xlsx文件必须有三个字段：开始时间、经度、纬度

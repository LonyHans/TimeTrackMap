import pandas as pd
from jinja2 import Environment
import os

def generate_map_html(key, time_interval, xlsx_path, phone_number, start_time, end_time):
    # 检查时间范围
    if pd.to_datetime(start_time) > pd.to_datetime(end_time):
        print("\n错误：开始时间必须小于结束时间\n")
        return  # 不生成 HTML

    # 读取 Excel 文件
    df = pd.read_excel(xlsx_path)

    # 确保开始时间字段是 datetime 格式
    df['开始时间'] = pd.to_datetime(df['开始时间'])

    # 按开始时间排序
    df = df.sort_values(by='开始时间').reset_index(drop=True)

    # 过滤出开始时间和结束时间之间的点
    df = df[(df['开始时间'] >= pd.to_datetime(start_time)) & (df['开始时间'] <= pd.to_datetime(end_time))]
    df = df[~((df['经度'] == 0) & (df['纬度'] == 0) | df['经度'].isnull() | df['纬度'].isnull())]

    # 检查过滤后的数据
    if df.empty:
        print(f"\n提示：在 {start_time} 到 {end_time} 之间没有时间点\n")
        return  # 退出函数

    # 将开始时间转换为字符串用于显示
    df['开始时间_str'] = df['开始时间'].dt.strftime('%Y-%m-%d %H:%M:%S')

    # 按经纬度对重复的点进行分组
    df['重复计数'] = df.groupby(['经度', '纬度']).cumcount()

    # 将开始时间列转换为字符串以便于 JSON 序列化
    df['开始时间'] = df['开始时间'].dt.strftime('%Y-%m-%d %H:%M:%S')

    # Jinja2 模板字符串
    template_string = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>轨迹地图</title>
        <style>
            #map {
                height: 100vh;
                width: 100%;
            }
        </style>
        <script src="https://webapi.amap.com/maps?v=1.4.15&key={{ key }}"></script>
    </head>
    <body>
        <div id="map"></div>
        <script>
            var map = new AMap.Map('map', {
                zoom: 12,
                center: [{{ points[0].经度 }}, {{ points[0].纬度 }}]
            });

            var lastMarker = null;
            var lastLine = null;

            var points = {{ points | tojson }};
            setTimeout(function() {
                points.forEach(function(point, index) {
                    setTimeout(function() {
                        // 创建标记
                        var marker = new AMap.Marker({
                            position: [point.经度, point.纬度],
                            title: '{{ phone_number }}：' + point.开始时间,  // 添加电话号码和时间到 title
                        });
                        marker.setMap(map);

                        // 动态设置偏移量，每个重复点的文本标注会向下偏移更多
                        var offsetY = 5 + 13 * point.重复计数; // 初始偏移 + 根据重复计数向下偏移

                        // 添加时间文本
                        var label = new AMap.Text({
                            text: '{{ phone_number }}：' + point.开始时间,
                            position: [point.经度, point.纬度], // 与标记位置相同
                            offset: new AMap.Pixel(0, offsetY), // 根据偏移量调整位置
                            style: {
                                'background-color': 'white',
                                'padding': '1px',
                                'font-size': '9px',
                                'color': 'black',
                                'border': 'none', // 去掉边框
                                'border-radius': '0', // 确保是直角
                                'box-shadow': 'none' // 去掉阴影
                            }
                        });
                        label.setMap(map); // 添加文本标注到地图
                        
                        // 画线
                        if (lastMarker) {
                            var line = new AMap.Polyline({
                                path: [lastMarker.getPosition(), marker.getPosition()],
                                strokeColor: 'rgba(255, 0, 0, 0.6)',  // 透明的亮红色
                                strokeWeight: 8,      // 增加线条宽度
                                showDir: true,        // 显示方向
                                dirColor: '#FFFFFF',  // 更亮的白色
                                dirOpacity: 1,        // 设置箭头的透明度
                            });
                            line.setMap(map);
                            
                            // 更新上一条线为透明的亮蓝色，但最后一条线保持为红色
                            if (lastLine) {
                                lastLine.setOptions({ strokeColor: 'rgba(0, 0, 255, 0.6)' });
                            }
                            lastLine = line; // 更新上一条线
                        }

                        lastMarker = marker; // 更新最后一个标记
                    }, index * {{ time_interval }}); // 每个点之间的间隔
                });
            }, 2000); // 延迟 2 秒后开始打点
        </script>
    </body>
    </html>
    """

    # 创建 Jinja2 环境
    env = Environment()

    # 渲染 HTML
    html_content = env.from_string(template_string).render(
        points=df.to_dict(orient='records'), 
        key=key, 
        time_interval=time_interval, 
        phone_number=phone_number
    )

    # 输出 HTML 文件
    output_file = '轨迹地图.html'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)

    print(f"\n地图 HTML 文件已生成：{output_file}\n")

if __name__ == "__main__":

    while True:

        key = ""    # 高德地图 API Key
        print("\n--TimeTrackMap3.0--\n")

        # 获取用户输入
        while True:
            xlsx_path = input("\n请输入Excel文件路径：").strip().replace('"', '')  # Excel 文件路径
            if not os.path.exists(xlsx_path):
                print("文件路径不正确！请重新输入正确的路径！")
            else:
                break  # 路径正确，退出循环

        phone_number = input("\n请输入电话号码：")  # 设置电话号码
        
        while True:
            start_time = input("\n请输入开始时间（格式：2024-9-1 9:00:00）：")  # 设置开始时间
            end_time = input("\n请输入结束时间（格式：2024-9-30 10:00:00）：")  # 设置结束时间
            try:
                start_dt = pd.to_datetime(start_time)  # 检查开始时间格式
                end_dt = pd.to_datetime(end_time)  # 检查结束时间格式
                if start_dt >= end_dt:
                    print("错误：开始时间必须小于结束时间，请重新输入。")
                    continue  # 开始时间不小于结束时间，继续循环
                break  # 时间格式正确且开始时间小于结束时间，退出循环
            except ValueError:
                print("时间格式不正确，请按照 'YYYY-MM-DD HH:MM:SS' 格式重新输入。")
        
        while True:
            time_interval = int(input("\n请输入打点时间间隔（毫秒）："))  # 打点时间间隔
            if time_interval <= 0 or time_interval >= 10000:
                print("时间间隔必须大于0且小于10000！请重新输入。")
            else:
                break  # 时间间隔有效，退出循环

        # 调用生成地图 HTML 的函数
        generate_map_html(key, time_interval, xlsx_path, phone_number, start_time, end_time)

        end = input("\n继续请输入y，退出请输入n：").strip().lower()
        if end != 'y':
            print("退出程序")
            break

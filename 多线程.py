import time
import requests
import re
import pandas as pd
from PyQt5.Qt import *
from UI.collection_ui import Ui_Form
import datetime

class Worker(QThread, Ui_Form, QWidget):
    finished = pyqtSignal() # 完成信号
    progress = pyqtSignal(dict) # 执行信号
    def __init__(self):
        super().__init__()

    def run(self):
        # 耗时任务
        self.start_filter()

    # 获取商品数据
    def start_filter(self):
        try:
            # 获取代理IP
            proxy = self.get_ip()
            print('已获取代理ip......开始执行......')
            # 读取商品数据
            with open('../resource/等待过滤_数据.txt', 'r') as f:
                shop_data_list = f.readlines()
            shop_data_list = [s.strip() for s in shop_data_list]
            # 提取ID
            url_list = []
            # key列表
            temp_verifyFp = [self.key_1_edi.text(), self.key_2_edi.text(), self.key_3_edi.text(), self.key_4_edi.text(),
                             self.key_5_edi.text(), self.key_6_edi.text(), self.key_7_edi.text(), self.key_8_edi.text()]
            verifyFp = []
            for key in temp_verifyFp:
                if key:
                    verifyFp.append(key)
            # 遍历网站 与 ID 进行拼接
            index = 0
            for item in shop_data_list:
                url_list.append(
                    f'https://ec.snssdk.com/product/fxgajaxstaticitem?&verifyFp={verifyFp[index]}&b_type_new=0&device_id=0&is_outside=1&preview=0&is_native_h5=1&is_in_app=1&id=' + item[
                                                                                                                                                                                    -19:])
                if index < len(verifyFp) - 1:
                    index += 1
                else:
                    index = 0
            # 爬取数据并进行解析
            result_output = {'商品名称': [], '商品价格': [], '佣金额': [], '佣金率': [], '发货类型': [], '保质期': [],
                             '贮存条件': [], '一级类目': [],
                             '二级类目': [],
                             '三级类目': [], '四级类目': [], '链接': []}

            # 从这里开始循环爬取数据
            for num, url in enumerate(url_list):
                try:
                    print(f'正在采集第{num + 1}个商品..........')
                    headers = {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.5359.95 Safari/537.36',
                        'Referer': f'https://haohuo.jinritemai.com/views/product/detail?id={url[-19:]}'
                    }

                    # requests请求数据
                    # 代理IP 请求
                    response = requests.get(url, headers=headers, proxies=proxy, timeout=10)
                    spid = url[-19:]
                    print(f'正在获取ID为:{spid}的 《抖音信息》')
                    # 本地IP 请求
                    # response = requests.get(url, headers=headers, timeout=10)
                    # 商品名称
                    spmc = re.findall('"mobile":"","name":"(.*?)[",&]', response.text)
                    # 如果能采集到商品信息才进行数据写入
                    if spmc:
                        result_output['商品名称'].append(spmc)
                        print('当前商品------>', str(spmc).replace("['", '').replace("']", ''))
                        # 获取星选对应的商品信息汇总 再逐一进行解析
                        yongjin_data = self.get_spyj(spid)
                        # 佣金率
                        if yongjin_data['spyj']:
                            result_output['佣金率'].append(yongjin_data['spyj'])
                        else:
                            result_output['佣金率'].append('None')
                        # 佣金金额
                        if yongjin_data['spyje']:
                            result_output['佣金额'].append(yongjin_data['spyje'])
                        else:
                            result_output['佣金额'].append('None')
                        # 商品价格
                        if yongjin_data['spjg']:
                            result_output['商品价格'].append(yongjin_data['spjg'])
                        else:
                            result_output['商品价格'].append('None')
                        # 判断发货时间类型
                        item1 = re.findall('"sku_delay_desc":"(\d*)小时内发货"', response.text)
                        item2 = re.findall('"sku_presell_delay_desc":"(\d*)天内发货"', response.text)
                        item3 = re.findall('"detail_delay_desc":"(\d*)小时内发货"', response.text)
                        item4 = re.findall('"detail_delay_desc":"最晚(\d*)天内发货"', response.text)
                        item5 = re.findall('(.*?)商品已失效(.*?)', response.text)
                        item6 = re.findall('(.*?)商品已下架(.*?)', response.text)
                        item7 = re.findall('"detail_delay_desc":"最晚(\d*)小时内发货"', response.text)
                        item8 = re.findall('"detail_delay_desc":"最晚(\d*)月(\d*)日发货"', response.text)
                        item9 = re.findall('"status":400,"msg":"因(.*?)，该商品暂无法购买"', response.text)
                        item10 = re.findall('"detail_delay_desc":"(.*?)明天发货"', response.text)
                        item11 = self.get_spsq(spid)

                        if item11:
                            result_output['发货类型'].append('抖客400')
                        elif item1 and item2:
                            result_output['发货类型'].append('同时存在2种')
                        elif item2 or item4 or item7 or item8 or item9 :
                            result_output['发货类型'].append('预售')
                        elif item1 or item3 or item10:
                            result_output['发货类型'].append('非预售')
                        elif item5:
                            result_output['发货类型'].append('失效')
                        elif item6:
                            result_output['发货类型'].append('下架')
                        else:
                            print('当前未知产品数据----->', response.text)
                            result_output['发货类型'].append('未知')
                        # 保质期
                        bzq = re.findall('"保质期":"(.*?)[",&]', response.text)
                        if bzq:
                            result_output['保质期'].append(bzq)
                        else:
                            result_output['保质期'].append('None')
                        # 贮存条件
                        zctj = re.findall('"贮存条件":"(.*?)[",&]', response.text)
                        if zctj:
                            result_output['贮存条件'].append(zctj)
                        else:
                            result_output['贮存条件'].append('None')
                        # 一级类目
                        first_type = re.findall('"first_cname":"(.*?)[",&]', response.text)
                        if first_type:
                            result_output['一级类目'].append(first_type)
                        else:
                            result_output['一级类目'].append('None')
                        # 二级类目
                        second_type = re.findall('"second_cname":"(.*?)[",&]', response.text)
                        if second_type:
                            result_output['二级类目'].append(second_type)
                        else:
                            result_output['二级类目'].append('None')
                        # 三级类目
                        third_type = re.findall('"third_cname":"(.*?)[",&]', response.text)
                        if third_type:
                            result_output['三级类目'].append(third_type)
                        else:
                            result_output['三级类目'].append('None')
                        # 四级类目
                        fourth_type = re.findall('"fourth_cname":"(.*?)[",&]', response.text)
                        if fourth_type:
                            result_output['四级类目'].append(fourth_type)
                        else:
                            result_output['四级类目'].append('None')
                        # 链接
                        item_url = "https://haohuo.jinritemai.com/views/product/detail?id=" + url[-19:]
                        if item_url:
                            result_output['链接'].append(item_url)
                        else:
                            result_output['链接'].append('None')
                        print(f'第{num + 1}个商品采集成功!')
                        print('-' * 50)
                    # 商品信息获取失败 将当前url进行保存
                    # 商品信息获取失败 更换代理IP继续后面采集(当前失败商品无法重新采集，已做保存处理)
                    else:
                        print('商品信息获取失败!更换代理IP继续后面采集(当前失败商品无法重新采集，已做保存处理)', url)
                        with open('../resource/采集失败_数据.txt', 'a+') as f:
                            fail_url = "https://haohuo.jinritemai.com/views/product/detail?id=" + url[-19:]
                            f.write(fail_url + "\n")
                        # 更新代理IP
                        proxy = self.get_ip()
                        print('已更新代理ip......继续执行!')
                except Exception as e:
                    print(e)
                    print('IP过期,更换代理IP继续后面采集(当前失败商品无法重新采集，已做保存处理)')
                    with open('../resource/采集失败_数据.txt', 'a+') as f:
                        f.write(url + "\n")
                    proxy = self.get_ip()
                    print('已更新代理ip......继续执行!')
                # 当前获取数结束，发送dict数据信号
                print(result_output)
                self.progress.emit(result_output)
            # 任务结束 发送完成信号
            self.finished.emit()
        except Exception as e:
            print('start_filter内出了问题，请检查！')
            print(e)

    # 获取 星选 佣金 信息
    def get_spyj(self, spid):
        data_list = {
            'spyj': '',
            'spyje': '',
            'spjg' : ''
        }
        url = f'https://douke.reduxingxuan.com/api/douke/view?product_id={spid}'
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.5359.95 Safari/537.36',
            'Referer': f'https://douke.reduxingxuan.com/detail?id=3{spid}'
        }
        temp_response = requests.get(url, headers=headers, timeout=10)
        print(f'正在获取ID为:{spid}的 《星选信息佣金信息》')
        data_list['spyj'] = re.findall('"cos_ratio":(.*?),"', temp_response.text)
        data_list['spyje'] = re.findall('"cos_fee":(.*?),"', temp_response.text)
        data_list['spjg'] = re.findall('"coupon_price":(.*?),"', temp_response.text)
        return data_list

    # 获取 星选 推广权限 信息
    def get_spsq(self, spid):
        # 推广位ID
        adid = self.tgid_edi.text()
        authori_zation = self.tgsqm_edi.text()
        url = f'https://douke.reduxingxuan.com/api/douke/click_url?product_id={spid}&adid={adid}'
        headers = {
            'Authori-zation': f'{authori_zation}',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/537.36',
        }
        response = requests.get(url, headers=headers)
        print(f'正在获取ID为:{spid}的 《星选信息推广权限信息》')
        print('-' * 50)
        sq_code = re.findall('"status":(\d*),"', response.text)
        if response.text:
            if sq_code:
                if not sq_code[0] == '200':
                    return True

    # 获取代理IP 测试代理IP
    def get_ip(self):
        try:
            url = f'http://api.tianqiip.com/getip'
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.5359.95 Safari/537.36',
            }
            params = {
                # 'secret': 'wgt84asv86j9d2zz', #我自己的
                'secret': 'fjl2yl7hu15ghhox',  # 他的
                'num': '1',
                'type': 'txt',
                'port': '2',
                'time': '3',
                'mr': '1',
                # 'sign': '89627f1dcd137332605f176d51db382f' #我自己的
                'sign': '7b60b2546feb0781bfcbba3ab16d38c8'  # 他的
            }
            response = requests.get(url, headers=headers, params=params)
            ip = re.findall('(.*?):', response.text)
            port = re.findall(':(\d*)', response.text)

            # 请求地址
            targetUrl = "https://ip.tool.lu/"
            #
            # #代理服务器
            proxyHost = None
            proxyPort = None
            for IP, PORT in zip(ip, port):
                proxyHost = IP
                proxyPort = PORT
            # 非账号密码验证
            proxyMeta = "http://%(host)s:%(port)s" % {
                "host": proxyHost,
                "port": proxyPort,
            }
            proxies = {
                "https": proxyMeta
            }
            # 测试IP
            resp = requests.get(targetUrl, proxies=proxies, timeout=10)
            print(resp.text)
            print('正在获取代理ip中....延迟5秒执行！')
            time.sleep(5)
            return proxies
        except Exception as e:
            print(e)


class Window(QWidget, Ui_Form):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.creat_table()

    # 多线程任务
    def taskstart(self):
        # 验证检查
        time.sleep(1)
        self.lock_program()
        time.sleep(2)
        self.start_collection_btn.setEnabled(False)
        self.worker = Worker()
        self.worker.progress.connect(self.updateProgress)
        self.worker.finished.connect(self.taskfinished)
        self.worker.start()

    # 任务更新
    def updateProgress(self, value):
        self.write_table(value)
        print('任务更新数据:', value)

    # 任务完成
    def taskfinished(self):
        print('任务结束')

    # 生成表格
    def creat_table(self):
        try:
            # 表头颜色
            self.result_amonut_table.horizontalHeader().setStyleSheet("QHeaderView::section{background:lightgreen;}")
            # 隐藏垂直标题
            self.result_amonut_table.verticalHeader().setVisible(False)

            # 设置表头
            result_amount_table_header = [
                {"filed": "spmc", "text": "商品名称", "width": 400},
                {"filed": "spmc", "text": "商品价格", "width": 60},
                {"filed": "spmc", "text": "佣金额", "width": 60},
                {"filed": "spmc", "text": "佣金率", "width": 60},
                {"filed": "fhlx", "text": "发货类型", "width": 60},
                {"filed": "bzq", "text": "保质期", "width": 60},
                {"filed": "zctj", "text": "贮存条件", "width": 60},
                {"filed": "one_type", "text": "一级类目", "width": 120},
                {"filed": "two_type", "text": "二级类目", "width": 120},
                {"filed": "three_type", "text": "三级类目", "width": 120},
                {"filed": "four_type", "text": "四级类目", "width": 120},
                {"filed": "four_type", "text": "链接", "width": 120},
            ]

            for idx, info in enumerate(result_amount_table_header):
                item = QTableWidgetItem()
                item.setText(info['text'])
                self.result_amonut_table.setHorizontalHeaderItem(idx, item)
                self.result_amonut_table.setColumnWidth(idx, info['width'])
        except Exception as e:
            print(e)

    # 将数据写入表格
    def write_table(self, result_output):
        try:
            # 先清空表格
            self.result_amonut_table.setRowCount(0)
            # 重新创建表格
            self.result_amonut_table.setRowCount(20000)
            self.result_amonut_table.setColumnCount(12)
            self.creat_table()
            # 获取数据
            self.data = result_output

            # 输出匹配信息到表格
            for column, items in enumerate(self.data.values()):
                for row, item in enumerate(items):
                    cell = QTableWidgetItem(str(item).replace("['", '').replace("']", ''))
                    self.result_amonut_table.setItem(row, column, cell)
                    # 不可编辑
                    # cell.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
                    # 居中显示
                    cell.setTextAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
            self.spsl_label.setText(str(len(self.data['商品名称'])))
        except Exception as e:
            print('是这里',e)

    # 导出数据到cvs
    def export_csv(self):
        try:
            # 创建一个空的DataFrame
            df = pd.DataFrame(
                columns=['商品名称', '商品价格', '佣金额', '佣金率', '发货类型', '保质期', '贮存条件', '一级类目',
                         '二级类目', '三级类目',
                         '四级类目', '链接'])

            # 遍历data字典中的子列表
            for i in range(len(self.data['商品名称'])):
                # 将子列表的元素添加到DataFrame中
                df.loc[i] = [self.data['商品名称'][i], self.data['商品价格'][i], self.data['佣金额'][i],
                             self.data['佣金率'][i],
                             self.data['发货类型'][i],
                             self.data['保质期'][i],
                             self.data['贮存条件'][i],
                             self.data['一级类目'][i],
                             self.data['二级类目'][i],
                             self.data['三级类目'][i],
                             self.data['四级类目'][i],
                             self.data['链接'][i]]

            df.to_csv('过滤完成数据.csv', index=False)  # 将DataFrame导出为CSV文件，不包括行索引
            print('已将数据导出表格,请到主程序目录下查看')
        except Exception as e:
            print(e)

    # 时间锁
    def lock_program(self):
        # 定义起始时间和使用期限
        start_date = datetime.datetime(2023, 3, 2, 0, 0)
        duration_days = 7

        # 定义获取时间函数，使用互联网时间
        def get_current_time():
            try:
                response = requests.get('http://www.baidu.com', timeout=10)
                current_time_str = response.headers['date']
                current_time = datetime.datetime.strptime(current_time_str, '%a, %d %b %Y %H:%M:%S %Z')
            except:
                raise Exception('非连网状态无法采集')
            return current_time

        # 获取当前时间
        current_time = get_current_time()
        # 判断当前时间是否在使用期限内
        if current_time < start_date or current_time >= start_date + datetime.timedelta(days=duration_days):
            exit()
        # 可以开始使用程序了

    # 获取代理IP 测试代理IP
    def get_ip(self):
        try:
            url = f'http://api.tianqiip.com/getip'
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.5359.95 Safari/537.36',
            }
            params = {
                # 'secret': 'wgt84asv86j9d2zz', #我自己的
                'secret': 'fjl2yl7hu15ghhox',  # 他的
                'num': '1',
                'type': 'txt',
                'port': '2',
                'time': '3',
                'mr': '1',
                # 'sign': '89627f1dcd137332605f176d51db382f' #我自己的
                'sign': '7b60b2546feb0781bfcbba3ab16d38c8'  # 他的
            }
            response = requests.get(url, headers=headers, params=params)
            ip = re.findall('(.*?):', response.text)
            port = re.findall(':(\d*)', response.text)

            # 请求地址
            targetUrl = "https://ip.tool.lu/"
            #
            # #代理服务器
            proxyHost = None
            proxyPort = None
            for IP, PORT in zip(ip, port):
                proxyHost = IP
                proxyPort = PORT
            # 非账号密码验证
            proxyMeta = "http://%(host)s:%(port)s" % {
                "host": proxyHost,
                "port": proxyPort,
            }
            proxies = {
                "https": proxyMeta
            }
            # 测试IP
            resp = requests.get(targetUrl, proxies=proxies, timeout=10)
            print(resp.text)
            print('正在获取代理ip中....延迟5秒执行！')
            time.sleep(5)
            return proxies
        except Exception as e:
            print(e)


if __name__ == '__main__':
    import sys

    app = QApplication(sys.argv)
    window = Window()
    window.show()
    sys.exit(app.exec_())

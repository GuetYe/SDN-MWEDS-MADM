'''
Author: 孙石泉 786721684@qq.com
Date: 2024-01-21 10:18:49
LastEditTime: 2024-04-01 22:42:40
LastEditors: 孙石泉
Description: 客户端上传文件/文件夹的请求
FilePath: \SD-UANET_load_balance\client\client_operation\client_request.py
'''



import sys
import platform
import re
import subprocess
from scapy.layers.inet import IP, TCP
from scapy.sendrecv import send
import random

my_client_platform = platform.system()  # 读取客户端平台类型

if my_client_platform == 'Windows':  # Windows平台下加载模块的方法
    sys.path.append('../')
    from client_operation.file_utils import File_Utils
    import config.setting as setting
elif my_client_platform == 'Linux':  # Linux平台下加载模块的方法
    sys.path.append('../Client_Project/client_operation')
    sys.path.append('../Client_Project/config')
    from client_operation.file_utils import File_Utils
    import config.setting as setting


class ClientRequest:
    def __init__(self, host_ip) -> None:
        self.src_ip = host_ip
        self.dst_ip = setting.CONTROLLER_IP[0]

    @staticmethod
    def get_host_IP():
        """
        # description: 获取主机的IP(Linux)
        # return {*} 主机IP
        """
        # shell=True ： 执行的命令当初一个字符串
        original_data = subprocess.check_output("hostname -I", shell=True).decode('utf-8')
        # re.search、group(0)：返回第1个匹配到的IP地址
        host_ip = re.search('\d+.\d+.\d+.\d+', original_data).group(0)

        return host_ip

    def request_save(self, file_path):
        # 1.获得文件信息
        file_name = File_Utils.file_name(file_path)
        file_size = File_Utils.file_size(file_path)

        # 2.构造IP数据包
        ip_packet = IP()
        ip_packet.src = self.src_ip
        ip_packet.dst = self.dst_ip

        # 3.构造TCP负载数据
        data = '[ClientRequest(file_name=%s,file_size=%s)]' % (file_name, file_size)

        # 4.将TCP负载数据添加到IP数据包中
        tcp_packet = TCP()
        ip_packet.payload = tcp_packet / data
        send(ip_packet)  # 广播数据。可以使用"iface"形参指定网卡发送。show_device_interfaces()函数可以显示所有网卡


if __name__ == '__main__':
    # IP包源地址为10.0.0.202，目的地址：控制器
    client_ = ClientRequest('10.0.0.1')
    # 通过TCP协议发送文件
    client_.request_save('D:/test_iso1.iso')
'''
Author: 孙石泉 786721684@qq.com
Date: 2024-01-21 10:23:16
LastEditTime: 2024-04-01 22:40:49
LastEditors: 孙石泉
Description: 接收控制器发过来的文件分割方案
FilePath: \SD-UANET_load_balance\client\client_operation\receive_result.py
'''



import sys
import platform
import re

my_client_platform = platform.system()  # 读取客户端平台类型
if my_client_platform == 'Windows':  # Windows平台下加载模块的方法
    sys.path.append('../')
    import config.setting as setting
    from scapy.all import sniff
elif my_client_platform == 'Linux':  # Linux平台下加载模块的方法
    sys.path.append('../Client_Project/config')
    from scapy.sendrecv import sniff
    import config.setting as setting


class ReceivePacket:
    def __init__(self) -> None:
        self.receive_dict = {}

    def parsing_packet(self, packet):
        eth_src_mac = packet.src
        print("<receive_result> -->  eth_src_mac:", eth_src_mac)
        # 来自控制器的包
        if eth_src_mac == setting.CONTROLLER_MAC:
            arp_src_ip = packet.payload.psrc
            print("<receive_result> -->  arp_src_ip:", arp_src_ip)
        else:
            return
        if arp_src_ip in setting.CONTROLLER_IP:  # 必须筛选包的源IP为控制器
            arp_packet_load = str(packet.payload.load)
            # 使用re模块搜索结果
            result = re.findall(pattern='\{.+\}', string=arp_packet_load, )
            if result:
                self.receive_dict = eval(result[0])
            else:
                print("<receive_result.py> The split result returned by the controller cannot be found")
                self.receive_dict = None

    def catch_pack(self):
        self.receive_dict = {}  # 清空属性
        # count等0表示一直监听，要想监听数据包，需要首先安装winpcap或npcap  iface=setting.SNIFF_IFACE,
        # 一定要指定接口iface才可以接受包

        sniff(filter='arp', prn=self.parsing_packet, count=0, timeout=setting.SNIFF_TIMEOUT, iface="WLAN")


if __name__ == '__main__':
    a = ReceivePacket()
    a.catch_pack()
    print(a.receive_dict)
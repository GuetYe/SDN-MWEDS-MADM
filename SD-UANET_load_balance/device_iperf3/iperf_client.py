'''
Author: 孙石泉 786721684@qq.com
Date: 2023-07-20 20:49:58
LastEditTime: 2024-05-09 21:58:01
LastEditors: 孙石泉
Description: 
FilePath: \SD-UANET_load_balance-24-4-19\device_iperf3\iperf_client.py
'''


import subprocess
import time
import random



server_host_ip = "192.168.2.23"





def run_iperf(command):
    try:
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        output, error = process.communicate()
        return output.decode(), error.decode()
    except Exception as e:
        return None, str(e)

def send_data_flow(server_address, port, duration, rate):
    iperf_command = f"iperf3 -u -c {server_address} -p {port} -b {rate} -t {duration} -i 1"
    return run_iperf(iperf_command)

def main():
    # server_addresses = [server_h1_ip, server_h2_ip, server_h3_ip]
    server_ports = "5201"  # 假设所有服务器都在相同的端口上运行iperf3
    data_rate = ["10K", "200K", "600K", "1M", "2M", "5M"]  # 每秒发送数据流的速率

    flow_period = 60  # 发流周期

    while True:
        # 配置iperf发流的参数
        server_address = server_host_ip
        rate = random.choice(data_rate)

        print(f"Sending data flow to {server_address} for {flow_period} seconds at {rate}")
        output, error = send_data_flow(server_address, server_ports, flow_period, rate)
        print("Client output:")
        print(output)

        # print(f"Sleeping for {flow_period} seconds...")
        # time.sleep(flow_period) 

if __name__ == "__main__":
    main()





